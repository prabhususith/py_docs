r"""
Concurrency Architectures: Multithreading, Multiprocessing, and the GIL
========================================================================
Description: Empirical and theoretical demonstration of CPython's Global Interpreter Lock (GIL).
             Features comparative benchmarking of `concurrent.futures.ThreadPoolExecutor`
             versus `concurrent.futures.ProcessPoolExecutor` across I/O-bound and CPU-bound workloads.
Enterprise Mapping:
- The Global Interpreter Lock (GIL): A mutual-exclusion lock preventing multiple native OS threads
  from executing Python bytecodes simultaneously. Compare to Node.js's single-threaded V8 execution
  model and PHP's share-nothing process isolation under PHP-FPM.
- I/O-Bound Concurrency (`ThreadPoolExecutor`): Operating system threads excel when waiting on network,
  disk, or database I/O because CPython explicitly releases the GIL during blocking system calls.
  Lightweight memory overhead (~8-16KB stack per thread) vs Node.js worker pools.
- CPU-Bound Parallelism (`ProcessPoolExecutor`): True multi-core parallelism achieved by spawning
  separate operating system processes, each possessing an independent Python interpreter, memory space,
  and GIL. Analogous to Node.js `worker_threads` / `cluster` module and PHP multi-process workers.

Official Documentation References:
- Concurrent Futures Framework: https://docs.python.org/3/library/concurrent.futures.html
- Python Global Interpreter Lock (GIL): https://docs.python.org/3/glossary.html#term-global-interpreter-lock
- Multiprocessing Guidelines (Windows Spawning): https://docs.python.org/3/library/multiprocessing.html#programming-guidelines
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import os
import time
from typing import Final, Sequence


# ==============================================================================
# 1. Workload Definitions: CPU-Bound vs I/O-Bound
# ==============================================================================
def cpu_bound_task(iteration_count: int, seed: int) -> str:
    """
    Simulate CPU-bound computational workload: iterative SHA-256 hashing.
    Executes pure Python bytecode under continuous GIL contention.
    """
    current_data = f"seed-{seed}-{os.getpid()}".encode("utf-8")
    for _ in range(iteration_count):
        current_data = hashlib.sha256(current_data).digest()
    return current_data.hex()[:16]


def io_bound_task(duration_seconds: float, task_id: int) -> str:
    """
    Simulate I/O-bound workload: blocking network/database latency.
    time.sleep() in CPython explicitly releases the GIL, allowing other
    threads to execute simultaneously on the underlying OS scheduler.
    """
    time.sleep(duration_seconds)
    return f"task_{task_id}_completed_by_pid_{os.getpid()}"


# ==============================================================================
# 2. Benchmarking Engines
# ==============================================================================
def benchmark_io_workload(
    task_count: int = 12, task_latency: float = 0.05
) -> dict[str, float]:
    """
    Compare Sequential vs ThreadPool vs ProcessPool on I/O-bound operations.
    Expected Result: ThreadPool provides massive speedups (~Nx) with minimal memory footprint.
    """
    print("\n" + "=" * 60)
    print(" 1. BENCHMARKING I/O-BOUND WORKLOAD (Simulated Network Latency)")
    print(f"    Tasks: {task_count} | Latency Per Task: {task_latency * 1000:.0f}ms")
    print("=" * 60)

    # 1. Sequential Execution
    t0 = time.perf_counter()
    for i in range(task_count):
        io_bound_task(task_latency, i)
    t_seq = time.perf_counter() - t0
    print(f"  [Sequential] Execution Time: {t_seq:.3f}s")

    # 2. ThreadPoolExecutor (OS Threads, Shared Memory, Releases GIL during I/O)
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=task_count) as executor:
        futures = [executor.submit(io_bound_task, task_latency, i) for i in range(task_count)]
        concurrent.futures.wait(futures)
    t_threads = time.perf_counter() - t0
    speedup_threads = t_seq / t_threads if t_threads > 0 else 1.0
    print(f"  [ThreadPool] Execution Time: {t_threads:.3f}s (Speedup: {speedup_threads:.1f}x)")

    # 3. ProcessPoolExecutor (Forked/Spawned Processes, Separate Interpreters)
    t0 = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(task_count, 4)) as executor:
        futures = [executor.submit(io_bound_task, task_latency, i) for i in range(task_count)]
        concurrent.futures.wait(futures)
    t_processes = time.perf_counter() - t0
    print(f"  [ProcessPool] Execution Time: {t_processes:.3f}s (Process spawn overhead present)")

    return {"sequential": t_seq, "thread_pool": t_threads, "process_pool": t_processes}


def benchmark_cpu_workload(
    task_count: int = 6, iterations_per_task: int = 250_000
) -> dict[str, float]:
    """
    Compare Sequential vs ThreadPool vs ProcessPool on CPU-bound operations.
    Expected Result:
    - ThreadPool does NOT provide multi-core speedup due to GIL serialization.
    - ProcessPool achieves near-linear multi-core acceleration across physical cores.
    """
    print("\n" + "=" * 60)
    print(" 2. BENCHMARKING CPU-BOUND WORKLOAD (Cryptographic SHA-256 Hashing)")
    print(f"    Tasks: {task_count} | Iterations Per Task: {iterations_per_task:,}")
    print("=" * 60)

    # 1. Sequential Execution
    t0 = time.perf_counter()
    for i in range(task_count):
        cpu_bound_task(iterations_per_task, i)
    t_seq = time.perf_counter() - t0
    print(f"  [Sequential] Execution Time: {t_seq:.3f}s")

    # 2. ThreadPoolExecutor (Contending on Single GIL)
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=task_count) as executor:
        futures = [executor.submit(cpu_bound_task, iterations_per_task, i) for i in range(task_count)]
        concurrent.futures.wait(futures)
    t_threads = time.perf_counter() - t0
    ratio_threads = t_threads / t_seq if t_seq > 0 else 1.0
    print(f"  [ThreadPool] Execution Time: {t_threads:.3f}s (GIL lock contention penalty: {ratio_threads:.2f}x)")

    # 3. ProcessPoolExecutor (Bypassing GIL via Multiple Interpreters)
    t0 = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(task_count, os.cpu_count() or 4)) as executor:
        futures = [executor.submit(cpu_bound_task, iterations_per_task, i) for i in range(task_count)]
        concurrent.futures.wait(futures)
    t_processes = time.perf_counter() - t0
    speedup_processes = t_seq / t_processes if t_processes > 0 else 1.0
    print(f"  [ProcessPool] Execution Time: {t_processes:.3f}s (Multi-Core Speedup: {speedup_processes:.1f}x)")

    return {"sequential": t_seq, "thread_pool": t_threads, "process_pool": t_processes}


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
if __name__ == "__main__":
    # CRITICAL: Windows process spawning requires the `if __name__ == '__main__':`
    # guard to prevent recursive child process re-import loops.
    print("=" * 70)
    print(" LEVEL 3: 03_MULTITHREADING_VS_MULTIPROCESSING - ENTERPRISE RUNTIME DEMO")
    print(f" Host Physical CPU Cores Available: {os.cpu_count()}")
    print("=" * 70)

    # 1. Run I/O benchmark
    io_metrics = benchmark_io_workload(task_count=10, task_latency=0.03)
    assert io_metrics["thread_pool"] < io_metrics["sequential"]
    print("  [PASS] ThreadPool successfully parallelized I/O-bound workload.")

    # 2. Run CPU benchmark
    cpu_metrics = benchmark_cpu_workload(task_count=4, iterations_per_task=150_000)
    print("  [PASS] CPU benchmark completed successfully across all execution engines.")

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 03_multithreading_vs_multiprocessing module executed cleanly.")
    print("=" * 70)
