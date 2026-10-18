r"""
Metaclasses and Class Decorators Architecture
============================================
Description: Production implementation of Python's class construction lifecycle via `type()`,
             custom metaclasses (`__new__`, `__init__`), class decorators, and modern
             `__init_subclass__` registration patterns (PEP 487).

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * TypeScript provides Class Decorators (`@Entity()`, `@Injectable()`, `@Controller()` in NestJS/TypeORM).
    Decorators wrap the constructor function after it has been defined.
  * **Key Limitation**: TypeScript and JavaScript have NO metaclass architecture! A JavaScript class
    cannot intercept its own prototype allocation or enforce structural schema rules *during* class creation.
- PHP / Laravel:
  * PHP 8 introduced Attributes (`#[ORM\Entity]`, `#[Route('/api')]`). However, PHP Attributes are strictly
    passive metadata bags; they execute zero code during class loading. A separate reflection runner
    (e.g., Doctrine Annotation Reader / Laravel Container) must manually parse them via `ReflectionClass`.
  * PHP classes cannot dynamically alter their own method table during compilation.
- Memory & Performance Tradeoffs:
  * In Python, "classes are instances of metaclasses" (by default, `type`).
  * Metaclass `__new__` and `__init_subclass__` execute strictly ONCE at module import time when the
    class definition is evaluated.
  * There is **zero runtime overhead** during instance creation or method invocation, making metaclasses
    the preferred pattern for ORMs (SQLAlchemy, Django) and serialization engines (Pydantic).

Official Documentation References:
- Python Metaclasses: https://docs.python.org/3/reference/datamodel.html#metaclasses
- Customizing Class Creation (__init_subclass__): https://docs.python.org/3/reference/datamodel.html#customizing-class-creation
- PEP 487 – Simpler customization of class creation: https://peps.python.org/pep-0487/
"""

from __future__ import annotations

import sys
import time
from typing import Any, Callable, ClassVar, Dict, List, Optional, Type, TypeVar

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
# 1. Custom Metaclass: Enterprise Model Contract Enforcement
# ==============================================================================


class EnterpriseEntityMeta(type):
    """
    Custom Metaclass for Enterprise Domain Entities.

    Responsibilities:
    1. Enforce that every entity declares a `TABLE_NAME` class attribute.
    2. Enforce that method names conform to snake_case naming conventions.
    3. Automatically register all subclasses into a central Schema Registry.
    """

    # Global Schema Registry mapping table names to Entity Classes
    REGISTRY: Dict[str, Type[Any]] = {}

    def __new__(
        mcs,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> type:
        """
        Allocates and constructs the class object itself (runs at import time).
        mcs: The metaclass (EnterpriseEntityMeta)
        name: The name of the class being created (e.g. 'UserEntity')
        bases: Tuple of base classes
        namespace: Dictionary of attributes and methods defined in class body
        """
        # Skip validation on the root abstract base itself
        if name != "BaseEnterpriseEntity":
            # 1. Enforce TABLE_NAME class variable
            if "TABLE_NAME" not in namespace or not namespace["TABLE_NAME"]:
                raise TypeError(
                    f"Entity class '{name}' must declare non-empty 'TABLE_NAME'."
                )

            # 2. Enforce snake_case naming on all defined methods
            for attr_name, attr_val in namespace.items():
                if callable(attr_val) and not attr_name.startswith("__"):
                    if any(c.isupper() for c in attr_name):
                        raise TypeError(
                            f"Method '{attr_name}' in class '{name}' violates snake_case convention."
                        )

        # Allocate class object via type.__new__
        new_class = super().__new__(mcs, name, bases, namespace)

        # 3. Register entity into global registry
        if name != "BaseEnterpriseEntity":
            table_name = namespace["TABLE_NAME"]
            mcs.REGISTRY[table_name] = new_class

        return new_class


class BaseEnterpriseEntity(metaclass=EnterpriseEntityMeta):
    """
    Root base entity inheriting the EnterpriseEntityMeta metaclass.
    All subclasses automatically undergo metaclass validation and registration.
    """

    TABLE_NAME: ClassVar[str] = ""

    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


# ==============================================================================
# 2. Modern Alternative: PEP 487 `__init_subclass__`
# ==============================================================================


class PluginRegistryBase:
    """
    Modern alternative to metaclasses introduced in Python 3.6 (PEP 487).
    Eliminates metaclass conflict issues in multi-inheritance hierarchies.

    Polyglot Comparison:
    - Node.js: Requires manual `@Plugin()` decorator or decorator factory.
    - PHP: Requires scanning classes via Reflection or Laravel Service Provider discovery.
    - Python: Native language hook `__init_subclass__` automatically called whenever
      a class inherits from `PluginRegistryBase`.
    """

    PLUGINS: ClassVar[Dict[str, Type[PluginRegistryBase]]] = {}

    @classmethod
    def __init_subclass__(cls, plugin_code: str, **kwargs: Any) -> None:
        """
        Hook called at subclass definition time.
        Allows passing keyword arguments directly in the class definition header!
        """
        super().__init_subclass__(**kwargs)
        if not plugin_code:
            raise ValueError(f"Class '{cls.__name__}' must specify a non-empty plugin_code.")
        if plugin_code in cls.PLUGINS:
            raise KeyError(f"Plugin code '{plugin_code}' is already registered by '{cls.PLUGINS[plugin_code].__name__}'.")

        cls.PLUGINS[plugin_code] = cls

    @classmethod
    def execute_plugin(cls, plugin_code: str, *args: Any, **kwargs: Any) -> Any:
        """Factory method instantiating and executing registered plugin by code."""
        if plugin_code not in cls.PLUGINS:
            raise KeyError(f"Unknown plugin code: '{plugin_code}'.")
        plugin_instance = cls.PLUGINS[plugin_code]()
        return plugin_instance.run(*args, **kwargs)

    def run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("Subclasses must implement run().")


# ==============================================================================
# 3. Class Decorators: Cross-Cutting Metadata & Interception
# ==============================================================================


def track_instantiations(cls: Type[T]) -> Type[T]:
    """
    Class decorator that wraps `__init__` to record instance metrics.

    Polyglot Comparison:
    - Node.js / TypeScript: Identical to TypeScript class decorators:
      `function track(target: Function) { ... }`.
    - PHP: PHP Attributes cannot alter constructor behavior directly; they only provide metadata.
    """
    orig_init = cls.__init__
    cls._instance_count = 0  # type: ignore[attr-defined]

    def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
        cls._instance_count += 1  # type: ignore[attr-defined]
        self._created_timestamp = time.time()
        orig_init(self, *args, **kwargs)

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    return cls


# ==============================================================================
# 4. Concrete Domain Models Demonstrating Concepts
# ==============================================================================


class UserEntity(BaseEnterpriseEntity):
    """Fulfills metaclass contract: defines TABLE_NAME and snake_case methods."""

    TABLE_NAME = "users"

    def get_full_name(self) -> str:
        return f"{getattr(self, 'first_name', '')} {getattr(self, 'last_name', '')}".strip()


class PaymentAuditEntity(BaseEnterpriseEntity):
    """Fulfills metaclass contract with unique table."""

    TABLE_NAME = "payment_audits"

    def calculate_total_tax(self, rate: float) -> float:
        return float(getattr(self, "amount", 0.0)) * rate


# Concrete Plugins utilizing PEP 487 __init_subclass__
class StripePaymentPlugin(PluginRegistryBase, plugin_code="stripe"):
    def run(self, amount: float) -> str:
        return f"Processed ${amount:.2f} via Stripe Gateway"


class PayPalPaymentPlugin(PluginRegistryBase, plugin_code="paypal"):
    def run(self, amount: float) -> str:
        return f"Processed ${amount:.2f} via PayPal Express"


# Class Decorator Usage
@track_instantiations
class EphemeralSession:
    def __init__(self, session_token: str) -> None:
        self.session_token = session_token


# ==============================================================================
# 5. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying metaclass enforcement, PEP 487, and decorators."""
    console.print(
        Panel.fit(
            "[bold cyan]Advanced OOP: Metaclasses & Class Decorators[/bold cyan]\n"
            "[dim]Verifying metaclass __new__ validation, global registry, and __init_subclass__ (PEP 487).[/dim]",
            border_style="cyan",
        )
    )

    # 1. Metaclass Auto-Registration Verification
    console.print("[dim]Phase 1: Validating metaclass automatic schema registration...[/dim]")
    registry = EnterpriseEntityMeta.REGISTRY
    assert "users" in registry, "UserEntity was not registered by metaclass."
    assert registry["users"] is UserEntity
    assert "payment_audits" in registry
    assert registry["payment_audits"] is PaymentAuditEntity
    console.print(f"  [green][PASS] Metaclass successfully registered entities: {list(registry.keys())}[/green]")

    # 2. Metaclass Enforcement Rejections (Failure Modes)
    console.print("[dim]Phase 2: Validating metaclass schema and naming enforcement...[/dim]")

    # Missing TABLE_NAME
    try:
        class InvalidMissingTable(BaseEnterpriseEntity):
            pass
        assert False, "Should raise TypeError on missing TABLE_NAME"
    except TypeError as exc:
        assert "must declare non-empty 'TABLE_NAME'" in str(exc)
        console.print("  [green][PASS] Metaclass blocked entity missing TABLE_NAME.[/green]")

    # CamelCase method violation
    try:
        class InvalidCamelCaseMethod(BaseEnterpriseEntity):
            TABLE_NAME = "test_table"
            def calculateTotal(self): pass  # Violates snake_case
        assert False, "Should raise TypeError on camelCase method"
    except TypeError as exc:
        assert "violates snake_case convention" in str(exc)
        console.print("  [green][PASS] Metaclass blocked method violating snake_case naming.[/green]")

    # 3. PEP 487 __init_subclass__ Plugin Architecture
    console.print("[dim]Phase 3: Validating PEP 487 __init_subclass__ plugin dispatch...[/dim]")
    assert "stripe" in PluginRegistryBase.PLUGINS
    assert "paypal" in PluginRegistryBase.PLUGINS

    res_stripe = PluginRegistryBase.execute_plugin("stripe", amount=149.99)
    assert res_stripe == "Processed $149.99 via Stripe Gateway"

    res_paypal = PluginRegistryBase.execute_plugin("paypal", amount=29.50)
    assert res_paypal == "Processed $29.50 via PayPal Express"
    console.print("  [green][PASS] Plugin discovery and dispatch via __init_subclass__ verified.[/green]")

    # 4. Class Decorator Verification
    console.print("[dim]Phase 4: Validating class decorator constructor wrapping...[/dim]")
    assert EphemeralSession._instance_count == 0  # type: ignore[attr-defined]
    s1 = EphemeralSession("tok_abc")
    s2 = EphemeralSession("tok_xyz")
    assert EphemeralSession._instance_count == 2  # type: ignore[attr-defined]
    assert hasattr(s1, "_created_timestamp")
    console.print(f"  [green][PASS] Class decorator constructor wrapping verified (instances={EphemeralSession._instance_count}).[/green]")

    # Summary Table
    table = Table(title="Metaprogramming Architecture: Python vs TS vs PHP", border_style="green")
    table.add_column("Metaprogramming Mechanism", style="bold cyan")
    table.add_column("Execution Timing", style="white")
    table.add_column("Modification Power", style="bold green")
    table.add_column("TypeScript Equivalent", style="yellow")
    table.add_column("PHP Equivalent", style="magenta")

    table.add_row(
        "Metaclass (`type`)",
        "Class compilation (import time)",
        "Can alter class namespace, slots, bases, and prevent class creation",
        "NOT SUPPORTED",
        "NOT SUPPORTED",
    )
    table.add_row(
        "`__init_subclass__`",
        "Subclass definition time (PEP 487)",
        "Can validate subclass, register plugins, and pass class args",
        "Class Decorator factory",
        "Manual Reflection discovery",
    )
    table.add_row(
        "Class Decorator",
        "Post-class creation (import time)",
        "Can wrap methods, add class properties, or return proxy class",
        "Class Decorators (`@Injectable()`)",
        "PHP 8 Attributes (passive metadata only)",
    )

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
