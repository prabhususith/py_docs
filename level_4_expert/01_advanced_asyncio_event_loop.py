r"""
Advanced AsyncIO: Structured Concurrency, TaskGroups, and Backpressure Throttling
==================================================================================
Description: Production architectural patterns for Python's asynchronous event loop.
             Covers Python 3.11+ structured concurrency via `asyncio.TaskGroup`, deterministic
             cancellation semantics, `ExceptionGroup` handling, backpressure regulation using
             `asyncio.Semaphore`, bounded producer-consumer queue pipelines, and low-level loop hooks.
Enterprise Mapping:
- `asyncio.TaskGroup`: Direct counterpart to Structured Concurrency (nurseries in Trio,
  `Promise.all()` with automatic sibling abort in TypeScript, and Amp/Revolt fiber supervisors in PHP).
  If any child coroutine raises an exception, all other active tasks in the group are immediately
  and deterministically cancelled before the `ExceptionGroup` is propagated.
- `asyncio.Semaphore`: Replaces `p-limit` / bottleneck libraries in Node.js and concurrency tokens
  in distributed PHP queue consumers. Controls access to scarce downstream resources (e.g. DB pools, APIs).
- Bounded Queues (`asyncio.Queue(maxsize=k)`): Enforces architectural backpressure, pausing producers
  when downstream workers lag, preventing Out-Of-Memory (OOM) crashes under heavy load.

Official Documentation References:
- AsyncIO Task Groups: https://docs.python.org/3/library/asyncio-task.html#task-groups
- AsyncIO Synchronization Primitives (Semaphore): https://docs.python.org/3/library/asyncio-sync.html#asyncio.Semaphore
- AsyncIO Queues: https://docs.python.org/3/library/asyncio-queue.html
- Python Exception Groups (PEP 654): https://peps.python.org/pep-0654/
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Final, Sequence


# ==============================================================================
# 1. Backpressure Regulation via asyncio.Semaphore
# ==============================================================================
class ThrottledDownstreamClient:
    """
    Demonstrates rate-limiting and connection-capping via asyncio.Semaphore.
    Guarantees no more than `max_concurrency` requests hit the target resource concurrently.
    """

    def __init__(self, max_concurrency: int = 3) -> None:
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(max_concurrency)
        self.active_counter: int = 0
        self.peak_concurrency: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    async def execute_request(self, request_id: int) -> dict[str, int | float]:
        """Execute request under semaphore governance."""
        async with self.semaphore:
            # Track peak concurrency safely
            async with self._lock:
                self.active_counter += 1
                if self.active_counter > self.peak_concurrency:
                    self.peak_concurrency = self.active_counter
                current_active = self.active_counter

            # Simulated I/O latency
            await asyncio.sleep(0.04)

            async with self._lock:
                self.active_counter -= 1

            return {"request_id": request_id, "active_during_exec": current_active}


async def demonstrate_semaphore_throttling(total_requests: int = 12) -> int:
    """Demonstrate throttling 12 concurrent requests down to a strict max concurrency of 3."""
    print("\n--- 1. asyncio.Semaphore Backpressure Throttling ---")
    throttler = ThrottledDownstreamClient(max_concurrency=3)

    # Launch all requests concurrently
    tasks = [throttler.execute_request(i) for i in range(total_requests)]
    results = await asyncio.gather(*tasks)

    print(f"  Dispatched {total_requests} requests concurrently.")
    print(f"  Enforced Max Concurrency Limit: 3")
    print(f"  Observed Peak Concurrency:      {throttler.peak_concurrency}")
    assert throttler.peak_concurrency <= 3
    return throttler.peak_concurrency


# ==============================================================================
# 2. Structured Concurrency via Python 3.11+ asyncio.TaskGroup
# ==============================================================================
async def _resilient_subservice(service_name: str, duration: float) -> str:
    await asyncio.sleep(duration)
    return f"{service_name}:OK"


async def _failing_subservice(service_name: str, fail_after: float) -> None:
    await asyncio.sleep(fail_after)
    raise RuntimeError(f"Critical fault in upstream dependency: '{service_name}'")


async def demonstrate_taskgroup_success() -> list[str]:
    """
    Demonstrate successful structured concurrency execution with asyncio.TaskGroup.
    All spawned tasks are awaited cleanly before leaving the context block.
    """
    print("\n--- 2. asyncio.TaskGroup (Happy Path) ---")
    results: list[str] = []

    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(_resilient_subservice("payment-gateway", 0.03))
        t2 = tg.create_task(_resilient_subservice("inventory-service", 0.02))
        t3 = tg.create_task(_resilient_subservice("auth-provider", 0.01))

    # Once context exits, all tasks are guaranteed complete
    results = [t1.result(), t2.result(), t3.result()]
    print(f"  TaskGroup results synchronized successfully: {results}")
    return results


async def demonstrate_taskgroup_cancellation_semantics() -> bool:
    """
    Demonstrate automatic sibling cancellation on failure within a TaskGroup.
    When one task fails, remaining tasks are promptly cancelled, and an
    ExceptionGroup is raised.
    """
    print("\n--- 3. TaskGroup Cancellation & ExceptionGroup Handling ---")
    sibling_was_cancelled = False

    async def _long_running_sibling() -> None:
        nonlocal sibling_was_cancelled
        try:
            await asyncio.sleep(1.0)  # Attempting long work
        except asyncio.CancelledError:
            sibling_was_cancelled = True
            print("  [CANCELLATION ACKNOWLEDGED] Sibling task cancelled promptly upon peer failure.")
            raise

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(_long_running_sibling())
            tg.create_task(_failing_subservice("bad-microservice", fail_after=0.02))
    except* RuntimeError as eg:
        # PEP 654 except* syntax captures matching exceptions within ExceptionGroup
        print(f"  [CAUGHT EXCEPTIONGROUP] Handled expected sub-service failure: {eg.exceptions}")

    assert sibling_was_cancelled is True
    print("  Verified: Structured concurrency guaranteed zero orphaned zombie tasks.")
    return sibling_was_cancelled


# ==============================================================================
# 3. Bounded Producer-Consumer Pipeline with Backpressure
# ==============================================================================
async def bounded_pipeline_producer(queue: asyncio.Queue[int | None], item_count: int) -> None:
    """Produces items into a bounded queue, pausing when buffer is full."""
    for item in range(1, item_count + 1):
        await queue.put(item)  # Blocks if queue reaches maxsize
    # Sentinel termination signal
    await queue.put(None)


async def bounded_pipeline_consumer(queue: asyncio.Queue[int | None]) -> list[int]:
    """Consumes items at controlled processing pace."""
    consumed_items: list[int] = []
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        # Process item
        await asyncio.sleep(0.005)
        consumed_items.append(item * 10)
        queue.task_done()
    return consumed_items


async def demonstrate_bounded_queue() -> list[int]:
    """Execute producer-consumer pipeline with backpressure enforced."""
    print("\n--- 4. Bounded Queue Producer-Consumer Pipeline ---")
    # Queue with capacity of 5: enforces backpressure on producer
    bounded_queue: asyncio.Queue[int | None] = asyncio.Queue(maxsize=5)

    producer_coro = bounded_pipeline_producer(bounded_queue, item_count=15)
    consumer_coro = bounded_pipeline_consumer(bounded_queue)

    _, consumed = await asyncio.gather(producer_coro, consumer_coro)
    print(f"  Successfully processed {len(consumed)} pipeline items with bounded memory.")
    return consumed


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
async def main() -> None:
    print("=" * 70)
    print(" LEVEL 4: 01_ADVANCED_ASYNCIO_EVENT_LOOP - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Semaphore test
    peak = await demonstrate_semaphore_throttling(total_requests=10)
    assert peak <= 3

    # 2. TaskGroup happy path
    tg_results = await demonstrate_taskgroup_success()
    assert len(tg_results) == 3

    # 3. TaskGroup exception & cancellation semantics
    cancelled_ok = await demonstrate_taskgroup_cancellation_semantics()
    assert cancelled_ok is True

    # 4. Bounded pipeline test
    pipeline_results = await demonstrate_bounded_queue()
    assert len(pipeline_results) == 15
    assert pipeline_results[0] == 10
    assert pipeline_results[-1] == 150

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 01_advanced_asyncio_event_loop module executed cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
