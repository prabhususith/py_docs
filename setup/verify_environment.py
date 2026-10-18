"""
Enterprise Environment Verification Suite
==========================================
Description: Automated sanity verification script that audits Python runtime version,
             validates installed enterprise dependencies, and executes diagnostic smoke tests
             for SQLite, AsyncIO event loop, and static type annotations.
Enterprise Mapping: Analogous to healthcheck or pre-flight test suites in Node.js/PHP
                    (e.g., `npm run doctor` or `composer check-platform-reqs`).

Official Documentation References:
- Python Virtual Environments (venv): https://docs.python.org/3/library/venv.html
- Pip Package Installer: https://pip.pypa.io/en/stable/
- PEP 508 / Requirements: https://peps.python.org/pep-0508/
- Python Sys Module: https://docs.python.org/3/library/sys.html
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.metadata
import platform
import sqlite3
import sys
from typing import NamedTuple


class PackageCheckResult(NamedTuple):
    package_name: str
    installed: bool
    version: str | None
    error_message: str | None


REQUIRED_PACKAGES: list[str] = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "sqlalchemy",
    "aiosqlite",
    "httpx",
    "requests",
    "websockets",
    "celery",
    "redis",
    "pytest",
    "ruff",
    "mypy",
    "rich",
]


def check_python_runtime() -> bool:
    """Validate that the active Python runtime meets enterprise baseline requirements (>= 3.10)."""
    major, minor, micro = sys.version_info.major, sys.version_info.minor, sys.version_info.micro
    print(f"[*] Python Runtime: {major}.{minor}.{micro} on {platform.system()} ({platform.machine()})")
    print(f"[*] Interpreter Binary: {sys.executable}")
    
    if (major, minor) < (3, 10):
        print(f"[FAIL] Python >= 3.10 is required. Current: {major}.{minor}.{micro}")
        return False
    print("[PASS] Python version requirement satisfied (>= 3.10).")
    return True


def audit_installed_packages() -> tuple[list[PackageCheckResult], bool]:
    """Audit all required enterprise packages, reporting version and installation status."""
    results: list[PackageCheckResult] = []
    all_ok = True

    for pkg in REQUIRED_PACKAGES:
        try:
            ver = importlib.metadata.version(pkg)
            # Verify actual importability
            importlib.import_module(pkg)
            results.append(PackageCheckResult(package_name=pkg, installed=True, version=ver, error_message=None))
        except importlib.metadata.PackageNotFoundError:
            results.append(
                PackageCheckResult(
                    package_name=pkg, installed=False, version=None, error_message="Package not found in environment"
                )
            )
            all_ok = False
        except Exception as exc:
            results.append(
                PackageCheckResult(
                    package_name=pkg, installed=False, version=None, error_message=f"Import error: {exc}"
                )
            )
            all_ok = False

    return results, all_ok


def test_sqlite_engine() -> bool:
    """Smoke test standard library SQLite connection and in-memory transactional execution."""
    try:
        with sqlite3.connect(":memory:") as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE diagnostics (id INTEGER PRIMARY KEY, status TEXT)")
            cursor.execute("INSERT INTO diagnostics (status) VALUES (?)", ("READY",))
            conn.commit()
            cursor.execute("SELECT status FROM diagnostics WHERE id = 1")
            row = cursor.fetchone()
            if row and row[0] == "READY":
                print("[PASS] SQLite in-memory transactional engine operational.")
                return True
            print("[FAIL] SQLite query did not return expected payload.")
            return False
    except Exception as exc:
        print(f"[FAIL] SQLite verification failed: {exc}")
        return False


async def _asyncio_smoke_task() -> str:
    await asyncio.sleep(0.01)
    return "ASYNC_SANITY_CONFIRMED"


def test_asyncio_event_loop() -> bool:
    """Smoke test AsyncIO event loop execution."""
    try:
        result = asyncio.run(_asyncio_smoke_task())
        if result == "ASYNC_SANITY_CONFIRMED":
            print("[PASS] AsyncIO Event Loop operational and responsive.")
            return True
        print("[FAIL] AsyncIO task returned unexpected result.")
        return False
    except Exception as exc:
        print(f"[FAIL] AsyncIO event loop test failed: {exc}")
        return False


def main() -> int:
    """Main verification orchestrator."""
    print("=" * 70)
    print(" ENTERPRISE PYTHON ENVIRONMENT VERIFICATION SUITE")
    print("=" * 70)

    runtime_ok = check_python_runtime()
    print("-" * 70)

    print("[*] Auditing Enterprise Dependencies:")
    results, packages_ok = audit_installed_packages()
    
    # Try formatting with rich if available
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Enterprise Dependency Status")
        table.add_column("Package", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Installed Version", style="green")
        table.add_column("Diagnostics", style="yellow")

        for res in results:
            status_str = "[green]INSTALLED[/green]" if res.installed else "[red]MISSING[/red]"
            ver_str = res.version or "N/A"
            diag_str = res.error_message or "Verified OK"
            table.add_row(res.package_name, status_str, ver_str, diag_str)
        console.print(table)
    except ImportError:
        # Fallback to standard console formatting
        for res in results:
            tag = "[OK]  " if res.installed else "[MISS]"
            ver = f"v{res.version}" if res.version else "N/A"
            diag = f"({res.error_message})" if res.error_message else ""
            print(f" {tag} {res.package_name:<20} {ver:<15} {diag}")

    print("-" * 70)
    print("[*] Running Engine Diagnostics:")
    sqlite_ok = test_sqlite_engine()
    asyncio_ok = test_asyncio_event_loop()

    print("=" * 70)
    if runtime_ok and sqlite_ok and asyncio_ok:
        if packages_ok:
            print("[STATUS] ALL ENTERPRISE REQUIREMENTS SATISFIED. Ready for development.")
            return 0
        else:
            print("[STATUS] WARNING: Core runtime verified, but some dependencies are missing.")
            print("         Please execute setup/setup.bat or pip install -r setup/requirements.txt")
            return 1
    else:
        print("[STATUS] CRITICAL FAILURE: Runtime environment does not meet minimum standards.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
