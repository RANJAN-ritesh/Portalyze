#!/usr/bin/env python3
"""
Test lightweight JavaScript execution alternatives to Playwright
Goal: Find something that works on Render free tier (~120MB vs 300MB)
"""

import asyncio

# Option 1: requests-html (uses pyppeteer, ~120MB)
async def test_requests_html():
    """
    requests-html - Lightweight, ~120MB Chromium
    Pros: Simple API, lighter than Playwright
    Cons: Still downloads browser but smaller
    """
    print("\n=== Testing requests-html ===")
    try:
        from requests_html import AsyncHTMLSession

        session = AsyncHTMLSession()
        response = await session.get('https://myportfolio-manjari5506.vercel.app/')

        # Execute JavaScript
        await response.html.arender(sleep=2)

        html = response.html.html
        print(f"✅ HTML Length: {len(html)}")
        print(f"✅ Has content: {'<div id=\"root\">' in html}")
        print(f"✅ Sample: {html[:500]}")

        await session.close()
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


# Option 2: selenium-wire with minimal Chrome
async def test_selenium():
    """
    Selenium - Mature but heavier
    Pros: Very stable, widely used
    Cons: ~200MB, more complex setup
    """
    print("\n=== Testing Selenium ===")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=options)
        driver.get('https://myportfolio-manjari5506.vercel.app/')

        # Wait for JS to execute
        await asyncio.sleep(2)

        html = driver.page_source
        print(f"✅ HTML Length: {len(html)}")

        driver.quit()
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


# Option 3: httpx + Pre-rendering service (external)
async def test_prerender_service():
    """
    Use external pre-rendering service
    Pros: No local browser needed, very light
    Cons: Requires external service, potential cost
    """
    print("\n=== Testing Prerender.io (Free tier) ===")
    try:
        import httpx

        # Prerender.io free tier (500 pages/month)
        url = 'https://myportfolio-manjari5506.vercel.app/'
        prerender_url = f'https://service.prerender.io/{url}'

        async with httpx.AsyncClient() as client:
            response = await client.get(prerender_url)
            html = response.text

            print(f"✅ HTML Length: {len(html)}")
            return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


if __name__ == '__main__':
    print("Testing lightweight JavaScript execution options...")
    print("=" * 60)

    # Run tests
    asyncio.run(test_requests_html())
    # asyncio.run(test_selenium())
    # asyncio.run(test_prerender_service())
