"""
Pythonic Creational and Behavioral Design Patterns Architecture
===============================================================
Description: Production implementation of core software engineering design patterns adapted
             idiomatically to Python: Thread-Safe Singleton, Factory Method, Observer (Pub/Sub Event Bus),
             and Strategy Pattern (via first-class callables vs class hierarchies).

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * Observer Pattern: Node.js standardizes on `EventEmitter` (`events` core module). In frontend
    applications, RxJS Subject / Observable streams represent the reactive standard.
  * Singleton Pattern: In Node.js, `require('./module')` is cached in `require.cache`. However, this
    can fail and create multiple singleton instances if the module is symlinked or imported across
    differing package paths.
  * Strategy Pattern: In TypeScript, functions are first-class values (`type PricingStrategy = (cart: Cart) => number`),
    avoiding heavy GoF strategy class boilerplate.
- PHP / Laravel:
  * Singleton & Factory Patterns: Governed centrally by Laravel's Inversion of Control (IoC) Service Container:
    `$this->app->singleton(PaymentGateway::class, fn() => new StripeGateway())`.
  * Observer Pattern: Laravel Model Observers (`UserObserver::created()`) and Event Listeners (`Event::dispatch()`).
  * Strategy Pattern: In traditional PHP, requires `interface StrategyInterface` with separate class files
    for each algorithm, though PHP 7.4+ arrow functions allow lightweight callable strategies.
- Memory & Performance Tradeoffs:
  * Python supports both heavy OOP strategy classes AND lightweight functional strategies using `Callable[[T], R]`.
    Passing pure functions avoids heap-allocated Strategy class instances, saving memory in high-throughput loops.
  * Thread-safe Singletons in Python require double-checked locking using `threading.Lock()` to prevent
    race conditions in multithreaded servers (Gunicorn threads / ThreadPoolExecutor).

Official Documentation References:
- Python Classes Tutorial: https://docs.python.org/3/tutorial/classes.html
- Python Threading Synchronization Primitives: https://docs.python.org/3/library/threading.html#lock-objects
- Python Callable Types: https://docs.python.org/3/library/typing.html#callable
"""

from __future__ import annotations

import sys
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar

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
# 1. Thread-Safe Singleton Pattern (Double-Checked Locking)
# ==============================================================================


class GlobalConfigurationRegistry:
    """
    Thread-Safe Singleton managing centralized runtime application configuration.

    Polyglot Comparison:
    - Node.js: Often relies on module caching: `export const config = new Config()`.
    - PHP (Laravel): Registered in Service Provider: `$this->app->singleton(Config::class, ...)`.
    - Python: Implemented using `__new__` with double-checked locking on `threading.Lock()`.
    """

    _instance: Optional[GlobalConfigurationRegistry] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> GlobalConfigurationRegistry:
        # First check (unlocked) for optimal read performance
        if cls._instance is None:
            with cls._lock:
                # Second check (locked) guarantees single instance across concurrent threads
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False  # type: ignore[attr-defined]
        return cls._instance

    def __init__(self, environment: str = "production") -> None:
        if getattr(self, "_initialized", False):
            return
        self.environment = environment
        self._settings: Dict[str, Any] = {}
        self._initialized = True

    def set_setting(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)


# ==============================================================================
# 2. Factory Method Pattern
# ==============================================================================


class NotificationService(ABC):
    """Abstract Product interface for notifications."""

    @abstractmethod
    def send(self, recipient: str, message: str) -> bool:
        ...


class EmailNotificationService(NotificationService):
    def send(self, recipient: str, message: str) -> bool:
        return True


class SlackNotificationService(NotificationService):
    def send(self, recipient: str, message: str) -> bool:
        return True


class SMSNotificationService(NotificationService):
    def send(self, recipient: str, message: str) -> bool:
        return True


class NotificationFactory:
    """
    Factory Method pattern creating notification service instances based on channel.

    Polyglot Comparison:
    - Node.js: `NotificationFactory.create(channel: 'email' | 'slack' | 'sms')`.
    - PHP (Laravel): Factory class or container resolution `app()->make("notification.{$channel}")`.
    """

    _CREATORS: Dict[str, Type[NotificationService]] = {
        "email": EmailNotificationService,
        "slack": SlackNotificationService,
        "sms": SMSNotificationService,
    }

    @classmethod
    def register_channel(cls, channel_name: str, service_cls: Type[NotificationService]) -> None:
        """Extensible registry allowing third parties to register new channels."""
        cls._CREATORS[channel_name.lower()] = service_cls

    @classmethod
    def create(cls, channel_name: str) -> NotificationService:
        channel = channel_name.lower()
        if channel not in cls._CREATORS:
            raise ValueError(f"Unsupported notification channel: '{channel_name}'. Supported: {list(cls._CREATORS.keys())}")
        return cls._CREATORS[channel]()


# ==============================================================================
# 3. Observer Pattern (Event Bus / Pub-Sub)
# ==============================================================================


@dataclass(frozen=True)
class SystemEvent:
    """Immutable event payload published across observer channels."""

    event_type: str
    data: Dict[str, Any]
    source: str


class EnterpriseEventBus:
    """
    Publish-Subscribe Event Bus (Observer Pattern).

    Polyglot Comparison:
    - Node.js: Identical to native `EventEmitter`:
      `bus.on('tenant.created', (event) => { ... })` and `bus.emit('tenant.created', payload)`.
    - PHP (Laravel): Identical to `Event::listen('tenant.created', ...)` and `Event::dispatch(...)`.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[SystemEvent], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[SystemEvent], None]) -> None:
        """Register listener callback for specific event_type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[SystemEvent], None]) -> bool:
        """Remove listener callback."""
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            return True
        return False

    def publish(self, event: SystemEvent) -> int:
        """
        Notify all registered observers synchronously.
        Returns the number of listeners dispatched.
        """
        listeners = self._subscribers.get(event.event_type, [])
        for listener in listeners:
            listener(event)
        return len(listeners)


# ==============================================================================
# 4. Strategy Pattern (Functional vs Class-Based)
# ==============================================================================


@dataclass
class InvoiceItem:
    description: str
    unit_price: float
    quantity: int


# Functional Strategy Type Definition
PricingStrategyFunc = Callable[[List[InvoiceItem]], float]


def standard_pricing_strategy(items: List[InvoiceItem]) -> float:
    """Standard baseline pricing: sum(qty * unit_price)."""
    return sum(item.quantity * item.unit_price for item in items)


def bulk_discount_pricing_strategy(items: List[InvoiceItem]) -> float:
    """Bulk pricing: 15% discount if total quantity >= 10 units."""
    subtotal = sum(item.quantity * item.unit_price for item in items)
    total_qty = sum(item.quantity for item in items)
    if total_qty >= 10:
        return subtotal * 0.85
    return subtotal


def enterprise_vip_pricing_strategy(items: List[InvoiceItem]) -> float:
    """VIP enterprise pricing: 25% flat discount."""
    subtotal = sum(item.quantity * item.unit_price for item in items)
    return subtotal * 0.75


class InvoiceCalculator:
    """
    Context class executing interchangeable pricing strategies.

    Polyglot Architectural Note:
    - In Python, we do NOT need 3 separate classes (`StandardStrategy`, `BulkStrategy`, `VIPStrategy`)
      with inheritance hierarchies. Because functions are first-class objects, passing pure functions
      (`Callable`) fulfills the Strategy pattern cleanly, saving memory and eliminating class boilerplate.
    """

    def __init__(self, strategy: Optional[PricingStrategyFunc] = None) -> None:
        self.strategy: PricingStrategyFunc = strategy or standard_pricing_strategy

    def calculate_total(self, items: List[InvoiceItem]) -> float:
        return self.strategy(items)


# ==============================================================================
# 5. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying Singleton, Factory, Observer, and Strategy patterns."""
    console.print(
        Panel.fit(
            "[bold cyan]Advanced OOP: Creational & Behavioral Design Patterns[/bold cyan]\n"
            "[dim]Verifying Thread-Safe Singleton, Factory Method, Event Bus Observer, and Strategy.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Thread-Safe Singleton Verification
    console.print("[dim]Phase 1: Validating Thread-Safe Singleton with concurrent threads...[/dim]")
    registry_instances: List[GlobalConfigurationRegistry] = []

    def _worker_instantiate():
        inst = GlobalConfigurationRegistry("production")
        registry_instances.append(inst)

    threads = [threading.Thread(target=_worker_instantiate) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Assert that all 10 threads received the exact same in-memory object instance (id)
    first_id = id(registry_instances[0])
    assert all(id(inst) == first_id for inst in registry_instances), "Singleton contract violated!"

    # Test state persistence across references
    c1 = GlobalConfigurationRegistry()
    c2 = GlobalConfigurationRegistry()
    c1.set_setting("DB_POOL_SIZE", 25)
    assert c2.get_setting("DB_POOL_SIZE") == 25
    console.print(f"  [green][PASS] Thread-Safe Singleton verified across {len(registry_instances)} concurrent threads.[/green]")

    # 2. Factory Method Verification
    console.print("[dim]Phase 2: Validating Factory Method channel creation...[/dim]")
    email_svc = NotificationFactory.create("email")
    slack_svc = NotificationFactory.create("slack")
    assert isinstance(email_svc, EmailNotificationService)
    assert isinstance(slack_svc, SlackNotificationService)

    # Test invalid channel
    try:
        NotificationFactory.create("unsupported_telepathy")
        assert False, "Should raise ValueError on invalid channel"
    except ValueError as exc:
        assert "Unsupported notification channel" in str(exc)
    console.print("  [green][PASS] NotificationFactory correctly created concrete products.[/green]")

    # 3. Observer Pattern (EnterpriseEventBus) Verification
    console.print("[dim]Phase 3: Validating Observer Pattern (Pub-Sub Event Bus)...[/dim]")
    bus = EnterpriseEventBus()
    received_events: List[SystemEvent] = []

    def audit_listener(event: SystemEvent) -> None:
        received_events.append(event)

    bus.subscribe("order.placed", audit_listener)

    # Publish event
    test_event = SystemEvent("order.placed", {"order_id": "ord_9901", "total": 450.0}, "checkout_api")
    dispatched_count = bus.publish(test_event)
    assert dispatched_count == 1
    assert len(received_events) == 1
    assert received_events[0].data["order_id"] == "ord_9901"

    # Test unsubscribe
    bus.unsubscribe("order.placed", audit_listener)
    dispatched_after_unsub = bus.publish(test_event)
    assert dispatched_after_unsub == 0
    assert len(received_events) == 1  # No new events received
    console.print("  [green][PASS] EnterpriseEventBus subscribe, dispatch, and unsubscribe verified.[/green]")

    # 4. Strategy Pattern Verification
    console.print("[dim]Phase 4: Validating Functional Strategy Pattern...[/dim]")
    items = [
        InvoiceItem("Cloud Compute Instance", 100.0, 5),
        InvoiceItem("Object Storage Tier", 20.0, 10),
    ]
    # Total units = 15. Subtotal = (5*100) + (10*20) = 500 + 200 = 700.0

    calc = InvoiceCalculator(standard_pricing_strategy)
    assert calc.calculate_total(items) == 700.0

    # Switch strategy to bulk discount (15% off 700.0 = 595.0)
    calc.strategy = bulk_discount_pricing_strategy
    assert calc.calculate_total(items) == 595.0

    # Switch strategy to VIP (25% off 700.0 = 525.0)
    calc.strategy = enterprise_vip_pricing_strategy
    assert calc.calculate_total(items) == 525.0
    console.print("  [green][PASS] Functional Strategy swapping verified (Standard: 700, Bulk: 595, VIP: 525).[/green]")

    # Summary Table
    table = Table(title="Design Patterns Architecture vs Node.js & PHP", border_style="green")
    table.add_column("Pattern", style="bold cyan")
    table.add_column("Pythonic Implementation", style="white")
    table.add_column("Node.js (TypeScript) Equivalent", style="yellow")
    table.add_column("PHP (Laravel) Equivalent", style="magenta")

    table.add_row("Singleton", "`__new__` + double-checked locking", "Module caching (`require.cache`)", "Laravel IoC Container `singleton()`")
    table.add_row("Factory Method", "Class registry mapping + create()", "Static factory or dependency injection", "Service Provider factory closures")
    table.add_row("Observer", "Callable subscription registry", "`EventEmitter` (`events` core module)", "Laravel `Event::listen()` / Observers")
    table.add_row("Strategy", "First-class `Callable` functions", "Function parameters / lambdas", "Strategy interface or arrow functions")

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
