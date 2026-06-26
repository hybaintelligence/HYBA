#!/usr/bin/env python3
"""Create GitHub repository secrets using REST API directly.

Required environment variable:
  GITHUB_TOKEN - Personal access token with 'repo' and 'workflow' scopes
"""

import os
import sys
import json
import base64
import subprocess
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests")
    sys.exit(1)

# Secrets to create
SECRETS = {
    "JWT_SECRET": "T-HjQLuo5vC_FDIsH2WnlmrjCydl1n63x_2AwLxqeU8",
    "HYBA_OPERATOR_CREDENTIALS": "operator:$argon2id$v=19$m=65536,t=3,p=4$evdwh5nzDeODqYfk51XwmA$cbGUMInUbNVnDLJ+h9unojYBVyl7mctrgqJTvCe/mI4:mining_operator",
}

# Repository info
OWNER = "hybaintelligence"
REPO = "HYBA"


def get_github_token():
    """Get GitHub token from environment or gh CLI."""
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token
    
    # Try to get from gh CLI
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        print("ERROR: GITHUB_TOKEN not set and gh auth token failed")
        print("Set GITHUB_TOKEN environment variable or use: gh auth login")
        sys.exit(1)


def get_public_key(token):
    """Fetch the repository's public key for secret encryption."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/secrets/public-key"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"ERROR: Failed to get public key: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    return response.json()


def encrypt_secret(public_key_str, secret_value):
    """Encrypt secret using the public key (libsodium sealed box)."""
    try:
        import nacl.public
        import nacl.utils
    except ImportError:
        print("ERROR: PyNaCl required. Install with: pip install pynacl")
        sys.exit(1)
    
    # Decode the public key
    public_key_bytes = base64.b64decode(public_key_str)
    public_key = nacl.public.PublicKey(public_key_bytes)
    
    # Encrypt the secret
    encrypted = nacl.public.SealedBox(public_key).encrypt(secret_value.encode("utf-8"))
    
    # Return base64-encoded ciphertext
    return base64.b64encode(encrypted.ciphertext).decode("utf-8")


def create_secret(token, secret_name, secret_value, public_key_info):
    """Create a GitHub repository secret."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/secrets/{secret_name}"
    
    # Encrypt the secret value
    encrypted_value = encrypt_secret(public_key_info["key"], secret_value)
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    data = {
        "encrypted_value": encrypted_value,
        "key_id": public_key_info["key_id"],
    }
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in (201, 204):
        print(f"✅ Created secret: {secret_name}")
        return True
    else:
        print(f"❌ Failed to create {secret_name}: {response.status_code}")
        print(response.text)
        return False


def main():
    print(f"Creating GitHub secrets for: {OWNER}/{REPO}")
    print()
    
    # Get token
    token = get_github_token()
    print("✅ GitHub authentication successful")
    
    # Get public key
    print("Fetching repository public key...")
    public_key_info = get_public_key(token)
    print("✅ Public key retrieved")
    print()
    
    # Create secrets
    print("Creating secrets:")
    success_count = 0
    for secret_name, secret_value in SECRETS.items():
        if create_secret(token, secret_name, secret_value, public_key_info):
            success_count += 1
    
    print()
    print(f"✅ Created {success_count}/{len(SECRETS)} secrets")
    
    if success_count == len(SECRETS):
        print()
        print("Next steps:")
        print("1. Push code to main branch: git push origin main")
        print("2. GitHub Actions workflows will trigger automatically")
        print("3. Docker Build Cloud will build multi-platform images")
        print("4. Images will push to Docker Hub")
        return 0
    else:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
