"""
Linked Lists & Double-Ended Queues (Deques) Architecture
=========================================================
Description: Production implementation of Singly Linked List data structure and standard
             library `collections.deque` (Double-Ended Queue). Explores node pointer management,
             O(1) bidirectional mutations, memory layouts, and algorithmic tradeoffs.

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * In V8, JavaScript arrays (`[]`) are dynamic arrays. Calling `array.shift()` or `array.unshift()`
    is an O(N) operation because V8 must shift and re-index all remaining elements in the underlying
    contiguous backing store. Developers mistakenly use `Array` as a FIFO queue, causing quadratic
    O(N^2) bottlenecks in event stream processors.
  * Node.js lacks a native deque in the standard library, requiring third-party libraries
    (e.g., `denque` or `@datastructures-js/deque`).
- PHP / Laravel:
  * PHP provides `SplDoublyLinkedList` in the Standard PHP Library (SPL), which offers O(1)
    push/pop/shift/unshift. However, each node in SPL incurs substantial memory overhead due to
    Zend Engine `zval` struct wrappers and reference-counting metadata.
  * Laravel Collections (`collect([...])`) wrap native PHP arrays (Zend Hash Tables), where `shift()`
    re-indexes numeric keys via `array_shift()`, resulting in O(N) complexity.
- Memory & Performance Tradeoffs:
  * Python `list` is a contiguous dynamic array of pointer references (like V8 JS Arrays).
  * Python `collections.deque` is implemented in C as a doubly linked list of 64-element
    unrolled blocks (`BLOCKLEN = 64`). This achieves O(1) appends and pops from both ends, minimizes
    malloc fragmentation, and retains excellent CPU L1/L2 cache locality compared to traditional
    node-per-element linked lists.

Official Documentation References:
- Python collections.deque: https://docs.python.org/3/library/collections.html#collections.deque
- Python Data Structures: https://docs.python.org/3/tutorial/datastructures.html
- CPython deque source implementation: https://github.com/python/cpython/blob/main/Modules/_collectionsmodule.c
"""

from __future__ import annotations

import sys
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Generic, Iterator, Optional, TypeVar

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
# 1. Singly Linked List Implementation
# ==============================================================================


@dataclass
class ListNode(Generic[T]):
    """
    Individual node in a Singly Linked List.

    Polyglot Comparison:
    - Node.js: Analogous to `{ value: T, next: ListNode<T> | null }` object literal.
      V8 allocates this in the V8 heap as a JSObject with hidden class (Shape/Map) transitions.
    - PHP: Analogous to a class with `public mixed $value; public ?ListNode $next = null;`.
      Each instance consumes a Zend Object structure (~32-48 bytes overhead plus zval).
    - Python: Implemented using `@dataclass`. Under standard CPython, each node has `__dict__`
      unless `__slots__` is defined. Here, we prioritize clear structural typing.
    """

    value: T
    next: Optional[ListNode[T]] = None


class SinglyLinkedList(Generic[T]):
    """
    Singly Linked List with head pointer, size tracking, and O(1) prepend / O(N) append.

    Polyglot Architectural Analysis:
    - In TypeScript: Often written manually or via linked list packages. Without manual memory
      management, V8 garbage collector (Orinoco/Scavenger) traverses the reference chain.
    - In PHP: Replaces manual pointer loops. PHP's circular reference garbage collector handles
      unreachable cycles, but memory is freed immediately upon scope exit if strictly linear.
    - In Python: Supports native Python protocols: `len(ll)` via `__len__`, `iter(ll)` via `__iter__`,
      and pretty printing via `__repr__`.
    """

    def __init__(self) -> None:
        """Initialize an empty Singly Linked List."""
        self._head: Optional[ListNode[T]] = None
        self._size: int = 0

    def __len__(self) -> int:
        """
        Return the number of elements in O(1) time.
        PHP equivalent: Implementing the `Countable` interface (`count($list)`).
        Node.js equivalent: Getter property `get length(): number`.
        """
        return self._size

    def is_empty(self) -> bool:
        """Check if linked list contains zero nodes."""
        return self._head is None

    def prepend(self, value: T) -> None:
        """
        Insert value at the front of the list in O(1) time and O(1) space.

        Node.js equivalent: `array.unshift(value)` (O(N) - slow, shifts entire array).
        PHP equivalent: `$splDoublyLinkedList->unshift($value)` (O(1)).
        """
        new_node = ListNode(value=value, next=self._head)
        self._head = new_node
        self._size += 1

    def append(self, value: T) -> None:
        """
        Insert value at the end of the list in O(N) time (without tail pointer).

        Node.js equivalent: `array.push(value)` (O(1) amortized).
        PHP equivalent: `$splDoublyLinkedList->push($value)` (O(1)).
        """
        new_node = ListNode(value=value)
        if self._head is None:
            self._head = new_node
        else:
            current = self._head
            while current.next is not None:
                current = current.next
            current.next = new_node
        self._size += 1

    def delete(self, value: T) -> bool:
        """
        Remove the first node matching `value`. Returns True if found and removed.
        Time Complexity: O(N) search + O(1) pointer redirection.
        Space Complexity: O(1).

        Node.js equivalent: `const idx = arr.indexOf(val); if(idx !== -1) arr.splice(idx, 1);`
        PHP equivalent: Unsetting key in array and calling `array_values()` to re-index.
        """
        current = self._head
        previous: Optional[ListNode[T]] = None

        while current is not None:
            if current.value == value:
                if previous is None:
                    # Deleting head node
                    self._head = current.next
                else:
                    previous.next = current.next
                self._size -= 1
                return True
            previous = current
            current = current.next

        return False

    def search(self, target: T) -> Optional[int]:
        """
        Search for `target` value, returning 0-based index or None if absent.
        Time Complexity: O(N) linear scan.
        """
        current = self._head
        index = 0
        while current is not None:
            if current.value == target:
                return index
            current = current.next
            index += 1
        return None

    def __iter__(self) -> Iterator[T]:
        """
        Generator protocol enabling `for item in linked_list:`.
        Node.js equivalent: Implementing `[Symbol.iterator]()` generator method.
        PHP equivalent: Implementing the `Iterator` or `IteratorAggregate` interface.
        """
        current = self._head
        while current is not None:
            yield current.value
            current = current.next

    def __repr__(self) -> str:
        """String representation showing arrow pointer chain."""
        nodes = [str(val) for val in self]
        return " -> ".join(nodes) + " -> None" if nodes else "EmptyList"


# ==============================================================================
# 2. High-Performance Double-Ended Queue (collections.deque)
# ==============================================================================


class EnterpriseFastQueue(Generic[T]):
    """
    Thread-safe, double-ended queue wrapping CPython's C-accelerated `collections.deque`.

    Polyglot Comparison:
    - Node.js (TypeScript):
      * When developers write `const queue = []; queue.push(item); queue.shift();`, the `shift()`
        operation forces V8 to re-index the array in O(N) time. For 100,000 items, this turns an
        O(N) batch pipeline into an O(N^2) processing disaster.
      * Python's `collections.deque.popleft()` is strictly O(1) in C, making it the production
        standard for message brokers, BFS graph traversals, and sliding window buffers.
    - PHP (Laravel):
      * In Laravel, `$collection->shift()` internally calls `array_shift()`, which in PHP's C source
        re-keys all integer indexes in the Zend Hash Table, incurring O(N) execution time.
      * `SplDoublyLinkedList` / `SplQueue` offers O(1) dequeue, but lacks Python's block-unrolling
        cache locality (`BLOCKLEN = 64`), creating higher heap fragmentation.
    """

    def __init__(self, maxlen: Optional[int] = None) -> None:
        """
        Initialize deque with optional bounded capacity (ring-buffer mode).
        If `maxlen` is specified, appending beyond capacity automatically discards
        elements from the opposing end in O(1) time without raising exceptions.
        """
        self._deque: deque[T] = deque(maxlen=maxlen)

    def enqueue_right(self, item: T) -> None:
        """
        Push item to the right side (tail) in O(1) time.
        Node.js equivalent: `array.push(item)` (O(1)).
        PHP equivalent: `$splQueue->enqueue($item)` (O(1)).
        """
        self._deque.append(item)

    def enqueue_left(self, item: T) -> None:
        """
        Push item to the left side (head) in O(1) time.
        Node.js equivalent: `array.unshift(item)` (O(N) - SLOW).
        PHP equivalent: `$splDoublyLinkedList->unshift($item)` (O(1)).
        """
        self._deque.appendleft(item)

    def dequeue_left(self) -> T:
        """
        Pop and return item from the left side (FIFO queue behavior) in O(1) time.
        Raises IndexError if empty.

        Node.js equivalent: `array.shift()` (O(N) - SLOW).
        PHP equivalent: `$splQueue->dequeue()` (O(1)).
        """
        if not self._deque:
            raise IndexError("dequeue from empty queue")
        return self._deque.popleft()

    def dequeue_right(self) -> T:
        """
        Pop and return item from the right side (LIFO stack behavior) in O(1) time.
        Raises IndexError if empty.

        Node.js equivalent: `array.pop()` (O(1)).
        PHP equivalent: `$splDoublyLinkedList->pop()` (O(1)).
        """
        if not self._deque:
            raise IndexError("pop from empty queue")
        return self._deque.pop()

    def peek_left(self) -> T:
        """Peek at head without removing in O(1) time."""
        if not self._deque:
            raise IndexError("peek from empty queue")
        return self._deque[0]

    def peek_right(self) -> T:
        """Peek at tail without removing in O(1) time."""
        if not self._deque:
            raise IndexError("peek from empty queue")
        return self._deque[-1]

    def rotate(self, steps: int = 1) -> None:
        """
        Rotate deque `steps` to the right (positive) or left (negative) in O(K) time.
        Useful for round-robin scheduler implementations.
        """
        self._deque.rotate(steps)

    def __len__(self) -> int:
        return len(self._deque)

    def __iter__(self) -> Iterator[T]:
        return iter(self._deque)

    def __repr__(self) -> str:
        return f"EnterpriseFastQueue({list(self._deque)})"


# ==============================================================================
# 3. Micro-Benchmark: Python list.pop(0) vs collections.deque.popleft()
# ==============================================================================


def benchmark_list_vs_deque(element_count: int = 30_000) -> Tuple[float, float, float]:
    """
    Demonstrates the concrete performance delta between O(N) array shifts and O(1) deque pops.
    Simulates high-throughput queue operations (such as consumer message polling).

    Returns:
        Tuple of (list_time_seconds, deque_time_seconds, speedup_factor)
    """
    # 1. Benchmark Python list.pop(0) -> O(N) per pop -> O(N^2) total
    test_list = list(range(element_count))
    t0 = time.perf_counter()
    while test_list:
        test_list.pop(0)
    list_time = time.perf_counter() - t0

    # 2. Benchmark collections.deque.popleft() -> O(1) per pop -> O(N) total
    test_deque = deque(range(element_count))
    t1 = time.perf_counter()
    while test_deque:
        test_deque.popleft()
    deque_time = time.perf_counter() - t1

    speedup = list_time / max(deque_time, 1e-9)
    return list_time, deque_time, speedup


# ==============================================================================
# 4. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying correctness and performance contracts."""
    console.print(
        Panel.fit(
            "[bold cyan]DSA Pillar 1: Linked Lists & Deques Verification[/bold cyan]\n"
            "[dim]Comparing Python linked memory structures with Node.js V8 arrays & PHP SPL.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Singly Linked List Verification
    console.print("[dim]Phase 1: Validating SinglyLinkedList pointer manipulation...[/dim]")
    sll = SinglyLinkedList[str]()
    assert sll.is_empty(), "Initial list must be empty."
    assert len(sll) == 0

    sll.append("AuthService")
    sll.append("PaymentService")
    sll.prepend("APIGateway")
    # Expected order: APIGateway -> AuthService -> PaymentService -> None
    assert len(sll) == 3
    assert list(sll) == ["APIGateway", "AuthService", "PaymentService"]
    assert sll.search("AuthService") == 1
    assert sll.search("NonExistent") is None

    # Delete middle node
    deleted = sll.delete("AuthService")
    assert deleted is True
    assert list(sll) == ["APIGateway", "PaymentService"]
    assert len(sll) == 2

    # Delete head node
    deleted_head = sll.delete("APIGateway")
    assert deleted_head is True
    assert list(sll) == ["PaymentService"]
    assert len(sll) == 1
    console.print("  [green][PASS] SinglyLinkedList prepend, append, delete, search passed.[/green]")

    # 2. EnterpriseFastQueue (deque) Verification
    console.print("[dim]Phase 2: Validating EnterpriseFastQueue O(1) double-ended operations...[/dim]")
    q = EnterpriseFastQueue[int](maxlen=5)
    for val in [10, 20, 30]:
        q.enqueue_right(val)
    assert len(q) == 3
    assert q.peek_left() == 10
    assert q.peek_right() == 30

    # Pop FIFO
    first_out = q.dequeue_left()
    assert first_out == 10
    assert len(q) == 2

    # Bounded maxlen overflow test
    q_bounded = EnterpriseFastQueue[str](maxlen=3)
    q_bounded.enqueue_right("A")
    q_bounded.enqueue_right("B")
    q_bounded.enqueue_right("C")
    # Appending 4th element should evict 'A' from the left
    q_bounded.enqueue_right("D")
    assert list(q_bounded) == ["B", "C", "D"]
    assert len(q_bounded) == 3

    # Rotation test (Round-Robin)
    q_bounded.rotate(1)
    assert list(q_bounded) == ["D", "B", "C"]
    console.print("  [green][PASS] EnterpriseFastQueue bounded ring-buffer & rotation passed.[/green]")

    # 3. Algorithmic Benchmark: O(N) vs O(1)
    console.print("[dim]Phase 3: Running micro-benchmark (30,000 pops: list.pop(0) vs deque.popleft())...[/dim]")
    list_time, deque_time, speedup = benchmark_list_vs_deque(30_000)
    console.print(f"  • list.pop(0) (O(N) re-indexing) : {list_time * 1000:.2f} ms")
    console.print(f"  • deque.popleft() (O(1) pointer) : {deque_time * 1000:.2f} ms")
    console.print(f"  • Deque Performance Speedup     : [bold green]{speedup:.1f}x faster[/bold green]")
    assert speedup > 5.0, "deque should be orders of magnitude faster than list.pop(0)."

    # Summary Table
    table = Table(title="Linked Lists & Deque Architecture Matrix", border_style="green")
    table.add_column("Data Structure", style="bold cyan")
    table.add_column("Prepend / Shift", style="white")
    table.add_column("Append / Push", style="white")
    table.add_column("Node.js Equivalent", style="yellow")
    table.add_column("PHP Equivalent", style="magenta")

    table.add_row(
        "SinglyLinkedList",
        "O(1)",
        "O(N)",
        "Custom class (V8 heap objects)",
        "Custom class (Zend zvals)",
    )
    table.add_row(
        "Python list",
        "O(N) (pop(0)/insert(0))",
        "O(1) amortized",
        "Array (`[]`) with `shift()` O(N)",
        "Array (`$arr[]`) with `array_shift()` O(N)",
    )
    table.add_row(
        "collections.deque",
        "O(1) (popleft/appendleft)",
        "O(1)",
        "`denque` / `@datastructures-js/deque`",
        "`SplDoublyLinkedList` / `SplQueue`",
    )

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
