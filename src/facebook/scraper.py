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
                        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
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
    
    async def search_posts(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """Search for posts containing keywords"""
        posts = []
        session = await self._get_session()
        
        logger.info(f"Searching for posts with keywords: {keywords}")
        
        for keyword in keywords:
            try:
                # Visit Facebook homepage
                async with session.get("https://m.facebook.com") as home_response:
                    logger.info(f"Facebook homepage: HTTP {home_response.status}")
                    if home_response.status != 200:
                        logger.error(f"Failed to access Facebook: {home_response.status}")
                        continue
                
                # Search
                from urllib.parse import quote
                encoded_keyword = quote(keyword)
                search_url = f"{self.base_url}/search/posts/?q={encoded_keyword}"
                
                logger.info(f"Searching: {search_url}")
                
                async with session.get(search_url) as response:
                    logger.info(f"Search response: HTTP {response.status}, URL: {response.url}")
                    
                    if response.status != 200:
                        logger.error(f"Search failed: HTTP {response.status}")
                        continue
                    
                    html = await response.text()
                    logger.info(f"HTML length: {len(html)} bytes")
                    
                    # Check login
                    if "login" in response.url.path.lower() or "log in" in html.lower():
                        logger.error("Session expired. Need re-authenticate.")
                        continue
                    
                    # Preview HTML
                    logger.info(f"HTML preview: {html[:500]}")
                    
                    parsed_posts = self._parse_search_results(html, keyword)
                    logger.info(f"Found {len(parsed_posts)} posts for '{keyword}'")
                    posts.extend(parsed_posts[:limit])
            
            except Exception as e:
                logger.error(f"Error searching '{keyword}': {e}", exc_info=True)
        
        logger.info(f"Total posts found: {len(posts)}")
        return posts
    
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