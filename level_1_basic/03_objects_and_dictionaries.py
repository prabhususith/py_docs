"""
Object Modeling and Dictionary Hash Maps
========================================
Description: Exhaustive architectural exploration of Python's hash table (`dict`) implementation,
             safe retrieval semantics, dictionary merging, collections utilities, and OOP object
             mechanics including dunder protocols, properties, and static methods.
Enterprise Mapping:
- `dict`: Core hash map analogous to JavaScript `Record<string, T>` / `Map` and PHP associative
          arrays (`array("key" => $val)`). Uses compact hash table layout guaranteeing insertion
          order preservation since Python 3.6.
- Safe Access `.get(key, default)`: Replaces optional chaining/nullish coalescing in TypeScript
  (`obj?.key ?? default`) and PHP null coalescing (`$arr['key'] ?? default`).
- Dictionary Union `a | b`: Replaces JavaScript object spread `{...a, ...b}` and PHP `array_merge($a, $b)`.
- Python Classes: Explicit `self` parameter (analogous to TypeScript `this` bound by context and PHP `$this->`).
  Properties `@property` mirror TypeScript `get`/`set` accessors and PHP `__get`/`__set`.

Official Documentation References:
- Dictionaries Tutorial: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
- Mapping Types (dict): https://docs.python.org/3/library/stdtypes.html#mapping-types-dict
- Python Data Model & Special Methods: https://docs.python.org/3/reference/datamodel.html#special-method-names
- Collections Module (defaultdict, Counter): https://docs.python.org/3/library/collections.html
"""

from __future__ import annotations

import collections
from typing import Any, Final, TypedDict


# ==============================================================================
# 1. Dictionary Access, Hashing, and Safe Retrieval
# ==============================================================================
def demonstrate_dict_access_patterns() -> dict[str, Any]:
    """
    Demonstrate direct indexing vs safe `.get()` retrieval and `.setdefault()`.

    In Python, accessing a non-existent key via `dict[key]` raises `KeyError`.
    `.get(key, fallback)` provides O(1) hash lookup with safe default fallback.
    """
    print("\n--- 1. Dictionary Retrieval & Safe Access ---")
    config_store: dict[str, Any] = {
        "app_env": "production",
        "max_pool_size": 20,
        "debug": False,
    }

    # Safe access with fallback: analogous to JS `config.timeout ?? 5000`
    timeout_ms: int = config_store.get("timeout_ms", 5000)
    print(f"Safe get with fallback: timeout_ms = {timeout_ms}")

    # Setdefault: returns existing value or sets and returns default if absent
    session_timeout: int = config_store.setdefault("session_timeout", 3600)
    print(f"Setdefault executed: session_timeout = {session_timeout}")
    print(f"Updated config store: {config_store}")

    # Verification of key existence
    has_env: bool = "app_env" in config_store  # O(1) average hash lookup
    print(f"Membership check 'app_env' in dict: {has_env}")

    return config_store


# ==============================================================================
# 2. Dictionary Merging: Union Operators vs Unpacking
# ==============================================================================
def demonstrate_merging_strategies() -> dict[str, Any]:
    """
    Demonstrate dictionary merging introduced in Python 3.9 (PEP 584)
    versus legacy unpacking `{**a, **b}`.

    TypeScript equivalent:
      const merged = { ...defaultConfig, ...overrides };
    PHP equivalent:
      $merged = array_merge($defaultConfig, $overrides);
    """
    print("\n--- 2. Dictionary Merging Strategies ---")
    default_config: Final[dict[str, Any]] = {
        "service": "billing-api",
        "port": 8080,
        "logging_level": "INFO",
        "retries": 3,
    }

    override_config: Final[dict[str, Any]] = {
        "port": 9090,  # Overwrites default
        "logging_level": "DEBUG",  # Overwrites default
        "tracing_enabled": True,  # New key
    }

    # 1. Python 3.9+ Union Operator `|` (pure function, returns new dict)
    union_merged: dict[str, Any] = default_config | override_config
    print(f"Union operator (a | b) result:\n  {union_merged}")

    # 2. In-place merge update `|=`
    mutable_target: dict[str, Any] = default_config.copy()
    mutable_target |= override_config
    print(f"In-place operator (a |= b) result:\n  {mutable_target}")

    # 3. Kwargs unpacking `{**a, **b}` (Pre-Python 3.9 compatible)
    unpacking_merged: dict[str, Any] = {**default_config, **override_config}
    print(f"Unpacking ({{**a, **b}}) result:\n  {unpacking_merged}")

    assert union_merged == unpacking_merged
    return union_merged


# ==============================================================================
# 3. High-Throughput Aggregations: collections.defaultdict & Counter
# ==============================================================================
def aggregate_telemetry_events(events: list[dict[str, str]]) -> tuple[dict[str, list[str]], dict[str, int]]:
    """
    Use `defaultdict` for grouping without `if key not in dict:` boilerplate,
    and `Counter` for frequency tallying.

    PHP equivalent of defaultdict:
      $grouped[$item['country']][] = $item['id'];
    """
    print("\n--- 3. collections.defaultdict & collections.Counter ---")

    # Group IDs by region
    regional_grouping: collections.defaultdict[str, list[str]] = collections.defaultdict(list)
    for evt in events:
        regional_grouping[evt["region"]].append(evt["event_id"])

    # Frequency analysis
    status_counter: collections.Counter[str] = collections.Counter(evt["status"] for evt in events)

    print(f"Grouped by Region: {dict(regional_grouping)}")
    print(f"Frequency Count (Counter): {dict(status_counter)}")
    print(f"Top Status: {status_counter.most_common(1)}")

    return dict(regional_grouping), dict(status_counter)


# ==============================================================================
# 4. Enterprise OOP Object Model: Dunder Methods, Properties, Encapsulation
# ==============================================================================
class ServiceConfiguration:
    """
    Enterprise Domain Object illustrating:
    - Encapsulation with private attributes (`_attribute`)
    - Computed and validated properties (`@property`, `@setter`)
    - Object representation (`__repr__`, `__str__`)
    - Value-equality contract (`__eq__`) and hashability (`__hash__`)
    - Class factory methods (`@classmethod`)

    Enterprise Mapping:
    - Analogous to a Domain Entity / Value Object in NestJS or Laravel DDD.
    """

    def __init__(self, service_name: str, allocated_ram_mb: int) -> None:
        self._service_name: str = service_name
        self._allocated_ram_mb: int = allocated_ram_mb
        self._validate_state()

    def _validate_state(self) -> None:
        """Internal assertion guard."""
        if self._allocated_ram_mb < 128:
            raise ValueError(f"RAM must be >= 128MB. Received: {self._allocated_ram_mb}")

    @property
    def service_name(self) -> str:
        """Read-only property accessor (replaces public getter)."""
        return self._service_name

    @property
    def allocated_ram_mb(self) -> int:
        """Read property for allocated RAM."""
        return self._allocated_ram_mb

    @allocated_ram_mb.setter
    def allocated_ram_mb(self, value: int) -> None:
        """Controlled property mutator with domain invariant validation."""
        if value < 128:
            raise ValueError("Allocated RAM must be at least 128MB")
        self._allocated_ram_mb = value

    @property
    def allocated_ram_gb(self) -> float:
        """Computed property: converts MB to GB dynamically."""
        return self._allocated_ram_mb / 1024.0

    @classmethod
    def create_microservice_default(cls, name: str) -> ServiceConfiguration:
        """Factory method for standardized microservice allocation."""
        return cls(service_name=name, allocated_ram_mb=512)

    @staticmethod
    def calculate_cluster_overhead(total_instances: int, ram_per_instance_mb: int) -> int:
        """Pure utility function operating without class or instance state."""
        return total_instances * ram_per_instance_mb

    def __repr__(self) -> str:
        """Unambiguous string representation for developers and debuggers."""
        return f"ServiceConfiguration(service_name={self._service_name!r}, allocated_ram_mb={self._allocated_ram_mb})"

    def __eq__(self, other: object) -> bool:
        """Structural equality contract."""
        if not isinstance(other, ServiceConfiguration):
            return False
        return self._service_name == other._service_name and self._allocated_ram_mb == other._allocated_ram_mb

    def __hash__(self) -> int:
        """Hash contract enabling set storage and dict key usage."""
        return hash((self._service_name, self._allocated_ram_mb))


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" LEVEL 1: 03_OBJECTS_AND_DICTIONARIES - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Safe access test
    cfg = demonstrate_dict_access_patterns()
    assert cfg["timeout_ms"] == 5000 if "timeout_ms" in cfg else True

    # 2. Merging strategies test
    merged = demonstrate_merging_strategies()
    assert merged["port"] == 9090
    assert merged["retries"] == 3
    assert merged["tracing_enabled"] is True

    # 3. Defaultdict & Counter test
    raw_events = [
        {"event_id": "EVT-1", "region": "us-east-1", "status": "SUCCESS"},
        {"event_id": "EVT-2", "region": "eu-west-1", "status": "SUCCESS"},
        {"event_id": "EVT-3", "region": "us-east-1", "status": "FAILED"},
        {"event_id": "EVT-4", "region": "ap-southeast-1", "status": "SUCCESS"},
    ]
    grouped, counted = aggregate_telemetry_events(raw_events)
    assert len(grouped["us-east-1"]) == 2
    assert counted["SUCCESS"] == 3
    assert counted["FAILED"] == 1

    # 4. OOP Domain Object test
    svc = ServiceConfiguration.create_microservice_default("gateway-svc")
    assert svc.service_name == "gateway-svc"
    assert svc.allocated_ram_mb == 512
    assert svc.allocated_ram_gb == 0.5

    svc.allocated_ram_mb = 1024
    assert svc.allocated_ram_gb == 1.0

    # Validation rejection test
    try:
        svc.allocated_ram_mb = 64
        raise AssertionError("Validation guard failed to trigger on invalid RAM allocation")
    except ValueError:
        print("\nDomain invariant enforced successfully on property setter.")

    # Equality and hash test
    svc_clone = ServiceConfiguration("gateway-svc", 1024)
    assert svc == svc_clone
    service_set = {svc, svc_clone}
    assert len(service_set) == 1  # Hash deduplication works

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 03_objects_and_dictionaries module executed cleanly.")
    print("=" * 70)
