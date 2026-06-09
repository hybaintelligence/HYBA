"""
JWT Authentication Handler
HYBA Genesis Platform Security
"""

import jwt
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

class TokenPayload(BaseModel):
    sub: str  # user_id
    username: str
    roles: List[str]
    exp: int
    iat: int
    iss: str = "genesis.hyba.ai"

class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_blacklist = set()
    
    def create_access_token(self, user_id: str, username: str, roles: List[str]) -> str:
        payload = {
            "sub": user_id,
            "username": username,
            "roles": roles,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "iss": "genesis.hyba.ai"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> TokenPayload:
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        return TokenPayload(**payload)

class APIKeyManager:
    def __init__(self):
        self.valid_keys = {
            "hgsk_1a2b3c4d5e6f7g8h9i0j": {"role": "admin", "user_id": "system"},
            "hqsk_2b3c4d5e6f7g8h9i0j1k": {"role": "quantum", "user_id": "quantum_solver"}
        }
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, str]]:
        return self.valid_keys.get(api_key)
