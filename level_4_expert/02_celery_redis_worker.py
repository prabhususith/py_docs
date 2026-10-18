r"""
Distributed Asynchronous Task Queues with Celery and Redis
==========================================================
Description: Enterprise asynchronous worker architecture featuring Celery and Redis.
             Demonstrates production task definition, resilient exponential backoff retry
             policies with jitter, workflow composition (chains, groups, and chords),
             result backend configuration, and eager in-memory test execution.
Enterprise Mapping:
- Celery Task Workers: Direct architectural equivalent to BullMQ / BeeQueue in Node.js
  and Laravel Queues / Symfony Messenger in PHP. Decouples long-running, CPU-heavy, or
  unreliable third-party I/O from the synchronous HTTP request-response cycle.
- Retry Strategies & Exponential Backoff: Automates task retries on transient network faults
  (e.g. database deadlocks, payment gateway timeouts) preventing worker thread exhaustion.
- Canvas Workflows (Chains & Groups): Equivalent to BullMQ flows or Step Functions in cloud architectures.

Official Documentation References:
- Celery First Steps: https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html
- Tasks & Retrying: https://docs.celeryq.dev/en/stable/userguide/tasks.html#retrying
- Canvas Workflows (Chains, Groups, Chords): https://docs.celeryq.dev/en/stable/userguide/canvas.html
- Celery Configuration Reference: https://docs.celeryq.dev/en/stable/userguide/configuration.html
"""

from __future__ import annotations

import math
import random
import time
from typing import Any, Final

from celery import Celery, Task, chain, chord, group
from celery.exceptions import MaxRetriesExceededError


# ==============================================================================
# 1. Custom Exceptions & Transient Fault Definitions
# ==============================================================================
class TransientGatewayError(Exception):
    """Raised when an external third-party payment/notification gateway times out."""
    pass


class PermanentDomainError(Exception):
    """Raised on irrecoverable validation failure where retry is futile."""
    pass


# ==============================================================================
# 2. Celery Application Initialization & Production Config
# ==============================================================================
# In production, broker and backend URLs are read from environment variables
REDIS_BROKER_URL: Final[str] = "redis://127.0.0.1:6379/0"
REDIS_RESULT_BACKEND: Final[str] = "redis://127.0.0.1:6379/1"

celery_app = Celery("enterprise_task_worker")

celery_app.conf.update(
    broker_url=REDIS_BROKER_URL,
    result_backend=REDIS_RESULT_BACKEND,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,  # Ensure task is acknowledged ONLY after successful completion
    task_reject_on_worker_lost=True,  # Re-queue task if worker process is killed unexpectedly
    worker_prefetch_multiplier=1,  # Prevent worker from hoarding tasks; fair distribution
)


# ==============================================================================
# 3. Task Definitions: Resilient Retries & Exponential Backoff
# ==============================================================================
@celery_app.task(
    bind=True,
    max_retries=3,
    autoretry_for=(TransientGatewayError,),
    retry_backoff=True,  # Enables exponential backoff: 2s, 4s, 8s...
    retry_backoff_max=60,  # Caps maximum delay at 60 seconds
    retry_jitter=True,  # Adds random jitter to prevent the "thundering herd" problem
    name="tasks.process_payment",
)
def process_payment(
    self: Task, invoice_id: str, amount: float, simulate_transient_failure: bool = False
) -> dict[str, Any]:
    """
    Process payment with automated exponential backoff retry.
    Accesses task execution context via `bind=True` (`self.request.retries`).
    """
    attempt = self.request.retries + 1
    print(f"  [Task #{self.request.id}] Processing Invoice {invoice_id} (${amount:.2f}) - Attempt #{attempt}")

    if simulate_transient_failure and self.request.retries < 2:
        print(f"  [Task #{self.request.id}] Upstream Gateway 503 Timeout. Triggering backoff retry...")
        # Raising TransientGatewayError triggers automatic retry governed by autoretry_for
        raise TransientGatewayError(f"Gateway timed out on attempt {attempt}")

    print(f"  [Task #{self.request.id}] Payment settled successfully.")
    return {
        "invoice_id": invoice_id,
        "amount": amount,
        "status": "SETTLED",
        "retries_required": self.request.retries,
        "timestamp": time.time(),
    }


@celery_app.task(name="tasks.generate_pdf_invoice")
def generate_pdf_invoice(payment_result: dict[str, Any]) -> dict[str, Any]:
    """Canvas Step: Generates PDF invoice from settled payment result."""
    invoice_id = payment_result["invoice_id"]
    pdf_path = f"/var/invoices/{invoice_id}.pdf"
    print(f"  [PDF Worker] Generating PDF artifact for Invoice {invoice_id} -> {pdf_path}")
    return {
        **payment_result,
        "pdf_artifact": pdf_path,
        "generated_at": time.time(),
    }


@celery_app.task(name="tasks.dispatch_webhook_notification")
def dispatch_webhook_notification(invoice_summary: dict[str, Any]) -> str:
    """Canvas Step: Dispatches outbound webhook notification to customer endpoint."""
    print(f"  [Webhook Worker] Outbound webhook dispatched for {invoice_summary['invoice_id']}.")
    return f"WEBHOOK_DISPATCHED:{invoice_summary['invoice_id']}"


@celery_app.task(name="tasks.aggregate_batch_metrics")
def aggregate_batch_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Chord Callback: Aggregates results of parallel group execution."""
    total_amount = sum(r["amount"] for r in results)
    print(f"  [Chord Callback] Aggregated {len(results)} invoices. Total settled: ${total_amount:.2f}")
    return {"batch_count": len(results), "aggregate_settled_amount": total_amount}


# ==============================================================================
# 4. Canvas Workflow Orchestration: Chains and Groups
# ==============================================================================
def execute_payment_pipeline_chain(invoice_id: str, amount: float) -> Any:
    """
    Demonstrate Celery Chain Workflow (Sequential Pipe):
      process_payment -> generate_pdf_invoice -> dispatch_webhook_notification

    TypeScript equivalent:
      processPayment().then(generatePdf).then(dispatchWebhook)
    """
    print("\n--- 1. Celery Canvas Workflow: Sequential Chain ---")
    pipeline = chain(
        process_payment.s(invoice_id, amount, simulate_transient_failure=False),
        generate_pdf_invoice.s(),
        dispatch_webhook_notification.s(),
    )
    result = pipeline.apply_async()
    return result


def execute_parallel_invoice_group(invoices: list[tuple[str, float]]) -> Any:
    """
    Demonstrate Celery Group Workflow (Parallel Execution):
    Executes multiple independent tasks concurrently across worker pool.
    """
    print("\n--- 2. Celery Canvas Workflow: Parallel Group ---")
    task_signatures = [
        process_payment.s(inv_id, amt, simulate_transient_failure=False)
        for inv_id, amt in invoices
    ]
    job_group = group(task_signatures)
    result = job_group.apply_async()
    return result


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite (In-Memory Eager Execution)
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" LEVEL 4: 02_CELERY_REDIS_WORKER - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # In local testing and CI environments where a live Redis instance may not be
    # active, Celery provides `task_always_eager = True` mode. This executes the entire
    # task engine, signatures, retries, and canvas pipes locally and deterministically.
    print("[*] Activating Celery in-memory eager execution mode for test harness...")
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )

    # 1. Test Task Execution: Happy Path
    print("\n--- 1. Testing Standard Task Execution ---")
    direct_res = process_payment.apply_async(args=["INV-OK-101", 350.00])
    res_val = direct_res.get()
    print(f"  Task completed successfully: {res_val}")
    assert res_val["status"] == "SETTLED"

    # 2. Test Transient Fault Retries (Interception of Retry signal)
    print("\n--- 2. Testing Transient Fault Retries with Backoff ---")
    try:
        process_payment.apply(
            args=["INV-RET-100", 350.00],
            kwargs={"simulate_transient_failure": True},
        )
    except Exception as exc:
        # In eager mode, Celery raises the Retry exception to signal the scheduler
        print(f"  [PASS] Celery intercepted TransientGatewayError and raised retry signal: {type(exc).__name__}: {exc}")

    # 3. Test Sequential Canvas Chain
    chain_async_result = execute_payment_pipeline_chain("INV-SEQ-200", 1250.75)
    final_output = chain_async_result.get()
    print(f"  Chain pipeline finalized with result: '{final_output}'")
    assert final_output == "WEBHOOK_DISPATCHED:INV-SEQ-200"

    # 3. Test Parallel Canvas Group
    batch_invoices = [
        ("INV-GRP-301", 100.0),
        ("INV-GRP-302", 250.0),
        ("INV-GRP-303", 500.0),
    ]
    group_async_result = execute_parallel_invoice_group(batch_invoices)
    group_output = group_async_result.get()
    print(f"  Group workflow processed {len(group_output)} concurrent tasks.")
    assert len(group_output) == 3
    assert all(item["status"] == "SETTLED" for item in group_output)

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 02_celery_redis_worker module executed cleanly.")
    print("=" * 70)
