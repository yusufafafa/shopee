"""Main entry point"""
import asyncio
import signal
from pathlib import Path

from src.core.config import Config
from src.core.logger import setup_logger
from src.database.connection import Database
from src.telegram.bot import TelegramBot
from src.facebook.commenter import AutoCommenter
from src.facebook.cookies import CookieManager
from src.ai_filter.classifier import TextClassifier


logger = setup_logger("main")


class AffiliateBot:
    """Main application orchestrator"""
    
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config.DATABASE_PATH)
        self.telegram_bot = None
        self.auto_commenter = None
        self.cookie_manager = CookieManager()
        self.classifier = TextClassifier()
        self.is_running = False
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received...")
            self.is_running = False
            if self.auto_commenter:
                self.auto_commenter.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run_auto_commenter(self):
        """Run auto-commenter loop"""
        self.auto_commenter = AutoCommenter(
            db=self.db,
            cookie_manager=self.cookie_manager,
            classifier=self.classifier,
            is_warm_mode=self.telegram_bot.is_warm_mode if self.telegram_bot else False,
            comment_delay=self.config.COMMENT_DELAY,
            warm_delay=self.config.WARM_MODE_DELAY
        )
        
        # Load accounts from database
        accounts = self.db.get_active_accounts()
        for account in accounts:
            self.cookie_manager.add_cookie(account.name, account.cookie)
        
        # Get keywords from config
        keywords = self.config.BUYER_KEYWORDS
        
        # Run auto-commenter
        await self.auto_commenter.run_loop(
            keywords=keywords,
            ai_api_key=self.config.AI_API_KEY
        )
    
    async def run(self):
        """Main run method"""
        if not self.config.validate():
            logger.error("Configuration validation failed!")
            return
        
        self.is_running = True
        self.setup_signal_handlers()
        
        logger.info("Starting Affiliate Bot...")
        
        # Initialize Telegram bot
        self.telegram_bot = TelegramBot(
            self.config.TELEGRAM_BOT_TOKEN,
            self.config.TELEGRAM_ADMIN_ID
        )
        self.telegram_bot.db = self.db
        
        # Start auto-commenter as background task
        auto_commenter_task = asyncio.create_task(self.run_auto_commenter())
        
        # Run Telegram bot in main thread (blocking, handles signals)
        # This will run until stopped, keeping the process alive
        self.telegram_bot.run()
        
        # Cancel auto-commenter if still running
        auto_commenter_task.cancel()
        
        logger.info("Affiliate Bot stopped")


def main():
    """Main entry point"""
    app = AffiliateBot()
    
    if not app.config.validate():
        logger.error("Configuration validation failed!")
        return
    
    app.is_running = True
    app.setup_signal_handlers()
    
    logger.info("Starting Affiliate Bot...")
    
    # Initialize Telegram bot
    app.telegram_bot = TelegramBot(
        app.config.TELEGRAM_BOT_TOKEN,
        app.config.TELEGRAM_ADMIN_ID
    )
    app.telegram_bot.db = app.db
    
    # Run auto-commenter in separate thread
    import threading
    def run_auto_commenter_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(app.run_auto_commenter())
        except asyncio.CancelledError:
            pass
        finally:
            loop.close()
    
    auto_thread = threading.Thread(target=run_auto_commenter_thread, daemon=True)
    auto_thread.start()
    logger.info("Auto-commenter started in background")
    
    # Run Telegram bot in main thread (blocking)
    app.telegram_bot.run()
    
    logger.info("Affiliate Bot stopped")


if __name__ == "__main__":
    main()