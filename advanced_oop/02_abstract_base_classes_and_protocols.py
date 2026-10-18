"""
Abstract Base Classes (ABCs) and Structural Protocols
=====================================================
Description: Enterprise architectural patterns contrasting Nominal Typing via `abc.ABC`
             with Structural Subtyping (Duck Typing) via `typing.Protocol` (PEP 544).
             Covers `@abc.abstractmethod`, virtual subclasses with `__subclasshook__`,
             and `@runtime_checkable` structural protocols.

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * TypeScript is structurally typed by default (`interface PaymentGateway { process(amount: number): boolean }`).
    Any object or class matching the method signatures satisfies the interface without an explicit `implements`
    declaration. However, TypeScript interfaces are completely erased at runtime (`typeof obj === 'object'`).
  * Python's `typing.Protocol` is the exact equivalent of TypeScript's structural interfaces, but with
    `@runtime_checkable`, Python allows runtime `isinstance(obj, PaymentGatewayProtocol)` validation!
- PHP / Laravel:
  * PHP is strictly nominally typed (`interface PaymentGatewayInterface` and `abstract class BaseGateway`).
    A PHP class MUST explicitly declare `implements PaymentGatewayInterface` or `extends BaseGateway`;
    PHP's type checker rejects classes with identical method signatures if the explicit nominal link is missing.
  * In Laravel, service containers resolve interfaces bound in Service Providers.
- Memory & Performance Tradeoffs:
  * `abc.ABC` checks abstract method fulfillment during class instantiation (`__new__`), incurring zero
    method dispatch overhead during runtime execution.
  * `typing.Protocol` with `@runtime_checkable` inspects the object's `__dict__` or type attributes during
    `isinstance()`, which is slightly more expensive than nominal `isinstance()` checks.

Official Documentation References:
- Python abc Module: https://docs.python.org/3/library/abc.html
- Python typing.Protocol: https://docs.python.org/3/library/typing.html#typing.Protocol
- PEP 544 – Protocols: Structural subtyping: https://peps.python.org/pep-0544/
"""

from __future__ import annotations

import abc
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

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
# 1. Nominal Typing: Abstract Base Classes (abc.ABC)
# ==============================================================================


class BaseMessageBroker(abc.ABC):
    """
    Formal nominal contract for messaging backbones (RabbitMQ, Kafka, SQS).

    Polyglot Comparison:
    - PHP: `abstract class BaseMessageBroker { abstract public function publish(...); }`.
      Enforces nominal inheritance; derived classes MUST use `extends BaseMessageBroker`.
    - TypeScript: `abstract class BaseMessageBroker { abstract publish(...): Promise<void>; }`.
    - Python: Instantiating `BaseMessageBroker` directly or subclassing without implementing
      abstract methods raises `TypeError: Can't instantiate abstract class with abstract method`.
    """

    def __init__(self, broker_uri: str) -> None:
        self.broker_uri = broker_uri
        self._connected: bool = False

    @abc.abstractmethod
    def connect(self) -> bool:
        """Establish connection to broker. Must be overridden by concrete subclass."""
        ...

    @abc.abstractmethod
    def publish(self, topic: str, payload: Dict[str, Any]) -> str:
        """Publish payload to topic, returning unique message confirmation ID."""
        ...

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Gracefully terminate connection."""
        ...

    # Concrete Template Method (Behavioral Pattern)
    def send_telemetry_event(self, event_name: str, data: Dict[str, Any]) -> str:
        """Template method orchestrating connect, payload enrichment, and publish."""
        if not self._connected:
            self.connect()
        enriched_data = {**data, "event_name": event_name, "broker": self.broker_uri}
        return self.publish(topic="telemetry.events", payload=enriched_data)


class RabbitMQBroker(BaseMessageBroker):
    """Concrete nominal implementation fulfilling the BaseMessageBroker contract."""

    def connect(self) -> bool:
        self._connected = True
        return True

    def publish(self, topic: str, payload: Dict[str, Any]) -> str:
        if not self._connected:
            raise ConnectionError("Broker not connected.")
        msg_id = f"rmq_msg_{abs(hash(str(payload))) % 100000:05d}"
        return msg_id

    def disconnect(self) -> None:
        self._connected = False


# ==============================================================================
# 2. Virtual Subclassing via __subclasshook__
# ==============================================================================


class Auditable(abc.ABC):
    """
    Dynamic interface checking compliance via `__subclasshook__`.
    Allows third-party classes to be recognized by `isinstance(obj, Auditable)`
    without explicitly inheriting from `Auditable`.
    """

    @abc.abstractmethod
    def get_audit_record(self) -> Dict[str, Any]:
        ...

    @classmethod
    def __subclasshook__(cls, subclass: type) -> Union[bool, Any]:
        """
        Invoked during `issubclass(subclass, Auditable)` and `isinstance(obj, Auditable)`.
        Inspects if `subclass` has `get_audit_record` in its MRO attributes.
        """
        if cls is Auditable:
            for base in subclass.__mro__:
                if "get_audit_record" in base.__dict__:
                    return True
        return NotImplemented


# ==============================================================================
# 3. Structural Subtyping: Protocols (typing.Protocol - PEP 544)
# ==============================================================================


@runtime_checkable
class VectorSearchEngine(Protocol):
    """
    Structural Duck Typing Protocol (Equivalent to TypeScript `interface`).

    Polyglot Comparison:
    - TypeScript:
      ```ts
      interface VectorSearchEngine {
        search(vector: number[], topK: number): Array<{ id: string; score: number }>;
      }
      ```
      Any class having `search(vector, topK)` satisfies this interface at compile time.
      However, `if (x instanceof VectorSearchEngine)` is a compile error in TypeScript!
    - PHP:
      PHP CANNOT do this. In PHP, duck typing is non-existent at the type-declaration level;
      classes must explicitly write `implements VectorSearchEngine`.
    - Python:
      Using `@runtime_checkable`, Python bridges TypeScript compile-time structural elegance
      with runtime introspection: `isinstance(engine, VectorSearchEngine)` evaluates to True
      for any class implementing the signature, without subclassing!
    """

    def search(self, query_vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search nearest neighbors by query vector."""
        ...


class ChromaDBSearchService:
    """
    Notice: This class does NOT inherit from VectorSearchEngine!
    It satisfies the protocol purely through structural duck typing.
    """

    def __init__(self, collection_name: str) -> None:
        self.collection_name = collection_name

    def search(self, query_vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        # Simulating vector retrieval
        return [
            {"id": f"doc_{i}", "score": round(1.0 - (i * 0.1), 2)}
            for i in range(1, top_k + 1)
        ]


class LegacyNonCompliantStore:
    """Class missing the `search` signature; does not satisfy VectorSearchEngine."""

    def query(self, raw_text: str) -> List[str]:
        return ["result"]


# ==============================================================================
# 4. Independent Class Satisfying Virtual Subclass
# ==============================================================================


class ThirdPartySecurityEvent:
    """
    Vendor class from external library. Does NOT inherit from Auditable!
    Yet satisfies `isinstance(e, Auditable)` via `Auditable.__subclasshook__`.
    """

    def __init__(self, actor: str, action: str) -> None:
        self.actor = actor
        self.action = action

    def get_audit_record(self) -> Dict[str, Any]:
        return {"actor": self.actor, "action": self.action, "compliant": True}


# ==============================================================================
# 5. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying ABC nominal typing and Protocol structural typing."""
    console.print(
        Panel.fit(
            "[bold cyan]Advanced OOP: ABCs vs Structural Protocols (PEP 544)[/bold cyan]\n"
            "[dim]Comparing Nominal Typing (PHP/Java) with Structural Duck Typing (TypeScript/Python).[/dim]",
            border_style="cyan",
        )
    )

    # 1. Nominal ABC Enforcement
    console.print("[dim]Phase 1: Validating nominal ABC enforcement with BaseMessageBroker...[/dim]")

    # Verify abstract instantiation rejection
    try:
        # BaseMessageBroker has abstract methods and cannot be instantiated directly
        BaseMessageBroker("amqp://localhost")  # type: ignore[abstract]
        assert False, "Should have raised TypeError on abstract class instantiation."
    except TypeError as exc:
        assert "Can't instantiate abstract class" in str(exc)
        console.print("  [green][PASS] ABC correctly blocked instantiation of unfulfilled contract.[/green]")

    # Verify concrete subclass
    rmq = RabbitMQBroker("amqp://guest:guest@localhost:5672")
    assert isinstance(rmq, BaseMessageBroker), "RabbitMQBroker must be an instance of BaseMessageBroker."
    msg_id = rmq.send_telemetry_event("user.login", {"user_id": "usr_9981"})
    assert msg_id.startswith("rmq_msg_")
    console.print(f"  [green][PASS] Concrete nominal subclass verified: msg_id={msg_id}[/green]")

    # 2. Virtual Subclassing via __subclasshook__
    console.print("[dim]Phase 2: Validating virtual subclassing via __subclasshook__...[/dim]")
    sec_event = ThirdPartySecurityEvent("admin@enterprise.io", "REVOKE_ROLE")

    # Auditable has __subclasshook__ that inspects method existence
    assert issubclass(ThirdPartySecurityEvent, Auditable), "Must be recognized as virtual subclass."
    assert isinstance(sec_event, Auditable), "Instance must satisfy Auditable protocol."
    audit_data = sec_event.get_audit_record()
    assert audit_data["actor"] == "admin@enterprise.io"
    console.print(f"  [green][PASS] Virtual subclass validated without inheritance: {audit_data}[/green]")

    # 3. Structural Typing: Protocol (PEP 544)
    console.print("[dim]Phase 3: Validating structural duck typing with typing.Protocol...[/dim]")
    chroma = ChromaDBSearchService("embeddings_v3")
    legacy = LegacyNonCompliantStore()

    # ChromaDBSearchService satisfies VectorSearchEngine structurally!
    assert isinstance(chroma, VectorSearchEngine), "ChromaDBSearchService must satisfy VectorSearchEngine."
    assert not isinstance(legacy, VectorSearchEngine), "LegacyNonCompliantStore must NOT satisfy VectorSearchEngine."

    results = chroma.search([0.1, 0.2, 0.3], top_k=2)
    assert len(results) == 2
    assert results[0]["id"] == "doc_1"
    console.print(f"  [green][PASS] Structural Protocol verified: isinstance(chroma, VectorSearchEngine) == True[/green]")

    # Summary Table
    table = Table(title="Type Systems Architecture: Python vs TS vs PHP", border_style="green")
    table.add_column("Type Mechanism", style="bold cyan")
    table.add_column("Subtyping Philosophy", style="white")
    table.add_column("Runtime Enforced?", style="bold green")
    table.add_column("TypeScript Equivalent", style="yellow")
    table.add_column("PHP Equivalent", style="magenta")

    table.add_row("`abc.ABC`", "Nominal (Explicit inheritance)", "Yes (`TypeError` on instantiation)", "`abstract class`", "`abstract class` / `interface`")
    table.add_row("`typing.Protocol`", "Structural (Duck typing)", "Yes (with `@runtime_checkable`)", "`interface` (compile-time only)", "NOT SUPPORTED in PHP")
    table.add_row("`__subclasshook__`", "Dynamic nominal extension", "Yes (via `isinstance` hook)", "Custom type guards (`is`)", "NOT SUPPORTED in PHP")

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
