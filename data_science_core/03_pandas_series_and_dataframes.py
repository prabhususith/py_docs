"""
Pandas Series and DataFrames Architecture
=========================================
Description: Production implementation of Pandas Series, DataFrames, label-based (`.loc`) vs
             positional (`.iloc`) indexing, boolean masking, missing value imputation strategies,
             and conditional column derivations.

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * In Node.js, tabular data processing typically relies on `danfojs` (a JavaScript port of Pandas)
    or `arquero` (Wrangler/D3 style verb-based data tables).
  * Chaining native JavaScript array methods (`data.filter(...).map(...)`) creates intermediate heap
    arrays on every step, triggering garbage collection pauses in V8 on large payloads.
- PHP / Laravel:
  * In Laravel, developers use `Collection` pipelines:
    `collect($users)->filter(fn($u) => $u['age'] > 30)->map(...)`.
  * While expressive, Laravel Collections wrap native PHP arrays where every element is an individual
    `zval` struct. Running analytical queries on 100,000 records in PHP consumes ~50MB+ RAM and
    executes sequentially through the Zend bytecode VM without column-oriented optimization.
- Memory & Performance Tradeoffs:
  * A Pandas DataFrame is a collection of contiguous 1D NumPy/PyArrow arrays sharing an index.
  * Operations along columns are executed as contiguous memory scans, avoiding the pointer-chasing
    cache misses inherent in row-oriented Node.js object arrays and PHP associative arrays.

Official Documentation References:
- Pandas 10 Minutes Guide: https://pandas.pydata.org/docs/user_guide/10min.html
- Pandas Indexing & Slicing: https://pandas.pydata.org/docs/user_guide/indexing.html
- Pandas Missing Data: https://pandas.pydata.org/docs/user_guide/missing_data.html
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ==============================================================================
# 1. Dataset Generation & Schema Setup
# ==============================================================================


def create_sample_telemetry_dataframe() -> pd.DataFrame:
    """Construct representative enterprise cloud infrastructure telemetry dataset."""
    raw_data = {
        "node_id": ["node-us-01", "node-us-02", "node-eu-01", "node-eu-02", "node-ap-01", "node-ap-02"],
        "region": ["us-east-1", "us-east-1", "eu-west-1", "eu-west-1", "ap-south-1", "ap-south-1"],
        "cluster_role": ["primary", "worker", "primary", "worker", "primary", "worker"],
        "cpu_usage_pct": [78.5, 45.2, 91.0, np.nan, 34.8, 88.3],  # Contains missing data
        "memory_used_gb": [42.1, 18.0, 58.4, 61.2, np.nan, 29.5],  # Contains missing data
        "active_tenants": [120, 45, 180, 210, 30, 95],
        "status": ["HEALTHY", "HEALTHY", "DEGRADED", "DEGRADED", "HEALTHY", "DEGRADED"],
    }
    df = pd.DataFrame(raw_data)
    # Set explicit non-integer string index for testing .loc vs .iloc
    df.index = [f"inst_{i:03d}" for i in range(1, len(df) + 1)]
    return df


# ==============================================================================
# 2. Indexing Mechanics: .loc vs .iloc
# ==============================================================================


def demonstrate_loc_vs_iloc(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.DataFrame]:
    """
    Clarify the critical difference between label-based (.loc) and positional (.iloc) indexing.

    Polyglot Comparison:
    - Node.js: `array[0]` is always positional (like `.iloc[0]`). Looking up by ID requires
      searching an object map: `map.get('inst_001')` (like `.loc['inst_001']`).
    - PHP: PHP associative arrays conflate string keys and numeric indexes (`$arr['key']` vs `$arr[0]`),
      leading to subtle bugs when integer-like strings ("123") are automatically cast to ints by Zend.
    - Python Pandas:
      * `.loc[row_label, col_label]`: Strictly label-based. Slicing `'inst_001':'inst_003'` is INCLUSIVE
        of both start and end labels!
      * `.iloc[row_idx, col_idx]`: Strictly integer positional (0 to N-1). Slicing `0:2` is EXCLUSIVE
        of the end bound (standard Python slice semantics).
    """
    # 1. Label-based lookup via .loc
    row_by_label = df.loc["inst_001"]

    # 2. Positional lookup via .iloc (first row)
    row_by_position = df.iloc[0]

    # 3. Sliced cross-section: rows inst_001 to inst_003, columns 'region' and 'cpu_usage_pct'
    sliced_cross_section = df.loc["inst_001":"inst_003", ["region", "cpu_usage_pct"]]

    return row_by_label, row_by_position, sliced_cross_section


# ==============================================================================
# 3. Missing Data Handling (Imputation & Dropping)
# ==============================================================================


def handle_missing_telemetry(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Demonstrate missing value detection, forward-fill, and statistical median imputation.

    Polyglot Comparison:
    - Node.js: Missing values are either `undefined` or `null`. Cleaning requires filtering:
      `arr.filter(x => x !== null && x !== undefined)` or ternary fallbacks `x ?? median`.
    - PHP: Handled via `is_null()`, `$val ?? $default`, or `array_filter()`.
    - Pandas: Vectorized missing value methods: `isna()`, `dropna()`, `fillna()`.
    """
    df_imputed = df.copy()

    # Calculate region-specific median or global median
    median_cpu = df_imputed["cpu_usage_pct"].median()
    median_mem = df_imputed["memory_used_gb"].median()

    # Impute missing values with column median
    df_imputed["cpu_usage_pct"] = df_imputed["cpu_usage_pct"].fillna(median_cpu)
    df_imputed["memory_used_gb"] = df_imputed["memory_used_gb"].fillna(median_mem)

    # Alternate strategy: drop rows with any missing values
    df_dropped = df.dropna(subset=["cpu_usage_pct", "memory_used_gb"])

    return df_imputed, df_dropped


# ==============================================================================
# 4. Boolean Masking & Conditional Column Derivation
# ==============================================================================


def apply_business_logic_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter rows and derive computed columns using vectorized boolean expressions and `np.where`.

    Polyglot Comparison:
    - Node.js: `data.filter(row => row.cpu > 80 && row.status === 'DEGRADED')`.
    - PHP: `collect($data)->filter(fn($row) => $row['cpu'] > 80 && $row['status'] === 'DEGRADED')`.
    - Pandas: `df[(df['cpu_usage_pct'] > 80) & (df['status'] == 'DEGRADED')]`.
      Notice: Bitwise `&` and `|` MUST be used instead of Python's logical `and` / `or`
      because `&` acts element-wise across the boolean Series.
    """
    df_result = df.copy()

    # Vectorized boolean mask: CPU > 80% AND status is DEGRADED
    high_alert_mask = (df_result["cpu_usage_pct"] > 80.0) & (df_result["status"] == "DEGRADED")
    df_result["alert_triggered"] = high_alert_mask

    # Conditional column derivation via np.where (vectorized ternary operator)
    # If CPU > 85% -> 'CRITICAL', elif CPU > 65% -> 'WARNING', else 'NORMAL'
    conditions = [
        df_result["cpu_usage_pct"] >= 85.0,
        df_result["cpu_usage_pct"] >= 65.0,
    ]
    choices = ["CRITICAL", "WARNING"]
    df_result["load_severity"] = np.select(conditions, choices, default="NORMAL")

    # Ratio calculation: Tenants per GB Memory
    df_result["tenants_per_gb"] = (df_result["active_tenants"] / df_result["memory_used_gb"]).round(2)

    return df_result


# ==============================================================================
# 5. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying DataFrame indexing, missing data, and boolean masks."""
    console.print(
        Panel.fit(
            "[bold cyan]Data Science Core: Pandas Series & DataFrames[/bold cyan]\n"
            "[dim]Verifying .loc vs .iloc, missing data imputation, and vectorized boolean logic.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Dataset Instantiation
    console.print("[dim]Phase 1: Creating telemetry DataFrame with custom index...[/dim]")
    df = create_sample_telemetry_dataframe()
    assert len(df) == 6
    assert df.shape == (6, 7)
    assert "inst_001" in df.index
    console.print(f"  [green][PASS] DataFrame initialized with shape {df.shape} and index {df.index.tolist()[:3]}...[/green]")

    # 2. .loc vs .iloc Verification
    console.print("[dim]Phase 2: Validating .loc (label inclusive) vs .iloc (positional exclusive)...[/dim]")
    row_label, row_pos, cross_sec = demonstrate_loc_vs_iloc(df)

    # .loc['inst_001'] and .iloc[0] point to the exact same first record
    assert row_label["node_id"] == "node-us-01"
    assert row_pos["node_id"] == "node-us-01"
    assert row_label.name == "inst_001"

    # .loc slicing is INCLUSIVE of both start and end labels (inst_001, inst_002, inst_003) -> 3 rows!
    assert len(cross_sec) == 3
    assert list(cross_sec.columns) == ["region", "cpu_usage_pct"]
    assert cross_sec.index.tolist() == ["inst_001", "inst_002", "inst_003"]
    console.print("  [green][PASS] .loc and .iloc indexing semantics verified.[/green]")

    # 3. Missing Data Imputation Verification
    console.print("[dim]Phase 3: Validating missing data detection and median imputation...[/dim]")
    assert df["cpu_usage_pct"].isna().sum() == 1
    assert df["memory_used_gb"].isna().sum() == 1

    df_imputed, df_dropped = handle_missing_telemetry(df)
    assert df_imputed["cpu_usage_pct"].isna().sum() == 0, "No NaNs should remain after fillna."
    assert df_imputed["memory_used_gb"].isna().sum() == 0

    # Verify dropped rows (6 rows - 2 with NaN = 4 rows)
    assert len(df_dropped) == 4
    console.print(f"  [green][PASS] Missing data handled: Imputed 0 NaNs, Dropped DataFrame length = {len(df_dropped)}[/green]")

    # 4. Boolean Masking & Conditional Column Verification
    console.print("[dim]Phase 4: Validating boolean masking and np.select severity classification...[/dim]")
    df_annotated = apply_business_logic_rules(df_imputed)

    # Check alert_triggered: node-eu-01 (CPU 91.0, DEGRADED) and node-ap-02 (CPU 88.3, DEGRADED) -> True
    alert_nodes = df_annotated[df_annotated["alert_triggered"]]["node_id"].tolist()
    assert alert_nodes == ["node-eu-01", "node-ap-02"]

    # Check load_severity categorization
    assert df_annotated.loc["inst_003", "load_severity"] == "CRITICAL"  # 91.0% >= 85.0%
    assert df_annotated.loc["inst_001", "load_severity"] == "WARNING"   # 78.5% >= 65.0%
    assert df_annotated.loc["inst_005", "load_severity"] == "NORMAL"    # 34.8% < 65.0%
    console.print(f"  [green][PASS] Boolean masking verified: {len(alert_nodes)} alerts triggered ({alert_nodes})[/green]")

    # Summary Table
    table = Table(title="Pandas DataFrame vs Node.js & PHP Architecture", border_style="green")
    table.add_column("Operation", style="bold cyan")
    table.add_column("Pandas Mechanism", style="white")
    table.add_column("Node.js (TypeScript) Equivalent", style="yellow")
    table.add_column("PHP (Laravel) Equivalent", style="magenta")

    table.add_row(
        "Label Indexing",
        "`df.loc['row_label', 'col']`",
        "`map.get('id')?.property`",
        "`$collection->get('key')`",
    )
    table.add_row(
        "Integer Indexing",
        "`df.iloc[0:5, 1:3]`",
        "`array.slice(0, 5)`",
        "`array_slice($arr, 0, 5)`",
    )
    table.add_row(
        "Missing Data",
        "`df.fillna(median)` / `dropna()`",
        "`arr.filter(x => x != null)`",
        "`array_filter($arr)` / `?? $default`",
    )
    table.add_row(
        "Boolean Masking",
        "`df[(df['a'] > 5) & (df['b'] == 1)]`",
        "`arr.filter(x => x.a > 5 && x.b === 1)`",
        "`$collection->where('a', '>', 5)`",
    )
    table.add_row(
        "Conditional Columns",
        "`np.select([conds], [vals])`",
        "`arr.map(x => cond ? a : b)`",
        "`$collection->map(fn($x) => ...)`",
    )

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
