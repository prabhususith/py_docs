"""
Data Transformation: Comprehensions, Projections, and Lazy Generators
=====================================================================
Description: In-depth exploration of Python's comprehension expressions across lists,
             dictionaries, and sets, contrasting declarative transformation pipelines
             against JavaScript/TypeScript array methods and PHP array pipelines.
Enterprise Mapping:
- List Comprehensions: Declaratively replaces chained JavaScript `.filter().map()` calls
  and nested PHP `array_map(fn, array_filter($arr, fn))`. Comprehensions are executed in
  optimized C-level loops, avoiding Python function-call stack overhead.
- Dict Comprehensions: Replaces JavaScript `Object.fromEntries(arr.map(...))` or `reduce()`,
  and PHP `array_column($arr, 'val', 'key')` / associative transformations.
- Set Comprehensions: Replaces `new Set(arr.map(x => x.prop))` in TypeScript and
  `array_unique(array_column($arr, 'prop'))` in PHP.
- Generator Expressions `(...)`: Implements streaming lazy evaluation with O(1) memory,
  analogous to Node.js / RxJS streaming pipelines and PHP `yield` generators.

Official Documentation References:
- List Comprehensions: https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
- Nested List Comprehensions: https://docs.python.org/3/tutorial/datastructures.html#nested-list-comprehensions
- Generator Expressions (PEP 289): https://peps.python.org/pep-0289/
- Built-in Functions (map, filter, any, all): https://docs.python.org/3/library/functions.html
"""

from __future__ import annotations

import sys
from typing import Any, Final, Generator, NamedTuple


class AccountRecord(NamedTuple):
    account_id: str
    owner: str
    balance: float
    is_active: bool
    tier: str


# ==============================================================================
# 1. List Comprehension vs JS filter/map vs PHP array_filter/array_map
# ==============================================================================
def filter_and_transform_accounts(accounts: list[AccountRecord]) -> list[str]:
    """
    Demonstrate list comprehension:
    [expression for item in iterable if condition]

    TypeScript equivalent:
      accounts
        .filter(a => a.is_active && a.balance > 1000.0)
        .map(a => `VIP Account: ${a.account_id} (${a.owner})`);

    PHP equivalent:
      $filtered = array_filter($accounts, fn($a) => $a->is_active && $a->balance > 1000.0);
      $result = array_map(fn($a) => "VIP Account: {$a->account_id} ({$a->owner})", $filtered);
    """
    print("\n--- 1. List Comprehension Transformation ---")

    # Declarative Python syntax executes in optimized bytecode loop
    vip_summaries: list[str] = [
        f"VIP Account: {acc.account_id} ({acc.owner})"
        for acc in accounts
        if acc.is_active and acc.balance > 1000.0
    ]

    for summary in vip_summaries:
        print(f"  {summary}")

    return vip_summaries


# ==============================================================================
# 2. Dictionary Comprehension (Indexing, Inversion, Grouping)
# ==============================================================================
def create_lookup_indices(accounts: list[AccountRecord]) -> tuple[dict[str, AccountRecord], dict[str, float]]:
    """
    Demonstrate dict comprehensions:
    {key_expr: value_expr for item in iterable if condition}

    TypeScript equivalent:
      const idLookup = Object.fromEntries(accounts.map(a => [a.account_id, a]));
      const balances = Object.fromEntries(accounts.map(a => [a.account_id, a.balance]));

    PHP equivalent:
      $idLookup = array_column($accounts, null, 'account_id');
      $balances = array_column($accounts, 'balance', 'account_id');
    """
    print("\n--- 2. Dict Comprehensions ---")

    # Map primary identifier to entity record
    account_index: dict[str, AccountRecord] = {acc.account_id: acc for acc in accounts}

    # Map identifier to calculated/projected value for active accounts only
    balance_index: dict[str, float] = {
        acc.account_id: acc.balance for acc in accounts if acc.is_active
    }

    print(f"  Indexed {len(account_index)} entities by account_id.")
    print(f"  Active Balance Lookup: {balance_index}")

    return account_index, balance_index


# ==============================================================================
# 3. Set Comprehension (Unique Extraction & Deduplication)
# ==============================================================================
def extract_unique_tiers(accounts: list[AccountRecord]) -> set[str]:
    """
    Demonstrate set comprehensions:
    {expression for item in iterable if condition}

    TypeScript equivalent:
      const uniqueTiers = new Set(accounts.filter(a => a.is_active).map(a => a.tier));

    PHP equivalent:
      $active = array_filter($accounts, fn($a) => $a->is_active);
      $uniqueTiers = array_unique(array_column($active, 'tier'));
    """
    print("\n--- 3. Set Comprehensions ---")

    # Extracts unique tiers directly into a hash set
    distinct_tiers: set[str] = {acc.tier.upper() for acc in accounts if acc.is_active}
    print(f"  Distinct Active Tiers (Deduplicated): {distinct_tiers}")

    return distinct_tiers


# ==============================================================================
# 4. Nested Comprehensions: Flattening Matrices (JS flatMap / PHP array_merge)
# ==============================================================================
def flatten_permission_matrix(role_matrix: dict[str, list[str]]) -> list[str]:
    """
    Flatten a 2D structure using nested comprehensions.

    TypeScript equivalent:
      Object.values(role_matrix).flatMap(permissions => permissions);

    Reading rule for nested comprehensions in Python:
    Read outer loop first, then inner loop, just as you would write nested `for` statements.
    """
    print("\n--- 4. Flattening Nested Matrices ---")

    flattened_unique: list[str] = sorted(
        {perm for perms in role_matrix.values() for perm in perms}
    )
    print(f"  Flattened & Deduplicated Permissions:\n    {flattened_unique}")

    return flattened_unique


# ==============================================================================
# 5. Generator Expressions: Lazy Evaluation vs Eager Memory Allocation
# ==============================================================================
def compare_eager_vs_lazy_memory() -> None:
    """
    Benchmark memory consumption between eager list comprehension and lazy generator expression.

    Generator expressions `(x for x in data)` generate items on-demand, consuming
    O(1) memory irrespective of data scale (e.g. 10 million records).
    Compare to Node.js Streams or PHP Generators (`yield`).
    """
    print("\n--- 5. Generator Expression (Lazy) vs List Comprehension (Eager) ---")
    scale: Final[int] = 500_000

    # 1. Eager List Comprehension: Allocates full array in RAM immediately
    eager_list: list[int] = [x * 2 for x in range(scale)]
    eager_memory_bytes: int = sys.getsizeof(eager_list)

    # 2. Lazy Generator Expression: Allocates only the iterator state object
    lazy_gen: Generator[int, None, None] = (x * 2 for x in range(scale))
    lazy_memory_bytes: int = sys.getsizeof(lazy_gen)

    print(f"Dataset Cardinality: {scale:,} elements")
    print(f"  Eager List Memory:      {eager_memory_bytes:,} bytes")
    print(f"  Lazy Generator Memory:  {lazy_memory_bytes:,} bytes")
    savings_factor: float = eager_memory_bytes / lazy_memory_bytes
    print(f"  Memory Efficiency Ratio: Generator consumes {savings_factor:.1f}x less memory!")

    # Demonstrating lazy consumption with built-ins (sum, any, all)
    # Evaluates without ever holding 500,000 items simultaneously in memory
    total_sum: int = sum(x * 2 for x in range(100))
    print(f"  Lazy sum(0..99 * 2): {total_sum}")


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" LEVEL 1: 04_COMPREHENSIONS_AND_MANIPULATION - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    sample_accounts: list[AccountRecord] = [
        AccountRecord("ACC-101", "Acme Corp", 5400.50, True, "Enterprise"),
        AccountRecord("ACC-102", "Initech LLC", 750.00, True, "Standard"),
        AccountRecord("ACC-103", "Umbrella Corp", 99000.00, False, "Enterprise"),
        AccountRecord("ACC-104", "Hooli Inc", 12500.00, True, "Enterprise"),
        AccountRecord("ACC-105", "Stark Ind", 250.00, False, "Standard"),
        AccountRecord("ACC-106", "Wayne Ent", 45000.00, True, "VIP"),
    ]

    # 1. Test list comprehension
    vips = filter_and_transform_accounts(sample_accounts)
    assert len(vips) == 3
    assert any("ACC-101" in v for v in vips)
    assert any("ACC-104" in v for v in vips)
    assert any("ACC-106" in v for v in vips)

    # 2. Test dict comprehensions
    acc_map, bal_map = create_lookup_indices(sample_accounts)
    assert len(acc_map) == 6
    assert len(bal_map) == 4  # Only 4 active accounts
    assert bal_map["ACC-101"] == 5400.50

    # 3. Test set comprehensions
    unique_tiers = extract_unique_tiers(sample_accounts)
    assert unique_tiers == {"ENTERPRISE", "STANDARD", "VIP"}

    # 4. Test nested comprehension flattening
    role_permissions = {
        "admin": ["read", "write", "delete", "audit"],
        "editor": ["read", "write"],
        "viewer": ["read"],
    }
    flat_perms = flatten_permission_matrix(role_permissions)
    assert flat_perms == ["audit", "delete", "read", "write"]

    # 5. Test generator memory benchmark
    compare_eager_vs_lazy_memory()

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 04_comprehensions_and_manipulation module executed cleanly.")
    print("=" * 70)
