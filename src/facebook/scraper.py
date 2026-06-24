"""Facebook post scraper"""
import asyncio
import re
from typing import List, Dict, Optional
from datetime import datetime
from ..core.logger import setup_logger

logger = setup_logger("FacebookScraper")


class FacebookScraper:
    """Scrape Facebook posts using cookies"""
    
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.base_url = "https://m.facebook.com"
        self.session = None
    
async def _get_session(self):
        """Get aiohttp session with cookie and mobile headers"""
        if self.session is None:
            try:
                import aiohttp
                self.session = aiohttp.ClientSession(
                    cookies=self._parse_cookies(self.cookie),
                    headers={
                        # Android Chrome Mobile User-Agent
                        "User-Agent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Cache-Control": "max-age=0",
                        # Force mobile view
                        "X-Requested-With": "com.android.chrome",
                    }
                )
            except ImportError:
                raise ImportError("aiohttp not installed. Run: pip install aiohttp")
        return self.session
    
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
        session = await self._get_session()
        
        logger.info("Scraping personal home feed")
        
        try:
            # Force mobile homepage with redirect prevention
            async with session.get("https://m.facebook.com/home.php", allow_redirects=False) as response:
                logger.info(f"Home feed response: HTTP {response.status}, Location: {response.headers.get('Location', 'N/A')}")
                
                # If redirected to www, follow it but log warning
                if response.status == 302 and 'www.facebook.com' in response.headers.get('Location', ''):
                    logger.warning("Facebook redirected to desktop. Cookie may be from desktop session.")
                    async with session.get("https://m.facebook.com/home.php") as response:
                        html = await response.text()
                elif response.status == 200:
                    html = await response.text()
                else:
                    logger.error(f"Failed to access home feed: HTTP {response.status}")
                    return posts
                
                logger.info(f"Feed HTML length: {len(html)} bytes")
                
                # Check login
                if "login" in response.url.path.lower():
                    logger.error("Redirected to login - session invalid")
                    return posts
                
                # Parse feed
                parsed_posts = self._parse_feed(html)
                logger.info(f"Found {len(parsed_posts)} posts in feed")
                posts.extend(parsed_posts[:limit])
        
        except Exception as e:
            logger.error(f"Error scraping feed: {e}", exc_info=True)
        
        return posts
    
    def _parse_feed(self, html: str) -> List[Dict]:
        """Parse posts from personal feed"""
        posts = []
        logger.debug(f"Parsing feed, HTML length: {len(html)}")
        
        # Preview HTML for debugging
        logger.info(f"Feed HTML preview: {html[:500]}")
        
        # Look for posts - feed uses article tags or div with data-ft
        post_pattern = r'<article[^>]*>(.*?)</article>'
        post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
        
        # Fallback: div with role="article"
        if not post_matches:
            post_pattern = r'<div[^>]*role=["\']article["\'][^>]*>(.*?)</div>'
            post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
        
        # Fallback: look for posts with profile links
        if not post_matches:
            post_pattern = r'(<a[^>]*profile\.php[^>]*>.*?</a>.*?(?:</div>|<br[^>]*>))'
            post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
        
        logger.debug(f"Found {len(post_matches)} potential posts in feed")
        
        for post_html in post_matches:
            try:
                # Author
                author = "Unknown"
                author_match = re.search(r'<a[^>]*href=["\'][^/]*profile\.php\?id=\d+[^>]*>([^<]+)</a>', post_html, re.IGNORECASE)
                if author_match:
                    author = author_match.group(1).strip()
                
                # Content
                content = ""
                content_match = re.search(r'</a>[^>]*>([^<]{20,500})', post_html, re.IGNORECASE)
                if content_match:
                    content = re.sub(r'<[^>]+>', '', content_match.group(1)).strip()
                    content = content.replace('"', '"').replace('&', '&')
                
                # URL
                url = ""
                url_match = re.search(r'href=["\'](/story\.php\?[^"\']+)["\']', post_html, re.IGNORECASE)
                if url_match:
                    url = f"{self.base_url}{url_match.group(1)}"
                
                # Timestamp
                timestamp = "Unknown"
                time_match = re.search(r'(\d+\s*[hdwm]\s*ago|\d+\s*jam\s*yang\s*lalu)', post_html, re.IGNORECASE)
                if time_match:
                    timestamp = time_match.group(1).strip()
                
                # Add if valid
                if content and url and len(content) > 10:
                    posts.append({
                        "author": author,
                        "content": content,
                        "url": url,
                        "timestamp": timestamp,
                        "source": "feed"
                    })
            
            except Exception as e:
                logger.error(f"Error parsing feed post: {e}")
                continue
        
        logger.info(f"Parsed {len(posts)} valid posts from feed")
        return posts
    
    async def scrape_group_feed(self, group_url: str, limit: int = 20) -> List[Dict]:
        """Scrape posts from a Facebook group feed"""
        posts = []
        session = await self._get_session()
        
        logger.info(f"Scraping group: {group_url}")
        
        try:
            # Normalize group URL to mobile
            if "www.facebook.com" in group_url:
                group_url = group_url.replace("www.facebook.com", "m.facebook.com")
            elif "facebook.com" in group_url and "m.facebook.com" not in group_url:
                group_url = group_url.replace("facebook.com", "m.facebook.com")
            
            logger.info(f"Normalized URL: {group_url}")
            
            async with session.get(group_url) as response:
                logger.info(f"Group response: HTTP {response.status}")
                
                if response.status != 200:
                    logger.error(f"Failed to access group: HTTP {response.status}")
                    return posts
                
                html = await response.text()
                logger.info(f"Group HTML length: {len(html)} bytes")
                
                # Check login
                if "login" in response.url.path.lower():
                    logger.error("Redirected to login - session invalid")
                    return posts
                
                # Parse posts
                parsed_posts = self._parse_group_feed(html, group_url)
                logger.info(f"Found {len(parsed_posts)} posts in group")
                posts.extend(parsed_posts[:limit])
        
        except Exception as e:
            logger.error(f"Error scraping group {group_url}: {e}", exc_info=True)
        
        return posts
    
    def _parse_group_feed(self, html: str, group_url: str) -> List[Dict]:
        """Parse posts from group feed"""
        posts = []
        logger.debug(f"Parsing group feed, HTML length: {len(html)}")
        
        # Preview HTML
        logger.info(f"Group HTML preview: {html[:500]}")
        
        # Look for posts in group - groups use article or div with data-ft
        post_pattern = r'<article[^>]*>(.*?)</article>'
        post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
        
        # Fallback: look for div with role="article"
        if not post_matches:
            post_pattern = r'<div[^>]*role=["\']article["\'][^>]*>(.*?)</div>'
            post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
        
        # Fallback: look for posts with profile links
        if not post_matches:
            post_pattern = r'(<a[^>]*profile\.php[^>]*>.*?</a>.*?(?:</div>|<br[^>]*>))'
            post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
        
        logger.debug(f"Found {len(post_matches)} potential posts in group")
        
        for post_html in post_matches:
            try:
                # Author
                author = "Unknown"
                author_match = re.search(r'<a[^>]*href=["\'][^/]*profile\.php\?id=\d+[^>]*>([^<]+)</a>', post_html, re.IGNORECASE)
                if author_match:
                    author = author_match.group(1).strip()
                
                # Content
                content = ""
                content_match = re.search(r'</a>[^>]*>([^<]{20,500})', post_html, re.IGNORECASE)
                if content_match:
                    content = re.sub(r'<[^>]+>', '', content_match.group(1)).strip()
                    content = content.replace('"', '"').replace('&', '&')
                
                # URL
                url = ""
                url_match = re.search(r'href=["\'](/story\.php\?[^"\']+)["\']', post_html, re.IGNORECASE)
                if url_match:
                    url = f"{self.base_url}{url_match.group(1)}"
                
                # Timestamp
                timestamp = "Unknown"
                time_match = re.search(r'(\d+\s*[hdwm]\s*ago|\d+\s*jam\s*yang\s*lalu)', post_html, re.IGNORECASE)
                if time_match:
                    timestamp = time_match.group(1).strip()
                
                # Add if valid
                if content and url and len(content) > 10:
                    posts.append({
                        "author": author,
                        "content": content,
                        "url": url,
                        "timestamp": timestamp,
                        "source": "group",
                        "group_url": group_url
                    })
            
            except Exception as e:
                logger.error(f"Error parsing group post: {e}")
                continue
        
        logger.info(f"Parsed {len(posts)} valid posts from group")
        return posts
    
    async def search_posts(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """Search for posts containing keywords (deprecated, use scrape_group_feed instead)"""
        # Legacy method - return empty
        logger.warning("search_posts() is deprecated. Use scrape_group_feed() instead.")
        return []
    
    def _parse_search_results(self, html: str, keyword: str) -> List[Dict]:
        """Parse HTML search results"""
        posts = []
        logger.debug(f"Parsing HTML for '{keyword}', length: {len(html)}")
        
        # Look for posts with profile links
        post_pattern = r'(<a[^>]*profile\.php[^>]*>.*?</a>.*?(?:</div>|<br[^>]*>))'
        post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
        
        logger.debug(f"Found {len(post_matches)} potential posts")
        
        for post_html in post_matches:
            try:
                # Author
                author = "Unknown"
                author_match = re.search(r'<a[^>]*href=["\'][^/]*profile\.php\?id=\d+[^>]*>([^<]+)</a>', post_html, re.IGNORECASE)
                if author_match:
                    author = author_match.group(1).strip()
                
                # Content
                content = ""
                content_match = re.search(r'</a>[^>]*>([^<]{20,500})', post_html, re.IGNORECASE)
                if content_match:
                    content = re.sub(r'<[^>]+>', '', content_match.group(1)).strip()
                    content = content.replace('"', '"').replace('&', '&')
                
                # URL
                url = ""
                url_match = re.search(r'href=["\'](/story\.php\?[^"\']+)["\']', post_html, re.IGNORECASE)
                if url_match:
                    url = f"{self.base_url}{url_match.group(1)}"
                
                # Timestamp
                timestamp = "Unknown"
                time_match = re.search(r'(\d+\s*[hdwm]\s*ago|\d+\s*jam\s*yang\s*lalu)', post_html, re.IGNORECASE)
                if time_match:
                    timestamp = time_match.group(1).strip()
                
                # Add if valid
                if content and url and len(content) > 10:
                    posts.append({
                        "author": author,
                        "content": content,
                        "url": url,
                        "timestamp": timestamp,
                        "keyword": keyword
                    })
            
            except Exception as e:
                logger.error(f"Error parsing post: {e}")
                continue
        
        logger.info(f"Parsed {len(posts)} valid posts")
        return posts
    
    async def post_comment(self, post_url: str, comment_text: str) -> bool:
        """Post comment on a Facebook post"""
        session = await self._get_session()
        
        try:
            # Normalize URL
            if "www.facebook.com" in post_url:
                post_url = post_url.replace("www.facebook.com", "m.facebook.com")
            elif "facebook.com" in post_url and "m.facebook.com" not in post_url:
                post_url = post_url.replace("facebook.com", "m.facebook.com")
            
            # Get post page
            async with session.get(post_url) as response:
                post_html = await response.text()
                if "login" in response.url.path.lower():
                    logger.error("Redirected to login")
                    return False
            
            # Extract story FID
            fid_match = re.search(r'["\']ft_ent_identifier["\']:\s*["\']([^"\']+)["\']', post_html)
            if not fid_match:
                fid_match = re.search(r'data-ft=["\'].+?ft_ent_identifier=([^"&]+)', post_html)
            if not fid_match:
                fid_match = re.search(r'story\.php\?[^&]*fbid=([^&]+)', post_url)
            
            story_fid = fid_match.group(1) if fid_match else post_url.split("=")[-1]
            
            # Extract CSRF token
            dtsg_match = re.search(r'["\']fb_dtsg["\']:\s*["\']([^"\']+)["\']', post_html)
            fb_dtsg = dtsg_match.group(1) if dtsg_match else None
            
            # Build comment URL
            comment_url = f"{self.base_url}/a/comment.php"
            
            # Form data
            form_data = {
                "comment_text": comment_text,
                "ft_ent_identifier": story_fid,
                "source": "www",
            }
            
            if fb_dtsg:
                form_data["fb_dtsg"] = fb_dtsg
            
            # Post comment
            async with session.post(comment_url, data=form_data) as response:
                result = await response.text()
                if "error" not in result.lower() and "failed" not in result.lower():
                    return True
                logger.warning(f"Comment may have failed: {result[:200]}")
                return False
        
        except Exception as e:
            logger.error(f"Error posting comment: {e}")
            return False
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None