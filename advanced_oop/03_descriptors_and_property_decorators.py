"""
Python Descriptors and Property Decorators Architecture
=======================================================
Description: Production implementation of the Python Descriptor Protocol (`__get__`, `__set__`,
             `__delete__`, and `__set_name__` via PEP 487). Demonstrates reusable attribute validation
             descriptors, the difference between Data and Non-Data descriptors, and standard `@property`.

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * In JavaScript, property interception is configured per-property via `Object.defineProperty()`
    or TypeScript getter/setter accessors (`get field()`, `set field(val)`).
  * JavaScript has NO first-class reusable descriptor object protocol. To reuse validation logic,
    TypeScript requires stage-3 experimental decorators (`@Validate()`), which rely on reflection
    metadata (`reflect-metadata`).
- PHP / Laravel:
  * PHP relies on magic methods `__get($name)` and `__set($name, $value)`. In Laravel, Eloquent models
    route all column access through `__get` and `__set` to implement mutators and accessors (`getAttribute`).
  * Drawback of PHP's `__set`: It acts as a global catch-all for ANY non-public property, disabling
    IDE autocompletion and degrading Zend Engine property lookup speed (bypassing fast-path opcode caches).
- Memory & Performance Tradeoffs:
  * Python descriptors live strictly on the **Class** object (`cls.__dict__`), NOT on individual instances.
    When 100,000 instances access `record.salary`, they all reference the single shared descriptor object.
  * `__set_name__` (PEP 487) automatically captures the attribute name during class creation, eliminating
    the historical requirement to duplicate variable names (e.g., `salary = BoundedNumeric('salary')`).

Official Documentation References:
- Python Descriptor Guide: https://docs.python.org/3/howto/descriptor.html
- Python Data Model Descriptors: https://docs.python.org/3/reference/datamodel.html#descriptors
- PEP 487 – Simpler customization of class creation: https://peps.python.org/pep-0487/
"""

from __future__ import annotations

import re
import sys
from typing import Any, Callable, Generic, Optional, Type, TypeVar

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
# 1. Reusable Validation Descriptors (Data Descriptors)
# ==============================================================================


class BoundedNumeric:
    """
    Reusable data descriptor enforcing numeric boundaries.

    Polyglot Comparison:
    - Node.js: Requires writing individual setters or using class-validator `@Min()`, `@Max()`.
    - PHP: Requires explicit validation checks inside `public function setAge(int $age)` or inside `__set`.
    - Python: Reusable descriptor: `quota_gb = BoundedNumeric(min_val=10, max_val=5000)`.
    """

    def __init__(self, min_val: Optional[float] = None, max_val: Optional[float] = None) -> None:
        self.min_val = min_val
        self.max_val = max_val
        self.storage_name: str = ""

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        """
        PEP 487 hook automatically called at class creation time.
        Injects private backing attribute name (e.g., '_quota_gb').
        """
        self.storage_name = f"_{name}"

    def __get__(self, instance: Optional[object], owner: Type[Any]) -> Any:
        """
        Descriptor getter.
        If accessed from Class (e.g., `TenantConfig.quota_gb`), returns descriptor itself.
        If accessed from instance (`config.quota_gb`), returns underlying value.
        """
        if instance is None:
            return self
        return getattr(instance, self.storage_name, None)

    def __set__(self, instance: object, value: float) -> None:
        """
        Descriptor setter enforcing validation rules.
        """
        if not isinstance(value, (int, float)):
            raise TypeError(f"Attribute '{self.storage_name[1:]}' must be a numeric value.")

        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"Attribute '{self.storage_name[1:]}' ({value}) cannot be less than {self.min_val}.")

        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"Attribute '{self.storage_name[1:]}' ({value}) cannot exceed {self.max_val}.")

        setattr(instance, self.storage_name, value)


class RegexValidatedString:
    """Reusable data descriptor enforcing regex compliance (e.g., corporate emails)."""

    def __init__(self, regex_pattern: str, error_message: str = "Invalid string format.") -> None:
        self.pattern = re.compile(regex_pattern)
        self.error_message = error_message
        self.storage_name: str = ""

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.storage_name = f"_{name}"

    def __get__(self, instance: Optional[object], owner: Type[Any]) -> Any:
        if instance is None:
            return self
        return getattr(instance, self.storage_name, None)

    def __set__(self, instance: object, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"Attribute '{self.storage_name[1:]}' must be a string.")

        if not self.pattern.match(value):
            raise ValueError(f"Validation failed for '{self.storage_name[1:]}': {self.error_message}")

        setattr(instance, self.storage_name, value)


# ==============================================================================
# 2. Non-Data Descriptor (Lazy Property / Computed Cache)
# ==============================================================================


class LazyComputedProperty(Generic[T]):
    """
    Non-Data Descriptor computing an expensive attribute once and caching it
    directly in the instance's `__dict__`.

    Mechanics:
    - Because this descriptor defines `__get__` but NOT `__set__`, Python's attribute
      lookup order gives precedence to instance `__dict__` over non-data descriptors.
    - On first access: `__get__` runs, calculates value, and sets `instance.__dict__[name] = val`.
    - On second access: Python finds the value directly in `instance.__dict__`, completely
      bypassing `__get__` for optimal O(1) performance!
    """

    def __init__(self, func: Callable[[Any], T]) -> None:
        self.func = func
        self.attr_name: str = ""

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.attr_name = name

    def __get__(self, instance: Optional[object], owner: Type[Any]) -> Any:
        if instance is None:
            return self

        # Compute expensive value
        computed_val = self.func(instance)
        # Store directly in instance dict to shadow descriptor on subsequent calls
        instance.__dict__[self.attr_name] = computed_val
        return computed_val


# ==============================================================================
# 3. Domain Model Utilizing Descriptors & @property
# ==============================================================================


class EnterpriseCloudTenant:
    """
    Tenant configuration model combining data descriptors, lazy non-data descriptors,
    and standard `@property` accessors.
    """

    # Reusable Data Descriptors (with automatic __set_name__ binding)
    quota_gb = BoundedNumeric(min_val=10.0, max_val=10000.0)
    cpu_cores = BoundedNumeric(min_val=1, max_val=128)
    admin_email = RegexValidatedString(
        regex_pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        error_message="Must be a valid corporate email.",
    )

    def __init__(self, tenant_id: str, admin_email: str, quota_gb: float, cpu_cores: int) -> None:
        self.tenant_id = tenant_id
        # Descriptors intercept assignments
        self.admin_email = admin_email
        self.quota_gb = quota_gb
        self.cpu_cores = cpu_cores
        self._maintenance_mode: bool = False

    # Standard Built-in @property
    @property
    def maintenance_mode(self) -> bool:
        """Read-only or validated getter for maintenance status."""
        return self._maintenance_mode

    @maintenance_mode.setter
    def maintenance_mode(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("Maintenance mode must be a boolean.")
        self._maintenance_mode = enabled

    # Non-Data Descriptor (Calculated Once, Cached Forever in __dict__)
    @LazyComputedProperty
    def billing_tier_hash(self) -> str:
        """Simulate expensive cryptographic license key computation."""
        # Simulated expensive hashing
        import hashlib
        raw = f"{self.tenant_id}_{self.admin_email}_{self.quota_gb}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ==============================================================================
# 4. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying descriptor behavior and caching contracts."""
    console.print(
        Panel.fit(
            "[bold cyan]Advanced OOP: Descriptors & Property Decorators[/bold cyan]\n"
            "[dim]Verifying Data Descriptors, Non-Data Lazy Descriptors, and PEP 487 __set_name__.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Valid Assignment Verification
    console.print("[dim]Phase 1: Validating valid descriptor property bindings...[/dim]")
    tenant = EnterpriseCloudTenant(
        tenant_id="tenant-alpha-001",
        admin_email="sre-lead@cloud.enterprise.com",
        quota_gb=500.0,
        cpu_cores=16,
    )
    assert tenant.quota_gb == 500.0
    assert tenant.cpu_cores == 16
    assert tenant.admin_email == "sre-lead@cloud.enterprise.com"
    console.print("  [green][PASS] Valid descriptor attributes accepted and stored.[/green]")

    # 2. Boundary Validation (BoundedNumeric)
    console.print("[dim]Phase 2: Validating BoundedNumeric bounds enforcement...[/dim]")
    try:
        tenant.quota_gb = 5.0  # Min is 10.0
        assert False, "Should have raised ValueError on quota < 10"
    except ValueError as exc:
        assert "cannot be less than 10.0" in str(exc)

    try:
        tenant.quota_gb = 50000.0  # Max is 10000.0
        assert False, "Should have raised ValueError on quota > 10000"
    except ValueError as exc:
        assert "cannot exceed 10000.0" in str(exc)

    console.print("  [green][PASS] BoundedNumeric successfully rejected out-of-bounds values.[/green]")

    # 3. Regex String Validation (RegexValidatedString)
    console.print("[dim]Phase 3: Validating RegexValidatedString email format enforcement...[/dim]")
    try:
        tenant.admin_email = "not-a-valid-email"
        assert False, "Should have raised ValueError on invalid email format"
    except ValueError as exc:
        assert "Must be a valid corporate email" in str(exc)
    console.print("  [green][PASS] RegexValidatedString successfully rejected malformed email.[/green]")

    # 4. Non-Data Descriptor: Lazy Caching
    console.print("[dim]Phase 4: Validating LazyComputedProperty non-data descriptor caching...[/dim]")
    assert "billing_tier_hash" not in tenant.__dict__, "Lazy property should not be cached before first access."
    hash_val_1 = tenant.billing_tier_hash
    assert len(hash_val_1) == 16
    # After first access, property is stored directly in instance __dict__
    assert "billing_tier_hash" in tenant.__dict__
    assert tenant.__dict__["billing_tier_hash"] == hash_val_1
    console.print(f"  [green][PASS] LazyComputedProperty cached: {hash_val_1}[/green]")

    # 5. Standard @property setter validation
    console.print("[dim]Phase 5: Validating standard @property setter...[/dim]")
    tenant.maintenance_mode = True
    assert tenant.maintenance_mode is True
    try:
        tenant.maintenance_mode = "invalid_string"  # type: ignore[assignment]
        assert False, "Should raise TypeError on non-bool"
    except TypeError:
        pass
    console.print("  [green][PASS] Standard @property setter type checks verified.[/green]")

    # Summary Table
    table = Table(title="Descriptor Architecture vs Node.js & PHP", border_style="green")
    table.add_column("Mechanism", style="bold cyan")
    table.add_column("Protocol Methods", style="white")
    table.add_column("Memory Scope", style="bold green")
    table.add_column("Node.js Equivalent", style="yellow")
    table.add_column("PHP Equivalent", style="magenta")

    table.add_row(
        "Data Descriptor",
        "`__get__` + `__set__`",
        "Class level (`cls.__dict__`)",
        "`Object.defineProperty` / TypeScript setters",
        "`__set($k, $v)` magic method",
    )
    table.add_row(
        "Non-Data Descriptor",
        "`__get__` only",
        "Shadowed by instance `__dict__`",
        "Getter caching in `this._cache`",
        "`__get($k)` with `$this->cache[$k]`",
    )
    table.add_row(
        "`@property`",
        "Built-in Data Descriptor",
        "Class level",
        "`get prop()` / `set prop()`",
        "Getter / Setter methods",
    )
    table.add_row(
        "`__set_name__`",
        "Automatic attribute naming",
        "Class creation time (PEP 487)",
        "TypeScript Property Decorators",
        "PHP 8 Attributes (via Reflection)",
    )

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
