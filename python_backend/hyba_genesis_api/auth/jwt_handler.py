"""
JWT Authentication Handler
HYBA Genesis Platform Security
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
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
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        if not secret_key:
            raise RuntimeError("JWT_SECRET is required")
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_blacklist = set()

    def create_access_token(self, user_id: str, username: str, roles: List[str]) -> str:
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "username": username,
            "roles": roles,
            "exp": now + timedelta(hours=1),
            "iat": now,
            "iss": "genesis.hyba.ai",
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


def get_jwt_manager() -> JWTManager:
    secret = os.getenv("JWT_SECRET")
    if not secret and os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower() != "production":
        secret = "dev-local-only-change-me"
    if not secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="JWT runtime is not configured")
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
