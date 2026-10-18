"""
Sequential Data Structures: Lists and Tuples
===========================================
Description: Deep architectural analysis of Python's dynamic array (`list`) and immutable
             sequence (`tuple`) types, memory allocation semantics, slicing mechanics,
             and type-safe immutable records via `typing.NamedTuple`.
Enterprise Mapping:
- `list`: Dynamic array analogous to JavaScript `Array` and PHP indexed arrays (`$arr[] = $val`).
          Internally implemented as a contiguous vector of pointer references with over-allocation
          yielding amortized O(1) appends, O(1) indexing, and O(n) insert/delete.
- `tuple`: Fixed-length, immutable sequence. Analogous to TypeScript `readonly [T1, T2]` or
           `as const` tuples, and PHP 8.2 readonly value objects. Tuples are hashable (can be
           dict keys) if all contained elements are hashable.
- Slicing `arr[start:stop:step]`: Replaces JS `arr.slice()` and PHP `array_slice()`, with
          stride syntax `arr[::2]` and reverse stride `arr[::-1]`.

Official Documentation References:
- More on Lists: https://docs.python.org/3/tutorial/datastructures.html#more-on-lists
- Tuples and Sequences: https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences
- Standard Library Sequence Types: https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range
- Typing NamedTuple: https://docs.python.org/3/library/typing.html#typing.NamedTuple
"""

from __future__ import annotations

import copy
import sys
from typing import Final, NamedTuple


# ==============================================================================
# 1. Dynamic Array (List) Operations & Complexity
# ==============================================================================
def demonstrate_list_mutations() -> list[str]:
    """
    Demonstrate list operations and their computational complexity:
    - append(x): O(1) amortized
    - pop(): O(1) from tail
    - insert(0, x) / pop(0): O(n) due to shifting pointers in contiguous memory
    - extend(iterable): O(k) where k is the length of iterable
    """
    print("\n--- 1. List Operations & Pointer Mechanics ---")
    buffer: list[str] = ["evt_001", "evt_002"]

    # Amortized O(1) append
    buffer.append("evt_003")
    print(f"After append: {buffer}")

    # In-place extension: O(k)
    buffer.extend(["evt_004", "evt_005"])
    print(f"After extend: {buffer}")

    # Tail pop: O(1)
    tail_item: str = buffer.pop()
    print(f"Popped tail item '{tail_item}': {buffer}")

    # Arbitrary insertion: O(n) - caution in high-throughput hot paths
    buffer.insert(1, "evt_interleaved")
    print(f"After insert at index 1: {buffer}")

    # In-place sorting: Timsort / Powersort algorithm O(n log n)
    buffer.sort(reverse=True)
    print(f"After reverse sort: {buffer}")

    return buffer


# ==============================================================================
# 2. Advanced Slicing Mechanics: Stride, Reversal, Shallow vs Deep Copy
# ==============================================================================
def demonstrate_slicing_semantics() -> dict[str, list[int]]:
    """
    Demonstrate Python's slice syntax: sequence[start:stop:step]

    JS equivalent of arr[1:4]:
      arr.slice(1, 4)
    PHP equivalent:
      array_slice($arr, 1, 3)
    """
    print("\n--- 2. Slicing Patterns & Strides ---")
    data_series: list[int] = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
    print(f"Original Sequence: {data_series}")

    # Standard slice: [inclusive_start : exclusive_stop]
    sub_slice: list[int] = data_series[2:7]
    print(f"Sub-slice [2:7]: {sub_slice}")

    # Stride slicing: taking every 2nd element (e.g., downsampling telemetry)
    even_stride: list[int] = data_series[::2]
    print(f"Even Stride [::2] (Downsampled 50%): {even_stride}")

    # Stride with offset: odd elements
    odd_stride: list[int] = data_series[1::2]
    print(f"Odd Stride [1::2]: {odd_stride}")

    # Reverse stride: high-speed reverse traversal
    reversed_series: list[int] = data_series[::-1]
    print(f"Reversed via Stride [::-1]: {reversed_series}")

    # Shallow copy via slice `[:]` vs deepcopy
    nested_origin: list[list[int]] = [[1, 2], [3, 4]]
    shallow_copy: list[list[int]] = nested_origin[:]
    deep_copy: list[list[int]] = copy.deepcopy(nested_origin)

    # Mutating nested member illustrates shallow pointer sharing
    nested_origin[0][0] = 999
    print(f"Origin after nested mutation: {nested_origin}")
    print(f"Shallow copy reflects mutation: {shallow_copy} (Same inner object ref)")
    print(f"Deep copy isolates mutation:   {deep_copy} (Independent memory)")

    return {
        "sub_slice": sub_slice,
        "even_stride": even_stride,
        "reversed": reversed_series,
    }


# ==============================================================================
# 3. Tuple Immutability, Hashability, and Memory Footprint
# ==============================================================================
def compare_list_vs_tuple_memory() -> tuple[int, int]:
    """
    Benchmark memory overhead of list vs tuple.

    Python lists maintain spare over-allocated capacity to support O(1) appends.
    Tuples have fixed sizes known at creation, resulting in lower memory footprint
    and zero reallocation overhead.
    """
    print("\n--- 3. List vs Tuple Memory Footprint ---")
    cardinality: Final[int] = 1_000

    test_list: list[int] = list(range(cardinality))
    test_tuple: tuple[int, ...] = tuple(range(cardinality))

    list_size_bytes: int = sys.getsizeof(test_list)
    tuple_size_bytes: int = sys.getsizeof(test_tuple)

    print(f"Cardinality: {cardinality} integers")
    print(f"  List Memory Overhead:  {list_size_bytes} bytes")
    print(f"  Tuple Memory Overhead: {tuple_size_bytes} bytes")
    diff_percent: float = ((list_size_bytes - tuple_size_bytes) / list_size_bytes) * 100
    print(f"  Memory Economy of Tuple: {diff_percent:.1f}% savings")

    # Immutability & Hashability Demonstration
    # Tuples can serve as composite dictionary keys or set elements
    coordinate_tuple: tuple[int, int, str] = (40, -74, "datacenter-us-east")
    cache_store: dict[tuple[int, int, str], str] = {coordinate_tuple: "DC-ACTIVE-1"}
    print(f"Tuple used as Dict Key: {cache_store[coordinate_tuple]}")

    return list_size_bytes, tuple_size_bytes


# ==============================================================================
# 4. Typed Immutable Records with typing.NamedTuple
# ==============================================================================
class DatabaseEndpoint(NamedTuple):
    """
    Enterprise Typed Immutable Record.

    Equivalent to TypeScript:
      interface DatabaseEndpoint {
        readonly host: string;
        readonly port: number;
        readonly database: string;
        readonly sslEnabled: boolean;
      }
    Equivalent to PHP 8.2:
      readonly class DatabaseEndpoint {
        public function __construct(
          public string $host,
          public int $port,
          public string $database,
          public bool $sslEnabled
        ) {}
      }
    """

    host: str
    port: int
    database: str
    ssl_enabled: bool = True

    def connection_uri(self) -> str:
        """Produce a standard database connection DSN string."""
        scheme = "postgresql+ssl" if self.ssl_enabled else "postgresql"
        return f"{scheme}://{self.host}:{self.port}/{self.database}"


def demonstrate_named_tuples() -> DatabaseEndpoint:
    """Demonstrate type-safe, indexable, and attribute-accessible NamedTuples."""
    print("\n--- 4. Enterprise NamedTuple Demonstration ---")
    primary_db = DatabaseEndpoint(
        host="postgres-cluster.internal.net",
        port=5432,
        database="accounts_prod",
        ssl_enabled=True,
    )

    # Named attribute access
    print(f"Host: {primary_db.host} | Port: {primary_db.port}")

    # Indexed tuple access (backward-compatible with standard tuples)
    print(f"Indexed access [0]: {primary_db[0]}")

    # Method execution
    print(f"Generated DSN: {primary_db.connection_uri()}")

    # Guaranteed immutability: attempting to assign raises AttributeError
    try:
        # type-ignore comment verifies static checker awareness
        primary_db.port = 5433  # type: ignore[misc]
    except AttributeError as err:
        print(f"Immutability Enforced: Mutation attempt raised: {err}")

    return primary_db


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" LEVEL 1: 02_ARRAYS_LISTS_TUPLES - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. List mutation test
    mutated = demonstrate_list_mutations()
    assert len(mutated) == 5

    # 2. Slicing test
    slice_results = demonstrate_slicing_semantics()
    assert slice_results["even_stride"] == [0, 20, 40, 60, 80]
    assert slice_results["reversed"] == [90, 80, 70, 60, 50, 40, 30, 20, 10, 0]

    # 3. Memory benchmark
    list_bytes, tuple_bytes = compare_list_vs_tuple_memory()
    assert tuple_bytes <= list_bytes

    # 4. NamedTuple test
    endpoint = demonstrate_named_tuples()
    assert endpoint.port == 5432
    assert "postgresql+ssl" in endpoint.connection_uri()

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 02_arrays_lists_tuples module executed cleanly.")
    print("=" * 70)
