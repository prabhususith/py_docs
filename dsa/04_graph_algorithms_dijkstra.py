"""
Graph Algorithms: Adjacency Lists, Dijkstra's Shortest Path & Topological Sort
=============================================================================
Description: Production implementation of directed weighted graphs, Dijkstra's Single-Source
             Shortest Path algorithm with path reconstruction, and Kahn's algorithm for
             Topological Sorting and cycle detection in Directed Acyclic Graphs (DAGs).

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * In TypeScript, graphs are typically modeled using `Map<string, Array<{ to: string, weight: number }>>`.
    Without a built-in min-heap, engineers either implement Dijkstra with an unoptimized O(V^2) array
    scan or import `@datastructures-js/priority-queue`.
  * Cycle detection in build tools (e.g. Webpack, Turborepo package dependency graphs) relies on
    Kahn's algorithm using JavaScript `Set` and `Map`.
- PHP / Laravel:
  * In PHP, graphs are modeled with nested associative arrays (`$graph[$u][] = ['node' => $v, 'w' => $weight]`).
    In Laravel, job batch dependencies (`Bus::batch()`) and service container circular dependency
    detection internally execute topological graph resolution.
  * Memory footprint: A PHP array representing a 10,000-node graph consumes ~4x–6x more memory
    than Python's compact dictionary due to Zend `zval` and `Bucket` allocation overhead.
- Memory & Performance Tradeoffs:
  * Python dictionaries use a split-table compact hash table (PEP 468/PEP 509) preserving insertion
    order and packing indices in a contiguous sparse array, maximizing cache locality.
  * Dijkstra using `heapq` runs in O((V + E) log V) time and O(V + E) space, providing optimal
    theoretical and practical efficiency for sparse networks (e.g., microservice route meshes).

Official Documentation References:
- Python heapq Module: https://docs.python.org/3/library/heapq.html
- Python Mapping Types (dict): https://docs.python.org/3/library/stdtypes.html#mapping-types-dict
- Python collections.deque: https://docs.python.org/3/library/collections.html#collections.deque
"""

from __future__ import annotations

import heapq
import sys
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

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
# 1. Directed Weighted Graph Representation
# ==============================================================================


@dataclass(frozen=True)
class Edge:
    """Directed weighted edge connecting two vertices."""

    target: str
    weight: float


class DirectedGraph:
    """
    Adjacency List representation of a Directed Weighted Graph.

    Polyglot Comparison:
    - Node.js: `class DirectedGraph { private adj = new Map<string, Edge[]>(); }`.
    - PHP: `class DirectedGraph { private array $adj = []; }`.
    """

    def __init__(self) -> None:
        # vertex -> list of outgoing Edges
        self._adjacency_list: Dict[str, List[Edge]] = {}

    def add_vertex(self, vertex: str) -> None:
        """Add vertex to graph if not present."""
        if vertex not in self._adjacency_list:
            self._adjacency_list[vertex] = []

    def add_edge(self, source: str, target: str, weight: float = 1.0) -> None:
        """Add directed edge from source to target with given weight."""
        if weight < 0:
            raise ValueError("Dijkstra requires non-negative edge weights.")
        self.add_vertex(source)
        self.add_vertex(target)
        self._adjacency_list[source].append(Edge(target=target, weight=weight))

    def get_neighbors(self, vertex: str) -> List[Edge]:
        """Return list of outgoing edges from vertex."""
        return self._adjacency_list.get(vertex, [])

    @property
    def vertices(self) -> List[str]:
        """Return list of all vertices."""
        return list(self._adjacency_list.keys())

    @property
    def vertex_count(self) -> int:
        return len(self._adjacency_list)

    @property
    def edge_count(self) -> int:
        return sum(len(edges) for edges in self._adjacency_list.values())

    def __repr__(self) -> str:
        return f"DirectedGraph(vertices={self.vertex_count}, edges={self.edge_count})"


# ==============================================================================
# 2. Dijkstra's Shortest Path Algorithm
# ==============================================================================


@dataclass
class ShortestPathResult:
    """Result payload from Dijkstra execution containing distance and path route."""

    source: str
    target: str
    total_cost: float
    path: List[str]


def dijkstra_shortest_path(
    graph: DirectedGraph,
    source: str,
    target: Optional[str] = None,
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """
    Dijkstra's Single-Source Shortest Path algorithm using a min-heap.

    Time Complexity: O((V + E) log V) where V is vertices, E is edges.
    Space Complexity: O(V) for distances and predecessors dictionaries.

    Polyglot Comparison:
    - Node.js: Requires `@datastructures-js/priority-queue` or manual array search.
    - PHP: Handled via custom `SplPriorityQueue` subclass inverted for Min-Heap.
    """
    if source not in graph.vertices:
        raise ValueError(f"Source vertex '{source}' not in graph.")

    # Distance map initialized to infinity
    distances: Dict[str, float] = {v: float("inf") for v in graph.vertices}
    distances[source] = 0.0

    # Predecessor map for path reconstruction
    predecessors: Dict[str, Optional[str]] = {v: None for v in graph.vertices}

    # Min-Heap stores tuples of: (cumulative_distance, current_vertex)
    priority_queue: List[Tuple[float, str]] = [(0.0, source)]

    visited: Set[str] = set()

    while priority_queue:
        current_dist, u = heapq.heappop(priority_queue)

        if u in visited:
            continue
        visited.add(u)

        # Early termination if target reached
        if target is not None and u == target:
            break

        # Stale distance check (tombstone optimization)
        if current_dist > distances[u]:
            continue

        for edge in graph.get_neighbors(u):
            v = edge.target
            weight = edge.weight

            if v in visited:
                continue

            new_dist = current_dist + weight
            if new_dist < distances[v]:
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(priority_queue, (new_dist, v))

    return distances, predecessors


def reconstruct_path(
    predecessors: Dict[str, Optional[str]],
    source: str,
    target: str,
) -> List[str]:
    """Reconstruct sequence of vertices from source to target using predecessor map."""
    path: List[str] = []
    current: Optional[str] = target

    while current is not None:
        path.append(current)
        if current == source:
            break
        current = predecessors.get(current)

    if not path or path[-1] != source:
        return []  # Target is unreachable from source

    path.reverse()
    return path


# ==============================================================================
# 3. Topological Sort & Cycle Detection (Kahn's Algorithm)
# ==============================================================================


def topological_sort_kahns(graph: DirectedGraph) -> Tuple[List[str], bool]:
    """
    Kahn's Algorithm for Topological Sorting of a Directed Acyclic Graph (DAG).
    Simultaneously discovers valid linear dependency order and detects cyclic dependencies.

    Time Complexity: O(V + E)
    Space Complexity: O(V) for in-degree map and FIFO queue.

    Polyglot Comparison:
    - Node.js: Used in build systems (Nx/Turborepo/Lerna) to determine package build order.
    - PHP: Used in Laravel service container to resolve constructor dependency graphs.

    Returns:
        Tuple of (sorted_order: List[str], has_cycle: bool)
    """
    # 1. Compute in-degree for every vertex
    in_degrees: Dict[str, int] = {v: 0 for v in graph.vertices}
    for u in graph.vertices:
        for edge in graph.get_neighbors(u):
            in_degrees[edge.target] += 1

    # 2. Enqueue all vertices with in-degree 0 (no prerequisites)
    queue: deque[str] = deque([v for v, deg in in_degrees.items() if deg == 0])

    topological_order: List[str] = []

    # 3. Process vertices
    while queue:
        u = queue.popleft()  # O(1) in collections.deque
        topological_order.append(u)

        for edge in graph.get_neighbors(u):
            v = edge.target
            in_degrees[v] -= 1
            if in_degrees[v] == 0:
                queue.append(v)

    # If topological order contains all vertices, no cycles exist
    has_cycle = len(topological_order) < graph.vertex_count
    return topological_order, has_cycle


# ==============================================================================
# 4. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying graph modeling, Dijkstra, and Kahn's algorithm."""
    console.print(
        Panel.fit(
            "[bold cyan]DSA Pillar 1: Graph Algorithms & Dijkstra Verification[/bold cyan]\n"
            "[dim]Verifying Adjacency List graph, Dijkstra's shortest path, and Kahn's DAG topological sort.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Build Network Mesh
    console.print("[dim]Phase 1: Building microservice latency network graph...[/dim]")
    network = DirectedGraph()
    # Microservice network with latency weights (ms)
    network.add_edge("Gateway", "Auth", 12.0)
    network.add_edge("Gateway", "Inventory", 25.0)
    network.add_edge("Auth", "UserDB", 8.0)
    network.add_edge("Auth", "Payment", 18.0)
    network.add_edge("Inventory", "Payment", 10.0)
    network.add_edge("Payment", "Notification", 5.0)
    network.add_edge("UserDB", "Notification", 30.0)

    assert network.vertex_count == 6
    assert network.edge_count == 7
    console.print(f"  [green][PASS] Graph initialized with {network.vertex_count} nodes and {network.edge_count} edges.[/green]")

    # 2. Run Dijkstra's Algorithm
    console.print("[dim]Phase 2: Executing Dijkstra's algorithm from 'Gateway' to 'Notification'...[/dim]")
    distances, predecessors = dijkstra_shortest_path(network, source="Gateway", target="Notification")

    # Path 1: Gateway -> Auth (12) -> Payment (18) -> Notification (5) = 35.0 ms
    # Path 2: Gateway -> Inventory (25) -> Payment (10) -> Notification (5) = 40.0 ms
    # Optimal shortest path is Path 1 with 35.0 ms
    assert distances["Notification"] == 35.0, f"Expected 35.0 ms, got {distances['Notification']}"

    path = reconstruct_path(predecessors, source="Gateway", target="Notification")
    assert path == ["Gateway", "Auth", "Payment", "Notification"]
    console.print(f"  [green][PASS] Shortest path verified: {' -> '.join(path)} (Cost: {distances['Notification']} ms).[/green]")

    # 3. Topological Sort & Dependency DAG
    console.print("[dim]Phase 3: Testing Kahn's Algorithm on build pipeline DAG...[/dim]")
    build_dag = DirectedGraph()
    build_dag.add_edge("CompileCode", "RunUnitTests")
    build_dag.add_edge("RunUnitTests", "BuildDockerImage")
    build_dag.add_edge("GenerateDocs", "BuildDockerImage")
    build_dag.add_edge("BuildDockerImage", "DeployStaging")

    sorted_order, has_cycle = topological_sort_kahns(build_dag)
    assert not has_cycle, "DAG should not have cycles."
    assert len(sorted_order) == 5

    # Verify dependencies precede dependents
    assert sorted_order.index("CompileCode") < sorted_order.index("RunUnitTests")
    assert sorted_order.index("RunUnitTests") < sorted_order.index("BuildDockerImage")
    assert sorted_order.index("BuildDockerImage") < sorted_order.index("DeployStaging")
    console.print(f"  [green][PASS] Valid topological order: {' -> '.join(sorted_order)}[/green]")

    # 4. Cycle Detection Test
    console.print("[dim]Phase 4: Testing cycle detection in circular dependency graph...[/dim]")
    cyclic_graph = DirectedGraph()
    cyclic_graph.add_edge("ServiceA", "ServiceB")
    cyclic_graph.add_edge("ServiceB", "ServiceC")
    cyclic_graph.add_edge("ServiceC", "ServiceA")  # Creates cycle: A -> B -> C -> A

    _, cyclic_flag = topological_sort_kahns(cyclic_graph)
    assert cyclic_flag is True, "Cyclic graph must be detected."
    console.print("  [green][PASS] Circular dependency cycle successfully detected by Kahn's algorithm.[/green]")

    # Summary Table
    table = Table(title="Graph Algorithms & Complexity Reference", border_style="green")
    table.add_column("Algorithm", style="bold cyan")
    table.add_column("Core Mechanism", style="white")
    table.add_column("Time Complexity", style="bold green")
    table.add_column("Space Complexity", style="bold green")
    table.add_column("Polyglot Equivalent", style="yellow")

    table.add_row("Dijkstra Shortest Path", "Min-Heap priority queue (`heapq`)", "O((V + E) log V)", "O(V)", "Node.js `@datastructures-js/pq` / PHP `SplPriorityQueue`")
    table.add_row("Topological Sort", "Kahn's algorithm (in-degrees + deque)", "O(V + E)", "O(V)", "Webpack / Turborepo / Laravel Container DAG")
    table.add_row("Cycle Detection", "Kahn's vertex count check", "O(V + E)", "O(V)", "Circular dependency validation")

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
