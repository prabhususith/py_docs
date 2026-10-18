"""
Enterprise Data Science Core: Pandas GroupBy, Multi-Metric Aggregations & Relational Merges
=============================================================================================

This module provides an exhaustive, production-grade implementation of high-throughput data
aggregation, relational joins, multi-index restructuring, and cross-tabulations in Pandas,
benchmarked and architecturally contrasted against Node.js (TypeScript) and PHP (Laravel).

Architectural Polyglot Comparison:
----------------------------------
1. GroupBy Aggregation Pipeline:
   - Node.js (TypeScript):
     Requires manual reduction: `data.reduce((acc, row) => { ... }, {})`. For multi-metric
     aggregations (mean, max, median), engineers must maintain running sums, counters, and
     sorted arrays per group key. High heap churn and garbage collection pressure under large datasets.
   - PHP (Laravel):
     `collect($records)->groupBy('department')->map(fn($group) => ['avg' => $group->avg('salary'), ...])`.
     Laravel creates nested `Illuminate\\Support\\Collection` instances for every group key, allocating
     Zend hash tables (`zend_array`) and `zval` containers per record, leading to 10x-50x memory bloat.
   - Python (Pandas):
     Utilizes Cython-optimized grouping engines (`GroupBy` / `hash_grouper`). Rows are mapped to integer
     group codes (`group_info`), allowing vector kernels to aggregate columnar NumPy arrays in contiguous
     C memory with SIMD speed without materializing Python sub-lists.

2. Relational Merges (Joins):
   - Node.js:
     Typically performed via nested lookups: `records.map(r => ({ ...r, dept: deptMap.get(r.deptId) }))`.
     Requires manual construction of Map indices. Outer joins require custom set difference logic.
   - PHP:
     Accomplished via Eloquent eager loading (`$emp->load('department')`) or database-level SQL joins.
     In-memory collections require custom Cartesian product or key-matching pipelines.
   - Pandas:
     `pd.merge(left, right, on='key', how='inner'|'left'|'right'|'outer', indicator=True)` executes
     hash joins or sort-merge joins directly in C/Cython, handling composite keys, overlapping column
     suffixes, and merge diagnostics natively.

Official Documentation References:
- Pandas DataFrame.groupby:
  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.groupby.html
- Pandas DataFrame.agg:
  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.agg.html
- Pandas DataFrame.merge:
  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html
- Pandas Concat:
  https://pandas.pydata.org/docs/reference/api/pandas.concat.html
- Pandas Pivot Table:
  https://pandas.pydata.org/docs/reference/api/pandas.pivot_table.html
- Pandas Crosstab:
  https://pandas.pydata.org/docs/reference/api/pandas.crosstab.html
"""

from __future__ import annotations

import sys
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Configure UTF-8 encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()


# ==============================================================================
# 1. Dataset Generation: Enterprise Organization & Workforce Schemas
# ==============================================================================


def create_enterprise_workforce_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Construct realistic relational datasets: Employees, Departments, and Engineering Projects.
    Contains intentional unmatched records to demonstrate left, right, and outer join semantics.
    """
    employees_data = {
        "employee_id": [101, 102, 103, 104, 105, 106, 107, 108],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Evan", "Fiona", "George", "Hannah"],
        "dept_id": [1, 1, 2, 2, 3, 3, 99, 2],  # dept_id 99 has no department record (unmatched)
        "salary": [135000, 115000, 160000, 142000, 98000, 105000, 120000, 150000],
        "tenure_years": [4.5, 2.0, 7.0, 5.5, 1.5, 3.0, 2.5, 6.0],
        "rating": [4.8, 3.9, 4.9, 4.2, 3.5, 4.0, 3.8, 4.7],
        "remote": [True, True, False, True, False, False, True, False],
    }

    departments_data = {
        "dept_id": [1, 2, 3, 4],  # dept_id 4 has no employees (unmatched)
        "dept_name": ["Frontend Engineering", "AI Platform", "Site Reliability", "Security Ops"],
        "budget_usd": [1200000, 3500000, 1800000, 1500000],
        "cost_center": ["CC-101", "CC-202", "CC-303", "CC-404"],
    }

    contractors_data = {
        "employee_id": [201, 202],
        "name": ["Ian", "Julia"],
        "dept_id": [2, 3],
        "salary": [140000, 110000],
        "tenure_years": [1.0, 0.8],
        "rating": [4.1, 4.3],
        "remote": [True, True],
    }

    df_employees = pd.DataFrame(employees_data)
    df_departments = pd.DataFrame(departments_data)
    df_contractors = pd.DataFrame(contractors_data)

    return df_employees, df_departments, df_contractors


# ==============================================================================
# 2. Multi-Metric GroupBy & Aggregations
# ==============================================================================


def compute_department_aggregations(
    df_employees: pd.DataFrame, df_departments: pd.DataFrame
) -> pd.DataFrame:
    """
    Perform multi-metric aggregations across employee departments with flattened column headers.

    Polyglot Comparison:
    - Node.js:
      Requires mapping employee records into buckets and performing iterative math:
      ```typescript
      const groups = new Map<number, Employee[]>();
      for (const e of employees) {
          if (!groups.has(e.deptId)) groups.set(e.deptId, []);
          groups.get(e.deptId)!.push(e);
      }
      const summary = Array.from(groups.entries()).map(([deptId, emps]) => ({
          deptId,
          salaryMean: emps.reduce((s, x) => s + x.salary, 0) / emps.length,
          salaryMax: Math.max(...emps.map(x => x.salary)),
          tenureMedian: calculateMedian(emps.map(x => x.tenure)),
      }));
      ```
    - PHP (Laravel):
      ```php
      $summary = $employees->groupBy('dept_id')->map(function ($group) {
          return [
              'salary_mean' => $group->avg('salary'),
              'salary_max'  => $group->max('salary'),
              'count'       => $group->count(),
              'tenure_median' => $group->median('tenure_years'),
          ];
      });
      ```
    - Pandas:
      Single-pass vector aggregation using optimized C kernels. MultiIndex columns are
      produced and cleanly flattened for production API consumption.
    """
    # Merge employee records with department names first
    merged = df_employees.merge(df_departments, on="dept_id", how="inner")

    # Multi-metric dictionary mapping column -> list of aggregation functions
    agg_spec = {
        "salary": ["count", "mean", "max"],
        "tenure_years": ["median"],
        "rating": ["mean"],
    }

    # Group by dept_name and compute aggregations
    grouped = merged.groupby("dept_name").agg(agg_spec)

    # Flatten hierarchical MultiIndex columns: e.g. ('salary', 'mean') -> 'salary_mean'
    grouped.columns = [f"{col}_{stat}" for col, stat in grouped.columns]

    # Reset index so dept_name becomes a standard column
    result_df = grouped.reset_index()

    # Round floating-point metrics for clean presentation
    result_df["salary_mean"] = result_df["salary_mean"].round(2)
    result_df["rating_mean"] = result_df["rating_mean"].round(2)

    return result_df


# ==============================================================================
# 3. Relational Merges (Inner, Left, Outer, and Diagnostics)
# ==============================================================================


def perform_relational_merges(
    df_employees: pd.DataFrame, df_departments: pd.DataFrame
) -> Dict[str, pd.DataFrame]:
    """
    Demonstrate inner, left, and full outer joins, including `_merge` indicator diagnostics.

    Polyglot Comparison:
    - Node.js:
      Outer joins require building Set difference logic:
      Find unmatched keys in left set vs right set and construct synthetic null rows.
    - PHP:
      Typically offloaded to SQL (`LEFT JOIN` / `FULL OUTER JOIN`). In-memory collection outer joins
      require complex nested collection loops with high cognitive and runtime overhead.
    - Pandas:
      Native relational algebra via `how='inner'|'left'|'right'|'outer'`.
      `indicator=True` injects a categorical `_merge` column with values:
      `left_only`, `right_only`, or `both`.
    """
    # 1. Inner Join: Only rows where dept_id exists in BOTH tables
    inner_df = pd.merge(df_employees, df_departments, on="dept_id", how="inner")

    # 2. Left Join: All employees preserved; unmatched dept_id (e.g. 99) gets NaN
    left_df = pd.merge(df_employees, df_departments, on="dept_id", how="left")

    # 3. Full Outer Join with indicator diagnostics:
    # Preserves employees without depts AND depts without employees (e.g. dept 4 - Security Ops)
    outer_df = pd.merge(
        df_employees,
        df_departments,
        on="dept_id",
        how="outer",
        indicator=True,
    )

    return {
        "inner": inner_df,
        "left": left_df,
        "outer": outer_df,
    }


# ==============================================================================
# 4. Concatenation: Stacking Records & Data Sources
# ==============================================================================


def combine_workforce_sources(
    df_employees: pd.DataFrame, df_contractors: pd.DataFrame
) -> pd.DataFrame:
    """
    Demonstrate vertical concatenation (row stacking) of disparate workforce streams.

    Polyglot Comparison:
    - Node.js: `[...employees, ...contractors]` or `employees.concat(contractors)`.
      Creates a new JavaScript Array of object references.
    - PHP: `array_merge($employees, $contractors)` or `$collection->concat($contractors)`.
    - Pandas: `pd.concat([df1, df2], ignore_index=True)` aligns columnar memory buffers
      in contiguous C arrays, re-indexing automatically.
    """
    stacked = pd.concat([df_employees, df_contractors], ignore_index=True)
    return stacked


# ==============================================================================
# 5. Pivot Tables & Cross-Tabulations (OLAP Operations)
# ==============================================================================


def generate_pivot_and_crosstab(
    df_employees: pd.DataFrame, df_departments: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate multidimensional summary views:
    1. Pivot Table: Average salary by department and remote work status.
    2. Crosstab: Frequency count of performance ratings across departments with margins.

    Polyglot Comparison:
    - Node.js:
      Requires 2D hash tables or multidimensional arrays: `map[dept][rating] = count`.
      Extremely tedious to calculate row and column marginal totals ('All').
    - PHP:
      Requires nested `foreach` loops or matrix aggregation libraries.
    - Pandas:
      `pd.pivot_table()` and `pd.crosstab()` execute vectorized multidimensional slicing
      with built-in marginal summations (`margins=True`).
    """
    merged = df_employees.merge(df_departments, on="dept_id", how="inner")

    # 1. Pivot Table: Mean salary by dept_name (rows) vs remote (columns)
    pivot_salaries = pd.pivot_table(
        merged,
        values="salary",
        index="dept_name",
        columns="remote",
        aggfunc="mean",
        fill_value=0.0,
    ).round(2)

    # 2. Crosstab: Remote status vs Department frequency with row and column totals (margins)
    dept_remote_crosstab = pd.crosstab(
        index=merged["dept_name"],
        columns=merged["remote"],
        margins=True,
        margins_name="Total",
    )

    return pivot_salaries, dept_remote_crosstab


# ==============================================================================
# 6. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying GroupBy aggregations, merges, pivots, and crosstabs."""
    console.print(
        Panel.fit(
            "[bold cyan]Data Science Core: Pandas GroupBy, Aggregations & Joins[/bold cyan]\n"
            "[dim]Verifying multi-metric aggregation, inner/left/outer merges, pivots, and cross-tabulation.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Setup Data
    console.print("[dim]Phase 1: Generating enterprise workforce schemas...[/dim]")
    df_emp, df_dept, df_contract = create_enterprise_workforce_data()
    assert len(df_emp) == 8
    assert len(df_dept) == 4
    assert len(df_contract) == 2
    console.print(f"  [green][PASS] Datasets initialized: {len(df_emp)} employees, {len(df_dept)} depts, {len(df_contract)} contractors.[/green]")

    # 2. Multi-Metric GroupBy Verification
    console.print("[dim]Phase 2: Computing and validating multi-metric GroupBy aggregations...[/dim]")
    dept_summary = compute_department_aggregations(df_emp, df_dept)

    # Validate aggregated schema
    expected_cols = ["dept_name", "salary_count", "salary_mean", "salary_max", "tenure_years_median", "rating_mean"]
    assert list(dept_summary.columns) == expected_cols

    # Department 2 (AI Platform) has 3 employees: Charlie (160k), Diana (142k), Hannah (150k)
    ai_platform = dept_summary[dept_summary["dept_name"] == "AI Platform"].iloc[0]
    assert ai_platform["salary_count"] == 3
    assert ai_platform["salary_max"] == 160000
    # Mean: (160000 + 142000 + 150000) / 3 = 452000 / 3 = 150666.67
    assert np.isclose(ai_platform["salary_mean"], 150666.67, atol=0.01)
    # Median tenure: Charlie (7.0), Diana (5.5), Hannah (6.0) -> sorted: [5.5, 6.0, 7.0] -> median is 6.0
    assert ai_platform["tenure_years_median"] == 6.0
    console.print(f"  [green][PASS] GroupBy aggregations verified: AI Platform mean salary = ${ai_platform['salary_mean']:,.2f}[/green]")

    # 3. Relational Merges Verification
    console.print("[dim]Phase 3: Validating relational joins (inner, left, outer) & indicator flags...[/dim]")
    merges = perform_relational_merges(df_emp, df_dept)

    # Inner Join: employee 107 (dept 99) and dept 4 (no emps) are EXCLUDED -> 7 rows
    assert len(merges["inner"]) == 7
    assert 99 not in merges["inner"]["dept_id"].values
    assert "Security Ops" not in merges["inner"]["dept_name"].values

    # Left Join: all 8 employees preserved, employee 107 has NaN for dept_name
    assert len(merges["left"]) == 8
    emp_107 = merges["left"][merges["left"]["employee_id"] == 107].iloc[0]
    assert pd.isna(emp_107["dept_name"])

    # Outer Join: 7 matched ('both') + 1 employee without dept ('left_only') + 1 dept without emps ('right_only') = 9 rows
    outer_df = merges["outer"]
    assert len(outer_df) == 9
    merge_counts = outer_df["_merge"].value_counts().to_dict()
    assert merge_counts["both"] == 7
    assert merge_counts["left_only"] == 1
    assert merge_counts["right_only"] == 1
    console.print(f"  [green][PASS] Merge semantics verified: Inner (7), Left (8), Outer (9 with diagnostic flags).[/green]")

    # 4. Vertical Concatenation Verification
    console.print("[dim]Phase 4: Validating vertical DataFrame concatenation...[/dim]")
    total_workforce = combine_workforce_sources(df_emp, df_contract)
    assert len(total_workforce) == 10
    assert total_workforce.iloc[8]["name"] == "Ian"
    assert total_workforce.iloc[9]["name"] == "Julia"
    console.print(f"  [green][PASS] Concatenation verified: Total workforce shape = {total_workforce.shape}[/green]")

    # 5. Pivot Tables & Cross-Tabulations Verification
    console.print("[dim]Phase 5: Validating pivot tables and cross-tabulation margins...[/dim]")
    piv_salary, cross_remote = generate_pivot_and_crosstab(df_emp, df_dept)

    # In AI Platform: Charlie and Hannah are remote=False, Diana is remote=True
    # Charlie (160k), Hannah (150k) -> mean = 155000.0
    # Diana (142k) -> mean = 142000.0
    assert piv_salary.loc["AI Platform", False] == 155000.0
    assert piv_salary.loc["AI Platform", True] == 142000.0

    # Cross-tab total row / col margins
    assert cross_remote.loc["Total", "Total"] == 7  # 7 employees with valid dept
    assert cross_remote.loc["AI Platform", "Total"] == 3
    console.print(f"  [green][PASS] Pivot and Crosstab verified: Margins total = {cross_remote.loc['Total', 'Total']}[/green]")

    # Display Architectural Summary Table
    table = Table(title="Pandas GroupBy & Joins vs Node.js & PHP Architecture", border_style="green")
    table.add_column("Operation", style="bold cyan")
    table.add_column("Pandas Implementation", style="white")
    table.add_column("Node.js (TypeScript) Pattern", style="yellow")
    table.add_column("PHP (Laravel) Pattern", style="magenta")

    table.add_row(
        "Multi-Metric GroupBy",
        "`df.groupby().agg({'col': ['mean', 'max']})`",
        "`arr.reduce()` into Map with manual counters",
        "`$col->groupBy()->map(fn($g) => ...)`",
    )
    table.add_row(
        "Inner / Left Joins",
        "`pd.merge(a, b, on='key', how='left')`",
        "`left.map(r => ({ ...r, ...map.get(r.id) }))`",
        "Eloquent `$emp->load('dept')` or SQL join",
    )
    table.add_row(
        "Full Outer Join",
        "`pd.merge(a, b, how='outer', indicator=True)`",
        "Set diff + synthetic null objects",
        "SQL FULL OUTER JOIN or complex array loops",
    )
    table.add_row(
        "Row Concatenation",
        "`pd.concat([df1, df2], ignore_index=True)`",
        "`[...arr1, ...arr2]` (Spread operator)",
        "`$collection->concat($other)` / `array_merge`",
    )
    table.add_row(
        "Pivot & Crosstab",
        "`pd.pivot_table()` / `pd.crosstab(margins=True)`",
        "Manual 2D hash tables with loop summations",
        "Nested foreach loops with array accumulation",
    )

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
