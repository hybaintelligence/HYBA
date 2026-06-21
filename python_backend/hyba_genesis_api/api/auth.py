"""Authentication API endpoints."""

from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from hyba_genesis_api.auth.jwt_handler import (
    ACCESS_COOKIE_NAME,
    TokenPayload,
    get_jwt_manager,
    get_token_payload,
)
from hyba_genesis_api.database import SessionLocal
from consciousness_db.models import User
from core.error_handling import (
    handle_error,
    AuthenticationError,
    ValidationError,
    DatabaseError,
    HybaError,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
_password_hasher = PasswordHasher()


class AuthRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=512)


def _is_production() -> bool:
    return os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower() == "production"


def _cookie_samesite() -> str:
    return os.getenv("HYBA_AUTH_COOKIE_SAMESITE", "strict" if _is_production() else "lax")


def _cookie_secure() -> bool:
    return os.getenv("HYBA_AUTH_COOKIE_SECURE", "true" if _is_production() else "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _credential_entries(raw: str) -> List[str]:
    """Return credential entries while preserving Argon2 parameter commas.

    Production credentials use semicolon or newline-delimited entries because the
    Argon2id encoded hash contains commas in the memory/time/parallelism segment.
    A single Argon2 credential without a semicolon is accepted for operational
    convenience; legacy comma separation remains available only for non-Argon2
    local/development entries.
    """
    normalized = raw.strip()
    if not normalized:
        return []
    if ";" in normalized or "\n" in normalized:
        return [item.strip() for item in normalized.replace("\n", ";").split(";") if item.strip()]
    if "$argon2" in normalized:
        return [normalized]
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _allowed_operator_hashes() -> Dict[str, Dict[str, Any]]:
    """Load operator credentials from HYBA_OPERATOR_CREDENTIALS.

    Production format: username:$argon2id$...:role[;username:$argon2id$...:role]
    Legacy SHA-256 hashes are accepted only outside production for local smoke tests.
    """
    raw = os.getenv("HYBA_OPERATOR_CREDENTIALS", "")
    operators: Dict[str, Dict[str, Any]] = {}
    for item in _credential_entries(raw):
        parts = item.split(":", 2)
        if len(parts) != 3:
            continue
        username, password_hash, role = parts
        username = username.strip()
        password_hash = password_hash.strip()
        role = role.strip()
        if not username or not password_hash or not role:
            continue
        operators[username] = {"password_hash": password_hash, "roles": [role]}
    return operators


def _password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _verify_password(password: str, expected_hash: str) -> bool:
    if expected_hash.startswith("$argon2id$") or expected_hash.startswith("$argon2i$"):
        try:
            return _password_hasher.verify(expected_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    # Compatibility shim for development fixtures only. Production validation and
    # runtime auth both reject raw SHA-256 operator hashes.
    if not _is_production():
        return hmac.compare_digest(_password_hash(password), expected_hash.lower())

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": "operator_credentials_not_production_safe",
            "message": "HYBA_OPERATOR_CREDENTIALS must use Argon2id hashes in production.",
        },
    )


def _verify_operator(username: str, password: str) -> List[str]:
    # First try database authentication
    try:
        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        if user and user.is_active:
            try:
                if _password_hasher.verify(user.password_hash, password):
                    # Update last login
                    user.last_login = datetime.now(timezone.utc)
                    db.commit()
                    db.close()
                    return [user.role.value]
            except (VerifyMismatchError, VerificationError, InvalidHashError) as e:
                handle_error(
                    AuthenticationError(f"Password verification failed: {e}"),
                    context={"username": username},
                    raise_http=False
                )
        db.close()
    except Exception as e:
        handle_error(
            DatabaseError(f"Database authentication failed: {e}"),
            context={"username": username},
            raise_http=False
        )
        # Fall back to env var auth if database fails
        pass

    # Fall back to environment variable authentication
    operators = _allowed_operator_hashes()
    operator = operators.get(username)
    if not operator:
        if _is_production():
            raise handle_error(
                AuthenticationError("Invalid credentials"),
                context={"username": username}
            )
        # Development-only operator for local smoke testing; disabled in production.
        if username == "operator" and password == "operator":
            return ["operator"]
        raise handle_error(
            AuthenticationError("Invalid credentials"),
            context={"username": username}
        )

    expected = operator["password_hash"]
    if not _verify_password(password, expected):
        raise handle_error(
            AuthenticationError("Invalid credentials"),
            context={"username": username}
        )
    return operator["roles"]


@router.post("/login", response_model=Dict[str, Any])
async def login(req: AuthRequest, response: Response):
    roles = _verify_operator(req.username, req.password)
    token = get_jwt_manager().create_access_token(
        user_id=req.username,
        username=req.username,
        roles=roles,
    )
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
        max_age=3600,
        path="/",
    )
    return {
        "success": True,
        # Token is retained only for local CLI/backward-compatibility. Browser
        # clients should rely on the httpOnly cookie and must not persist it in
        # localStorage/sessionStorage.
        "token": token if not _is_production() else None,
        "token_transport": "httpOnly_cookie",
        "user": {
            "id": req.username,
            "username": req.username,
            "role": roles[0] if roles else "operator",
            "roles": roles,
            "createdAt": None,
        },
    }


@router.post("/logout", response_model=Dict[str, Any])
async def logout(response: Response, payload: TokenPayload = Depends(get_token_payload)):
    response.delete_cookie(
        key=ACCESS_COOKIE_NAME,
        path="/",
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
    )
    return {
        "success": True,
        "user": payload.username,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/register", response_model=Dict[str, Any])
async def register(_req: AuthRequest):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "registration_disabled",
            "message": "Self-service registration is disabled. Provision operators through HYBA_OPERATOR_CREDENTIALS.",
        },
    )


@router.get("/profile", response_model=Dict[str, Any])
async def profile(payload: TokenPayload = Depends(get_token_payload)):
    return {
        "success": True,
        "user": {
            "id": payload.sub,
            "username": payload.username,
            "role": payload.roles[0] if payload.roles else "operator",
            "roles": payload.roles,
            "createdAt": None,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_current_user(payload: TokenPayload = Depends(get_token_payload)) -> TokenPayload:
    """FastAPI dependency to get the current authenticated user from JWT token."""
    return payload
