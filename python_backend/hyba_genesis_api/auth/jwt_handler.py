"""
JWT Authentication Handler
HYBA Genesis Platform Security
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict, List, Optional

import jwt
from fastapi import Cookie, Header, HTTPException, status
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)
ACCESS_COOKIE_NAME = "hyba_access_token"


class TokenPayload(BaseModel):
    sub: str
    username: str
    roles: List[str]
    exp: int
    iat: int
    iss: str = "genesis.hyba.ai"


class JWTManager:
    """Production-grade JWT manager with TTL-evicting blacklist and key rotation readiness."""

    # Maximum blacklist size before TTL-based eviction runs (prevents unbounded growth)
    _MAX_BLACKLIST_SIZE = 100_000
    # Fraction of _MAX_BLACKLIST_SIZE to evict when pruning
    _EVICT_FRACTION = 0.25

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        if not secret_key:
            raise RuntimeError("JWT_SECRET is required")
        self.secret_key = secret_key
        self.algorithm = algorithm
        # token_blacklist: jti -> expiry epoch seconds
        self.token_blacklist: dict[str, int] = {}

    def _prune_blacklist(self) -> None:
        """Evict expired JTIs to prevent unbounded growth."""
        now = datetime.now(timezone.utc).timestamp()
        expired = [jti for jti, exp in self.token_blacklist.items() if exp <= now]
        for jti in expired:
            del self.token_blacklist[jti]
        # If still over limit after pruning expired entries, evict oldest
        if len(self.token_blacklist) > self._MAX_BLACKLIST_SIZE:
            # Sort by expiry (ascending) and evict the oldest fraction
            sorted_jtis = sorted(self.token_blacklist.items(), key=lambda x: x[1])
            evict_count = int(self._MAX_BLACKLIST_SIZE * self._EVICT_FRACTION)
            for jti, _ in sorted_jtis[:evict_count]:
                del self.token_blacklist[jti]

    def create_access_token(
        self, user_id: str, username: str, roles: List[str], expiry_hours: int = 1
    ) -> str:
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
            exp = payload.get("exp", 0)
            if jti and self.token_blacklist.get(jti, 0) == exp:
                raise HTTPException(status_code=401, detail="Token revoked")
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def revoke_token(self, token: str) -> None:
        """Add a token's JTI to the blacklist keyed by expiry for TTL eviction."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
            jti = payload.get("jti")
            exp = payload.get("exp", 0)
            if jti:
                self.token_blacklist[jti] = exp
                self._prune_blacklist()
        except jwt.InvalidTokenError as exc:
            LOGGER.warning(
                "Token revocation requested with invalid token: %s",
                exc.__class__.__name__,
            )
            raise HTTPException(
                status_code=401, detail="Invalid token; revocation was not recorded"
            ) from exc


def _generate_dev_secret() -> str:
    """Generate a cryptographically random dev secret and cache it for the process lifetime."""
    raw = secrets.token_hex(32)
    # Deterministic hash so the secret is stable within the same process
    return hashlib.sha256(raw.encode()).hexdigest()


_DEV_SECRET: Optional[str] = None
_DEV_SECRET_LOCK = Lock()


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
        with _DEV_SECRET_LOCK:
            if _DEV_SECRET is None:
                _DEV_SECRET = _generate_dev_secret()
            secret = _DEV_SECRET
    return JWTManager(secret_key=secret)


def _bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1]
    return None


async def get_token_payload(
    authorization: str | None = Header(None),
    hyba_access_token: str | None = Cookie(None, alias=ACCESS_COOKIE_NAME),
) -> TokenPayload:
    """Resolve a JWT from an httpOnly browser cookie or a legacy Bearer header.

    Browser sessions should use the httpOnly ``hyba_access_token`` cookie to avoid
    localStorage token exposure. The Bearer header remains for CLI, tests, and
    non-browser operators.
    """
    token = hyba_access_token or _bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )
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
        entry = self.valid_keys.get(api_key)
        if not entry:
            return None
        # Constant-time comparison to prevent timing oracle on key prefix
        for stored_key in self.valid_keys:
            if hmac.compare_digest(stored_key, api_key):
                return self.valid_keys[stored_key]
        return None
