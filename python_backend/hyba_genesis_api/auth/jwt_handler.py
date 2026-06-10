"""
JWT Authentication Handler
HYBA Genesis Platform Security
"""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import jwt
from fastapi import Header, HTTPException, status
from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str
    username: str
    roles: List[str]
    exp: int
    iat: int
    iss: str = "genesis.hyba.ai"


class JWTManager:
    """Production-grade JWT manager with blacklist support and key rotation readiness."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        if not secret_key:
            raise RuntimeError("JWT_SECRET is required")
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_blacklist: set[str] = set()

    def create_access_token(self, user_id: str, username: str, roles: List[str], expiry_hours: int = 1) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "username": username,
            "roles": roles,
            "exp": now + timedelta(hours=expiry_hours),
            "iat": now,
            "iss": "genesis.hyba.ai",
            "jti": secrets.token_hex(16),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            jti = payload.get("jti", "")
            if jti and jti in self.token_blacklist:
                raise HTTPException(status_code=401, detail="Token revoked")
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def revoke_token(self, token: str) -> None:
        """Add a token's JTI to the blacklist."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get("jti")
            if jti:
                self.token_blacklist.add(jti)
        except jwt.InvalidTokenError:
            pass


def _generate_dev_secret() -> str:
    """Generate a cryptographically random dev secret and cache it for the process lifetime."""
    raw = secrets.token_hex(32)
    # Deterministic hash so the secret is stable within the same process
    return hashlib.sha256(raw.encode()).hexdigest()


_DEV_SECRET: Optional[str] = None


def get_jwt_manager() -> JWTManager:
    global _DEV_SECRET
    secret = os.getenv("JWT_SECRET")
    if not secret:
        env = os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower()
        if env == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="JWT_SECRET environment variable is required in production",
            )
        if _DEV_SECRET is None:
            _DEV_SECRET = _generate_dev_secret()
        secret = _DEV_SECRET
    return JWTManager(secret_key=secret)


async def get_token_payload(authorization: str = Header(None)) -> TokenPayload:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.split(" ", 1)[1]
    return get_jwt_manager().verify_token(token)


class APIKeyManager:
    def __init__(self):
        self.valid_keys = self._load_keys()

    @staticmethod
    def _load_keys() -> Dict[str, Dict[str, str]]:
        raw = os.getenv("HYBA_API_KEYS", "")
        keys: Dict[str, Dict[str, str]] = {}
        for item in raw.split(","):
            if not item.strip():
                continue
            try:
                key, role, user_id = item.split(":", 2)
            except ValueError:
                continue
            keys[key] = {"role": role, "user_id": user_id}
        return keys

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, str]]:
        return self.valid_keys.get(api_key)
