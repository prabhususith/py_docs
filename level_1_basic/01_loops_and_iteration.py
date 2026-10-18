"""
Loops and Iteration Mechanics in Python
======================================
Description: Comprehensive deep-dive into Python's looping protocols, iterator mechanics,
             sequence generators, and loop control structures with strict static typing.
Enterprise Mapping:
- `range()`: Replaces C-style `for (let i = 0; i < n; i++)` in TypeScript and `for ($i = 0; $i < $n; $i++)` in PHP.
- `enumerate()`: Replaces manual index tracking `array.forEach((val, idx) => ...)` in TS and `foreach ($arr as $idx => $val)` in PHP.
- `zip()`: Replaces manual tuple alignment or multi-array index access (e.g. `arrA[i], arrB[i]`) and PHP `array_map(null, $a, $b)`.
- `while...else`: Eliminates boilerplate boolean flag variables (e.g. `let found = false; ... if (!found)`) common in JS and PHP.

Official Documentation References:
- Core Control Flow Tools: https://docs.python.org/3/tutorial/controlflow.html
- Python Iterator Types: https://docs.python.org/3/library/stdtypes.html#iterator-types
- Built-in Functions (range, enumerate, zip): https://docs.python.org/3/library/functions.html
"""

from __future__ import annotations

import itertools
from typing import Final, Iterator, Sequence


# ==============================================================================
# 1. Sequence Generation with range()
# ==============================================================================
def demonstrate_range_semantics() -> list[int]:
    """
    Demonstrate range() step, start, stop, and reverse progression.

    In Python, range() produces an immutable sequence of integers.
    Unlike PHP range() which generates the full memory array eagerly,
    Python's range is a lazy sequence object consuming O(1) space regardless of size.
    """
    print("\n--- 1. range() Mechanics ---")

    # Range with start, stop (exclusive), step: equivalent to for(let i = 10; i < 30; i += 5)
    fwd_range: range = range(10, 30, 5)
    fwd_list: list[int] = list(fwd_range)
    print(f"Forward Range (10 to 30, step 5): {fwd_list}")

    # Reverse range with negative step: equivalent to for($i = 20; $i > 0; $i -= 5)
    rev_range: range = range(20, 0, -5)
    rev_list: list[int] = list(rev_range)
    print(f"Reverse Range (20 down to 0, step -5): {rev_list}")

    # O(1) membership check on range objects
    is_present: bool = 25 in fwd_range
    print(f"Is 25 in forward range? {is_present} (Evaluated in O(1) arithmetic time)")

    return fwd_list


# ==============================================================================
# 2. Indexed Traversal with enumerate()
# ==============================================================================
def process_order_batch(orders: Sequence[str], base_index: int = 1) -> list[str]:
    """
    Process an ordered batch using enumerate(iterable, start).

    TypeScript equivalent:
      orders.map((order, idx) => `Task #${idx + 1}: ${order}`)
    PHP equivalent:
      $output = [];
      foreach ($orders as $idx => $order) {
          $output[] = "Task #" . ($idx + 1) . ": " . $order;
      }
    """
    print("\n--- 2. enumerate() Traversal ---")
    formatted_logs: list[str] = []

    # Enumerate yields (index, value) tuples with customizable start offset
    for index, order_id in enumerate(orders, start=base_index):
        log_entry: str = f"Batch Position #{index:03d} -> Processing Order ID: {order_id}"
        formatted_logs.append(log_entry)
        print(f"  {log_entry}")

    return formatted_logs


# ==============================================================================
# 3. Parallel Iteration with zip() & strict validation
# ==============================================================================
def synchronize_telemetry_streams(
    timestamps: Sequence[int],
    cpu_metrics: Sequence[float],
    memory_metrics: Sequence[float],
    enforce_strict: bool = True,
) -> list[dict[str, float | int]]:
    """
    Merge multiple parallel data streams using zip(*iterables, strict=True).

    strict=True (added in Python 3.10) guarantees that all streams possess
    equal cardinality, raising ValueError on length mismatch instead of
    silently truncating to the shortest stream.

    TypeScript equivalent:
      timestamps.map((t, i) => ({ timestamp: t, cpu: cpu_metrics[i], mem: memory_metrics[i] }))
    """
    print("\n--- 3. zip() Parallel Streaming ---")
    telemetry_records: list[dict[str, float | int]] = []

    try:
        # Zip bundles nth items together into a tuple
        for ts, cpu, mem in zip(timestamps, cpu_metrics, memory_metrics, strict=enforce_strict):
            record: dict[str, float | int] = {
                "timestamp": ts,
                "cpu_utilization": cpu,
                "memory_utilization": mem,
            }
            telemetry_records.append(record)
            print(f"  Synced Sample -> TS: {ts} | CPU: {cpu:.1f}% | RAM: {mem:.1f}%")
    except ValueError as exc:
        print(f"  [CRITICAL] Cardinality Mismatch Detected: {exc}")
        raise

    return telemetry_records


# ==============================================================================
# 4. Loop Completion Semantics: while...else & for...else
# ==============================================================================
def find_healthy_replica(nodes: Sequence[str], healthy_node_id: str) -> str | None:
    """
    Demonstrate Python's unique `for...else` / `while...else` construct.

    The `else` branch executes ONLY if the loop completes normally WITHOUT hitting
    a `break` statement. If a `break` occurs, the `else` block is completely bypassed.

    In Node.js / PHP, engineers maintain a boolean flag:
      let found = false;
      for (const node of nodes) {
        if (node === target) { found = true; break; }
      }
      if (!found) { handleNotFound(); }
    """
    print("\n--- 4. for...else & while...else Execution ---")
    print(f"Searching cluster for healthy node target: '{healthy_node_id}'...")

    for node in nodes:
        print(f"  Pinging node: {node}")
        if node == healthy_node_id:
            print(f"  [SUCCESS] Target replica found and acquired: {node}")
            return node
    else:
        # Executes only when loop finishes without 'break'
        print("  [ALERT] Cluster exhausted: No healthy replica satisfied the query!")
        return None


def poll_service_readiness(max_attempts: int = 5, ready_at_attempt: int = 3) -> bool:
    """
    Demonstrate `while...else` polling loop.
    """
    attempt: int = 1
    while attempt <= max_attempts:
        print(f"  Healthcheck attempt #{attempt} of {max_attempts}...")
        if attempt == ready_at_attempt:
            print("  [ONLINE] Service became ready!")
            break
        attempt += 1
    else:
        print("  [TIMEOUT] Service failed to report ready within allocated attempts.")
        return False

    return True


# ==============================================================================
# 5. Advanced Iterator Tooling: itertools
# ==============================================================================
def demonstrate_itertools_pipeline() -> None:
    """
    Demonstrate high-throughput iterator processing via itertools.
    Compare to RxJS or Lodash streaming pipelines in Node.js.
    """
    print("\n--- 5. itertools Stream Processing ---")

    # Infinite sequence generator with islice
    counter: Iterator[int] = itertools.count(start=1000, step=50)
    windowed_slice: list[int] = list(itertools.islice(counter, 5))
    print(f"  islice from infinite counter: {windowed_slice}")

    # Chaining multiple disparate sequences without array allocation
    alpha: list[str] = ["A", "B"]
    beta: list[str] = ["X", "Y"]
    combined_stream: Iterator[str] = itertools.chain(alpha, beta)
    print(f"  itertools.chain result: {list(combined_stream)}")


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" LEVEL 1: 01_LOOPS_AND_ITERATION - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Range test
    demo_range = demonstrate_range_semantics()
    assert demo_range == [10, 15, 20, 25]

    # 2. Enumerate test
    sample_orders: Final[list[str]] = ["ORD-9021", "ORD-9022", "ORD-9023"]
    logs = process_order_batch(sample_orders, base_index=101)
    assert len(logs) == 3

    # 3. Zip test
    ts_stream = [1700000000, 1700000010, 1700000020]
    cpu_stream = [24.5, 38.2, 51.0]
    mem_stream = [62.1, 62.8, 64.0]
    telemetry = synchronize_telemetry_streams(ts_stream, cpu_stream, mem_stream, enforce_strict=True)
    assert len(telemetry) == 3
    assert telemetry[0]["cpu_utilization"] == 24.5

    # 4. Loop...else tests
    cluster = ["node-us-east-1a", "node-us-east-1b", "node-us-east-1c"]
    found_node = find_healthy_replica(cluster, "node-us-east-1b")
    assert found_node == "node-us-east-1b"

    missing_node = find_healthy_replica(cluster, "node-eu-central-1a")
    assert missing_node is None

    poll_ok = poll_service_readiness(max_attempts=5, ready_at_attempt=3)
    assert poll_ok is True

    # 5. Itertools test
    demonstrate_itertools_pipeline()

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 01_loops_and_iteration module executed cleanly.")
    print("=" * 70)
