"""
Sorting, Binary Search, and Dynamic Programming Architecture
============================================================
Description: Production implementation of QuickSort, logarithmic Binary Search via `bisect`,
             the classic 0/1 Knapsack Dynamic Programming optimization, and function memoization
             using `functools.lru_cache`.

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * In V8, `Array.prototype.sort()` has used Timsort since V8 v7.0. A notorious JavaScript pitfall
    is calling `[10, 2, 5].sort()` without a comparator, which converts numbers to strings and
    sorts lexicographically into `[10, 2, 5]`. In Python, `sorted([10, 2, 5])` correctly sorts by value.
  * Memoization in Node.js typically relies on closure caches with `Map` or lodash `_.memoize()`.
- PHP / Laravel:
  * PHP provides `sort()`, `usort()`, and `uasort()`, which internally utilize a hybrid QuickSort
    and InsertionSort in the Zend Engine. PHP sorts do not guarantee stability unless using PHP 8.0+.
  * Laravel developers implement memoization via `Cache::remember('key', $ttl, fn() => ...)`
    backed by Redis, whereas Python's `@functools.lru_cache` provides process-level in-memory
    C-accelerated LRU caching with bounded capacity.
- Memory & Performance Tradeoffs:
  * Python's standard `list.sort()` is Timsort: O(N log N) worst-case, O(N) best-case on partially
    sorted real-world data, and strictly stable (maintains relative order of equal keys).
  * `functools.lru_cache(maxsize=128)` maintains a doubly linked list + hash map in C, executing
    O(1) cache hits and evicting the least recently used entries with zero memory leaks.

Official Documentation References:
- Python bisect Module: https://docs.python.org/3/library/bisect.html
- Python functools.lru_cache: https://docs.python.org/3/library/functools.html#functools.lru_cache
- CPython Sorting HOWTO: https://docs.python.org/3/howto/sorting.html
"""

from __future__ import annotations

import bisect
import functools
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ==============================================================================
# 1. QuickSort Implementation (Lomuto Partition Scheme)
# ==============================================================================


def quicksort(arr: List[int]) -> List[int]:
    """
    In-place recursive QuickSort algorithm using Lomuto partitioning.

    Time Complexity:
    - Average / Best Case: O(N log N)
    - Worst Case: O(N^2) (mitigated by choosing median-of-three or randomized pivot)
    Space Complexity: O(log N) call stack.

    Polyglot Comparison:
    - Node.js: `array.sort((a,b) => a - b)` (V8 Timsort, stable).
    - PHP: `usort($arr, fn($a, $b) => $a <=> $b)` (Zend hybrid QuickSort).
    """
    arr_copy = list(arr)

    def _quicksort_in_place(low: int, high: int) -> None:
        if low < high:
            pivot_idx = _partition(low, high)
            _quicksort_in_place(low, pivot_idx - 1)
            _quicksort_in_place(pivot_idx + 1, high)

    def _partition(low: int, high: int) -> int:
        pivot = arr_copy[high]
        i = low - 1
        for j in range(low, high):
            if arr_copy[j] <= pivot:
                i += 1
                arr_copy[i], arr_copy[j] = arr_copy[j], arr_copy[i]
        arr_copy[i + 1], arr_copy[high] = arr_copy[high], arr_copy[i + 1]
        return i + 1

    _quicksort_in_place(0, len(arr_copy) - 1)
    return arr_copy


# ==============================================================================
# 2. Binary Search & Interval Insertion (bisect)
# ==============================================================================


class MetricThresholdEvaluator:
    """
    Logarithmic threshold lookup engine using Python's C-accelerated `bisect` module.

    Polyglot Comparison:
    - Node.js: Lacks a native binary search in standard library; requires custom binary search loop.
    - PHP: No native `bisect`; developers often iterate linearly O(N) or write custom loops.
    """

    def __init__(self, thresholds: List[float], labels: List[str]) -> None:
        if len(labels) != len(thresholds) + 1:
            raise ValueError("Labels count must be thresholds count + 1.")
        # Ensure thresholds are monotonically increasing
        self._thresholds = sorted(thresholds)
        self._labels = labels

    def evaluate_metric(self, value: float) -> str:
        """
        Map a continuous value into a discrete category in O(log N) time using `bisect_right`.
        Example: [60, 70, 80, 90] with ['F', 'D', 'C', 'B', 'A']
        """
        idx = bisect.bisect_right(self._thresholds, value)
        return self._labels[idx]

    def insert_threshold(self, new_threshold: float, new_label: str) -> None:
        """
        Maintain sorted order during insertion in O(N) time (binary search O(log N) + insert O(N)).
        """
        idx = bisect.bisect_right(self._thresholds, new_threshold)
        self._thresholds.insert(idx, new_threshold)
        self._labels.insert(idx + 1, new_label)


# ==============================================================================
# 3. Dynamic Programming: 0/1 Knapsack Problem
# ==============================================================================


def knapsack_01_bottom_up(
    weights: List[int],
    values: List[int],
    capacity: int,
) -> Tuple[int, List[int]]:
    """
    Solve 0/1 Knapsack optimization problem using 2D Bottom-Up Dynamic Programming.

    Problem: Given N items, each with a weight and value, determine the maximum value
    that can be carried in a knapsack with maximum weight capacity W.

    Time Complexity: O(N * W) where N is number of items, W is capacity.
    Space Complexity: O(N * W) table (can be optimized to O(W) with 1D array).

    Returns:
        Tuple of (max_value, selected_item_indices)
    """
    n = len(weights)
    # dp[i][w] holds max value achievable with first i items and capacity w
    dp: List[List[int]] = [[0] * (capacity + 1) for _ in range(n + 1)]

    # Populate DP Table
    for i in range(1, n + 1):
        w_i = weights[i - 1]
        v_i = values[i - 1]
        for w in range(capacity + 1):
            if w_i <= w:
                # Max of: exclude item vs include item
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - w_i] + v_i)
            else:
                dp[i][w] = dp[i - 1][w]

    max_value = dp[n][capacity]

    # Backtrack to identify selected items
    selected_indices: List[int] = []
    rem_capacity = capacity
    for i in range(n, 0, -1):
        if dp[i][rem_capacity] != dp[i - 1][rem_capacity]:
            # Item i-1 was included
            selected_indices.append(i - 1)
            rem_capacity -= weights[i - 1]

    selected_indices.reverse()
    return max_value, selected_indices


def knapsack_01_space_optimized(
    weights: List[int],
    values: List[int],
    capacity: int,
) -> int:
    """
    Space-optimized 0/1 Knapsack using a single 1D array traversed backwards.
    Space Complexity: O(W) instead of O(N * W).
    """
    dp = [0] * (capacity + 1)
    for w_i, v_i in zip(weights, values):
        # Traverse backwards to prevent using the same item multiple times in one iteration
        for w in range(capacity, w_i - 1, -1):
            dp[w] = max(dp[w], dp[w - w_i] + v_i)
    return dp[capacity]


# ==============================================================================
# 4. Memoization with functools.lru_cache
# ==============================================================================


@functools.lru_cache(maxsize=128)
def fibonacci_memoized(n: int) -> int:
    """
    Compute Nth Fibonacci number using C-accelerated `@functools.lru_cache`.

    Without memoization: O(2^N) exponential time (branching recursion tree).
    With memoization: O(N) linear time and O(N) stack depth.

    Polyglot Comparison:
    - Node.js:
      ```ts
      const memo = new Map<number, number>();
      function fib(n: number): number {
        if (n <= 1) return n;
        if (memo.has(n)) return memo.get(n)!;
        const res = fib(n - 1) + fib(n - 2);
        memo.set(n, res);
        return res;
      }
      ```
    - PHP:
      ```php
      function fib(int $n, array &$memo = []): int {
          if ($n <= 1) return $n;
          return $memo[$n] ??= fib($n - 1, $memo) + fib($n - 2, $memo);
      }
      ```
    """
    if n <= 1:
        return n
    return fibonacci_memoized(n - 1) + fibonacci_memoized(n - 2)


# ==============================================================================
# 5. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying sorting, bisect, knapsack, and LRU cache."""
    console.print(
        Panel.fit(
            "[bold cyan]DSA Pillar 1: Sorting & Dynamic Programming Verification[/bold cyan]\n"
            "[dim]Verifying QuickSort, bisect logarithmic thresholds, 0/1 Knapsack DP, and LRU cache.[/dim]",
            border_style="cyan",
        )
    )

    # 1. QuickSort Verification
    console.print("[dim]Phase 1: Validating in-place QuickSort...[/dim]")
    unsorted = [64, 25, 12, 22, 11, 90, 42, 1, 73]
    sorted_res = quicksort(unsorted)
    assert sorted_res == sorted(unsorted), f"QuickSort failed: got {sorted_res}"
    console.print(f"  [green][PASS] QuickSort correctly sorted {len(unsorted)} elements: {sorted_res}[/green]")

    # 2. Binary Search & Bisect Verification
    console.print("[dim]Phase 2: Validating logarithmic threshold evaluator via bisect...[/dim]")
    evaluator = MetricThresholdEvaluator(
        thresholds=[50.0, 75.0, 90.0],
        labels=["NORMAL", "ELEVATED", "CRITICAL", "CATASTROPHIC"],
    )
    assert evaluator.evaluate_metric(30.0) == "NORMAL"
    assert evaluator.evaluate_metric(50.0) == "ELEVATED"  # bisect_right: <= 50 is NORMAL, > 50 is ELEVATED
    assert evaluator.evaluate_metric(74.9) == "ELEVATED"
    assert evaluator.evaluate_metric(85.0) == "CRITICAL"
    assert evaluator.evaluate_metric(95.0) == "CATASTROPHIC"
    console.print("  [green][PASS] Logarithmic bisect threshold evaluations verified.[/green]")

    # 3. Dynamic Programming: 0/1 Knapsack Verification
    console.print("[dim]Phase 3: Validating 0/1 Knapsack optimization...[/dim]")
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    capacity = 5

    # Optimal solution: items at index 0 (w=2, v=3) and index 1 (w=3, v=4) -> Total weight = 5, Total value = 7
    max_val, selected = knapsack_01_bottom_up(weights, values, capacity)
    assert max_val == 7, f"Expected max value 7, got {max_val}"
    assert selected == [0, 1], f"Expected selected items [0, 1], got {selected}"

    # Verify space-optimized version
    max_val_opt = knapsack_01_space_optimized(weights, values, capacity)
    assert max_val_opt == 7, f"Expected space-optimized max value 7, got {max_val_opt}"
    console.print(f"  [green][PASS] 0/1 Knapsack DP verified: max value = {max_val}, selected items = {selected}[/green]")

    # 4. Memoization Verification
    console.print("[dim]Phase 4: Validating @functools.lru_cache speedup on Fibonacci...[/dim]")
    fibonacci_memoized.cache_clear()
    ans = fibonacci_memoized(50)
    assert ans == 12586269025
    cache_info = fibonacci_memoized.cache_info()
    assert cache_info.hits > 0, "Cache hits must be recorded."
    console.print(f"  [green][PASS] Fibonacci(50) = {ans} computed in O(N) time with {cache_info.hits} cache hits.[/green]")

    # Summary Table
    table = Table(title="Sorting & DP Complexity Reference", border_style="green")
    table.add_column("Algorithm / Concept", style="bold cyan")
    table.add_column("Mechanism", style="white")
    table.add_column("Time Complexity", style="bold green")
    table.add_column("Space Complexity", style="bold green")
    table.add_column("Polyglot Equivalent", style="yellow")

    table.add_row("QuickSort", "Lomuto partition scheme", "O(N log N) avg", "O(log N)", "V8 Timsort / Zend QuickSort")
    table.add_row("Binary Search", "bisect.bisect_right", "O(log N)", "O(1)", "Custom binary search loop")
    table.add_row("0/1 Knapsack DP", "2D table / 1D rolling array", "O(N * W)", "O(N * W) or O(W)", "Matrix dynamic programming")
    table.add_row("LRU Memoization", "`@functools.lru_cache`", "O(1) hit", "O(Capacity)", "Lodash `_.memoize` / Laravel Cache")

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
