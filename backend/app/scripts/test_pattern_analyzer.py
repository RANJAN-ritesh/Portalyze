import asyncio
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
import json
from app.services.pattern_analyzer import PortfolioPatternAnalyzer
from typing import Dict, Any
import time

TEST_PORTFOLIOS = [
    {
        "name": "Portfolio 1",
        "url": "https://malik04121.github.io/"
    },
    {
        "name": "Portfolio 2",
        "url": "https://ashishkumarpalai.github.io/"
    },
    {
        "name": "Portfolio 3",
        "url": "https://sagu29.github.io/"
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
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                    await page.wait_for_selector('body', timeout=10000)
                    return await page.content()
                finally:
                    await browser.close()
        except TimeoutError:
            if attempt < max_retries - 1:
                print(f"Timeout fetching {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(2)
            else:
                raise
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            else:
                raise

def print_section_analysis(portfolio_name: str, sections: Dict[str, Any]):
    """Print the analysis results in a readable format."""
    print(f"\n{'='*50}")
    print(f"Analysis for {portfolio_name}")
    print(f"{'='*50}")
    
    for section_name, section_data in sections.items():
        print(f"\n{section_name.upper()} SECTION:")
        print("-" * 30)
        
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                if isinstance(value, (list, set)):
                    print(f"{key}: {len(value)} items found")
                    # Print first 3 items as examples
                    for item in list(value)[:3]:
                        print(f"  - {item}")
                else:
                    print(f"{key}: {value}")
        else:
            print(f"Found section with data: {section_data}")

async def test_pattern_analyzer():
    """Test the pattern analyzer with example portfolios."""
    analyzer = PortfolioPatternAnalyzer()
    
    for portfolio in TEST_PORTFOLIOS:
        print(f"\nTesting {portfolio['name']} at {portfolio['url']}")
        
        try:
            # Fetch portfolio content
            content = await fetch_portfolio_content(portfolio['url'])
            
            # Analyze portfolio
            patterns = analyzer.analyze_portfolio(content)
            
            # Print analysis results
            print_section_analysis(portfolio['name'], patterns)
            
            # Save detailed results to file
            output_file = f"analysis_{portfolio['name'].lower().replace(' ', '_')}.json"
            with open(output_file, 'w') as f:
                json.dump(patterns, f, indent=2)
            print(f"\nDetailed analysis saved to {output_file}")
            
        except Exception as e:
            print(f"Error analyzing {portfolio['name']}: {str(e)}")
            continue

if __name__ == "__main__":
    asyncio.run(test_pattern_analyzer()) 