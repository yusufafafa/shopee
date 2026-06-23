"""Facebook post scraper using Playwright for reliable scraping"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from playwright.async_api import async_playwright
from ..core.logger import setup_logger

logger = setup_logger("FacebookScraper")


class FacebookScraper:
    """Scrape Facebook posts using Playwright browser automation"""
    
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.browser = None
        self.page = None
    
    async def _init_browser(self):
        """Initialize Playwright browser with cookie"""
        if self.browser is None:
            playwright = await async_playwright.start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.page = await self.browser.new_page()
            
            # Set cookie
            cookie_dict = {}
            for item in self.cookie.split(";"):
                item = item.strip()
                if "=" in item:
                    key, value = item.split("=", 1)
                    cookie_dict[key.strip()] = value.strip()
            
            await self.page.context.add_cookies([{
                'name': key,
                'value': value,
                'domain': '.facebook.com',
                'path': '/'
            } for key, value in cookie_dict.items()])
            
            logger.debug("Browser initialized with cookies")
    
    async def search_posts(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """
        Search for posts containing keywords using Facebook mobile search.
        Returns list of posts with: author, content, url, timestamp
        """
        posts = []
        await self._init_browser()
        
        logger.info(f"Searching for posts with keywords: {keywords}")
        
        for keyword in keywords:
            try:
                # Navigate to Facebook mobile search
                from urllib.parse import quote
                encoded_keyword = quote(keyword)
                search_url = f"https://m.facebook.com/search/posts/?q={encoded_keyword}"
                
                logger.debug(f"Navigating to: {search_url}")
                
                # Navigate and wait for content
                await self.page.goto(search_url, wait_until='networkidle', timeout=30000)
                
                # Wait for posts to load
                await self.page.wait_for_selector('div[role="article"]', timeout=10000)
                
                # Check if logged in
                if 'login' in self.page.url.lower():
                    logger.error(f"Session expired for '{keyword}'. Need to re-authenticate.")
                    continue
                
                # Get all post elements
                post_elements = await self.page.query_selector_all('div[role="article"]')
                logger.debug(f"Found {len(post_elements)} post elements for '{keyword}'")
                
                for post_el in post_elements[:limit]:
                    try:
                        # Extract author
                        author_el = await post_el.query_selector('a[href*="/profile.php"]')
                        author = await author_el.inner_text() if author_el else "Unknown"
                        
                        # Extract content
                        content_el = await post_el.query_selector('p')
                        content = await content_el.inner_text() if content_el else ""
                        
                        # Extract URL
                        link_el = await post_el.query_selector('a[href*="/story.php"]')
                        if link_el:
                            href = await link_el.get_attribute('href')
                            url = f"https://m.facebook.com{href}" if href and href.startswith('/') else href
                        else:
                            url = ""
                        
                        # Extract timestamp
                        time_el = await post_el.query_selector('abbr')
                        timestamp = await time_el.get_attribute('title') if time_el else "Unknown"
                        
                        # Only add if we have content
                        if content and len(content) > 10:
                            posts.append({
                                "author": author,
                                "content": content.strip(),
                                "url": url,
                                "timestamp": timestamp,
                                "keyword": keyword
                            })
                            logger.debug(f"Extracted post: {author} - {content[:50]}")
                    
                    except Exception as e:
                        logger.error(f"Error extracting post: {e}")
                        continue
                
                logger.info(f"Found {len(posts)} posts for keyword '{keyword}'")
            
            except Exception as e:
                logger.error(f"Error searching '{keyword}': {e}", exc_info=True)
        
        logger.info(f"Total posts found: {len(posts)}")
        return posts
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
            logger.debug("Browser closed")