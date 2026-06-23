"""Facebook auto-comment executor"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from .scraper_playwright import FacebookScraper
from .cookies import CookieManager
from ..ai_filter.classifier import TextClassifier
from ..ai_filter.prompts import get_comment_template
from ..database.connection import Database
from ..core.logger import setup_logger
from ..core.settings import SettingsManager
import random
import asyncio
from datetime import datetime, timedelta


logger = setup_logger("FacebookCommenter")


class AutoCommenter:
    """Auto-comment executor with rotation and warm mode"""
    
    def __init__(
        self,
        db: Database,
        cookie_manager: CookieManager,
        classifier: TextClassifier,
        is_warm_mode: bool = False,
        comment_delay: int = 5,
        warm_delay: int = 60
    ):
        self.db = db
        self.cookie_manager = cookie_manager
        self.classifier = classifier
        self.settings = SettingsManager()
        self.is_warm_mode = is_warm_mode
        self.comment_delay = comment_delay
        self.warm_delay = warm_delay
        self.is_running = False
    
    async def process_post(self, post: Dict, ai_api_key: str = None) -> Dict:
        """
        Process a single post through the pipeline.
        Returns processing result.
        """
        result = {
            "success": False,
            "author": post.get("author", "Unknown"),
            "keyword": post.get("keyword", ""),
            "url": post.get("url", ""),
            "skip_type": None,
            "reason": "",
            "comment_text": None
        }
        
        # Step 1: Check if already commented
        # (In production, check database for URL)
        
        # Step 2: AI classification
        content = post.get("content", "")
        should_comment, skip_type, reason = await self.classifier.classify(
            content,
            api_key=ai_api_key,
            use_ai=True
        )
        
        if not should_comment:
            result["skip_type"] = skip_type
            result["reason"] = reason
            logger.info(f"Skipped post by {result['author']}: {reason}")
            return result
        
        # Step 3: Get active account
        active_cookies = self.cookie_manager.get_active_cookies()
        if not active_cookies:
            result["reason"] = "No active accounts"
            logger.error("No active Facebook accounts available")
            return result
        
        # Use first active account (rotation logic can be added)
        account_name = active_cookies[0]
        cookie_str = self.cookie_manager.get_cookie_string(account_name)
        
        # Step 4: Extract keyword from post for smart matching
        content = post.get("content", "")
        keyword = self.classifier.extract_keyword(content)
        
        # Track the search for analytics
        if keyword:
            self.db.track_keyword_search(keyword)
            logger.info(f"Extracted keyword from post: '{keyword}'")
        
        # Step 5: Get relevant link (smart matching with fallback)
        link = None
        if keyword:
            # Try to find matching products by name
            matched_links = self.db.search_links_by_name(keyword)
            if matched_links:
                # Random pick from matched links
                link = random.choice(matched_links)
                logger.info(f"Found {len(matched_links)} matches for '{keyword}', selected: {link.product_name}")
        
        # Fallback to random link if no match
        if not link:
            link = self.db.get_random_affiliate_link()
            if keyword:
                logger.info(f"No match for '{keyword}', using random link: {link.product_name if link else 'None'}")
        
        if not link:
            result["reason"] = "No affiliate links available"
            logger.error("No affiliate links in database")
            return result
        
        # Step 6: Get random template
        templates = self.db.get_all_templates()
        if not templates:
            templates = ["Cek ini kak: {link}"]
        
        template = random.choice(templates)
        comment_text = template.format(link=link.url)
        
        # Step 7: Post comment
        scraper = FacebookScraper(cookie_str)
        success = await scraper.post_comment(post["url"], comment_text)
        await scraper.close()
        
        if success:
            result["success"] = True
            result["comment_text"] = comment_text
            self.cookie_manager.update_last_used(account_name)
            
            # Update link stats
            self.db.increment_link_clicks(link.id)
            self.db.update_link_promoted(link.id)
            
            logger.info(f"Comment posted: {comment_text[:50]}... (keyword: {keyword}, product: {link.product_name})")
        else:
            result["reason"] = "Failed to post comment"
            # Deactivate account if blocked
            self.cookie_manager.deactivate_cookie(account_name)
            logger.error(f"Failed to post comment - {account_name} may be blocked")
        
        return result
    
    async def run_loop(self, keywords: List[str], ai_api_key: str = None, is_auto_mode_check = None):
        """
        Main running loop for auto-commenter.
        Scans and processes posts continuously.
        
        Args:
            keywords: List of keywords to search for
            ai_api_key: OpenAI API key for AI filter
            is_auto_mode_check: Optional callable that returns True if auto mode is ON
        """
        self.is_running = True
        logger.info("Auto-commenter started")
        
        while self.is_running:
            try:
                logger.info("DEBUG: Starting loop iteration")
                
                # Check auto mode - if OFF, just wait and continue
                if is_auto_mode_check and not is_auto_mode_check():
                    logger.info("Auto mode OFF, waiting... (toggle Auto ON in Telegram to start scanning)")
                    await asyncio.sleep(30)  # Check every 30 seconds
                    continue
                
                logger.info("DEBUG: Auto mode ON, checking operating hours")
                
                # Check operating hours
                current_hour = datetime.now().hour
                if not self.settings.is_within_operating_hours(current_hour):
                    logger.info(f"Outside operating hours ({self.settings.settings.operating_start}:00-{self.settings.settings.operating_end}:00), pausing...")
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                
                logger.info("DEBUG: Within operating hours, checking accounts")
                
                # Get active accounts
                active_accounts = self.db.get_active_accounts()
                if not active_accounts:
                    logger.warning("No active accounts, waiting...")
                    await asyncio.sleep(60)
                    continue
                
                logger.info(f"DEBUG: Found {len(active_accounts)} active accounts")
                
                # Update cookie manager
                for account in active_accounts:
                    self.cookie_manager.add_cookie(account.name, account.cookie)
                
                # Check if any account can still comment today
                can_comment_account = None
                for account in active_accounts:
                    today_stats = self.db.get_account_today_stats(account.id)
                    if not today_stats["is_blocked"]:
                        # Get account-specific limit
                        account_limit = self.db.get_account_limit(account.id)
                        if self.settings.can_comment_today(today_stats["comment_count"], account_limit):
                            can_comment_account = account
                            break
                
                if not can_comment_account:
                    logger.warning("All accounts reached daily limit or blocked. Pausing until tomorrow.")
                    # Calculate seconds until midnight
                    now = datetime.now()
                    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    seconds_until_midnight = (midnight - now).total_seconds()
                    await asyncio.sleep(min(seconds_until_midnight, 3600))  # Max wait 1 hour
                    continue
                
                # Search for posts
                scraper = FacebookScraper(can_comment_account.cookie)
                posts = await scraper.search_posts(keywords, limit=5)
                await scraper.close()
                
                # Process each post
                for post in posts:
                    if not self.is_running:
                        break
                    
                    # Check daily limit again before each comment
                    today_stats = self.db.get_account_today_stats(can_comment_account.id)
                    account_limit = self.db.get_account_limit(can_comment_account.id)
                    
                    if today_stats["is_blocked"] or not self.settings.can_comment_today(today_stats["comment_count"], account_limit):
                        logger.warning(f"Account {can_comment_account.name} reached daily limit ({today_stats['comment_count']}/{account_limit}), switching account...")
                        break  # Will select new account in next iteration
                    
                    result = await self.process_post(post, ai_api_key)
                    
                    # Update statistics
                    stats = self.db.get_today_stats()
                    stats.scanned += 1
                    
                    if result["skip_type"] == "manual":
                        stats.manual_skip += 1
                    elif result["skip_type"] == "ai":
                        stats.ai_skip += 1
                    elif result["success"]:
                        stats.found += 1
                        stats.commented += 1
                        # Track account daily limit
                        self.db.increment_account_comment_count(can_comment_account.id)
                    
                    self.db.update_stats(stats)
                    
                    # Smart delay (random between min and max)
                    min_delay, max_delay = self.settings.get_delay_range()
                    actual_delay = random.randint(min_delay, max_delay)
                    logger.info(f"Waiting {actual_delay}s before next comment...")
                    await asyncio.sleep(actual_delay)
                
                # Wait before next scan
                await asyncio.sleep(30)
            
            except Exception as e:
                logger.error(f"Error in run loop: {e}", exc_info=True)
                await asyncio.sleep(60)
        
        logger.info("Auto-commenter stopped")
    
    def stop(self):
        """Stop the auto-commenter"""
        self.is_running = False