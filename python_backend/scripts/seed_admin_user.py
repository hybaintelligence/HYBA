#!/usr/bin/env python3
"""Seed script to create an initial admin user for HYBA platform.

The first administrator credential must be supplied by the operator at runtime;
this file intentionally ships without a reusable default secret.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from argon2 import PasswordHasher
from consciousness_db.models import User, UserRole
from hyba_genesis_api.database import SessionLocal

_password_hasher = PasswordHasher()


def _validate_seed_secret(secret: str) -> None:
    """Reject missing, short, placeholder, or low-complexity seed credentials."""
    normalized = (secret or "").strip()
    if not normalized:
        raise ValueError("Initial admin secret is required via --password or HYBA_INITIAL_ADMIN_PASSWORD.")
    lowered = normalized.lower()
    if len(normalized) < 14 or "replace-with" in lowered or "change-me" in lowered:
        raise ValueError("Initial admin secret is not strong enough for seeding.")
    classes = [
        any(ch.islower() for ch in normalized),
        any(ch.isupper() for ch in normalized),
        any(ch.isdigit() for ch in normalized),
        any(not ch.isalnum() for ch in normalized),
    ]
    if sum(classes) < 3:
        raise ValueError("Initial admin secret must include at least three character classes.")


def create_admin_user(username: str, password: str, email: str | None = None):
    """Create an admin user in the database."""
    _validate_seed_secret(password)
    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"User '{username}' already exists. Skipping creation.")
            return existing

        user = User(
            username=username,
            email=email,
            password_hash=_password_hasher.hash(password),
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

    except Exception as exc:
        db.rollback()
        print(f"❌ Failed to create admin user: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create initial admin user for HYBA platform")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--password", default=None, help="Initial admin secret")
    parser.add_argument("--email", default=None, help="Admin email")
    args = parser.parse_args()

    supplied_secret = args.password or os.getenv("HYBA_INITIAL_ADMIN_PASSWORD")

    print("=" * 60)
    print("HYBA Admin User Seed Script")
    print("=" * 60)
    print()

    create_admin_user(args.username, supplied_secret or "", args.email)

    print()
    print("=" * 60)
    print("✅ Initial admin secret was supplied at runtime and passed local checks.")
    print("=" * 60)
