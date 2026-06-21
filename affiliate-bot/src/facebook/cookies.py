"""Facebook cookie manager"""
import json
from typing import Dict, Optional
from datetime import datetime


class CookieManager:
    """Manage Facebook cookies for authentication"""
    
    def __init__(self):
        self.cookies: Dict[str, dict] = {}
    
    def parse_cookie_string(self, cookie_str: str) -> Dict[str, str]:
        """Parse cookie string to dictionary"""
        cookies = {}
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                cookies[key.strip()] = value.strip()
        return cookies
    
    def add_cookie(self, name: str, cookie_str: str) -> bool:
        """
        Add cookie by name.
        Returns True if valid cookie format.
        """
        parsed = self.parse_cookie_string(cookie_str)
        
        # Check required Facebook cookie fields
        required = ["c_user", "xs"]
        for field in required:
            if field not in parsed:
                return False
        
        self.cookies[name] = {
            "cookie": parsed,
            "raw": cookie_str,
            "added_at": datetime.now().isoformat(),
            "last_used": None,
            "is_active": True
        }
        return True
    
    def get_cookie(self, name: str) -> Optional[Dict[str, str]]:
        """Get cookie by name"""
        if name in self.cookies:
            return self.cookies[name]["cookie"]
        return None
    
    def get_cookie_string(self, name: str) -> Optional[str]:
        """Get raw cookie string by name"""
        if name in self.cookies:
            return self.cookies[name]["raw"]
        return None
    
    def remove_cookie(self, name: str) -> bool:
        """Remove cookie by name"""
        if name in self.cookies:
            del self.cookies[name]
            return True
        return False
    
    def list_cookies(self) -> list:
        """List all cookie names"""
        return list(self.cookies.keys())
    
    def get_active_cookies(self) -> list:
        """Get list of active cookie names"""
        return [
            name for name, data in self.cookies.items()
            if data["is_active"]
        ]
    
    def deactivate_cookie(self, name: str):
        """Deactivate a cookie"""
        if name in self.cookies:
            self.cookies[name]["is_active"] = False
    
    def activate_cookie(self, name: str):
        """Activate a cookie"""
        if name in self.cookies:
            self.cookies[name]["is_active"] = True
    
    def update_last_used(self, name: str):
        """Update last used timestamp"""
        if name in self.cookies:
            self.cookies[name]["last_used"] = datetime.now().isoformat()
    
    def save_to_file(self, filepath: str):
        """Save cookies to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.cookies, f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load cookies from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.cookies = json.load(f)
        except FileNotFoundError:
            self.cookies = {}