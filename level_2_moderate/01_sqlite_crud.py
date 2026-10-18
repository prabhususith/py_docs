"""
Enterprise Relational Persistence with SQLite3
===============================================
Description: Production-grade relational database persistence utilizing Python's built-in
             `sqlite3` engine. Demonstrates connection context management, parameterized
             queries, ACID transaction boundaries with automatic rollback, custom row
             factories for associative mappings, and batch mutations.
Enterprise Mapping:
- Parameterized Queries (`?`): Direct counterpart to PDO prepared statements in PHP
  (`$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?")`) and parameterized drivers
  in Node.js (`pg.query("SELECT * FROM users WHERE id = $1", [id])`). Eliminates SQL injection.
- Connection Context Manager: Automates `BEGIN TRANSACTION`, `COMMIT` on block completion,
  and `ROLLBACK` on unhandled exception, eliminating manual boilerplate.
- `sqlite3.Row` Factory: Replaces PHP `PDO::FETCH_ASSOC` and Node.js record objects, allowing
  both key-based (`row["email"]`) and index-based (`row[0]`) column access.

Official Documentation References:
- Python SQLite3 Module: https://docs.python.org/3/library/sqlite3.html
- Transaction Control: https://docs.python.org/3/library/sqlite3.html#transaction-control
- SQLite Row Objects: https://docs.python.org/3/library/sqlite3.html#row-objects
"""

from __future__ import annotations

import contextlib
import os
import sqlite3
from typing import Any, Final, Generator, NamedTuple


class UserRecord(NamedTuple):
    user_id: int | None
    email: str
    username: str
    is_active: bool
    balance: float


class SQLiteDatabaseManager:
    """
    Enterprise Data Access Gateway managing connection lifecycles, schema migrations,
    and transactional CRUD operations.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path: str = db_path
        # When operating on an in-memory database, persist the connection so schema and data survive
        self._shared_conn: sqlite3.Connection | None = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:")
            self._shared_conn.row_factory = sqlite3.Row
            self._shared_conn.execute("PRAGMA foreign_keys = ON;")
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Create or return connection configured with foreign keys enabled and dictionary row factory."""
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_database(self) -> None:
        """Execute DDL migrations inside transaction."""
        schema_sql: Final[str] = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            balance REAL NOT NULL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """
        with self._get_connection() as conn:
            conn.executescript(schema_sql)

    # --------------------------------------------------------------------------
    # CREATE Operations
    # --------------------------------------------------------------------------
    def insert_user(self, email: str, username: str, balance: float = 0.0) -> int:
        """
        Insert a single user record using parameterized values.
        Returns newly generated primary key id.
        """
        sql: Final[str] = """
        INSERT INTO users (email, username, balance)
        VALUES (?, ?, ?);
        """
        # Connection context manager automatically commits on success and rolls back on exception
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (email.strip().lower(), username.strip(), balance))
            last_id: int = cursor.lastrowid
            return last_id

    def bulk_insert_users(self, records: list[tuple[str, str, float]]) -> int:
        """
        Execute high-throughput batch insertion via `executemany`.
        Equivalent to batch INSERT in Node.js Knex or PHP batch queries.
        """
        sql: Final[str] = """
        INSERT INTO users (email, username, balance)
        VALUES (?, ?, ?);
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, records)
            return cursor.rowcount

    # --------------------------------------------------------------------------
    # READ Operations
    # --------------------------------------------------------------------------
    def get_user_by_id(self, user_id: int) -> sqlite3.Row | None:
        """
        Retrieve record by primary key with parameterized lookup.
        """
        sql: Final[str] = "SELECT * FROM users WHERE id = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id,))
            row: sqlite3.Row | None = cursor.fetchone()
            return row

    def get_user_by_email(self, email: str) -> sqlite3.Row | None:
        """Retrieve record by unique email index."""
        sql: Final[str] = "SELECT * FROM users WHERE email = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (email.strip().lower(),))
            return cursor.fetchone()

    def list_active_users(self, min_balance: float = 0.0) -> list[sqlite3.Row]:
        """Query multiple rows with parameterized filter criteria."""
        sql: Final[str] = """
        SELECT id, email, username, balance, created_at
        FROM users
        WHERE is_active = 1 AND balance >= ?
        ORDER BY balance DESC;
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (min_balance,))
            rows: list[sqlite3.Row] = cursor.fetchall()
            return rows

    # --------------------------------------------------------------------------
    # UPDATE Operations
    # --------------------------------------------------------------------------
    def update_user_balance(self, user_id: int, new_balance: float) -> bool:
        """Update existing user record."""
        sql: Final[str] = "UPDATE users SET balance = ? WHERE id = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (new_balance, user_id))
            return cursor.rowcount > 0

    # --------------------------------------------------------------------------
    # DELETE Operations
    # --------------------------------------------------------------------------
    def soft_delete_user(self, user_id: int) -> bool:
        """Soft delete user by deactivating flag."""
        sql: Final[str] = "UPDATE users SET is_active = 0 WHERE id = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id,))
            return cursor.rowcount > 0

    def purge_user(self, user_id: int) -> bool:
        """Hard delete record from storage."""
        sql: Final[str] = "DELETE FROM users WHERE id = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id,))
            return cursor.rowcount > 0

    # --------------------------------------------------------------------------
    # Transaction Integrity & Rollback Mechanics
    # --------------------------------------------------------------------------
    def atomic_transfer(self, sender_id: int, recipient_id: int, amount: float) -> bool:
        """
        Demonstrate ACID transactional integrity.
        Debits sender, credits recipient in single atomic commit.
        If an exception triggers, rollback is automatically guaranteed.
        """
        if amount <= 0:
            raise ValueError("Transfer amount must be strictly positive.")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Check sender balance
            cursor.execute("SELECT balance FROM users WHERE id = ?", (sender_id,))
            sender_row = cursor.fetchone()
            if not sender_row or sender_row["balance"] < amount:
                raise ValueError("Insufficient balance for transfer.")

            # 2. Debit sender
            cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, sender_id))

            # 3. Credit recipient
            cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, recipient_id))
            if cursor.rowcount == 0:
                raise ValueError(f"Recipient user id {recipient_id} does not exist.")

            # Automatic commit occurs upon exiting the `with conn:` context block
            print(f"  [TX COMMITTED] Transferred ${amount:.2f} from User {sender_id} to User {recipient_id}")
            return True


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" LEVEL 2: 01_SQLITE_CRUD - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # Initialize manager with in-memory database for testing
    db = SQLiteDatabaseManager(":memory:")

    # 1. Single Insert
    uid1 = db.insert_user("alice@enterprise.io", "alice", 500.0)
    uid2 = db.insert_user("bob@enterprise.io", "bob", 200.0)
    print(f"Inserted Users: Alice (ID: {uid1}), Bob (ID: {uid2})")

    # 2. Bulk Insert
    batch = [
        ("charlie@enterprise.io", "charlie", 1500.0),
        ("diana@enterprise.io", "diana", 75.0),
        ("evan@enterprise.io", "evan", 3200.0),
    ]
    inserted_count = db.bulk_insert_users(batch)
    print(f"Bulk Inserted {inserted_count} additional user records.")

    # 3. Read & Row Access
    alice = db.get_user_by_id(uid1)
    assert alice is not None
    # Key-based and index-based access via sqlite3.Row
    print(f"Queried User via Row Factory: ID={alice['id']}, Email={alice['email']}, Balance=${alice['balance']:.2f}")
    assert alice["email"] == "alice@enterprise.io"

    # 4. Atomic Transaction & Rollback Test
    print("\n--- Executing ACID Transfer Transaction ---")
    db.atomic_transfer(sender_id=uid1, recipient_id=uid2, amount=150.0)

    alice_updated = db.get_user_by_id(uid1)
    bob_updated = db.get_user_by_id(uid2)
    assert alice_updated is not None and bob_updated is not None
    assert alice_updated["balance"] == 350.0
    assert bob_updated["balance"] == 350.0
    print(f"Post-Transfer Balances: Alice=${alice_updated['balance']:.2f}, Bob=${bob_updated['balance']:.2f}")

    # Rollback assertion: attempt transfer exceeding balance
    print("\n--- Testing Rollback on Invariant Violation ---")
    try:
        db.atomic_transfer(sender_id=uid1, recipient_id=uid2, amount=99999.0)
        raise AssertionError("Transaction should have failed on insufficient balance!")
    except ValueError as err:
        print(f"Transaction aborted cleanly: {err}")
        # Verify balances were not touched
        alice_post = db.get_user_by_id(uid1)
        assert alice_post is not None and alice_post["balance"] == 350.0
        print("Confirmed rollback: Alice balance remains exactly $350.00")

    # 5. Soft Delete
    db.soft_delete_user(uid2)
    active_users = db.list_active_users(min_balance=0.0)
    assert not any(u["id"] == uid2 for u in active_users)
    print(f"Active user count after soft-deleting Bob: {len(active_users)}")

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 01_sqlite_crud module executed cleanly.")
    print("=" * 70)
