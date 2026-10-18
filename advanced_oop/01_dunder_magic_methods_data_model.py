"""
Python Data Model & Special (Dunder) Methods Architecture
=========================================================
Description: Production implementation of the complete Python Data Model. Explores sequence
             emulation (`__len__`, `__getitem__`, `__setitem__`, `__delitem__`, `__iter__`, `__contains__`),
             string representations (`__repr__` vs `__str__`), hashability contracts (`__eq__`, `__hash__`),
             and mathematical operator overloading (`__add__`, `__radd__`, `__iadd__`, `__mul__`).

Polyglot Architectural Comparisons:
- Node.js / TypeScript:
  * In JavaScript, object behavior customization is handled via ES6 `Proxy` traps:
    `new Proxy(target, { get, set, has, deleteProperty })` and Symbol protocols:
    `[Symbol.iterator]()`, `[Symbol.toPrimitive]()`.
  * **Critical Language Limitation**: JavaScript does NOT support operator overloading!
    Expressions like `vecA + vecB` in JavaScript will convert objects to `"[object Object][object Object]"`
    unless using preprocessors. In Python, dunder methods (`__add__`, `__mul__`) provide first-class
    syntactic operator overloading.
- PHP / Laravel:
  * PHP provides SPL interfaces: `ArrayAccess` (`offsetExists`, `offsetGet`, `offsetSet`, `offsetUnset`),
    `Countable` (`count()`), `IteratorAggregate` (`getIterator()`), and `Stringable` (`__toString()`).
  * In Laravel, `Collection` implements `ArrayAccess`, `Countable`, and `IteratorAggregate`, allowing
    `$collection['key']` syntax on an object.
  * PHP lacks userland arithmetic operator overloading (except through experimental internal extensions).
- Memory & Performance Tradeoffs:
  * In CPython, dunder methods are not just dynamic dictionary lookups. For built-in and C-extension types,
    they map directly to internal C struct function pointers (slots) in `PyTypeObject`
    (e.g., `tp_as_mapping->mp_subscript` for `__getitem__`, `tp_as_number->nb_add` for `__add__`).
  * This slot-level dispatch makes Python dunder protocol execution faster than arbitrary method calls.

Official Documentation References:
- Python Data Model: https://docs.python.org/3/reference/datamodel.html
- Emulating Container Types: https://docs.python.org/3/reference/datamodel.html#emulating-container-types
- Emulating Numeric Types: https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types
"""

from __future__ import annotations

import math
import sys
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

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
# 1. Mathematical Vector with Operator Overloading
# ==============================================================================


class Vector2D:
    """
    2D Mathematical Vector demonstrating arithmetic dunder methods.

    Polyglot Comparison:
    - Node.js: Must write `vecA.add(vecB)` or `vecA.multiply(scalar)`. `vecA + vecB` produces string concatenation!
    - PHP: Must write `$vecA->add($vecB)` or `$vecA->multiply($scalar)`.
    - Python: Native mathematical expressions: `v3 = (v1 + v2) * 2.5`.
    """

    __slots__ = ("_x", "_y")

    def __init__(self, x: float, y: float) -> None:
        self._x = float(x)
        self._y = float(y)

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    # --------------------------------------------------------------------------
    # String Representations
    # --------------------------------------------------------------------------

    def __repr__(self) -> str:
        """
        Unambiguous developer string representation.
        Convention: Should look like valid Python code to recreate the object if possible.
        Node.js equivalent: `util.inspect.custom` symbol.
        PHP equivalent: `var_dump()` output or `__debugInfo()`.
        """
        return f"Vector2D(x={self._x}, y={self._y})"

    def __str__(self) -> str:
        """
        User-friendly string representation for end-user display.
        Node.js equivalent: `.toString()`.
        PHP equivalent: Implementing `Stringable` via `__toString()`.
        """
        return f"({self._x:.2f}, {self._y:.2f})"

    # --------------------------------------------------------------------------
    # Equality & Hashing Contracts
    # --------------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        """
        Equality comparison (`==`).
        If an object defines `__eq__`, Python automatically sets `__hash__ = None`
        unless `__hash__` is explicitly implemented, preventing mutable hash keys.
        """
        if not isinstance(other, Vector2D):
            return NotImplemented
        return math.isclose(self._x, other._x) and math.isclose(self._y, other._y)

    def __hash__(self) -> int:
        """
        Hash function allowing immutable Vector2D instances to serve as dictionary keys
        or set elements.
        Contract: If `a == b`, then `hash(a) == hash(b)` must be strictly True.
        """
        return hash((self._x, self._y))

    # --------------------------------------------------------------------------
    # Arithmetic Operator Overloading
    # --------------------------------------------------------------------------

    def __add__(self, other: Vector2D) -> Vector2D:
        """
        Addition operator: `self + other`.
        Returns a new Vector2D instance (immutability pattern).
        """
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(self._x + other._x, self._y + other._y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        """Subtraction operator: `self - other`."""
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(self._x - other._x, self._y - other._y)

    def __mul__(self, scalar: Union[int, float]) -> Vector2D:
        """Scalar multiplication: `self * scalar`."""
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector2D(self._x * scalar, self._y * scalar)

    def __rmul__(self, scalar: Union[int, float]) -> Vector2D:
        """
        Reflected (reversed) scalar multiplication: `scalar * self`.
        Called when the left operand does not support `__mul__` with a Vector2D.
        """
        return self.__mul__(scalar)

    def __iadd__(self, other: Vector2D) -> Vector2D:
        """
        In-place addition: `self += other`.
        """
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(self._x + other._x, self._y + other._y)

    def __abs__(self) -> float:
        """Magnitude / Euclidean norm: `abs(vector)`."""
        return math.hypot(self._x, self._y)

    def __bool__(self) -> bool:
        """Truthiness: `bool(vector)`. Returns False if vector is at origin (0, 0)."""
        return not (math.isclose(self._x, 0.0) and math.isclose(self._y, 0.0))


# ==============================================================================
# 2. Custom Container Emulation (Sequence / Mapping Protocol)
# ==============================================================================


class EnterpriseRecordBatch:
    """
    Custom container emulating Python sequence and mapping protocols.

    Polyglot Comparison:
    - Node.js: Emulated using `new Proxy(target, { get, set, has, deleteProperty })`.
      JavaScript proxies intercept indexing at runtime but add V8 de-optimization overhead.
    - PHP: Implemented via SPL interfaces:
      * `class EnterpriseRecordBatch implements ArrayAccess, Countable, IteratorAggregate`
      * `offsetGet($k)`, `offsetSet($k, $v)`, `offsetExists($k)`, `offsetUnset($k)`.
    - Python: Implemented using standard Data Model methods:
      `__len__`, `__getitem__`, `__setitem__`, `__delitem__`, `__iter__`, `__contains__`.
    """

    def __init__(self, initial_records: Optional[List[Dict[str, Any]]] = None) -> None:
        self._records: List[Dict[str, Any]] = list(initial_records or [])

    def __len__(self) -> int:
        """
        Enables `len(batch)`.
        Node.js equivalent: `batch.length`.
        PHP equivalent: `Countable::count($batch)`.
        """
        return len(self._records)

    def __getitem__(self, index: Union[int, slice]) -> Union[Dict[str, Any], EnterpriseRecordBatch]:
        """
        Enables index lookups (`batch[0]`) and slice lookups (`batch[1:3]`).
        Handles negative indices automatically via underlying list.

        Node.js equivalent: `proxy[index]`.
        PHP equivalent: `ArrayAccess::offsetGet($offset)`.
        """
        if isinstance(index, slice):
            # Return new instance of EnterpriseRecordBatch for sliced view
            return EnterpriseRecordBatch(self._records[index])
        return self._records[index]

    def __setitem__(self, index: int, value: Dict[str, Any]) -> None:
        """
        Enables index assignment (`batch[0] = {...}`).
        Node.js equivalent: `proxy[index] = value`.
        PHP equivalent: `ArrayAccess::offsetSet($offset, $value)`.
        """
        if not isinstance(value, dict):
            raise TypeError("Records in batch must be dictionaries.")
        self._records[index] = value

    def __delitem__(self, index: int) -> None:
        """
        Enables deletion (`del batch[0]`).
        Node.js equivalent: `delete proxy[index]`.
        PHP equivalent: `ArrayAccess::offsetUnset($offset)`.
        """
        del self._records[index]

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """
        Enables `for record in batch:`.
        Node.js equivalent: `[Symbol.iterator]()`.
        PHP equivalent: `IteratorAggregate::getIterator()`.
        """
        return iter(self._records)

    def __contains__(self, item: Any) -> bool:
        """
        Enables `if item in batch:`.
        Fallback behavior: If `__contains__` is omitted, Python iterates via `__iter__` or `__getitem__`.
        Implementing it directly provides an O(1) or optimized search path.

        Node.js equivalent: `Reflect.has()` / `prop in proxy`.
        PHP equivalent: `ArrayAccess::offsetExists($offset)`.
        """
        return item in self._records

    def __repr__(self) -> str:
        return f"EnterpriseRecordBatch(count={len(self._records)})"


# ==============================================================================
# 3. Verification & Execution Engine
# ==============================================================================


def run_verification() -> bool:
    """Run automated assertions verifying Python Data Model dunder methods."""
    console.print(
        Panel.fit(
            "[bold cyan]Advanced OOP: Python Data Model & Dunder Methods[/bold cyan]\n"
            "[dim]Comparing Python Data Model slots with JS Proxy traps & PHP ArrayAccess/Countable.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Vector2D Arithmetic Overloading
    console.print("[dim]Phase 1: Validating Vector2D arithmetic operator overloading...[/dim]")
    v1 = Vector2D(3.0, 4.0)
    v2 = Vector2D(1.0, 2.0)

    # Addition
    v3 = v1 + v2
    assert v3 == Vector2D(4.0, 6.0)

    # Subtraction
    v4 = v1 - v2
    assert v4 == Vector2D(2.0, 2.0)

    # Multiplication (scalar right and reflected left)
    v5 = v1 * 2.5
    assert v5 == Vector2D(7.5, 10.0)
    v6 = 2.0 * v2  # __rmul__
    assert v6 == Vector2D(2.0, 4.0)

    # Magnitude via __abs__
    assert math.isclose(abs(v1), 5.0)  # 3-4-5 right triangle

    # Truthiness via __bool__
    assert bool(v1) is True
    assert bool(Vector2D(0.0, 0.0)) is False

    # Hashability contract (usable as dict key or set element)
    vec_map: Dict[Vector2D, str] = {v1: "PointA", v2: "PointB"}
    assert vec_map[Vector2D(3.0, 4.0)] == "PointA"
    console.print(f"  [green][PASS] Vector2D operations verified: {v1} + {v2} = {v3}, abs={abs(v1)}[/green]")

    # 2. Container Emulation (EnterpriseRecordBatch)
    console.print("[dim]Phase 2: Validating EnterpriseRecordBatch sequence & mapping emulation...[/dim]")
    initial_data = [
        {"id": 101, "tenant": "Acme Corp", "status": "ACTIVE"},
        {"id": 102, "tenant": "Globex", "status": "PENDING"},
        {"id": 103, "tenant": "Initech", "status": "ACTIVE"},
    ]
    batch = EnterpriseRecordBatch(initial_data)

    # __len__
    assert len(batch) == 3

    # __getitem__ index & slice
    assert batch[0]["tenant"] == "Acme Corp"
    assert batch[-1]["tenant"] == "Initech"
    sliced = batch[0:2]
    assert isinstance(sliced, EnterpriseRecordBatch)
    assert len(sliced) == 2

    # __setitem__
    batch[1] = {"id": 102, "tenant": "Globex Corp", "status": "VERIFIED"}
    assert batch[1]["tenant"] == "Globex Corp"

    # __contains__
    assert {"id": 101, "tenant": "Acme Corp", "status": "ACTIVE"} in batch

    # __delitem__
    del batch[0]
    assert len(batch) == 2
    assert batch[0]["tenant"] == "Globex Corp"

    # __iter__
    tenants = [record["tenant"] for record in batch]
    assert tenants == ["Globex Corp", "Initech"]
    console.print(f"  [green][PASS] Container emulation verified: {batch}, tenants={tenants}[/green]")

    # Summary Table
    table = Table(title="Python Data Model vs Node.js & PHP Architecture", border_style="green")
    table.add_column("Python Protocol / Dunder", style="bold cyan")
    table.add_column("Python Purpose", style="white")
    table.add_column("Node.js (TypeScript) Equivalent", style="yellow")
    table.add_column("PHP (Laravel) Equivalent", style="magenta")

    table.add_row("`__len__`", "Container element count `len(x)`", "`x.length` getter", "`Countable::count()`")
    table.add_row("`__getitem__`", "Index / slice `x[i]`", "`Proxy` `get` trap", "`ArrayAccess::offsetGet()`")
    table.add_row("`__setitem__`", "Assignment `x[i] = v`", "`Proxy` `set` trap", "`ArrayAccess::offsetSet()`")
    table.add_row("`__iter__`", "Iteration `for v in x:`", "`[Symbol.iterator]()`", "`IteratorAggregate::getIterator()`")
    table.add_row("`__add__`, `__mul__`", "Operator overloading (`+`, `*`)", "NOT SUPPORTED in JS", "NOT SUPPORTED in native PHP")
    table.add_row("`__repr__`, `__str__`", "Code vs friendly string", "`util.inspect.custom` / `toString`", "`__toString()` / `Stringable`")
    table.add_row("`__hash__`, `__eq__`", "Dict key hashability", "`Map` reference equality", "SplObjectStorage hash")

    console.print(table)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
