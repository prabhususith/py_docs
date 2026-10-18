r"""
Enterprise Clean Architecture & Domain-Driven Design (DDD) API
==============================================================
Description: Complete production reference implementation of Clean Architecture / Hexagonal
             Architecture (Ports & Adapters). Demonstrates pure dataclass domain entities,
             structural subtyping interfaces via `typing.Protocol` (PEP 544), isolated Use Cases,
             infrastructure adapters (In-Memory & SQLite), and a FastAPI presentation layer
             with Pydantic v2 DTOs and dependency injection.
Enterprise Mapping:
- Hexagonal / Onion Architecture: Directly mirrors enterprise NestJS architectures and
  PHP Symfony/Laravel Clean Architecture patterns. Domain logic remains 100% decoupled from
  databases, web frameworks, and third-party vendor SDKs.
- `typing.Protocol` (PEP 544): Counterpart to TypeScript `interface` and PHP `interface`.
  Provides static structural duck typing without requiring explicit class inheritance (`implements`).
- Domain Entities (`@dataclass`): Replaces TypeScript domain classes / immutable records and
  PHP 8.2 readonly domain entities.

Official Documentation References:
- Python Dataclasses: https://docs.python.org/3/library/dataclasses.html
- Typing Protocols (PEP 544): https://docs.python.org/3/library/typing.html#typing.Protocol
- Abstract Base Classes (abc): https://docs.python.org/3/library/abc.html
- FastAPI Dependency Injection: https://fastapi.tiangolo.com/tutorial/dependencies/
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Annotated, Any, Final, Protocol, runtime_checkable

from fastapi import Depends, FastAPI, HTTPException, status
import httpx
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==============================================================================
# LAYER 1: DOMAIN LAYER (Zero Framework Dependencies)
# ==============================================================================
class DomainException(Exception):
    """Base domain exception for enterprise business rule violations."""
    pass


class UserAlreadyExistsException(DomainException):
    """Raised when an attempt is made to persist an entity with conflicting unique identity."""
    pass


class UserNotFoundException(DomainException):
    """Raised when an aggregate root is not found in persistence."""
    pass


class InvalidEmailDomainException(DomainException):
    """Raised when email does not conform to enterprise domain policy."""
    pass


@dataclass(frozen=True)
class UserDomainEntity:
    """
    Pure Domain Aggregate Root.
    Zero external dependencies (No FastAPI, No SQLAlchemy, No Pydantic).
    """

    user_id: str
    email: str
    full_name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Enforce domain invariants upon instantiation."""
        if not self.user_id.strip():
            raise DomainException("User ID cannot be empty.")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            raise InvalidEmailDomainException(f"Invalid domain email: '{self.email}'")


# ==============================================================================
# LAYER 2: PORTS / INTERFACE CONTRACTS (typing.Protocol)
# ==============================================================================
@runtime_checkable
class UserRepositoryProtocol(Protocol):
    """
    Outbound Port (Repository Interface).
    Equivalent to TypeScript `interface UserRepository` and PHP `interface UserRepositoryInterface`.
    """

    async def get_by_id(self, user_id: str) -> UserDomainEntity | None:
        """Fetch domain entity by ID."""
        ...

    async def get_by_email(self, email: str) -> UserDomainEntity | None:
        """Fetch domain entity by unique email."""
        ...

    async def save(self, user: UserDomainEntity) -> None:
        """Persist domain entity."""
        ...


@runtime_checkable
class NotificationPortProtocol(Protocol):
    """Outbound Port (Notification Service Contract)."""

    async def send_welcome_email(self, email: str, name: str) -> bool:
        """Dispatch welcome notification."""
        ...


# ==============================================================================
# LAYER 3: APPLICATION LAYER (USE CASES / INTERACTORS)
# ==============================================================================
class CreateUserUseCase:
    """
    Application Interactor orchestrating user creation business workflow.
    Dependencies are injected via constructor satisfying Protocol contracts.
    """

    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        notifier: NotificationPortProtocol,
    ) -> None:
        self.user_repo: UserRepositoryProtocol = user_repo
        self.notifier: NotificationPortProtocol = notifier

    async def execute(self, user_id: str, email: str, full_name: str) -> UserDomainEntity:
        """Execute atomic business workflow."""
        # 1. Enforce unique identity rule
        existing = await self.user_repo.get_by_email(email)
        if existing is not None:
            raise UserAlreadyExistsException(f"User with email '{email}' already registered.")

        # 2. Instantiate domain entity (triggers domain validations)
        user = UserDomainEntity(user_id=user_id, email=email, full_name=full_name)

        # 3. Persist via repository port
        await self.user_repo.save(user)

        # 4. Trigger side-effect notification port
        await self.notifier.send_welcome_email(user.email, user.full_name)

        return user


class GetUserProfileUseCase:
    """Application Interactor for querying profile aggregate."""

    def __init__(self, user_repo: UserRepositoryProtocol) -> None:
        self.user_repo: UserRepositoryProtocol = user_repo

    async def execute(self, user_id: str) -> UserDomainEntity:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundException(f"User aggregate '{user_id}' does not exist.")
        return user


# ==============================================================================
# LAYER 4: INFRASTRUCTURE ADAPTERS
# ==============================================================================
class InMemoryUserRepository:
    """
    In-Memory Adapter implementing UserRepositoryProtocol.
    Used for unit testing and fast integration simulation.
    """

    def __init__(self) -> None:
        self._storage: dict[str, UserDomainEntity] = {}
        self._lock = asyncio.Lock()

    async def get_by_id(self, user_id: str) -> UserDomainEntity | None:
        async with self._lock:
            return self._storage.get(user_id)

    async def get_by_email(self, email: str) -> UserDomainEntity | None:
        async with self._lock:
            for user in self._storage.values():
                if user.email.lower() == email.lower():
                    return user
            return None

    async def save(self, user: UserDomainEntity) -> None:
        async with self._lock:
            self._storage[user.user_id] = user


class MockNotificationService:
    """Mock Notification Adapter implementing NotificationPortProtocol."""

    def __init__(self) -> None:
        self.dispatched_notifications: list[tuple[str, str]] = []

    async def send_welcome_email(self, email: str, name: str) -> bool:
        self.dispatched_notifications.append((email, name))
        print(f"  [Notification Adapter] Welcome email transmitted to {email} ({name})")
        return True


# ==============================================================================
# LAYER 5: PRESENTATION / API LAYER (FASTAPI + PYDANTIC V2)
# ==============================================================================
class CreateUserRequestDTO(BaseModel):
    """Inbound presentation schema."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str = Field(..., min_length=3, max_length=50, examples=["usr_arch_001"])
    email: EmailStr = Field(..., examples=["architect@enterprise.io"])
    full_name: str = Field(..., min_length=2, max_length=100, examples=["Ada Lovelace"])


class UserProfileResponseDTO(BaseModel):
    """Outbound presentation schema."""

    user_id: str
    email: str
    full_name: str
    created_at_iso: str


# Global Infrastructure Singletons for DI Container
_global_user_repo = InMemoryUserRepository()
_global_notifier = MockNotificationService()


# Dependency Injection Providers
def get_user_repository() -> UserRepositoryProtocol:
    return _global_user_repo


def get_notification_service() -> NotificationPortProtocol:
    return _global_notifier


def get_create_user_use_case(
    repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
    notifier: Annotated[NotificationPortProtocol, Depends(get_notification_service)],
) -> CreateUserUseCase:
    return CreateUserUseCase(user_repo=repo, notifier=notifier)


def get_profile_use_case(
    repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
) -> GetUserProfileUseCase:
    return GetUserProfileUseCase(user_repo=repo)


app: Final[FastAPI] = FastAPI(title="Clean Architecture DDD Gateway")


@app.post(
    "/api/v1/accounts",
    response_model=UserProfileResponseDTO,
    status_code=status.HTTP_201_CREATED,
    tags=["Accounts"],
)
async def api_create_account(
    dto: CreateUserRequestDTO,
    use_case: Annotated[CreateUserUseCase, Depends(get_create_user_use_case)],
) -> UserProfileResponseDTO:
    """REST endpoint invoking the CreateUserUseCase."""
    try:
        domain_user = await use_case.execute(
            user_id=dto.user_id,
            email=str(dto.email),
            full_name=dto.full_name,
        )
        return UserProfileResponseDTO(
            user_id=domain_user.user_id,
            email=domain_user.email,
            full_name=domain_user.full_name,
            created_at_iso=domain_user.created_at.isoformat(),
        )
    except UserAlreadyExistsException as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except DomainException as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))


@app.get(
    "/api/v1/accounts/{user_id}",
    response_model=UserProfileResponseDTO,
    tags=["Accounts"],
)
async def api_get_account(
    user_id: str,
    use_case: Annotated[GetUserProfileUseCase, Depends(get_profile_use_case)],
) -> UserProfileResponseDTO:
    """REST endpoint invoking the GetUserProfileUseCase."""
    try:
        domain_user = await use_case.execute(user_id=user_id)
        return UserProfileResponseDTO(
            user_id=domain_user.user_id,
            email=domain_user.email,
            full_name=domain_user.full_name,
            created_at_iso=domain_user.created_at.isoformat(),
        )
    except UserNotFoundException as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite (Async ASGI Transport)
# ==============================================================================
async def run_clean_architecture_suite() -> None:
    """End-to-end integration verification across all architectural layers."""
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create User via Clean Architecture API
        print("\n--- 1. Testing CreateUserUseCase via REST API ---")
        payload = {
            "user_id": "usr_alpha_99",
            "email": "architect@enterprise.io",
            "full_name": "Senior Enterprise Architect",
        }
        res_post = await client.post("/api/v1/accounts", json=payload)
        print(f"  POST /api/v1/accounts status: {res_post.status_code}")
        assert res_post.status_code == 201
        created_data = res_post.json()
        print(f"  Created user payload: {created_data}")
        assert created_data["user_id"] == "usr_alpha_99"
        assert len(_global_notifier.dispatched_notifications) == 1

        # 2. Query User via GetUserProfileUseCase
        print("\n--- 2. Testing GetUserProfileUseCase via REST API ---")
        res_get = await client.get("/api/v1/accounts/usr_alpha_99")
        assert res_get.status_code == 200
        get_data = res_get.json()
        print(f"  Queried user profile: {get_data['full_name']} ({get_data['email']})")
        assert get_data["email"] == "architect@enterprise.io"

        # 3. Test Conflict Domain Rule (Duplicate Email)
        print("\n--- 3. Testing Duplicate Email Invariant Violation ---")
        res_dup = await client.post("/api/v1/accounts", json={
            "user_id": "usr_beta_100",
            "email": "architect@enterprise.io",  # Duplicate email
            "full_name": "Another User",
        })
        print(f"  POST duplicate email returned status: {res_dup.status_code} ({res_dup.json()})")
        assert res_dup.status_code == 409

        # 4. Test Not Found Domain Rule
        print("\n--- 4. Testing UserNotFoundException Handling ---")
        res_missing = await client.get("/api/v1/accounts/non_existent_id")
        assert res_missing.status_code == 404
        print(f"  GET non-existent user returned 404: {res_missing.json()}")


if __name__ == "__main__":
    print("=" * 70)
    print(" LEVEL 4: 03_CLEAN_ARCHITECTURE_ENTERPRISE_API - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    asyncio.run(run_clean_architecture_suite())

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 03_clean_architecture_enterprise_api module executed cleanly.")
    print("=" * 70)
