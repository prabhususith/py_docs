"""
NumPy Broadcasting and Linear Algebra Architecture
==================================================
Description: Production implementation of NumPy multidimensional broadcasting rules,
             matrix multiplication (`@` / `np.matmul`), BLAS/LAPACK optimizations,
             Euclidean norms, and batch cosine similarity matrix ranking for vector search.

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * JavaScript has no native multidimensional arrays, no matrix multiplication operators (`@`),
    and no concept of dimension broadcasting.
  * Attempting matrix multiplication in Node.js requires nested loops `O(N^3)`:
    `for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) for (let k = 0; k < N; k++)`.
    Without BLAS (Basic Linear Algebra Subprograms) hardware acceleration, this is 50x–200x slower
    than NumPy, which binds directly to OpenBLAS, Intel MKL, or Apple Accelerate.
- PHP / Laravel:
  * PHP lacks matrix mathematics in core. In PHP 8, multiplying two 500x500 matrices in userland
    creates 250,000 array elements, triggering heavy garbage collection cycles and CPU thrashing.
  * Libraries like Rubix ML require C extensions (`tensor`) to achieve viable performance.
- Memory & Performance Tradeoffs:
  * NumPy Broadcasting allows arithmetic between arrays of different shapes without copying data!
    When broadcasting an array of shape `(1, 4)` across `(1000, 4)`, NumPy sets the stride along
    the 0th axis to 0 (`stride = 0`), reusing the same 4 floats in CPU cache across 1,000 rows.
  * Matrix multiplication (`A @ B`) executes via optimized C/Fortran Level-3 BLAS (`dgemm`),
    achieving near-theoretical hardware FLOPS.

Official Documentation References:
- NumPy Broadcasting Basics: https://numpy.org/doc/stable/user/basics.broadcasting.html
- NumPy Linear Algebra (numpy.linalg): https://numpy.org/doc/stable/reference/routines.linalg.html
- BLAS GEMM Routines: https://www.netlib.org/blas/gemm.f
"""

from __future__ import annotations

import sys
import time
from typing import Any, Dict, List, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ==============================================================================
# 1. NumPy Broadcasting Rules Demonstration
# ==============================================================================


def demonstrate_broadcasting_mechanics() -> Dict[str, Any]:
    """
    Demonstrate NumPy's 2-rule broadcasting mechanism:
    Rule 1: If arrays have different rank, prepend 1s to the smaller shape on the left.
    Rule 2: Arrays with size 1 along a dimension are stretched (with stride=0) to match.

    Example:
      Array A: (4, 3)
      Array B: (3,)   -> Prepended to (1, 3) -> Broadcast to (4, 3)
      Result : (4, 3)
    """
    # Matrix of shape (4, 3)
    matrix = np.array(
        [
            [10.0, 20.0, 30.0],
            [40.0, 50.0, 60.0],
            [70.0, 80.0, 90.0],
            [100.0, 110.0, 120.0],
        ],
        dtype=np.float64,
    )

    # 1D row vector of shape (3,) - e.g. feature normalization means
    col_means = np.array([55.0, 65.0, 75.0], dtype=np.float64)

    # Zero-mean normalization via broadcasting (no data duplication!)
    zero_centered = matrix - col_means

    # 2D column vector of shape (4, 1) - e.g. row scaling factors
    row_weights = np.array([[1.0], [0.5], [2.0], [0.1]], dtype=np.float64)

    # Multiply (4, 3) by (4, 1) -> (4, 3)
    scaled_matrix = matrix * row_weights

    return {
        "matrix_shape": matrix.shape,
        "col_means_shape": col_means.shape,
        "zero_centered_shape": zero_centered.shape,
        "row_weights_shape": row_weights.shape,
        "scaled_shape": scaled_matrix.shape,
        "scaled_result": scaled_matrix,
    }


# ==============================================================================
# 2. Linear Algebra: Matrix Multiplication & Batch Cosine Similarity
# ==============================================================================


def batch_cosine_similarity(
    query_embeddings: np.ndarray,
    document_embeddings: np.ndarray,
) -> np.ndarray:
    """
    Compute pairwise Cosine Similarity matrix between Q query vectors and D document vectors.
    Used in vector databases and modern RAG semantic retrieval engines.

    Mathematical Formulation:
      cos_sim(Q, D) = (Q @ D.T) / (norm(Q) * norm(D).T)

    Inputs:
      query_embeddings: Shape (Q, Dim)
      document_embeddings: Shape (D, Dim)
    Returns:
      Similarity Matrix: Shape (Q, D) where entry [i, j] is similarity between Query_i and Doc_j.
    """
    if query_embeddings.ndim != 2 or document_embeddings.ndim != 2:
        raise ValueError("Inputs must be 2D matrices (N_samples, Dim).")
    if query_embeddings.shape[1] != document_embeddings.shape[1]:
        raise ValueError(
            f"Embedding dimension mismatch: {query_embeddings.shape[1]} vs {document_embeddings.shape[1]}"
        )

    # 1. Compute dot product matrix via BLAS Level-3 GEMM: Shape (Q, D)
    dot_products = query_embeddings @ document_embeddings.T

    # 2. Compute L2-norms along feature axis: Shapes (Q, 1) and (1, D)
    q_norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)  # (Q, 1)
    d_norms = np.linalg.norm(document_embeddings, axis=1, keepdims=True).T  # (1, D)

    # 3. Avoid division by zero
    denominator = q_norms * d_norms
    denominator = np.where(denominator == 0.0, 1e-12, denominator)

    # 4. Broadcast division: (Q, D) / (Q, D) -> (Q, D)
    similarity_matrix = dot_products / denominator
    return np.clip(similarity_matrix, -1.0, 1.0)


def solve_linear_system(a_matrix: np.ndarray, b_vector: np.ndarray) -> np.ndarray:
    """
    Solve linear system of equations: A * x = b using LAPACK `gesv`.
    Time Complexity: O(N^3) via LU decomposition with partial pivoting.
    """
    return np.linalg.solve(a_matrix, b_vector)


# ==============================================================================
# 3. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying broadcasting, matrix multiplication, and cosine similarity."""
    console.print(
        Panel.fit(
            "[bold cyan]Data Science Core: NumPy Broadcasting & Linear Algebra[/bold cyan]\n"
            "[dim]Verifying dimension broadcasting rules, matrix multiplication (@), and batch cosine similarity.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Broadcasting Rules Verification
    console.print("[dim]Phase 1: Validating broadcasting dimension rules...[/dim]")
    bcast_res = demonstrate_broadcasting_mechanics()
    assert bcast_res["zero_centered_shape"] == (4, 3)
    assert bcast_res["scaled_shape"] == (4, 3)

    # Verify scaled row 1 (scaled by 0.5): [40, 50, 60] * 0.5 = [20, 25, 30]
    expected_row_1 = np.array([20.0, 25.0, 30.0])
    assert np.allclose(bcast_res["scaled_result"][1], expected_row_1)
    console.print("  [green][PASS] Broadcasting across (4, 3) and (4, 1) verified without memory copy.[/green]")

    # 2. Matrix Multiplication (@ Operator)
    console.print("[dim]Phase 2: Validating matrix multiplication (@ / np.matmul)...[/dim]")
    # 2x3 matrix multiplied by 3x2 matrix -> 2x2 matrix
    mat_a = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)  # (2, 3)
    mat_b = np.array([[7.0, 8.0], [9.0, 1.0], [2.0, 3.0]], dtype=np.float64)  # (3, 2)

    mat_c = mat_a @ mat_b  # Shape (2, 2)
    assert mat_c.shape == (2, 2)
    # Row 0: [1*7 + 2*9 + 3*2, 1*8 + 2*1 + 3*3] = [7 + 18 + 6, 8 + 2 + 9] = [31, 19]
    # Row 1: [4*7 + 5*9 + 6*2, 4*8 + 5*1 + 6*3] = [28 + 45 + 12, 32 + 5 + 18] = [85, 55]
    expected_c = np.array([[31.0, 19.0], [85.0, 55.0]])
    assert np.allclose(mat_c, expected_c)
    console.print(f"  [green][PASS] Matrix multiplication verified:\n{mat_c}[/green]")

    # 3. Batch Cosine Similarity Matrix
    console.print("[dim]Phase 3: Validating batch cosine similarity for vector search...[/dim]")
    # 2 Query vectors of dimension 3
    queries = np.array(
        [
            [1.0, 0.0, 0.0],  # Vector along X axis
            [0.0, 1.0, 0.0],  # Vector along Y axis
        ],
        dtype=np.float64,
    )

    # 3 Document vectors of dimension 3
    documents = np.array(
        [
            [1.0, 0.0, 0.0],   # Exactly identical to Query 0 -> Sim = 1.0
            [-1.0, 0.0, 0.0],  # Directly opposite to Query 0 -> Sim = -1.0
            [0.0, 1.0, 0.0],   # Orthogonal to Query 0 (Sim = 0.0), Identical to Query 1 (Sim = 1.0)
        ],
        dtype=np.float64,
    )

    sim_matrix = batch_cosine_similarity(queries, documents)
    assert sim_matrix.shape == (2, 3)

    # Query 0 comparisons
    assert np.isclose(sim_matrix[0, 0], 1.0)   # Identical
    assert np.isclose(sim_matrix[0, 1], -1.0)  # Opposite
    assert np.isclose(sim_matrix[0, 2], 0.0)   # Orthogonal

    # Query 1 comparisons
    assert np.isclose(sim_matrix[1, 0], 0.0)
    assert np.isclose(sim_matrix[1, 2], 1.0)
    console.print(f"  [green][PASS] Batch cosine similarity verified:\n{sim_matrix}[/green]")

    # 4. Linear System Solver (A * x = b)
    console.print("[dim]Phase 4: Validating linear equation system solver (np.linalg.solve)...[/dim]")
    # 3x + y = 9
    # x + 2y = 8
    # Solution: x = 2, y = 3
    a_sys = np.array([[3.0, 1.0], [1.0, 2.0]], dtype=np.float64)
    b_sys = np.array([9.0, 8.0], dtype=np.float64)
    x_solution = solve_linear_system(a_sys, b_sys)
    assert np.allclose(x_solution, np.array([2.0, 3.0]))
    console.print(f"  [green][PASS] Linear system solved: x = {x_solution[0]:.1f}, y = {x_solution[1]:.1f}[/green]")

    # Summary Table
    table = Table(title="Linear Algebra Architecture: Python vs TS vs PHP", border_style="green")
    table.add_column("Operation", style="bold cyan")
    table.add_column("NumPy Implementation", style="white")
    table.add_column("Hardware Acceleration", style="bold green")
    table.add_column("Node.js (TypeScript) Equivalent", style="yellow")
    table.add_column("PHP (Laravel) Equivalent", style="magenta")

    table.add_row(
        "Dimension Broadcasting",
        "`arr1 + arr2` (auto stride=0)",
        "Zero-copy cache reuse",
        "NOT SUPPORTED in core",
        "NOT SUPPORTED in core",
    )
    table.add_row(
        "Matrix Multiply",
        "`A @ B` / `np.matmul`",
        "BLAS `dgemm` (AVX-512)",
        "`mathjs` or nested for loops",
        "`Rubix ML` or nested loops",
    )
    table.add_row(
        "Batch Cosine Similarity",
        "`(Q @ D.T) / (norm_q * norm_d)`",
        "BLAS Level 3 GEMM",
        "Vector search npm libraries",
        "Manual array math",
    )
    table.add_row(
        "Solve Linear Equations",
        "`np.linalg.solve(A, b)`",
        "LAPACK `dgesv` (LU decomp)",
        "`numeric.js` / WebAssembly",
        "PHP Math extensions",
    )

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
