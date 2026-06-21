"""Bot settings and configuration manager"""
import json
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class BotSettings:
    """Bot safety settings"""
    # Daily limits
    comments_per_account_per_day: int = 20
    max_comments_per_hour: int = 5
    
    # Delay settings (seconds)
    min_delay_seconds: int = 120      # 2 minutes
    max_delay_seconds: int = 600      # 10 minutes
    
    # Operating hours (24h format)
    operating_start: int = 9          # 9 AM
    operating_end: int = 20           # 8 PM
    
    # Account settings
    min_accounts_required: int = 5
    
    # Auto-pause settings
    auto_pause_on_block: bool = True
    pause_duration_minutes: int = 30


class SettingsManager:
    """Manage bot settings with persistence"""
    
    def __init__(self, settings_file: str = "./data/settings.json"):
        self.settings_file = Path(settings_file)
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings = self._load_settings()
    
    def _load_settings(self) -> BotSettings:
        """Load settings from file or create default"""
        if self.settings_file.exists():
            with open(self.settings_file, 'r') as f:
                data = json.load(f)
                return BotSettings(**data)
        else:
            # Create default settings
            settings = BotSettings()
            self._save_settings(settings)
            return settings
    
    def _save_settings(self, settings: BotSettings):
        """Save settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(asdict(settings), f, indent=2)
    
    def get(self) -> BotSettings:
        """Get current settings"""
        return self.settings
    
    def update(self, **kwargs):
        """Update specific settings"""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self._save_settings(self.settings)
    
    def get_delay_range(self) -> tuple:
        """Get delay range as tuple"""
        return (self.settings.min_delay_seconds, self.settings.max_delay_seconds)
    
    def is_within_operating_hours(self, hour: int) -> bool:
        """Check if current hour is within operating hours"""
        return self.settings.operating_start <= hour <= self.settings.operating_end
    
    def can_comment_today(self, today_count: int, account_limit: int = None) -> bool:
        """Check if account can still comment today"""
        limit = account_limit or self.settings.comments_per_account_per_day
        return today_count < limit
    
    def get_all_settings_dict(self) -> Dict[str, Any]:
        """Get all settings as dictionary"""
        return asdict(self.settings)