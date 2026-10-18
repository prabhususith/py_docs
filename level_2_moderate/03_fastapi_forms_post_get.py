r"""
FastAPI Enterprise Transport: GET Query Params, Form Data, and Pydantic v2 Body Models
======================================================================================
Description: Comprehensive ASGI REST API built with FastAPI showcasing typed GET query
             parameter validation, URL-encoded/Multipart form data processing, Pydantic v2
             schema validation with custom field rules, and dependency injection.
Enterprise Mapping:
- FastAPI Routing & Dependency Injection (`Depends`): Replaces Express/NestJS dependency
  injection and Laravel Service Containers / Middleware. Injected dependencies handle auth,
  database sessions, and contextual logging.
- Form Processing (`Form(...)`): Replaces PHP's classic `$_POST` array handling and Express
  `urlencoded({ extended: true })` middleware with strong typing and automated validation.
- Pydantic v2 Body Validation: Replaces TypeScript `class-validator` / `zod` schemas and
  Laravel Form Requests. Compiled in Rust (`pydantic-core`) for maximum throughput.

Official Documentation References:
- FastAPI Official Tutorial: https://fastapi.tiangolo.com/tutorial/
- FastAPI Form Data: https://fastapi.tiangolo.com/tutorial/request-forms/
- Pydantic v2 Models: https://docs.pydantic.dev/latest/concepts/models/
- FastAPI Dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Final

from fastapi import Depends, FastAPI, Form, HTTPException, Header, Query, status
import httpx
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ==============================================================================
# 1. Pydantic v2 Data Transfer Objects (DTOs) & Invariant Validators
# ==============================================================================
class UserCreationRequest(BaseModel):
    """
    Enterprise Pydantic v2 Inbound Request DTO.
    Equivalent to a TypeScript Zod schema or NestJS DTO with class-validator.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Alphanumeric enterprise identity handle",
        examples=["alice_architect"],
    )
    email: EmailStr = Field(
        ...,
        description="Corporate RFC 5322 compliant email address",
        examples=["alice@enterprise.corp"],
    )
    department: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Target corporate organizational unit",
        examples=["Infrastructure-Platform"],
    )
    quota_limit: int = Field(
        default=1000,
        ge=100,
        le=50000,
        description="Allocated monthly API transaction quota",
    )

    @field_validator("username")
    @classmethod
    def validate_username_alphanumeric(cls, value: str) -> str:
        """Enforce domain invariant: usernames must be alphanumeric or underscores only."""
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValueError("Username must contain strictly alphanumeric characters and underscores.")
        return value.lower()


class UserResponse(BaseModel):
    """Outbound API Response DTO."""

    user_id: int
    username: str
    email: str
    department: str
    quota_limit: int
    status: str = "PROVISIONED"


class FormSubmissionResponse(BaseModel):
    """Response payload for legacy URL-encoded form ingestion."""

    form_type: str
    received_action: str
    target_resource_id: str
    processed_status: str


# ==============================================================================
# 2. Dependency Injection: Security & Request Context
# ==============================================================================
def verify_enterprise_token(
    x_api_key: Annotated[str | None, Header(description="Enterprise Client API Key")] = None,
) -> str:
    """
    Dependency verifying presence and validity of client authentication token.
    Analogous to NestJS AuthGuard or Laravel Middleware.
    """
    if not x_api_key or x_api_key != "secret-enterprise-token-2026":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key enterprise authentication header.",
        )
    return x_api_key


# ==============================================================================
# 3. FastAPI Application Initialization & Route Architecture
# ==============================================================================
app: Final[FastAPI] = FastAPI(
    title="Enterprise Core API Gateway",
    version="1.0.0",
    description="Reference implementation of FastAPI query parsing, form handling, and Pydantic v2 schemas.",
)

# Simulated in-memory database store
_USER_STORE: list[dict[str, Any]] = [
    {"user_id": 1, "username": "alice", "email": "alice@corp.io", "department": "Core", "quota_limit": 5000},
    {"user_id": 2, "username": "bob", "email": "bob@corp.io", "department": "Platform", "quota_limit": 2000},
    {"user_id": 3, "username": "charlie", "email": "charlie@corp.io", "department": "Core", "quota_limit": 10000},
]


# ------------------------------------------------------------------------------
# Route 1: GET Query Parameters with Validation & Pagination
# ------------------------------------------------------------------------------
@app.get(
    "/api/v1/users",
    response_model=list[UserResponse],
    summary="List and filter enterprise users",
    tags=["Users"],
)
async def list_users(
    department: Annotated[
        str | None,
        Query(
            description="Optional filter by organizational department",
            min_length=2,
            max_length=50,
        ),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Page index (1-based)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Records per page")] = 10,
    _: str = Depends(verify_enterprise_token),
) -> list[dict[str, Any]]:
    """
    Query parameter handling with validation rules.
    TypeScript equivalent: Request query params with Zod validation.
    PHP equivalent: Validating $_GET['page'] and $_GET['department'].
    """
    filtered = _USER_STORE
    if department:
        filtered = [u for u in filtered if u["department"].lower() == department.lower()]

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return filtered[start_idx:end_idx]


# ------------------------------------------------------------------------------
# Route 2: POST JSON Body with Pydantic v2 Validation
# ------------------------------------------------------------------------------
@app.post(
    "/api/v1/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user via JSON body DTO",
    tags=["Users"],
)
async def create_user(
    payload: UserCreationRequest,
    _: str = Depends(verify_enterprise_token),
) -> dict[str, Any]:
    """
    Consumes JSON payload, automatically validated and parsed into UserCreationRequest.
    If payload is invalid, FastAPI automatically returns standard RFC 7807 422 Unprocessable Entity.
    """
    # Check for duplicate email
    if any(u["email"] == payload.email for u in _USER_STORE):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{payload.email}' already exists.",
        )

    new_user = {
        "user_id": len(_USER_STORE) + 1,
        "username": payload.username,
        "email": str(payload.email),
        "department": payload.department,
        "quota_limit": payload.quota_limit,
    }
    _USER_STORE.append(new_user)
    return new_user


# ------------------------------------------------------------------------------
# Route 3: POST URL-Encoded Form Data Processing
# ------------------------------------------------------------------------------
@app.post(
    "/api/v1/webhooks/legacy-form",
    response_model=FormSubmissionResponse,
    summary="Process legacy URL-encoded form post",
    tags=["Webhooks"],
)
async def submit_legacy_form(
    action: Annotated[str, Form(description="Action verb submitted by form")],
    resource_id: Annotated[str, Form(description="Target resource identifier")],
    csrf_token: Annotated[str, Form(description="Anti-CSRF validation token")],
) -> FormSubmissionResponse:
    """
    Ingests standard application/x-www-form-urlencoded or multipart form payloads.
    Equivalent to processing PHP $_POST['action'] or Express urlencoded body.
    """
    if not csrf_token.startswith("csrf_valid_"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid anti-CSRF token signature.",
        )

    return FormSubmissionResponse(
        form_type="application/x-www-form-urlencoded",
        received_action=action.upper(),
        target_resource_id=resource_id,
        processed_status="SUCCESSFULLY_ENQUEUED",
    )


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite (Async ASGI Transport)
# ==============================================================================
async def run_diagnostics() -> None:
    """Execute end-to-end endpoint verification directly via ASGI transport."""
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
    auth_header = {"X-API-Key": "secret-enterprise-token-2026"}

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test GET with query parameters & Auth Dependency
        print("\n--- 1. Testing GET /api/v1/users (Filtering & Pagination) ---")
        resp_unauth = await client.get("/api/v1/users")
        assert resp_unauth.status_code == 401
        print("  [PASS] Verified 401 Unauthorized when missing API Key.")

        resp_get = await client.get(
            "/api/v1/users",
            params={"department": "Core", "page": 1, "page_size": 10},
            headers=auth_header,
        )
        assert resp_get.status_code == 200
        users_data = resp_get.json()
        print(f"  [PASS] Queried {len(users_data)} users in department 'Core':")
        for u in users_data:
            print(f"    - User #{u['user_id']}: {u['username']} ({u['email']})")

        # 2. Test POST with Pydantic v2 JSON Validation
        print("\n--- 2. Testing POST /api/v1/users (Pydantic v2 Ingestion) ---")
        new_user_payload = {
            "username": "diana_lead",
            "email": "diana@enterprise.corp",
            "department": "Security",
            "quota_limit": 15000,
        }
        resp_post = await client.post("/api/v1/users", json=new_user_payload, headers=auth_header)
        assert resp_post.status_code == 201
        created_user = resp_post.json()
        print(f"  [PASS] Created user: ID={created_user['user_id']}, Username={created_user['username']}")

        # Validation rejection test: invalid username symbols
        bad_payload = {
            "username": "invalid-user-name!",
            "email": "bad@enterprise.corp",
            "department": "Security",
        }
        resp_bad = await client.post("/api/v1/users", json=bad_payload, headers=auth_header)
        assert resp_bad.status_code == 422
        print("  [PASS] Pydantic v2 automatically rejected invalid alphanumeric username with 422.")

        # 3. Test POST with Form Encoded Data
        print("\n--- 3. Testing POST /api/v1/webhooks/legacy-form (Form-Encoded) ---")
        form_data = {
            "action": "reindex_cluster",
            "resource_id": "cluster_us_east_4",
            "csrf_token": "csrf_valid_9981827471",
        }
        resp_form = await client.post("/api/v1/webhooks/legacy-form", data=form_data)
        assert resp_form.status_code == 200
        form_res = resp_form.json()
        print(f"  [PASS] Form Submission Processed: Action={form_res['received_action']}, Status={form_res['processed_status']}")


if __name__ == "__main__":
    import asyncio

    print("=" * 70)
    print(" LEVEL 2: 03_FASTAPI_FORMS_POST_GET - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    asyncio.run(run_diagnostics())

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 03_fastapi_forms_post_get module executed cleanly.")
    print("=" * 70)
