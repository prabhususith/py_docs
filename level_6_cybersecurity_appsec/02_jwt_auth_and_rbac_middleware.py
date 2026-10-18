r"""
Stateless JWT Authentication and Role-Based Access Control (RBAC)
=================================================================
Description: Production application security framework implementing stateless JSON Web Tokens
             (JWT) with cryptographic HMAC-SHA256 signatures, token issuance/refresh lifecycles,
             claim verification (sub, exp, roles, permissions, jti), and FastAPI Role-Based
             Access Control (RBAC) dependency injection guards.
Enterprise Mapping:
- JWT Authentication: Direct equivalent to Node.js `jsonwebtoken` / Passport.js and PHP
  `firebase/php-jwt` / Laravel Sanctum. Provides stateless, decentralized identity assertions
  across distributed microservices without database session lookups.
- RBAC Security Dependency Factories: Analogous to NestJS `@Roles('ADMIN')` Guards and Symfony
  Security Voters in PHP. Protects sensitive endpoints by enforcing principle of least privilege.
- Revocation & JTI Tracking: Token identifiers (`jti`) allow blacklisting compromised credentials
  prior to expiration.

Official Documentation References:
- FastAPI OAuth2 with Password & Bearer: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- PyJWT Documentation: https://pyjwt.readthedocs.io/en/latest/
- RFC 7519 (JSON Web Token): https://datatracker.ietf.org/doc/html/rfc7519
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import uuid
from typing import Annotated, Any, Final, Sequence

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
import jwt
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# 1. JWT Security Configuration & Token Schemas
# ==============================================================================
SECRET_KEY: Final[str] = "enterprise-production-super-secret-hmac-key-2026!"
ALGORITHM: Final[str] = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 15


class TokenPayload(BaseModel):
    """Decoded and validated JWT claims schema."""

    model_config = ConfigDict(extra="ignore")

    sub: str = Field(..., description="Subject identifier (User ID)")
    email: str
    roles: list[str] = Field(default_factory=list, description="Assigned enterprise RBAC roles")
    permissions: list[str] = Field(default_factory=list, description="Fine-grained granular permissions")
    jti: str = Field(..., description="Unique JWT ID for revocation tracking")
    exp: int = Field(..., description="Expiration timestamp (Unix Epoch seconds)")
    iat: int = Field(..., description="Issued-at timestamp")


class UserTokenResponse(BaseModel):
    """Outbound token issuance DTO."""

    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int


# In-memory blacklist for revoked token JTIs (mirrors Redis token cache)
_REVOKED_JTI_STORE: set[str] = set()


# ==============================================================================
# 2. Token Issuance & Verification Gateway
# ==============================================================================
class JwtTokenService:
    """Enterprise service for generating and cryptographically verifying JWTs."""

    @staticmethod
    def create_access_token(
        user_id: str,
        email: str,
        roles: list[str],
        permissions: list[str],
        expires_delta: timedelta | None = None,
    ) -> tuple[str, TokenPayload]:
        """Generate cryptographically signed JWT with standard and custom claims."""
        now = datetime.now(timezone.utc)
        expire_duration = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_at = now + expire_duration

        token_id = str(uuid.uuid4())
        claims = {
            "sub": user_id,
            "email": email,
            "roles": roles,
            "permissions": permissions,
            "jti": token_id,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        encoded_jwt = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
        validated_payload = TokenPayload.model_validate(claims)
        return encoded_jwt, validated_payload

    @staticmethod
    def decode_and_validate_token(token: str) -> TokenPayload:
        """
        Verify cryptographic signature, expiration boundary, and blacklist status.
        Raises HTTPException on failure.
        """
        try:
            raw_claims = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"require": ["exp", "iat", "sub", "jti"]},
            )
            payload = TokenPayload.model_validate(raw_claims)
        except jwt.ExpiredSignatureError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Security token has expired. Re-authentication required.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from err
        except (jwt.PyJWTError, Exception) as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Cryptographic signature verification failed: {err}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from err

        # Check revocation blacklist
        if payload.jti in _REVOKED_JTI_STORE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been explicitly revoked.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload


# ==============================================================================
# 3. FastAPI RBAC Security Dependencies
# ==============================================================================
security_bearer = HTTPBearer(auto_error=True)


async def get_current_user_claims(
    auth: Annotated[HTTPAuthorizationCredentials, Security(security_bearer)],
) -> TokenPayload:
    """FastAPI Dependency: extracts and verifies Bearer token from Authorization header."""
    return JwtTokenService.decode_and_validate_token(auth.credentials)


def require_roles(required_roles: Sequence[str]) -> Any:
    """
    Factory creating a FastAPI dependency enforcing Role-Based Access Control.
    Direct counterpart to NestJS `@Roles(...)` and Laravel `can:role`.
    """

    async def _role_guard(
        claims: Annotated[TokenPayload, Depends(get_current_user_claims)],
    ) -> TokenPayload:
        user_roles_set = set(claims.roles)
        required_set = set(required_roles)

        # User must possess at least one of the required roles
        if not (user_roles_set & required_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires one of the following roles: {list(required_roles)}. Possessed: {claims.roles}",
            )
        return claims

    return _role_guard


# ==============================================================================
# 4. FastAPI Protected Endpoint Router
# ==============================================================================
app: Final[FastAPI] = FastAPI(title="Enterprise JWT & RBAC Gateway")


@app.get("/api/v1/profile/me", tags=["Profile"])
async def get_my_profile(
    claims: Annotated[TokenPayload, Depends(get_current_user_claims)],
) -> dict[str, Any]:
    """Authenticated endpoint accessible by any valid token."""
    return {
        "user_id": claims.sub,
        "email": claims.email,
        "assigned_roles": claims.roles,
        "status": "AUTHENTICATED",
    }


@app.get("/api/v1/admin/audit-logs", tags=["Admin"])
async def get_audit_logs(
    _: Annotated[TokenPayload, Depends(require_roles(["ADMIN", "SECURITY_OFFICER"]))],
) -> dict[str, Any]:
    """Protected endpoint strictly requiring ADMIN or SECURITY_OFFICER role."""
    return {
        "audit_logs": [
            {"event": "DATABASE_BACKUP_COMPLETED", "cluster": "prod-1", "timestamp": "2026-10-14T07:00:00Z"},
            {"event": "IAM_ROLE_GRANTED", "target": "usr_99", "timestamp": "2026-10-14T07:12:00Z"},
        ],
        "access_granted_under": "RBAC_ENFORCED",
    }


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite (Async ASGI Transport)
# ==============================================================================
async def main() -> None:
    print("=" * 70)
    print(" LEVEL 6: 02_JWT_AUTH_AND_RBAC_MIDDLEWARE - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Issue Test Tokens for Different Personas
    print("\n--- 1. Cryptographic Token Issuance ---")
    standard_token, _ = JwtTokenService.create_access_token(
        user_id="usr_standard_101",
        email="developer@enterprise.io",
        roles=["DEVELOPER"],
        permissions=["read:repos"],
    )
    admin_token, admin_claims = JwtTokenService.create_access_token(
        user_id="usr_admin_999",
        email="ciso@enterprise.io",
        roles=["ADMIN"],
        permissions=["read:audit", "write:roles"],
    )
    print(f"  Issued Standard User Token: {standard_token[:35]}...")
    print(f"  Issued Admin User Token:    {admin_token[:35]}...")

    # 2. Test Endpoints via In-Memory ASGI Transport
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # A. Missing Token Guard -> 403 / 401
        print("\n--- 2. Testing Unauthenticated Access Rejection ---")
        unauth_resp = await client.get("/api/v1/profile/me")
        print(f"  Missing Token GET /profile/me status: {unauth_resp.status_code}")
        assert unauth_resp.status_code == 403  # HTTPBearer auto_error rejects without header

        # B. Standard User Accesses Standard Profile -> 200 OK
        print("\n--- 3. Testing Standard User Profile Access ---")
        std_resp = await client.get(
            "/api/v1/profile/me", headers={"Authorization": f"Bearer {standard_token}"}
        )
        assert std_resp.status_code == 200
        print(f"  Standard User Profile: {std_resp.json()['email']} | Roles: {std_resp.json()['assigned_roles']}")

        # C. Standard User Attempts Admin Endpoint -> 403 Forbidden
        print("\n--- 4. Testing RBAC Privilege Guard Rejection (403 Forbidden) ---")
        forbidden_resp = await client.get(
            "/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {standard_token}"}
        )
        print(f"  Standard User GET /admin/audit-logs status: {forbidden_resp.status_code}")
        assert forbidden_resp.status_code == 403
        print(f"  Rejection Detail: {forbidden_resp.json()['detail']}")

        # D. Admin User Accesses Admin Endpoint -> 200 OK
        print("\n--- 5. Testing Authorized Admin Access (200 OK) ---")
        admin_resp = await client.get(
            "/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_resp.status_code == 200
        print(f"  Admin Access Granted: Found {len(admin_resp.json()['audit_logs'])} audit records.")

        # E. Token Revocation / Blacklist Verification
        print("\n--- 6. Testing Token Revocation (JTI Blacklisting) ---")
        _REVOKED_JTI_STORE.add(admin_claims.jti)
        print(f"  Revoked Admin JTI: {admin_claims.jti}")

        revoked_resp = await client.get(
            "/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"}
        )
        print(f"  Revoked Token Request status: {revoked_resp.status_code} ({revoked_resp.json()['detail']})")
        assert revoked_resp.status_code == 401
        print("  [PASS] Blacklisted JTI successfully blocked at gateway.")

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 02_jwt_auth_and_rbac_middleware module executed cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
