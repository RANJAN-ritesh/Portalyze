import asyncio
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
import json
from app.services.pattern_analyzer import PortfolioPatternAnalyzer
from app.data.portfolio_cache import PortfolioCache
from typing import List, Dict, Any
import time

PORTFOLIOS = [
    {
        "github_url": "https://github.com/Malik04121/Malik04121.github.io",
        "deployed_url": "https://malik04121.github.io/"
    },
    {
        "github_url": "https://github.com/Karishma282/myportfolio",
        "deployed_url": "https://portfoliokarishma.vercel.app/"
    },
    {
        "github_url": "https://github.com/ashishkumarpalai/ashishkumarpalai.github.io",
        "deployed_url": "https://ashishkumarpalai.github.io/"
    },
    {
        "github_url": "https://github.com/sagu29/sagu29.github.io",
        "deployed_url": "https://sagu29.github.io/"
    },
    {
        "github_url": "https://github.com/khushboo787/Khushboo787.github.io",
        "deployed_url": "https://khushboo787.github.io/"
    },
    {
        "github_url": "https://github.com/pshriya01/pshriya01.github.io",
        "deployed_url": "https://pshriya01.github.io/"
    },
    {
        "github_url": "https://github.com/0126prashant/0126prashant.github.io",
        "deployed_url": "https://0126prashant.github.io/"
    }
]

async def fetch_portfolio_content(url: str, max_retries: int = 3) -> str:
    """Fetch portfolio content using Playwright with retries."""
    for attempt in range(max_retries):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                try:
                    # Set longer timeout for initial load
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                    
                    # Wait for content to be visible
                    await page.wait_for_selector('body', timeout=10000)
                    
                    # Get the content
                    content = await page.content()
                    return content
                finally:
                    await browser.close()
        except TimeoutError:
            if attempt < max_retries - 1:
                print(f"Timeout fetching {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(2)  # Wait before retry
            else:
                raise
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            else:
                raise

async def analyze_portfolios():
    """Analyze all portfolios and build pattern database."""
    cache = PortfolioCache()
    pattern_analyzer = PortfolioPatternAnalyzer()
    
    for portfolio in PORTFOLIOS:
        print(f"\nAnalyzing portfolio: {portfolio['deployed_url']}")
        
        # Check cache first
        cached_analysis = cache.get_portfolio_analysis(
            portfolio['github_url'],
            portfolio['deployed_url']
        )
        
        if cached_analysis:
            print("Using cached analysis")
            continue
        
        try:
            # Fetch and analyze portfolio
            content = await fetch_portfolio_content(portfolio['deployed_url'])
            patterns = pattern_analyzer.analyze_portfolio(content)
            
            # Save to cache
            cache.save_portfolio_analysis(
                portfolio['github_url'],
                portfolio['deployed_url'],
                patterns
            )
            
            print("Analysis completed and cached")
            
        except Exception as e:
            print(f"Error analyzing portfolio: {str(e)}")
            continue
    
    # Get all patterns and save to a separate file
    all_patterns = pattern_analyzer.get_patterns()
    with open('portfolio_patterns.json', 'w') as f:
        json.dump(all_patterns, f, indent=2)
    
    print("\nPattern analysis complete. Results saved to portfolio_patterns.json")

if __name__ == "__main__":
    asyncio.run(analyze_portfolios()) 