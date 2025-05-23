from app.services.portfolio_validator import PortfolioValidator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_image_validation():
    validator = PortfolioValidator()
    
    # Test URLs with various scenarios
    test_urls = [
        # Clear face images
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d",  # Single person
        "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61",  # Group of people
        
        # No face images
        "https://images.unsplash.com/photo-1682687220063-4742bd7fd538",  # Landscape
        "https://images.unsplash.com/photo-1682687220067-dced0a2c8e3f",  # Abstract
        "https://images.unsplash.com/photo-1682687220063-4742bd7fd538",  # Nature
        
        # Edge cases
        "https://images.unsplash.com/photo-1517841905240-472988babdf9",  # Profile face
        "https://images.unsplash.com/photo-1517841905240-472988babdf9",  # Same image (test caching)
        "https://images.unsplash.com/photo-1517841905240-472988babdf9",  # Same image again (test caching)
    ]
    
    logger.info("Starting face detection tests...\n")
    
    for i, url in enumerate(test_urls, 1):
        result = validator._is_valid_profile_image(url)
        logger.info(f"Test {i}:")
        logger.info(f"URL: {url}")
        logger.info(f"Contains face: {result}\n")

if __name__ == "__main__":
    test_image_validation() 