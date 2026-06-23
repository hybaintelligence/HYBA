"""User model for admin-managed operator accounts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """Operator account stored in the database for admin-managed access.

    Production credentials are stored as Argon2id hashes.  The legacy
    ``HYBA_OPERATOR_CREDENTIALS`` environment variable remains supported for
    bootstrapping but admin-created users take precedence when present.
    """

    __tablename__ = "users"

    id: str = Column(String(100), primary_key=True)
    username: str = Column(String(128), unique=True, nullable=False, index=True)
    password_hash: str = Column(Text, nullable=False)
    roles: str = Column(String(256), nullable=False, default="operator")
    is_active: bool = Column(Boolean, nullable=False, default=True)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_login: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    created_by: Optional[str] = Column(String(100), nullable=True)

    def role_list(self) -> List[str]:
        return [r.strip() for r in self.roles.split(",") if r.strip()]

    def set_roles(self, roles: List[str]) -> None:
        self.roles = ",".join(roles)
