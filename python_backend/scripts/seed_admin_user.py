#!/usr/bin/env python3
"""Seed script to create initial admin user for HYBA platform."""

import sys
import os
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from argon2 import PasswordHasher
from hyba_genesis_api.database import SessionLocal
from consciousness_db.models import User, UserRole

_password_hasher = PasswordHasher()


def create_admin_user(username: str, password: str, email: str = None):
    """Create an admin user in the database."""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"User '{username}' already exists. Skipping creation.")
            return existing
        
        # Hash password
        password_hash = _password_hasher.hash(password)
        
        # Create admin user
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
        
        print(f"✅ Admin user created successfully:")
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
    parser.add_argument("--password", default="admin123456", help="Admin password (default: admin123456)")
    parser.add_argument("--email", default=None, help="Admin email (optional)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("HYBA Admin User Seed Script")
    print("=" * 60)
    print()
    
    create_admin_user(args.username, args.password, args.email)
    
    print()
    print("=" * 60)
    print("⚠️  IMPORTANT: Change the default password in production!")
    print("=" * 60)
