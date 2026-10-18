r"""
SQLAlchemy 2.0 Async ORM: Declarative Mapping, Relationships, and Session Lifecycle
===================================================================================
Description: Enterprise-grade asynchronous Object-Relational Mapping (ORM) using SQLAlchemy 2.0.
             Demonstrates typed `Mapped` column specifications, asynchronous engine connection
             pooling, transactional `AsyncSession` context managers, eager relationship loading
             via `selectinload` to eliminate N+1 query antipatterns, and full CRUD mechanics.
Enterprise Mapping:
- SQLAlchemy 2.0 Data Mapper: Implements the Martin Fowler Data Mapper pattern, cleanly
  decoupling database schema persistence from domain object logic. Directly analogous to
  Doctrine ORM in PHP and Prisma / TypeORM (Data Mapper mode) in TypeScript.
- Async Engine & Session: Non-blocking coroutine-driven database operations allowing thousands
  of concurrent transactions on a single event loop without blocking thread pools.
- Eager Relationship Loading (`selectinload`): Directly replaces Prisma `include: { orders: true }`
  and Doctrine `JOIN FETCH` / Laravel `with('orders')` eager loaders.

Official Documentation References:
- SQLAlchemy 2.0 AsyncIO Extension: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Declarative Mapping Style: https://docs.sqlalchemy.org/en/20/orm/declarative_mapping_style.html
- Relationship Loading Techniques: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
- Working with Async Sessions: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-orm-avoid-lazyloads
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Final, Sequence

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, delete, func, select, update
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload


# ==============================================================================
# 1. SQLAlchemy 2.0 Modern Declarative Domain Entities
# ==============================================================================
class Base(AsyncAttrs, DeclarativeBase):
    """
    Abstract declarative base class for all enterprise domain models.
    AsyncAttrs enables coroutine-safe attribute access on loaded entities.
    """
    pass


class User(Base):
    """
    User entity mapping to table 'users'.
    Type annotations (`Mapped[...]`) enforce static type validation under MyPy.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # 1-to-Many Relationship with Cascade Delete
    orders: Mapped[list[Order]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Order.id",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username!r}, email={self.email!r})>"


class Order(Base):
    """
    Order entity mapping to table 'orders' with Foreign Key constraint.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)

    # Many-to-1 Relationship back to User
    user: Mapped[User] = relationship(back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, total=${self.total_amount:.2f}, status={self.status!r})>"


# ==============================================================================
# 2. Database Session Manager & Async Engine Configuration
# ==============================================================================
class AsyncDatabaseManager:
    """
    Encapsulates AsyncEngine lifecycle, connection pooling parameters,
    and AsyncSession context provisioning.
    """

    def __init__(self, connection_dsn: str = "sqlite+aiosqlite:///:memory:") -> None:
        # Configure connection pool
        self.engine: AsyncEngine = create_async_engine(
            connection_dsn,
            echo=False,  # Set to True for verbose SQL statement logging
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,  # Prevent lazy-load errors post-commit in async mode
            class_=AsyncSession,
        )

    async def initialize_schema(self) -> None:
        """Create database tables asynchronously."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """Dispose of the connection pool."""
        await self.engine.dispose()


# ==============================================================================
# 3. Enterprise Asynchronous CRUD Repository Layer
# ==============================================================================
class AsyncUserRepository:
    """
    Repository handling data persistence operations for User and Order entities.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session

    # --- CREATE ---
    async def create_user_with_orders(
        self, email: str, username: str, orders_data: list[float]
    ) -> User:
        """Atomically persist a user alongside initial orders."""
        user = User(email=email.strip().lower(), username=username.strip())
        for amount in orders_data:
            user.orders.append(Order(total_amount=amount, status="PENDING"))

        self.session.add(user)
        await self.session.flush()  # Populates user.id without closing transaction
        return user

    # --- READ ---
    async def get_user_by_id_with_orders(self, user_id: int) -> User | None:
        """
        Query user by ID eagerly loading orders via `selectinload`.
        In async SQLAlchemy, accessing un-loaded relationships outside a query
        raises `MissingGreenlet` / `DetachedInstanceError`.
        """
        stmt = (
            select(User)
            .options(selectinload(User.orders))
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users_with_order_totals(self) -> list[tuple[User, int, float]]:
        """
        Execute aggregate query joining users and orders with COUNT and SUM.
        Equivalent to complex SQL aggregations in TypeORM query builder.
        """
        stmt = (
            select(
                User,
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total_amount), 0.0).label("total_spent"),
            )
            .outerjoin(User.orders)
            .group_by(User.id)
            .order_by(User.id)
        )
        result = await self.session.execute(stmt)
        # Type-safe tuple mapping
        return [(row[0], row[1], row[2]) for row in result.all()]

    # --- UPDATE ---
    async def update_order_status(self, order_id: int, new_status: str) -> bool:
        """Execute atomic UPDATE statement."""
        stmt = (
            update(Order)
            .where(Order.id == order_id)
            .values(status=new_status)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    # --- DELETE ---
    async def delete_user(self, user_id: int) -> bool:
        """Delete user entity; cascade deletes all associated orders."""
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
async def main_diagnostics() -> None:
    """Execute complete async ORM lifecycle test."""
    print("=" * 70)
    print(" LEVEL 3: 01_ASYNC_CRUD_SQLALCHEMY - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Initialize async DB engine with SQLite in-memory
    db_manager = AsyncDatabaseManager("sqlite+aiosqlite:///:memory:")
    await db_manager.initialize_schema()
    print("[*] Database schema tables (users, orders) provisioned asynchronously.")

    try:
        # 2. CREATE: Populate users and associated orders
        async with db_manager.session_factory() as session:
            async with session.begin():
                repo = AsyncUserRepository(session)
                user1 = await repo.create_user_with_orders(
                    email="architect@corp.io",
                    username="architect",
                    orders_data=[299.99, 149.50, 89.00],
                )
                user2 = await repo.create_user_with_orders(
                    email="developer@corp.io",
                    username="developer",
                    orders_data=[49.99],
                )
                user1_id = user1.id
                user2_id = user2.id
                print(f"[+] Persisted User 1 (ID: {user1_id}) with 3 orders.")
                print(f"[+] Persisted User 2 (ID: {user2_id}) with 1 order.")

        # 3. READ: Query user eagerly loading related orders via selectinload
        async with db_manager.session_factory() as session:
            repo = AsyncUserRepository(session)
            retrieved = await repo.get_user_by_id_with_orders(user1_id)
            assert retrieved is not None
            print(f"\n[+] Eagerly Loaded User: {retrieved.username} (Email: {retrieved.email})")
            print(f"    Total Orders Attached: {len(retrieved.orders)}")
            for order in retrieved.orders:
                print(f"      - Order #{order.id}: ${order.total_amount:.2f} [{order.status}]")
            assert len(retrieved.orders) == 3

        # 4. UPDATE: Update order status
        async with db_manager.session_factory() as session:
            async with session.begin():
                repo = AsyncUserRepository(session)
                updated = await repo.update_order_status(order_id=1, new_status="FULFILLED")
                assert updated is True
                print("\n[+] Updated Order #1 status to 'FULFILLED'.")

        # 5. AGGREGATE: Query aggregates across joined tables
        async with db_manager.session_factory() as session:
            repo = AsyncUserRepository(session)
            aggregates = await repo.list_users_with_order_totals()
            print("\n[+] User Aggregate Financial Summary:")
            for usr, count, total in aggregates:
                print(f"    - User '{usr.username}': {count} orders totaling ${total:.2f}")

        # 6. DELETE: Verify cascade deletion
        async with db_manager.session_factory() as session:
            async with session.begin():
                repo = AsyncUserRepository(session)
                deleted = await repo.delete_user(user2_id)
                assert deleted is True
                print(f"\n[+] Deleted User 2 (ID: {user2_id}) - cascade deleted orders.")

            # Confirm deletion
            retrieved_deleted = await repo.get_user_by_id_with_orders(user2_id)
            assert retrieved_deleted is None
            print("    Confirmed: User 2 and associated orders purged completely.")

    finally:
        await db_manager.close()
        print("[*] Async connection pool disposed.")


if __name__ == "__main__":
    asyncio.run(main_diagnostics())

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 01_async_crud_sqlalchemy module executed cleanly.")
    print("=" * 70)
