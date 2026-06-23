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
        # Use m.facebook.com (mobile version)
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
                        # iOS Safari User-Agent (mobile)
                        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Cache-Control": "max-age=0",
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
        """
        Search for posts containing keywords.
        Returns list of posts with: author, content, url, timestamp
        """
        posts = []
        session = await self._get_session()
        
        logger.info(f"Searching for posts with keywords: {keywords}")
        
        for keyword in keywords:
            try:
                # First, visit Facebook homepage to ensure session is active
                async with session.get("https://m.facebook.com") as home_response:
                    logger.info(f"Facebook homepage status: {home_response.status}")
                    if home_response.status != 200:
                        logger.error(f"Failed to access Facebook homepage: {home_response.status}")
                        continue
                
                # Search URL for mobile Facebook
                from urllib.parse import quote
                encoded_keyword = quote(keyword)
                search_url = f"{self.base_url}/search/posts/?q={encoded_keyword}"
                
                logger.info(f"Searching: {search_url}")
                
                async with session.get(search_url) as response:
                    logger.info(f"Search response: HTTP {response.status}, URL: {response.url}")
                    
                    if response.status != 200:
                        logger.error(f"Search failed for '{keyword}': HTTP {response.status}")
                        continue
                    
                    html = await response.text()
                    logger.info(f"Response HTML length: {len(html)} bytes")
                    
                    # Check if redirected to login page
                    if "login" in response.url.path.lower() or "log in" in html.lower():
                        logger.error(f"Session expired or invalid for '{keyword}'. Need to re-authenticate.")
                        continue
                    
                    # Log first 1000 chars for debugging
                    logger.info(f"HTML preview: {html[:1000]}")
                    
                    parsed_posts = self._parse_search_results(html, keyword)
                    logger.info(f"Found {len(parsed_posts)} posts for keyword '{keyword}'")
                    posts.extend(parsed_posts[:limit])
            
            except Exception as e:
                logger.error(f"Error searching '{keyword}': {e}", exc_info=True)
        
        logger.info(f"Total posts found: {len(posts)}")
        return posts
    
    def _parse_search_results(self, html: str, keyword: str) -> List[Dict]:
        """Parse HTML search results from mbasic Facebook"""
        posts = []
        
        logger.debug(f"Parsing search results for '{keyword}', HTML length: {len(html)}")
        
        # mbasic Facebook uses simple table/div structure
        # Each post is typically in a <div> or <table> with specific patterns
        
        # Look for post containers - mbasic uses simple divs
        # Pattern: look for posts with author links
        post_pattern = r'<div[^>]*id=["\']mbasic_[^>]*>(.*?)</div>'
        post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
        
        # Fallback: try finding posts by looking for profile links
        if not post_matches:
            # mbasic typically has posts with profile.php links
            post_pattern = r'(<a[^>]*profile\.php[^>]*>.*?</a>.*?(?:</div>|<br[^>]*>))'
            post_matches = re.findall(post_pattern, html, re.DOTALL | re.IGNORECASE)
        
        logger.debug(f"Found {len(post_matches)} potential post containers")
        
        for post_html in post_matches:
            try:
                # Extract author - mbasic uses simple <a> tags
                author = "Unknown"
                author_match = re.search(r'<a[^>]*href=["\'][^/]*profile\.php\?id=\d+[^>]*>([^<]+)</a>', post_html, re.IGNORECASE)
                if author_match:
                    author = author_match.group(1).strip()
                else:
                    # Try alternative author pattern
                    author_match = re.search(r'<a[^>]*href=["\'][^>]*>([^<]{2,50})</a>', post_html, re.IGNORECASE)
                    if author_match:
                        author = author_match.group(1).strip()
                
                # Extract content - mbasic uses simple text in divs/spans
                content = ""
                # Look for text content after author link
                content_match = re.search(r'</a>[^>]*>([^<]{20,500})', post_html, re.IGNORECASE)
                if content_match:
                    content = re.sub(r'<[^>]+>', '', content_match.group(1)).strip()
                    # Clean up HTML entities
                    content = content.replace('"', '"').replace('&', '&').replace('<', '<').replace('>', '>')
                
                # Extract post URL
                url = ""
                url_match = re.search(r'href=["\'](/story\.php\?[^"\']+)["\']', post_html, re.IGNORECASE)
                if url_match:
                    url = f"{self.base_url}{url_match.group(1)}"
                else:
                    # Try alternative URL pattern
                    url_match = re.search(r'href=["\'](https?://[^"\']*facebook\.com/story\.php\?[^"\']+)["\']', post_html, re.IGNORECASE)
                    if url_match:
                        url = url_match.group(1)
                
                # Extract timestamp
                timestamp = "Unknown"
                time_match = re.search(r'(\d+\s*[hdwm]\s*ago|\d+\s*jam\s*yang\s*lalu|\d+\s*menit\s*yang\s*lalu)', post_html, re.IGNORECASE)
                if time_match:
                    timestamp = time_match.group(1).strip()
                
                # Only add if we have meaningful content
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
        
        logger.info(f"Parsed {len(posts)} valid posts from HTML")
        return posts
    
    async def post_comment(self, post_url: str, comment_text: str) -> bool:
        """
        Post comment on a Facebook post using mobile interface.
        Returns True if successful.
        
        Note: This is a simplified implementation. Facebook's comment form
        requires proper CSRF tokens and form data extraction.
        """
        session = await self._get_session()
        
        try:
            # Normalize URL - convert desktop URL to mobile if needed
            if "www.facebook.com" in post_url:
                post_url = post_url.replace("www.facebook.com", "m.facebook.com")
            elif "facebook.com" in post_url and "m.facebook.com" not in post_url:
                post_url = post_url.replace("facebook.com", "m.facebook.com")
            
            # Get post page to extract form data
            async with session.get(post_url) as response:
                post_html = await response.text()
                
                # Check if we're on the right page (not login/redirect)
                if "login" in response.url.path.lower():
                    print("Redirected to login - session may be invalid")
                    return False
            
            # Extract story FID (form ID) from the page
            # Facebook uses various patterns for this
            fid_match = re.search(r'["\']ft_ent_identifier["\']:\s*["\']([^"\']+)["\']', post_html)
            if not fid_match:
                fid_match = re.search(r'data-ft=["\'].+?ft_ent_identifier=([^"&]+)', post_html)
            if not fid_match:
                # Fallback: extract from URL
                fid_match = re.search(r'story\.php\?[^&]*fbid=([^&]+)', post_url)
            
            story_fid = fid_match.group(1) if fid_match else post_url.split("=")[-1]
            
            # Extract CSRF token (fb_dtsg)
            dtsg_match = re.search(r'["\']fb_dtsg["\']:\s*["\']([^"\']+)["\']', post_html)
            if not dtsg_match:
                dtsg_match = re.search(r'name=["\']fb_dtsg["\']\s+value=["\']([^"\']+)["\']', post_html)
            
            fb_dtsg = dtsg_match.group(1) if dtsg_match else None
            
            # Build comment URL
            comment_url = f"{self.base_url}/a/comment.php"
            
            # Prepare form data
            form_data = {
                "comment_text": comment_text,
                "ft_ent_identifier": story_fid,
                "source": "www",
            }
            
            # Add CSRF token if available
            if fb_dtsg:
                form_data["fb_dtsg"] = fb_dtsg
            
            # Post comment
            async with session.post(comment_url, data=form_data) as response:
                result = await response.text()
                
                # Check for success indicators
                if "comment" in result.lower() or response.status == 200:
                    # Additional check: look for error messages
                    if "error" not in result.lower() and "failed" not in result.lower():
                        return True
                
                print(f"Comment post may have failed. Response: {result[:200]}")
                return False
        
        except Exception as e:
            print(f"Error posting comment: {e}")
            return False
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None