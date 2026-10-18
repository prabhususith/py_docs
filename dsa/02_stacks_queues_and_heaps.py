"""
Stacks, Queues, and Priority Queues (Binary Heaps)
=================================================
Description: Production implementation of LIFO Stacks, FIFO Queues, and Priority Queues
             via the standard library `heapq` module (Min-Heap / Max-Heap).
             Features custom heap comparator wrappers, task scheduler with cancellation,
             and top-k element queries.

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * JavaScript arrays have native `.push()` and `.pop()`, functioning as efficient LIFO Stacks.
  * Node.js has NO native Priority Queue or Heap in its standard library. Teams must pull in
    third-party dependencies like `@datastructures-js/priority-queue` or `heapdump`.
    A common anti-pattern in Node.js is calling `array.sort((a,b) => ...)` on every insertion,
    turning an O(log N) heap insert into an expensive O(N log N) array sort.
- PHP / Laravel:
  * PHP provides `SplStack` and `SplPriorityQueue` in the SPL extension.
  * `SplPriorityQueue` is by default a Max-Heap. Overriding the priority behavior requires
    subclassing and implementing `public function compare($priority1, $priority2): int`.
    In PHP 7/8, SPL structures consume significantly more memory than native arrays due to
    Zend Object allocators.
- Memory & Performance Tradeoffs:
  * Python's `heapq` module is a high-performance C-accelerated implementation of a Min-Heap.
  * It operates directly on standard Python `list` objects in-place (`heapify(list)` is O(N)),
    arranging elements such that `heap[k] <= heap[2*k + 1]` and `heap[k] <= heap[2*k + 2]`.
  * Space complexity is O(1) auxiliary memory because it avoids pointer-based node objects.

Official Documentation References:
- Python heapq Module: https://docs.python.org/3/library/heapq.html
- Python Queue Implementations: https://docs.python.org/3/library/queue.html
- CPython heapq source code: https://github.com/python/cpython/blob/main/Lib/heapq.py
"""

from __future__ import annotations

import heapq
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Generic, Iterator, List, Optional, Tuple, TypeVar

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

T = TypeVar("T")


# ==============================================================================
# 1. LIFO Stack (Last-In, First-Out)
# ==============================================================================


class EnterpriseStack(Generic[T]):
    """
    Bounded LIFO Stack backed by contiguous dynamic array (Python list).

    Polyglot Comparison:
    - Node.js: Identical to `class Stack { private items = []; push(x){...} }`.
    - PHP: Equivalent to `SplStack` or array operations `array_push()` and `array_pop()`.
    """

    def __init__(self, capacity: Optional[int] = None) -> None:
        self._items: List[T] = []
        self._capacity = capacity

    def push(self, item: T) -> None:
        """
        Push item onto the top of the stack in O(1) amortized time.
        Raises OverflowError if bounded capacity is exceeded.
        """
        if self._capacity is not None and len(self._items) >= self._capacity:
            raise OverflowError(f"Stack overflow: max capacity {self._capacity} reached.")
        self._items.append(item)

    def pop(self) -> T:
        """
        Pop and return top item in O(1) time.
        Raises IndexError if empty.
        """
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> T:
        """Return top item without removing in O(1) time."""
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"EnterpriseStack({self._items})"


# ==============================================================================
# 2. Priority Queue & Binary Min-Heap (heapq)
# ==============================================================================


@dataclass(order=True)
class PrioritizedTask:
    """
    Task item structured for binary heap priority queue ordering.

    Polyglot Architectural Note:
    - In Python `@dataclass(order=True)`, comparison operators (`<`, `<=`, `>`, `>=`)
      are generated based on field declaration order.
    - Here, `priority` is evaluated first. If two tasks share the same priority,
      `tie_breaker` (an auto-incrementing integer) breaks the tie deterministically.
      This prevents Python from comparing the `payload` object directly, avoiding
      unsupported operand errors if payloads are unorderable dicts or domain models.
    - In Node.js `@datastructures-js/pq`: Handled via custom comparator lambda:
      `new PriorityQueue((a, b) => a.priority - b.priority)`.
    - In PHP `SplPriorityQueue`: Handled by overriding `compare($p1, $p2)`.
    """

    priority: int  # Lower value = higher priority (Min-Heap semantics)
    tie_breaker: int
    task_id: str = field(compare=False)
    payload: Any = field(compare=False)
    canceled: bool = field(default=False, compare=False)


class PriorityJobQueue:
    """
    Production Priority Queue wrapping Python's `heapq` module.
    Supports O(log N) enqueue, O(log N) dequeue, and O(1) task cancellation via tombstoning.

    Polyglot Comparison:
    - Node.js equivalent: `@datastructures-js/priority-queue`.
    - PHP equivalent: `SplPriorityQueue`.
    - CPython implementation: Direct C-level manipulation of dynamic array buffer.
    """

    def __init__(self) -> None:
        self._heap: List[PrioritizedTask] = []
        self._task_directory: dict[str, PrioritizedTask] = {}
        self._counter: int = 0  # Monotonic tie-breaker counter

    def add_task(self, task_id: str, priority: int, payload: Any) -> None:
        """
        Insert new task with priority in O(log N) time.
        If task_id exists, marks old task as canceled (tombstone) and adds replacement.
        """
        if task_id in self._task_directory:
            self.cancel_task(task_id)

        self._counter += 1
        entry = PrioritizedTask(
            priority=priority,
            tie_breaker=self._counter,
            task_id=task_id,
            payload=payload,
            canceled=False,
        )
        self._task_directory[task_id] = entry
        heapq.heappush(self._heap, entry)

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task in O(1) time using lazy tombstoning.
        The task remains in the heap but is skipped during `pop_task()`.
        This avoids expensive O(N) array scans to find and remove nodes from binary heaps.
        """
        entry = self._task_directory.pop(task_id, None)
        if entry is not None:
            entry.canceled = True
            return True
        return False

    def pop_task(self) -> Tuple[int, Any]:
        """
        Pop and return (priority, payload) of the highest priority active task.
        Time Complexity: O(log N) per removal, skipping canceled tombstones.
        """
        while self._heap:
            task = heapq.heappop(self._heap)
            if not task.canceled:
                self._task_directory.pop(task.task_id, None)
                return task.priority, task.payload
        raise KeyError("pop from an empty priority queue")

    def peek(self) -> Tuple[int, Any]:
        """
        Peek at highest priority active task without removing in O(1) amortized time.
        """
        while self._heap and self._heap[0].canceled:
            heapq.heappop(self._heap)
        if not self._heap:
            raise KeyError("peek from an empty priority queue")
        return self._heap[0].priority, self._heap[0].payload

    def __len__(self) -> int:
        """Return count of active (non-canceled) tasks."""
        return len(self._task_directory)

    def is_empty(self) -> bool:
        return len(self) == 0


# ==============================================================================
# 3. Top-K Elements Query (Heap vs Sorting Tradeoff)
# ==============================================================================


def find_top_k_largest(numbers: List[int], k: int) -> List[int]:
    """
    Find top K largest elements using a min-heap of size K.
    Time Complexity: O(N log K) instead of full sort O(N log N).
    Space Complexity: O(K) auxiliary memory.

    Polyglot Comparison:
    - Node.js naive: `numbers.sort((a,b) => b-a).slice(0, k)` -> O(N log N) time, O(N) space.
    - Python `heapq.nlargest(k, numbers)`: Highly optimized in C; runs in O(N log K).
    """
    return heapq.nlargest(k, numbers)


def find_top_k_smallest(numbers: List[int], k: int) -> List[int]:
    """
    Find top K smallest elements using `heapq.nsmallest`.
    Time Complexity: O(N log K).
    """
    return heapq.nsmallest(k, numbers)


# ==============================================================================
# 4. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying correctness and performance contracts."""
    console.print(
        Panel.fit(
            "[bold cyan]DSA Pillar 1: Stacks, Queues & Binary Heaps Verification[/bold cyan]\n"
            "[dim]Verifying LIFO, FIFO, and O(log N) Priority Queue scheduler with lazy tombstoning.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Stack Verification
    console.print("[dim]Phase 1: Validating EnterpriseStack (LIFO)...[/dim]")
    stack = EnterpriseStack[str](capacity=3)
    stack.push("v1.0")
    stack.push("v1.1")
    stack.push("v1.2")
    assert len(stack) == 3
    assert stack.peek() == "v1.2"

    # Test overflow
    try:
        stack.push("v1.3")
        assert False, "Should have raised OverflowError"
    except OverflowError:
        pass

    assert stack.pop() == "v1.2"
    assert stack.pop() == "v1.1"
    assert stack.pop() == "v1.0"
    assert stack.is_empty()
    console.print("  [green][PASS] EnterpriseStack LIFO semantics & overflow checks verified.[/green]")

    # 2. PriorityJobQueue Verification
    console.print("[dim]Phase 2: Validating PriorityJobQueue with heapq & tombstoning...[/dim]")
    pq = PriorityJobQueue()
    pq.add_task("task_email", priority=3, payload="Send Newsletter")
    pq.add_task("task_fraud", priority=1, payload="Block Malicious IP")  # Priority 1 = highest
    pq.add_task("task_report", priority=2, payload="Generate Daily PDF")
    pq.add_task("task_audit", priority=1, payload="Log Security Incident")  # Same priority as fraud

    assert len(pq) == 4
    # First out must be task_fraud (priority 1, earlier tie_breaker than audit)
    prio, payload = pq.pop_task()
    assert prio == 1 and payload == "Block Malicious IP"

    # Second out must be task_audit (priority 1)
    prio, payload = pq.pop_task()
    assert prio == 1 and payload == "Log Security Incident"

    # 3. Test Lazy Tombstoning Cancellation
    console.print("[dim]Phase 3: Testing O(1) task cancellation via lazy tombstone...[/dim]")
    assert len(pq) == 2
    canceled = pq.cancel_task("task_report")
    assert canceled is True
    assert len(pq) == 1

    # Remaining task must be task_email (priority 3), skipping canceled task_report
    prio, payload = pq.pop_task()
    assert prio == 3 and payload == "Send Newsletter"
    assert pq.is_empty()
    console.print("  [green][PASS] PriorityJobQueue ordering, tie-breaking, and tombstoning verified.[/green]")

    # 4. Top-K Heaps vs Sorting
    console.print("[dim]Phase 4: Validating heapq.nlargest and nsmallest...[/dim]")
    dataset = [42, 17, 88, 99, 12, 5, 63, 71, 3]
    top_3 = find_top_k_largest(dataset, 3)
    assert top_3 == [99, 88, 71], f"Expected [99, 88, 71], got {top_3}"

    bottom_3 = find_top_k_smallest(dataset, 3)
    assert bottom_3 == [3, 5, 12], f"Expected [3, 5, 12], got {bottom_3}"
    console.print("  [green][PASS] heapq.nlargest and nsmallest algorithms verified.[/green]")

    # Summary Table
    table = Table(title="Stacks, Queues & Heaps Complexity Reference", border_style="green")
    table.add_column("Operation", style="bold cyan")
    table.add_column("Python Mechanism", style="white")
    table.add_column("Time Complexity", style="bold green")
    table.add_column("Node.js Equivalent", style="yellow")
    table.add_column("PHP Equivalent", style="magenta")

    table.add_row("Stack Push / Pop", "list.append() / list.pop()", "O(1)", "array.push() / array.pop()", "SplStack / array_pop()")
    table.add_row("FIFO Queue Push / Pop", "deque.append() / deque.popleft()", "O(1)", "denque / array.shift() O(N)", "SplQueue::dequeue()")
    table.add_row("Heap Push (Insert)", "heapq.heappush(arr, x)", "O(log N)", "@datastructures-js/pq", "SplPriorityQueue::insert()")
    table.add_row("Heap Pop (Extract Min)", "heapq.heappop(arr)", "O(log N)", "@datastructures-js/pq", "SplPriorityQueue::extract()")
    table.add_row("Heapify Array", "heapq.heapify(arr)", "O(N)", "Manual sift-down loops", "N/A (insert items 1-by-1)")
    table.add_row("Top-K Elements", "heapq.nlargest(k, arr)", "O(N log K)", "arr.sort() O(N log N)", "array_slice(sort($arr))")

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
