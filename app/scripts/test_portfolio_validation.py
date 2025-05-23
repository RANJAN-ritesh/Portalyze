from app.services.portfolio_validator import PortfolioValidator
from app.services.portfolio_scorer import PortfolioScorer
import logging
import asyncio
import sys
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_portfolio_validation(url: str):
    validator = PortfolioValidator()
    scorer = PortfolioScorer()
    
    logger.info(f"\nValidating portfolio: {url}")
    try:
        # Get validation results
        results = await validator.validate_portfolio(url)
        validation_results = results["validation_results"]
        
        # Generate detailed report with scores
        report = scorer.generate_detailed_report(validation_results, url)
        
        # Print summary
        logger.info("\nValidation Summary:")
        logger.info("=" * 50)
        logger.info(report["summary"])
        logger.info("=" * 50)
        
        # Print detailed scores
        logger.info("\nDetailed Scores:")
        logger.info("=" * 50)
        for criterion, score in report["scores"].items():
            logger.info(f"{criterion.title()} ({score['weight']}%): {score['score']}/{score['max_score']} points")
        logger.info("=" * 50)
        
        # Print overall score
        logger.info(f"\nOverall Score: {report['overall_score']['percentage']:.1f}%")
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"portfolio_report_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"\nDetailed report saved to: {filename}")
        
    except Exception as e:
        logger.error(f"Error validating portfolio: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://ashishkumarpalai.github.io/"  # Default test URL
    
    asyncio.run(test_portfolio_validation(url)) 