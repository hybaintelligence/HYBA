"""Authentication API endpoints."""

from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from hyba_genesis_api.auth.jwt_handler import TokenPayload, get_jwt_manager, get_token_payload

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=512)


def _is_production() -> bool:
    return os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower() == "production"


def _allowed_operator_hashes() -> Dict[str, Dict[str, Any]]:
    """Load operator credentials from HYBA_OPERATOR_CREDENTIALS.

    Format: username:sha256_hex:role[,username:sha256_hex:role]
    """
    raw = os.getenv("HYBA_OPERATOR_CREDENTIALS", "")
    operators: Dict[str, Dict[str, Any]] = {}
    for item in raw.split(","):
        if not item.strip():
            continue
        parts = item.split(":")
        if len(parts) != 3:
            continue
        username, password_hash, role = parts
        operators[username] = {"password_hash": password_hash.lower(), "roles": [role]}
    return operators


def _password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _verify_operator(username: str, password: str) -> List[str]:
    operators = _allowed_operator_hashes()
    operator = operators.get(username)
    if not operator:
        if _is_production():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        # Development-only operator for local smoke testing; disabled in production.
        if username == "operator" and password == "operator":
            return ["operator"]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    expected = operator["password_hash"]
    actual = _password_hash(password)
    if not hmac.compare_digest(actual, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return operator["roles"]


@router.post("/login", response_model=Dict[str, Any])
async def login(req: AuthRequest):
    roles = _verify_operator(req.username, req.password)
    token = get_jwt_manager().create_access_token(
        user_id=req.username,
        username=req.username,
        roles=roles,
    )
    return {
        "success": True,
        "token": token,
        "user": {
            "id": req.username,
            "username": req.username,
            "role": roles[0] if roles else "operator",
            "roles": roles,
            "createdAt": None,
        },
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
        "timestamp": datetime.utcnow().isoformat(),
    }
