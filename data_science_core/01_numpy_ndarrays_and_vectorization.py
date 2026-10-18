"""
NumPy N-Dimensional Arrays (ndarrays) and Vectorization Architecture
===================================================================
Description: Production implementation of NumPy array mechanics, memory layout, data types,
             memory strides, contiguous memory buffers (C-order vs Fortran-order), and vectorized
             SIMD calculations eliminating slow interpreted for-loops.

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * In V8, standard JavaScript arrays (`[]`) are dynamic arrays of variable types (packed elements,
    holey elements, or dictionary mode).
  * Node.js provides `TypedArray` (`Float32Array`, `Int32Array`, `Float64Array`) for raw binary memory.
    However, JavaScript **lacks syntax for vectorized operations**: writing `arrA + arrB` on two
    Float32Arrays results in string conversion, forcing engineers to write manual `for` loops or compile
    WebAssembly C++/Rust modules for SIMD.
- PHP / Laravel:
  * In PHP, arrays are internally Zend Hash Tables (order-preserving associative hash maps).
    Every element in a PHP array is wrapped in a `zval` struct (16 bytes in PHP 7/8), which contains
    type tags, reference counting flags, and memory pointers.
  * A 1,000,000 element integer array in PHP consumes ~35MB to ~45MB of RAM due to Zend overhead!
    In NumPy, an `int64` array of 1,000,000 elements consumes exactly $8 \text{ bytes} \times 1,000,000 = 8.0 \text{ MB}$,
    packed contiguously with zero metadata per element.
- Memory & Performance Tradeoffs:
  * NumPy `ndarray` is a thin C-struct wrapping a single contiguous block of raw memory.
  * Vectorized operations (`a * 1.5 + b`) compile directly down to C-level loops that trigger
    hardware SIMD (Single Instruction, Multiple Data) processor instructions (AVX-2, AVX-512, NEON),
    executing 4 to 16 mathematical calculations per clock cycle.

Official Documentation References:
- NumPy ndarray: https://numpy.org/doc/stable/reference/arrays.ndarray.html
- NumPy Memory Layout & Strides: https://numpy.org/doc/stable/reference/generated/numpy.ndarray.strides.html
- NumPy Quickstart: https://numpy.org/doc/stable/user/quickstart.html
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
# 1. NumPy Memory Anatomy & Stride Inspection
# ==============================================================================


def inspect_ndarray_memory(arr: np.ndarray) -> Dict[str, Any]:
    """
    Expose internal C-level memory layout, strides, byte order, and flags of an ndarray.

    Strides Explanation:
    - `strides` is a tuple of bytes to step in each dimension when traversing the array.
    - For a 2D float64 array of shape (3, 4) in C-order:
      * Stride along axis 0 (rows) is $4 \times 8 \text{ bytes} = 32 \text{ bytes}$.
      * Stride along axis 1 (columns) is $1 \times 8 \text{ bytes} = 8 \text{ bytes}$.
      * `arr.strides == (32, 8)`.
    - This allows transpose operations (`arr.T`) to execute in O(1) time and 0 additional memory
      simply by swapping the strides tuple: `(8, 32)`, without copying any underlying data!
    """
    return {
        "shape": arr.shape,
        "dtype": str(arr.dtype),
        "itemsize": arr.itemsize,  # Bytes per element
        "nbytes": arr.nbytes,      # Total byte footprint
        "strides": arr.strides,    # Memory traversal stride
        "c_contiguous": arr.flags.c_contiguous,
        "f_contiguous": arr.flags.f_contiguous,
        "base_is_view": arr.base is not None,  # True if view, False if owns memory
    }


# ==============================================================================
# 2. Vectorized Math vs Interpreted Loops
# ==============================================================================


def calculate_haversine_distance_vectorized(
    lat1: np.ndarray,
    lon1: np.ndarray,
    lat2: np.ndarray,
    lon2: np.ndarray,
) -> np.ndarray:
    """
    Calculate great-circle distances between points on a sphere (Earth) in kilometers.
    Executes vectorized across millions of coordinate pairs simultaneously.

    Formula:
      a = sin^2(dlat/2) + cos(lat1) * cos(lat2) * sin^2(dlon/2)
      c = 2 * arcsin(sqrt(a))
      d = R * c  (where R = 6371 km)
    """
    r = 6371.0  # Earth's radius in kilometers

    # Convert degrees to radians in-place via SIMD
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = (
        np.sin(delta_phi / 2.0) ** 2
        + np.cos(phi1) * np.cos(phi2) * (np.sin(delta_lambda / 2.0) ** 2)
    )
    c = 2.0 * np.arcsin(np.sqrt(a))
    return r * c


def calculate_haversine_distance_python_loop(
    coords: List[Tuple[float, float, float, float]],
) -> List[float]:
    """Pure Python scalar loop for comparison."""
    import math

    r = 6371.0
    results: List[float] = []
    for lat1, lon1, lat2, lon2 in coords:
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * (math.sin(dlam / 2.0) ** 2)
        )
        c = 2.0 * math.asin(math.sqrt(a))
        results.append(r * c)
    return results


# ==============================================================================
# 3. Micro-Benchmark: Vectorization vs Pure Python Loops
# ==============================================================================


def benchmark_vectorization(size: int = 100_000) -> Tuple[float, float, float]:
    """
    Benchmark element-wise computation across 100,000 geographic coordinate pairs.
    Returns: (loop_duration_sec, vectorized_duration_sec, speedup_factor)
    """
    np.random.seed(42)
    lat1 = np.random.uniform(-90.0, 90.0, size)
    lon1 = np.random.uniform(-180.0, 180.0, size)
    lat2 = np.random.uniform(-90.0, 90.0, size)
    lon2 = np.random.uniform(-180.0, 180.0, size)

    # 1. Pure Python Loop
    coords_list = list(zip(lat1.tolist(), lon1.tolist(), lat2.tolist(), lon2.tolist()))
    t0 = time.perf_counter()
    _ = calculate_haversine_distance_python_loop(coords_list)
    loop_time = time.perf_counter() - t0

    # 2. NumPy Vectorized
    t1 = time.perf_counter()
    _ = calculate_haversine_distance_vectorized(lat1, lon1, lat2, lon2)
    vectorized_time = time.perf_counter() - t1

    speedup = loop_time / max(vectorized_time, 1e-9)
    return loop_time, vectorized_time, speedup


# ==============================================================================
# 4. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying ndarray memory layout and vectorization speed."""
    console.print(
        Panel.fit(
            "[bold cyan]Data Science Core: NumPy ndarrays & Vectorization[/bold cyan]\n"
            "[dim]Comparing contiguous C-buffers with Node.js Float32Arrays and PHP Zend zvals.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Memory Anatomy Inspection
    console.print("[dim]Phase 1: Inspecting contiguous memory strides and views...[/dim]")
    arr_2d = np.arange(12, dtype=np.float64).reshape((3, 4))
    info = inspect_ndarray_memory(arr_2d)

    assert info["shape"] == (3, 4)
    assert info["itemsize"] == 8  # 8 bytes per float64
    assert info["nbytes"] == 12 * 8  # 96 bytes total
    assert info["strides"] == (32, 8)  # 4 cols * 8 bytes = 32 bytes per row step
    assert info["c_contiguous"] is True

    # Test O(1) Transpose View (Zero copy)
    transposed = arr_2d.T
    trans_info = inspect_ndarray_memory(transposed)
    assert trans_info["shape"] == (4, 3)
    assert trans_info["strides"] == (8, 32)  # Swapped strides!
    assert trans_info["base_is_view"] is True  # Shares underlying memory buffer
    console.print(f"  [green][PASS] ndarray strides verified: (3, 4) strides={info['strides']} -> Transpose strides={trans_info['strides']}[/green]")

    # 2. Vectorized Math Verification
    console.print("[dim]Phase 2: Validating vectorized Haversine distance formula...[/dim]")
    # London (51.5074° N, 0.1278° W) to Paris (48.8566° N, 2.3522° E) = ~344 km
    lats1 = np.array([51.5074], dtype=np.float64)
    lons1 = np.array([-0.1278], dtype=np.float64)
    lats2 = np.array([48.8566], dtype=np.float64)
    lons2 = np.array([2.3522], dtype=np.float64)

    distance_km = calculate_haversine_distance_vectorized(lats1, lons1, lats2, lons2)
    assert np.isclose(distance_km[0], 343.5, atol=2.0), f"Expected ~344 km, got {distance_km[0]}"
    console.print(f"  [green][PASS] Haversine distance London to Paris = {distance_km[0]:.2f} km.[/green]")

    # 3. Vectorization Benchmark (100,000 coordinates)
    console.print("[dim]Phase 3: Running vectorization benchmark (100,000 coordinate pairs)...[/dim]")
    loop_time, vec_time, speedup = benchmark_vectorization(100_000)
    console.print(f"  • Pure Python interpreted loop : {loop_time * 1000:.2f} ms")
    console.print(f"  • NumPy SIMD vectorized        : {vec_time * 1000:.2f} ms")
    console.print(f"  • Vectorization Speedup        : [bold green]{speedup:.1f}x faster[/bold green]")
    assert speedup > 4.0, f"NumPy vectorization should be significantly faster than pure Python, got {speedup:.1f}x"

    # Summary Table
    table = Table(title="Array Memory & Compute Architecture: Python vs TS vs PHP", border_style="green")
    table.add_column("Runtime / Library", style="bold cyan")
    table.add_column("Memory Layout", style="white")
    table.add_column("Memory per 1M Ints", style="bold green")
    table.add_column("Vectorized Operators?", style="yellow")
    table.add_column("Execution Model", style="magenta")

    table.add_row(
        "NumPy `ndarray`",
        "Contiguous C-buffer (strided)",
        "8.0 MB (`int64`)",
        "Yes (`a + b`, `a * b` SIMD)",
        "Direct C loops (AVX2/AVX-512)",
    )
    table.add_row(
        "Node.js `Float32Array`",
        "Contiguous typed ArrayBuffer",
        "4.0 MB (`float32`)",
        "NO (requires manual for-loops)",
        "V8 Turbofan JIT compiler",
    )
    table.add_row(
        "PHP 8 Native Array",
        "Zend Hash Table (`zval` structs)",
        "~36.0 MB to 48.0 MB",
        "NO (requires `array_map` / loops)",
        "Zend VM opcode interpreter",
    )

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
