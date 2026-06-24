"""Facebook post scraper using Playwright for headless browser scraping"""
import asyncio
import re
from typing import List, Dict, Optional
from datetime import datetime
from ..core.logger import setup_logger

logger = setup_logger("FacebookScraper")


class FacebookScraper:
    """Scrape Facebook posts using Playwright headless browser"""
    
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.base_url = "https://www.facebook.com"
        self.browser = None
        self.context = None
        self.page = None
    
    async def _init_browser(self):
        """Initialize Playwright browser with cookie authentication"""
        if self.browser is not None:
            return
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("playwright not installed. Run: pip install playwright && playwright install")
        
        logger.info("Initializing Playwright browser (headless)...")
        
        playwright = await async_playwright().start()
        
        # Launch browser in headless mode
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
            ]
        )
        
        # Create context first (without cookies)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        
        # Parse and set cookies
        cookies = self._parse_cookies(self.cookie)
        formatted_cookies = [
            {
                'name': key,
                'value': value,
                'domain': '.facebook.com',
                'path': '/',
            }
            for key, value in cookies.items()
        ]
        
        await self.context.add_cookies(formatted_cookies)
        
        self.page = await self.context.new_page()
        logger.info("Browser initialized successfully")
    
    def _parse_cookies(self, cookie_str: str) -> Dict[str, str]:
        """Parse cookie string to dict"""
        cookies = {}
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                cookies[key.strip()] = value.strip()
        return cookies
    
    async def scrape_personal_feed(self, limit: int = 20) -> List[Dict]:
        """Scrape posts from user's personal home feed"""
        posts = []
        
        try:
            await self._init_browser()
            
            logger.info("Scraping personal home feed (desktop)")
            
            # Navigate to home feed
            await self.page.goto("https://www.facebook.com", wait_until='networkidle', timeout=60000)
            
            # Wait a bit for content to load
            await asyncio.sleep(3)
            
            # Get page HTML
            html = await self.page.content()
            logger.info(f"Feed HTML length: {len(html)} bytes")
            
            # Check if logged in
            if "login" in self.page.url.lower():
                logger.error("Redirected to login - session invalid")
                return posts
            
            # Parse posts from HTML
            posts = self._parse_posts(html, source="feed")
            logger.info(f"Found {len(posts)} posts in feed")
            
            return posts[:limit]
        
        except Exception as e:
            logger.error(f"Error scraping feed: {e}", exc_info=True)
            return posts
    
    async def scrape_group_feed(self, group_url: str, limit: int = 20) -> List[Dict]:
        """Scrape posts from a Facebook group feed"""
        posts = []
        
        try:
            await self._init_browser()
            
            logger.info(f"Scraping group: {group_url}")
            
            # Normalize URL to desktop
            if "m.facebook.com" in group_url:
                group_url = group_url.replace("m.facebook.com", "www.facebook.com")
            
            # Navigate to group
            await self.page.goto(group_url, wait_until='networkidle', timeout=60000)
            
            # Wait for content to load
            await asyncio.sleep(3)
            
            # Get page HTML
            html = await self.page.content()
            logger.info(f"Group HTML length: {len(html)} bytes")
            
            # Check if logged in
            if "login" in self.page.url.lower():
                logger.error("Redirected to login - session invalid")
                return posts
            
            # Parse posts
            posts = self._parse_posts(html, source="group", group_url=group_url)
            logger.info(f"Found {len(posts)} posts in group")
            
            return posts[:limit]
        
        except Exception as e:
            logger.error(f"Error scraping group {group_url}: {e}", exc_info=True)
            return posts
    
    def _parse_posts(self, html: str, source: str = "feed", group_url: str = None) -> List[Dict]:
        """Parse posts from HTML content"""
        posts = []
        logger.debug(f"Parsing posts from {source}, HTML length: {len(html)}")
        
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4 not installed. Run: pip install beautifulsoup4")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all post containers - Facebook uses various structures
        # Try multiple selectors
        post_containers = []
        
        # Selector 1: div with role="article"
        post_containers.extend(soup.find_all('div', role='article'))
        
        # Selector 2: article tags
        post_containers.extend(soup.find_all('article'))
        
        # Selector 3: div with data-testid="post"
        post_containers.extend(soup.find_all('div', attrs={'data-testid': lambda x: x and 'post' in x.lower()}))
        
        logger.debug(f"Found {len(post_containers)} potential post containers")
        
        for container in post_containers:
            try:
                post_data = self._extract_post_data(container, source, group_url)
                if post_data and post_data.get('content'):
                    posts.append(post_data)
            except Exception as e:
                logger.debug(f"Error parsing post container: {e}")
                continue
        
        logger.info(f"Parsed {len(posts)} valid posts")
        return posts
    
    def _extract_post_data(self, container, source: str, group_url: str = None) -> Optional[Dict]:
        """Extract post data from container element"""
        try:
            # Author
            author = "Unknown"
            author_elem = container.find('a', href=re.compile(r'profile\.php\?id=\d+'))
            if not author_elem:
                # Try finding by text pattern
                author_elem = container.find('a', string=re.compile(r'.{2,50}'))
            
            if author_elem:
                author = author_elem.get_text(strip=True)
                if len(author) > 50:
                    author = author[:50] + "..."
            
            # Content - look for text in spans, divs
            content = ""
            
            # Try to find post text
            text_elems = container.find_all(['span', 'div'], string=True)
            for elem in text_elems:
                text = elem.get_text(strip=True)
                # Filter for meaningful content (not just UI elements)
                if len(text) > 20 and len(text) < 1000:
                    # Avoid common UI text
                    if not any(skip in text.lower() for skip in ['comment', 'share', 'like', 'react', 'see more', 'see less']):
                        content = text
                        break
            
            if not content:
                # Fallback: get all text and clean it
                all_text = container.get_text(separator=' ', strip=True)
                if len(all_text) > 50:
                    content = all_text[:500]
            
            # URL - look for story links
            url = ""
            story_link = container.find('a', href=re.compile(r'/story\.php\?|/posts/|/permalink/'))
            if story_link:
                href = story_link.get('href', '')
                if href.startswith('/'):
                    url = f"{self.base_url}{href}"
                elif href.startswith('http'):
                    url = href
            
            # Timestamp
            timestamp = "Unknown"
            time_elem = container.find(['abbr', 'span'], string=re.compile(r'\d+\s*(h|d|w|m|jam|hari|minggu|bulan)\s*(ago|yang lalu)?', re.I))
            if time_elem:
                timestamp = time_elem.get_text(strip=True)
            
            # Only add if we have meaningful content
            if content and len(content) > 20 and url:
                post_data = {
                    "author": author,
                    "content": content,
                    "url": url,
                    "timestamp": timestamp,
                    "source": source
                }
                
                if source == "group" and group_url:
                    post_data["group_url"] = group_url
                
                return post_data
            
            return None
        
        except Exception as e:
            logger.debug(f"Error extracting post data: {e}")
            return None
    
    async def post_comment(self, post_url: str, comment_text: str) -> bool:
        """Post comment on a Facebook post using Playwright"""
        try:
            await self._init_browser()
            
            logger.info(f"Posting comment on: {post_url}")
            
            # Navigate to post
            await self.page.goto(post_url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(2)
            
            # Try to find comment box and post
            # Facebook's structure varies, so we try multiple approaches
            
            # Approach 1: Look for comment textarea
            comment_box = None
            selectors = [
                'textarea[placeholder*="comment"]',
                'textarea[placeholder*="Comment"]',
                'textarea[aria-label*="comment"]',
                'div[contenteditable="true"][role="textbox"]',
            ]
            
            for selector in selectors:
                comment_box = await self.page.query_selector(selector)
                if comment_box:
                    break
            
            if not comment_box:
                logger.error("Could not find comment box")
                return False
            
            # Type comment
            await comment_box.fill(comment_text)
            await asyncio.sleep(1)
            
            # Find and click post button
            post_button = await self.page.query_selector('button[type="submit"]')
            if not post_button:
                post_button = await self.page.query_selector('button:has-text("Post")')
            
            if post_button:
                await post_button.click()
                await asyncio.sleep(2)
                logger.info("Comment posted successfully")
                return True
            else:
                logger.error("Could not find post button")
                return False
        
        except Exception as e:
            logger.error(f"Error posting comment: {e}", exc_info=True)
            return False
    
    async def close(self):
        """Close browser"""
        if self.page:
            await self.page.close()
            self.page = None
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        logger.info("Browser closed")