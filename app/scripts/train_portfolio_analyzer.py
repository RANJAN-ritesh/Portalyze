import asyncio
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
import json
from app.services.pattern_analyzer import PortfolioPatternAnalyzer
from app.data.portfolio_cache import PortfolioCache
from typing import List, Dict, Any
import time
from collections import defaultdict

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
    
    analysis_results = []
    
    for portfolio in PORTFOLIOS:
        print(f"\nAnalyzing portfolio: {portfolio['deployed_url']}")
        
        # Check cache first
        cached_analysis = cache.get_portfolio_analysis(
            portfolio['github_url'],
            portfolio['deployed_url']
        )
        
        if cached_analysis:
            print("Using cached analysis")
            analysis_results.append({
                'url': portfolio['deployed_url'],
                'analysis': cached_analysis
            })
            continue
        
        try:
            # Fetch and analyze portfolio
            content = await fetch_portfolio_content(portfolio['deployed_url'])
            analysis = pattern_analyzer.analyze_portfolio(content)
            
            # Save to cache
            cache.save_portfolio_analysis(
                portfolio['github_url'],
                portfolio['deployed_url'],
                analysis
            )
            
            analysis_results.append({
                'url': portfolio['deployed_url'],
                'analysis': analysis
            })
            
            # Print detailed analysis
            print("\nPortfolio Analysis Results:")
            print("=" * 50)
            
            # Section Coverage
            coverage = analysis['quality_metrics']['section_coverage'] * 100
            print(f"\nSection Coverage: {coverage:.1f}%")
            
            # Content Quality
            print("\nContent Quality:")
            for section, metrics in analysis['quality_metrics']['content_quality'].items():
                print(f"\n{section.title()} Section:")
                print(f"- Content Length: {metrics['length']} characters")
                print(f"- Has Images: {'Yes' if metrics['has_images'] else 'No'}")
                print(f"- Has Links: {'Yes' if metrics['has_links'] else 'No'}")
                
                # Heading Structure
                heading_structure = metrics['heading_structure']
                print(f"- Heading Structure:")
                print(f"  * Main Heading: {'Yes' if heading_structure['has_main_heading'] else 'No'}")
                print(f"  * Heading Levels: {sorted(heading_structure['heading_levels'])}")
                print(f"  * Total Headings: {heading_structure['heading_count']}")
            
            # Accessibility
            print("\nAccessibility Analysis:")
            for section, metrics in analysis['quality_metrics']['content_quality'].items():
                accessibility = metrics['accessibility_score']
                print(f"\n{section.title()} Section:")
                print(f"- ARIA Labels: {'Yes' if accessibility['has_aria_labels'] else 'No'}")
                print(f"- Alt Text: {'Yes' if accessibility['has_alt_text'] else 'No'}")
                print(f"- Semantic Elements: {'Yes' if accessibility['has_semantic_elements'] else 'No'}")
                if accessibility['color_contrast_issues']:
                    print("- Color Contrast Issues:")
                    for issue in accessibility['color_contrast_issues']:
                        print(f"  * {issue}")
            
            # Technical Stack
            print("\nTechnical Stack:")
            for category, techs in analysis['tech_stack'].items():
                print(f"\n{category.title()}:")
                for tech_type, technologies in techs.items():
                    if technologies:
                        print(f"- {tech_type.replace('_', ' ').title()}: {', '.join(technologies)}")
            
            print("\nAnalysis completed and cached")
            
        except Exception as e:
            print(f"Error analyzing portfolio: {str(e)}")
            continue
    
    # Generate aggregate statistics
    print("\nAggregate Statistics:")
    print("=" * 50)
    
    # Calculate average section coverage
    avg_coverage = sum(r['analysis']['quality_metrics']['section_coverage'] for r in analysis_results) / len(analysis_results) * 100
    print(f"\nAverage Section Coverage: {avg_coverage:.1f}%")
    
    # Most common technologies
    tech_counts = defaultdict(int)
    for result in analysis_results:
        for category in result['analysis']['tech_stack'].values():
            for techs in category.values():
                for tech in techs:
                    tech_counts[tech] += 1
    
    print("\nMost Common Technologies:")
    for tech, count in sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"- {tech}: {count} portfolios")
    
    # Save detailed results
    with open('portfolio_analysis_results.json', 'w') as f:
        json.dump({
            'individual_analyses': analysis_results,
            'aggregate_statistics': {
                'average_coverage': avg_coverage,
                'technology_usage': dict(tech_counts)
            }
        }, f, indent=2)
    
    print("\nDetailed analysis saved to portfolio_analysis_results.json")

if __name__ == "__main__":
    asyncio.run(analyze_portfolios()) 