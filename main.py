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
    
    async def run_telegram_bot(self):
        """Run Telegram bot - runs polling in main event loop"""
        self.telegram_bot = TelegramBot(
            self.config.TELEGRAM_BOT_TOKEN,
            self.config.TELEGRAM_ADMIN_ID
        )
        # Pass database reference to bot
        self.telegram_bot.db = self.db
        
        # Run polling - this is blocking but runs in main thread
        self.telegram_bot.run()
        logger.info("Telegram bot stopped")
    
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
        
        # Initialize both services
        self.telegram_bot = TelegramBot(
            self.config.TELEGRAM_BOT_TOKEN,
            self.config.TELEGRAM_ADMIN_ID
        )
        self.telegram_bot.db = self.db
        
        # Run both concurrently using gather
        # Telegram bot runs in main thread (required for signal handlers)
        # Auto-commenter runs as async task
        await asyncio.gather(
            asyncio.create_task(self._run_auto_commenter_wrapper()),
            asyncio.create_task(self._run_telegram_bot_wrapper())
        )
        
        logger.info("Affiliate Bot stopped")
    
    async def _run_telegram_bot_wrapper(self):
        """Wrapper to run telegram bot in executor"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.telegram_bot.run)
    
    async def _run_auto_commenter_wrapper(self):
        """Wrapper to run auto-commenter"""
        await self.run_auto_commenter()


def main():
    """Main entry point"""
    app = AffiliateBot()
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()