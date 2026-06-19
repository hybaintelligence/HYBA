#!/usr/bin/env python3
"""Seed script to create an initial admin user for HYBA platform.

Security posture:
- no committed default password;
- password must be supplied explicitly or via HYBA_INITIAL_ADMIN_PASSWORD;
- weak/common deployment passwords are rejected before any database write.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from argon2 import PasswordHasher
from consciousness_db.models import User, UserRole
from hyba_genesis_api.database import SessionLocal

_password_hasher = PasswordHasher()

_COMMON_OR_LEAKY_PASSWORDS = {
    "admin",
    "admin123",
    "admin123456",
    "password",
    "password123",
    "changeme",
    "secret",
    "123",
    "123456",
    "anything123",
}


def _validate_seed_password(password: str) -> None:
    """Reject missing, weak, placeholder, or historically documented passwords."""
    normalized = (password or "").strip()
    if not normalized:
        raise ValueError(
            "Admin password is required. Pass --password or set HYBA_INITIAL_ADMIN_PASSWORD."
        )
    if len(normalized) < 14:
        raise ValueError("Admin password must be at least 14 characters long.")
    lowered = normalized.lower()
    if lowered in _COMMON_OR_LEAKY_PASSWORDS or "replace-with" in lowered:
        raise ValueError("Admin password is a known placeholder/default and is not allowed.")
    classes = [
        any(ch.islower() for ch in normalized),
        any(ch.isupper() for ch in normalized),
        any(ch.isdigit() for ch in normalized),
        any(not ch.isalnum() for ch in normalized),
    ]
    if sum(classes) < 3:
        raise ValueError(
            "Admin password must include at least three character classes: lower, upper, digit, symbol."
        )


def create_admin_user(username: str, password: str, email: str | None = None):
    """Create an admin user in the database."""
    _validate_seed_password(password)
    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"User '{username}' already exists. Skipping creation.")
            return existing

        password_hash = _password_hasher.hash(password)

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=UserRole.ADMIN,
            is_active=True,
            created_by="system_seed",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print("✅ Admin user created successfully:")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email or 'N/A'}")
        print(f"   Role: {user.role}")
        print(f"   Active: {user.is_active}")
        print(f"   Created at: {user.created_at}")

        return user

    except Exception as e:
        db.rollback()
        print(f"❌ Failed to create admin user: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create initial admin user for HYBA platform")
    parser.add_argument("--username", default="admin", help="Admin username (default: admin)")
    parser.add_argument(
        "--password",
        default=None,
        help="Admin password. If omitted, HYBA_INITIAL_ADMIN_PASSWORD is used.",
    )
    parser.add_argument("--email", default=None, help="Admin email (optional)")

    args = parser.parse_args()
    password = args.password or os.getenv("HYBA_INITIAL_ADMIN_PASSWORD")

    print("=" * 60)
    print("HYBA Admin User Seed Script")
    print("=" * 60)
    print()

    create_admin_user(args.username, password or "", args.email)

    print()
    print("=" * 60)
    print("✅ Admin password was supplied explicitly and passed local strength checks.")
    print("=" * 60)
