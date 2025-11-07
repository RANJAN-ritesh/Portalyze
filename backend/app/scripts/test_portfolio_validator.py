import asyncio
from app.services.portfolio_validator import PortfolioValidator
import json
from datetime import datetime

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

async def validate_portfolios():
    """Validate multiple portfolios and generate reports."""
    validator = PortfolioValidator()
    
    for portfolio in TEST_PORTFOLIOS:
        print(f"\n{'='*80}")
        print(f"Validating {portfolio['name']} at {portfolio['url']}")
        print(f"{'='*80}")
        
        try:
            # Validate portfolio
            results = await validator.validate_portfolio(portfolio['url'])
            
            # Print summary
            print("\nVALIDATION SUMMARY:")
            print("-" * 50)
            print(results["summary"])
            print(f"\nOverall Score: {results['score']}/100")
            
            # Save detailed results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"validation_{portfolio['name'].lower().replace(' ', '_')}_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nDetailed validation results saved to {output_file}")
            
        except Exception as e:
            print(f"Error validating {portfolio['name']}: {str(e)}")
            continue

if __name__ == "__main__":
    asyncio.run(validate_portfolios()) 