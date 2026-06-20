"""
Authentication management for HYBA CLI
"""

import os
from pathlib import Path
from typing import Optional
import json


class AuthManager:
    """Manages API key and authentication credentials"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".hyba"
        self.config_dir.mkdir(exist_ok=True)
        self.creds_file = self.config_dir / "credentials.json"
    
    def save_credentials(self, api_key: str, api_url: str = None):
        """Save API credentials"""
        creds = {
            "api_key": api_key,
            "api_url": api_url or "https://api.hyba.ai"
        }
        with open(self.creds_file, 'w') as f:
            json.dump(creds, f)
    
    def get_api_key(self) -> Optional[str]:
        """Get stored API key"""
        # Check environment variable first
        if os.environ.get("HYBA_API_KEY"):
            return os.environ.get("HYBA_API_KEY")
        
        # Check credentials file
        if self.creds_file.exists():
            try:
                with open(self.creds_file, 'r') as f:
                    creds = json.load(f)
                return creds.get("api_key")
            except:
                pass
        
        return None
    
    def clear_credentials(self):
        """Clear stored credentials"""
        if self.creds_file.exists():
            self.creds_file.unlink()
