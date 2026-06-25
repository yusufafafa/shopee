#!/usr/bin/env python3
"""Test script to verify Facebook cookie validity"""
import asyncio
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

async def test_cookie():
    """Test if Facebook cookie is still valid"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright")
        return
    
    print("🔍 Testing Facebook cookie...")
    
    # Get cookie from environment
    cookie = os.getenv('FB_COOKIE', '')
    if not cookie:
        print("❌ FB_COOKIE not found in .env")
        return
    
    print(f"✅ Found cookie ({len(cookie)} chars)")
    
    try:
        p = await async_playwright().start()
        
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        mobile_ua = "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        
        context = await browser.new_context(
            viewport={'width': 375, 'height': 812},
            user_agent=mobile_ua,
            is_mobile=True
        )
        
        # Parse and add cookies
        cookies = []
        for item in cookie.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies.append({
                    'name': key.strip(),
                    'value': value.strip(),
                    'domain': '.facebook.com',
                    'path': '/',
                })
        
        print(f"🍪 Adding {len(cookies)} cookies...")
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        # Test navigation
        print("📱 Navigating to m.facebook.com...")
        try:
            await page.goto('https://m.facebook.com', timeout=15000)
            await asyncio.sleep(3)
            
            url = page.url
            title = await page.title()
            
            print(f"\n📊 Results:")
            print(f"   URL: {url}")
            print(f"   Title: {title}")
            
            if 'login' in url.lower() or 'checkpoint' in url.lower():
                print("\n❌ COOKIE INVALID")
                print("   Cookie expired or account blocked.")
                print("   Solution: Add new account via Telegram (/addaccount)")
            else:
                print("\n✅ COOKIE VALID!")
                print("   Successfully logged in to Facebook.")
                
        except Exception as e:
            print(f"\n❌ TIMEOUT/ERROR: {e}")
            print("   Possible causes:")
            print("   1. Network too slow (VPS → Facebook)")
            print("   2. Facebook blocking datacenter IP")
            print("   3. Firewall blocking Facebook")
            print("\n   Try:")
            print("   - Check network: ping facebook.com")
            print("   - Test with proxy")
            print("   - Use residential IP")
        
        await browser.close()
        await p.stop()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cookie())