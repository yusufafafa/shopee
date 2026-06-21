"""Configuration loader from environment variables"""
import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager"""
    
    def __init__(self):
        # Load .env file
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(env_path)
        
        # Telegram
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))
        
        # Facebook
        self.FB_COOKIE = os.getenv("FB_COOKIE", "")
        
        # AI
        self.AI_API_KEY = os.getenv("AI_API_KEY", "")
        self.AI_MODEL = os.getenv("AI_MODEL", "gpt-3.5-turbo")
        
        # Database
        self.DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/affiliate.db")
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Bot settings
        self.SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "30"))  # seconds
        self.COMMENT_DELAY = int(os.getenv("COMMENT_DELAY", "5"))  # seconds between comments
        self.WARM_MODE_DELAY = int(os.getenv("WARM_MODE_DELAY", "60"))  # seconds in warm mode
        
        # Keywords
        self.BUYER_KEYWORDS = [
            "mau beli", "cari", "nyari", "butuh", "perlu",
            "ada yang jual", "rekomendasi", "suggest", "mohon saran"
        ]
        self.SELLER_KEYWORDS = [
            "jual", "dijual", "for sale", "open order", "ready stock"
        ]
    
    def validate(self) -> bool:
        """Validate required configuration"""
        required = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_ADMIN_ID"]
        for key in required:
            if not getattr(self, key):
                print(f"❌ Missing required config: {key}")
                return False
        return True