"""Test suite for Affiliate Bot"""
import pytest
import asyncio
from datetime import datetime


class TestTextClassifier:
    """Test AI text classifier"""
    
    def test_seller_detection(self):
        """Test manual filter detects seller posts"""
        from src.ai_filter.classifier import TextClassifier
        
        classifier = TextClassifier()
        
        # Test seller patterns
        seller_posts = [
            "Jual baju murah, ready stock!",
            "Open order dress korea, diskon 50%",
            "For sale: iPhone 15 Pro Max",
            "Promo spesial hari ini saja! 🛒"
        ]
        
        for post in seller_posts:
            is_skip, reason = classifier.manual_filter(post)
            assert is_skip == True
            assert reason == "seller"
    
    def test_buyer_detection(self):
        """Test manual filter detects buyer posts"""
        from src.ai_filter.classifier import TextClassifier
        
        classifier = TextClassifier()
        
        # Test buyer patterns
        buyer_posts = [
            "Mau beli sepatu running, ada rekomendasi?",
            "Cari dress kondangan warna navy",
            "Butuh laptop untuk editing video",
            "Mohon saran skincare untuk kulit berminyak"
        ]
        
        for post in buyer_posts:
            is_skip, reason = classifier.manual_filter(post)
            assert is_skip == False  # Passes manual filter
    
    def test_not_buyer_detection(self):
        """Test manual filter skips non-buyer posts"""
        from src.ai_filter.classifier import TextClassifier
        
        classifier = TextClassifier()
        
        # Test non-buyer patterns
        non_buyer_posts = [
            "Hari ini cuaca cerah",
            "Baru saja makan siang",
            "Siapa yang bisa datang besok?"
        ]
        
        for post in non_buyer_posts:
            is_skip, reason = classifier.manual_filter(post)
            assert is_skip == True
            assert reason == "not_buyer"


class TestCookieManager:
    """Test Facebook cookie manager"""
    
    def test_parse_cookie(self):
        """Test cookie string parsing"""
        from src.facebook.cookies import CookieManager
        
        manager = CookieManager()
        cookie_str = "c_user=100012345;xs=38%3Aabc123;fr=0abc123"
        parsed = manager.parse_cookie_string(cookie_str)
        
        assert "c_user" in parsed
        assert parsed["c_user"] == "100012345"
        assert "xs" in parsed
        assert "fr" in parsed
    
    def test_add_valid_cookie(self):
        """Test adding valid cookie"""
        from src.facebook.cookies import CookieManager
        
        manager = CookieManager()
        cookie_str = "c_user=100012345;xs=38%3Aabc123;fr=0abc123"
        
        result = manager.add_cookie("test_account", cookie_str)
        assert result == True
        assert "test_account" in manager.list_cookies()
    
    def test_add_invalid_cookie(self):
        """Test adding invalid cookie (missing required fields)"""
        from src.facebook.cookies import CookieManager
        
        manager = CookieManager()
        cookie_str = "c_user=100012345"  # Missing xs
        
        result = manager.add_cookie("test_account", cookie_str)
        assert result == False


class TestDatabase:
    """Test database operations"""
    
    def test_create_tables(self):
        """Test database table creation"""
        from src.database.connection import Database
        import tempfile
        import os
        
        # Create temp database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            db = Database(db_path)
            # Tables should be created automatically
            assert db.db_path.exists()
        finally:
            os.unlink(db_path)
    
    def test_add_account(self):
        """Test adding Facebook account"""
        from src.database.connection import Database
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            db = Database(db_path)
            account = db.add_account("test_cookies", "c_user=123;xs=abc")
            
            assert account.id is not None
            assert account.name == "test_cookies"
            assert account.is_active == True
        finally:
            os.unlink(db_path)
    
    def test_get_active_accounts(self):
        """Test getting active accounts"""
        from src.database.connection import Database
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            db = Database(db_path)
            db.add_account("active_account", "c_user=123;xs=abc")
            db.add_account("blocked_account", "c_user=456;xs=def")
            
            # Block second account
            accounts = db.get_all_accounts()
            db.update_account_status(accounts[1].id, is_active=False, is_blocked=True)
            
            active = db.get_active_accounts()
            assert len(active) == 1
            assert active[0].name == "active_account"
        finally:
            os.unlink(db_path)


class TestConfig:
    """Test configuration loading"""
    
    def test_config_validation(self):
        """Test config validation"""
        from src.core.config import Config
        import os
        
        # Save original env
        original_token = os.getenv("TELEGRAM_BOT_TOKEN")
        original_admin = os.getenv("TELEGRAM_ADMIN_ID")
        
        try:
            # Test with missing config
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
            os.environ.pop("TELEGRAM_ADMIN_ID", None)
            
            config = Config()
            assert config.validate() == False
            
            # Test with valid config
            os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
            os.environ["TELEGRAM_ADMIN_ID"] = "123456"
            
            config = Config()
            assert config.validate() == True
        finally:
            # Restore original env
            if original_token:
                os.environ["TELEGRAM_BOT_TOKEN"] = original_token
            if original_admin:
                os.environ["TELEGRAM_ADMIN_ID"] = original_admin


if __name__ == "__main__":
    pytest.main([__file__, "-v"])