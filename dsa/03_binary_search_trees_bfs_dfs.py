"""
Binary Search Trees (BST), BFS, and DFS Traversals
==================================================
Description: Production implementation of Binary Search Trees (BST), Breadth-First Search (BFS /
             level-order traversal), and Depth-First Search (DFS: in-order, pre-order, post-order).
             Explores node insertion, deletion with in-order successors, iterative vs recursive
             algorithms, and call-stack limits across runtimes.

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * In V8, recursive DFS execution is limited by the V8 C++ stack size (~10,000 frames). Exceeding
    this throws `RangeError: Maximum call stack size exceeded`. Production engines prefer iterative
    DFS with an explicit heap-allocated array stack (`const stack = [root]`) to prevent stack overflow.
  * Tree nodes in TypeScript: `interface TreeNode<T> { val: T; left?: TreeNode<T>; right?: TreeNode<T>; }`.
- PHP / Laravel:
  * In PHP, deep recursion triggers `Fatal error: Maximum function nesting level of '256' reached`
    when Xdebug is enabled, or fatal C segmentation faults under standard Zend Engine if stack frames
    exceed native OS stack limits (usually 8MB thread stack).
  * PHP arrays are often misused as ad-hoc adjacency trees, creating high memory overhead
    (Zend Hash Tables consume ~56 bytes minimum per bucket entry).
- Memory & Performance Tradeoffs:
  * Python enforces a strict recursion limit via `sys.getrecursionlimit()` (default: 1,000).
    Deeply skewed trees (e.g., sorted insertions without self-balancing AVL/Red-Black rotation)
    will raise `RecursionError`.
  * Production Python systems implement iterative BFS with `collections.deque` (O(1) popleft) and
    iterative DFS with `list` (O(1) pop) to avoid recursion limits entirely.

Official Documentation References:
- Python Data Structures: https://docs.python.org/3/tutorial/datastructures.html
- Python sys recursion limit: https://docs.python.org/3/library/sys.html#sys.setrecursionlimit
- CPython Execution Model: https://docs.python.org/3/reference/executionmodel.html
"""

from __future__ import annotations

import sys
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Generator, Generic, List, Optional, Tuple, TypeVar

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
# 1. Binary Tree Node Representation
# ==============================================================================


@dataclass
class BSTNode(Generic[T]):
    """
    Binary Search Tree Node holding a comparable key and left/right subtree pointers.

    Polyglot Comparison:
    - Node.js: `{ key: number, left: BSTNode | null, right: BSTNode | null }`.
    - PHP: Class with `public int $key; public ?BSTNode $left = null; public ?BSTNode $right = null;`.
    """

    key: int
    payload: Optional[T] = None
    left: Optional[BSTNode[T]] = None
    right: Optional[BSTNode[T]] = None


# ==============================================================================
# 2. Binary Search Tree (BST) Engine
# ==============================================================================


class BinarySearchTree(Generic[T]):
    """
    Production Binary Search Tree supporting insertion, search, deletion,
    and multiple traversal strategies.
    """

    def __init__(self) -> None:
        self._root: Optional[BSTNode[T]] = None
        self._node_count: int = 0

    @property
    def root(self) -> Optional[BSTNode[T]]:
        """Expose root node reference."""
        return self._root

    def is_empty(self) -> bool:
        return self._root is None

    def __len__(self) -> int:
        return self._node_count

    # --------------------------------------------------------------------------
    # Insertion (Iterative to avoid Python recursion limit)
    # --------------------------------------------------------------------------

    def insert(self, key: int, payload: Optional[T] = None) -> None:
        """
        Insert key/payload into BST in O(log N) average, O(N) worst case.
        Implemented iteratively to eliminate `RecursionError` on skewed inputs.

        Node.js equivalent: Iterative while loop updating `curr = curr.left/right`.
        PHP equivalent: Identical iterative pointer progression.
        """
        new_node = BSTNode(key=key, payload=payload)
        if self._root is None:
            self._root = new_node
            self._node_count += 1
            return

        current = self._root
        while True:
            if key < current.key:
                if current.left is None:
                    current.left = new_node
                    self._node_count += 1
                    break
                current = current.left
            elif key > current.key:
                if current.right is None:
                    current.right = new_node
                    self._node_count += 1
                    break
                current = current.right
            else:
                # Key already exists: update payload in-place
                current.payload = payload
                break

    # --------------------------------------------------------------------------
    # Search / Lookup
    # --------------------------------------------------------------------------

    def search(self, key: int) -> Optional[T]:
        """
        Find payload by key in O(log N) average time. Returns None if not found.
        """
        current = self._root
        while current is not None:
            if key == current.key:
                return current.payload
            elif key < current.key:
                current = current.left
            else:
                current = current.right
        return None

    def contains(self, key: int) -> bool:
        """Check if key exists in BST in O(log N) time."""
        return self.search(key) is not None or (self.search_node(key) is not None)

    def search_node(self, key: int) -> Optional[BSTNode[T]]:
        """Return the BSTNode matching key, or None."""
        current = self._root
        while current is not None:
            if key == current.key:
                return current
            elif key < current.key:
                current = current.left
            else:
                current = current.right
        return None

    # --------------------------------------------------------------------------
    # Deletion (Handles 0, 1, or 2 children with In-Order Successor)
    # --------------------------------------------------------------------------

    def delete(self, key: int) -> bool:
        """
        Delete node by key. Returns True if node was found and removed.
        Three cases:
        1. Leaf node: simply remove pointer.
        2. Single child: splice child to parent.
        3. Two children: replace with in-order successor (minimum node in right subtree).
        """
        initial_count = self._node_count
        self._root = self._delete_recursive(self._root, key)
        return self._node_count < initial_count

    def _delete_recursive(self, node: Optional[BSTNode[T]], key: int) -> Optional[BSTNode[T]]:
        if node is None:
            return None

        if key < node.key:
            node.left = self._delete_recursive(node.left, key)
        elif key > node.key:
            node.right = self._delete_recursive(node.right, key)
        else:
            # Node to delete found
            self._node_count -= 1

            # Case 1 & 2: 0 or 1 child
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left

            # Case 3: 2 children. Find in-order successor (min of right subtree)
            successor = self._find_min_node(node.right)
            node.key = successor.key
            node.payload = successor.payload
            # Restore count temporarily because the recursive call will decrement it
            self._node_count += 1
            node.right = self._delete_recursive(node.right, successor.key)

        return node

    def _find_min_node(self, node: BSTNode[T]) -> BSTNode[T]:
        current = node
        while current.left is not None:
            current = current.left
        return current

    # --------------------------------------------------------------------------
    # Breadth-First Search (BFS / Level-Order)
    # --------------------------------------------------------------------------

    def bfs_level_order(self) -> List[int]:
        """
        Breadth-First Search (Level-Order) traversal using an O(1) queue (`collections.deque`).
        Time Complexity: O(N) visits every node exactly once.
        Space Complexity: O(W) where W is max width of the tree (up to N/2 in full binary tree).

        Polyglot Comparison:
        - Node.js: Requires `denque` or array with slow `shift()`.
        - PHP: Handled via `SplQueue`.
        """
        if self._root is None:
            return []

        results: List[int] = []
        queue: deque[BSTNode[T]] = deque([self._root])

        while queue:
            node = queue.popleft()  # O(1) in C
            results.append(node.key)
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)

        return results

    # --------------------------------------------------------------------------
    # Depth-First Search (DFS) Traversals
    # --------------------------------------------------------------------------

    def dfs_in_order(self) -> List[int]:
        """
        In-order traversal (Left -> Root -> Right).
        Produces strictly monotonically ascending sorted keys in a valid BST.
        """
        results: List[int] = []

        def _traverse(node: Optional[BSTNode[T]]) -> None:
            if node is not None:
                _traverse(node.left)
                results.append(node.key)
                _traverse(node.right)

        _traverse(self._root)
        return results

    def dfs_pre_order(self) -> List[int]:
        """
        Pre-order traversal (Root -> Left -> Right).
        Used for tree serialization, cloning, and prefix expression evaluation.
        """
        results: List[int] = []

        def _traverse(node: Optional[BSTNode[T]]) -> None:
            if node is not None:
                results.append(node.key)
                _traverse(node.left)
                _traverse(node.right)

        _traverse(self._root)
        return results

    def dfs_post_order(self) -> List[int]:
        """
        Post-order traversal (Left -> Right -> Root).
        Used for bottom-up operations, memory deallocation, and directory size calculations.
        """
        results: List[int] = []

        def _traverse(node: Optional[BSTNode[T]]) -> None:
            if node is not None:
                _traverse(node.left)
                _traverse(node.right)
                results.append(node.key)

        _traverse(self._root)
        return results

    def dfs_in_order_iterative(self) -> List[int]:
        """
        Iterative in-order traversal using an explicit stack.
        Guarantees zero risk of `RecursionError` regardless of tree depth.
        Time: O(N), Space: O(H) where H is tree height.
        """
        results: List[int] = []
        stack: List[BSTNode[T]] = []
        current = self._root

        while current is not None or stack:
            # Reach the leftmost node of current
            while current is not None:
                stack.append(current)
                current = current.left

            current = stack.pop()
            results.append(current.key)
            current = current.right

        return results


# ==============================================================================
# 3. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying BST operations, traversals, and recursion bounds."""
    console.print(
        Panel.fit(
            "[bold cyan]DSA Pillar 1: Binary Search Trees, BFS & DFS Verification[/bold cyan]\n"
            "[dim]Verifying BST invariants, in-order successor deletion, level-order BFS, and DFS orders.[/dim]",
            border_style="cyan",
        )
    )

    # 1. BST Insertion & In-Order Property
    console.print("[dim]Phase 1: Validating BST insertion and sorted in-order traversal...[/dim]")
    bst = BinarySearchTree[str]()
    # Insert keys: 50, 30, 70, 20, 40, 60, 80
    keys_to_insert = [50, 30, 70, 20, 40, 60, 80]
    for k in keys_to_insert:
        bst.insert(k, f"Payload_{k}")

    assert len(bst) == 7
    in_order_keys = bst.dfs_in_order()
    assert in_order_keys == [20, 30, 40, 50, 60, 70, 80], f"In-order must be sorted, got {in_order_keys}"

    # Verify iterative in-order matches recursive
    iterative_in_order = bst.dfs_in_order_iterative()
    assert iterative_in_order == in_order_keys, "Iterative in-order does not match recursive in-order."
    console.print("  [green][PASS] BST insertion and in-order sorted traversal verified.[/green]")

    # 2. Search & Lookup
    console.print("[dim]Phase 2: Validating BST search lookups...[/dim]")
    assert bst.search(40) == "Payload_40"
    assert bst.search(999) is None
    assert bst.contains(70) is True
    assert bst.contains(123) is False
    console.print("  [green][PASS] O(log N) search lookups verified.[/green]")

    # 3. BFS (Level-Order) and DFS Traversals
    console.print("[dim]Phase 3: Validating BFS level-order, pre-order, and post-order...[/dim]")
    bfs_result = bst.bfs_level_order()
    assert bfs_result == [50, 30, 70, 20, 40, 60, 80], f"Expected BFS [50, 30, 70, 20, 40, 60, 80], got {bfs_result}"

    pre_order_result = bst.dfs_pre_order()
    assert pre_order_result == [50, 30, 20, 40, 70, 60, 80]

    post_order_result = bst.dfs_post_order()
    assert post_order_result == [20, 40, 30, 60, 80, 70, 50]
    console.print("  [green][PASS] BFS level-order and DFS (pre/in/post) verified.[/green]")

    # 4. Deletion Cases (0, 1, and 2 children)
    console.print("[dim]Phase 4: Validating deletion (Leaf, Single Child, Two Children with In-Order Successor)...[/dim]")
    # Case 1: Leaf node (20)
    assert bst.delete(20) is True
    assert len(bst) == 6
    assert bst.dfs_in_order() == [30, 40, 50, 60, 70, 80]

    # Case 2: Node with single child (30 has right child 40)
    assert bst.delete(30) is True
    assert len(bst) == 5
    assert bst.dfs_in_order() == [40, 50, 60, 70, 80]

    # Case 3: Root with two children (50 has children 40 and 70)
    assert bst.delete(50) is True
    assert len(bst) == 4
    # Root 50 is replaced by successor 60
    assert bst.root is not None and bst.root.key == 60
    assert bst.dfs_in_order() == [40, 60, 70, 80]
    console.print("  [green][PASS] All 3 deletion cases (in-order successor) verified.[/green]")

    # Summary Table
    table = Table(title="Tree Traversal & Complexity Architecture", border_style="green")
    table.add_column("Traversal / Op", style="bold cyan")
    table.add_column("Order / Mechanism", style="white")
    table.add_column("Time Complexity", style="bold green")
    table.add_column("Space Complexity", style="bold green")
    table.add_column("Node.js / PHP Equivalent", style="yellow")

    table.add_row("BST Search / Insert", "Binary split (Left < Root < Right)", "O(log N) avg, O(N) worst", "O(1) iterative", "Custom object pointers")
    table.add_row("BFS (Level-Order)", "FIFO Queue (`deque.popleft()`)", "O(N)", "O(W) max width", "`denque` / `SplQueue`")
    table.add_row("DFS In-Order", "Left -> Root -> Right", "O(N)", "O(H) height", "Recursive or stack loop")
    table.add_row("DFS Pre-Order", "Root -> Left -> Right", "O(N)", "O(H) height", "Tree serialization")
    table.add_row("DFS Post-Order", "Left -> Right -> Root", "O(N)", "O(H) height", "Bottom-up memory free")

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
