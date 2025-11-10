"""
Main Portfolio Analyzer
Coordinates all analysis services: web scraping, AI, rubrics, face detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup

# Try to import Playwright (optional dependency)
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightTimeout = TimeoutError
    print("⚠️  Playwright not available - trying lighter alternatives")

# Try to import requests-html (lighter alternative)
try:
    from requests_html import AsyncHTMLSession
    REQUESTS_HTML_AVAILABLE = True
    print("✅ requests-html available - using for JS rendering")
except ImportError:
    REQUESTS_HTML_AVAILABLE = False
    print("⚠️  requests-html not available - using aiohttp fallback")

from app.services.ai_analyzer import AIAnalyzer
from app.services.rubric_engine import RubricEngine
from app.services.image_validator import ImageValidator
from app.database.cache import cache_service
from app.config import settings
import time
import aiohttp

logger = logging.getLogger(__name__)


class PortfolioAnalyzer:
    """
    Main analyzer that coordinates all portfolio analysis
    - Web scraping with Playwright
    - AI analysis (Gemini/Groq fallback)
    - Rule-based rubric grading (27 parameters)
    - Face detection with MediaPipe
    - Caching for cost optimization
    """

    def __init__(self):
        self.ai_analyzer = AIAnalyzer()
        self.rubric_engine = RubricEngine()
        self.image_validator = ImageValidator()

    async def analyze(self, portfolio_url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Main analysis method

        Args:
            portfolio_url: Deployed portfolio URL
            force_refresh: If True, bypass cache and perform fresh analysis

        Returns:
            Complete analysis results with checklist, AI feedback, and metadata
        """
        start_time = time.time()
        logger.info(f"Starting analysis of {portfolio_url} (force_refresh={force_refresh})")

        try:
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_result = await cache_service.get_cached_result(portfolio_url)
                if cached_result:
                    cached_result["from_cache"] = True
                    cached_result["analysis_time"] = 0.1  # Instant from cache
                    logger.info(f"Returning cached result for {portfolio_url}")
                    return cached_result

            # Fetch portfolio content
            html_content, screenshot, viewport_data = await self._fetch_portfolio(portfolio_url)

            if not html_content:
                return self._error_result("Failed to fetch portfolio content")

            # Run analyses in parallel for speed
            results = await asyncio.gather(
                self._run_rubric_analysis(html_content, portfolio_url),
                self._run_ai_analysis(html_content),
                self._run_image_analysis(html_content),
                return_exceptions=True
            )

            rubric_result = results[0] if not isinstance(results[0], Exception) else {}
            ai_result = results[1] if not isinstance(results[1], Exception) else {}
            image_result = results[2] if not isinstance(results[2], Exception) else {}

            # Combine results
            final_result = {
                "portfolio_url": portfolio_url,
                "checklist": rubric_result.get("checklist", {}),
                "ai_analysis": ai_result.get("analysis", "AI analysis unavailable"),
                "ai_provider": ai_result.get("provider", "None"),
                "professional_photo": image_result,
                "screenshot_url": screenshot,
                "responsive_check": viewport_data,
                "analysis_time": round(time.time() - start_time, 2),
                "from_cache": False,
                "timestamp": time.time()
            }

            # Calculate score
            final_result["score"] = self._calculate_score(final_result["checklist"])

            # Generate learning resources
            final_result["learning_resources"] = self._generate_learning_resources(
                final_result["checklist"]
            )

            # Cache result
            await cache_service.set_cached_result(portfolio_url, final_result)

            # Create shareable link if enabled
            if settings.enable_shareable_links:
                share_id = await cache_service.create_shareable_link(
                    portfolio_url,
                    final_result,
                    expires_in_days=30
                )
                final_result["share_id"] = share_id
                final_result["share_url"] = f"{settings.api_base_url}/share/{share_id}"

            logger.info(
                f"Analysis complete for {portfolio_url} - "
                f"Score: {final_result['score']}% in {final_result['analysis_time']}s"
            )

            return final_result

        except asyncio.TimeoutError:
            logger.error(f"Analysis timeout for {portfolio_url}")
            return self._error_result("Analysis timeout - portfolio took too long to load")
        except Exception as e:
            logger.error(f"Analysis error for {portfolio_url}: {str(e)}")
            return self._error_result(f"Analysis failed: {str(e)}")

    async def _fetch_portfolio(self, url: str) -> tuple:
        """
        Fetch portfolio with cascading fallback:
        1. Playwright (full featured, heavy) - if available
        2. requests-html (JS execution, lighter) - BEST for Render free tier
        3. aiohttp (no JS, fastest) - last resort

        Returns: (html_content, screenshot_url, viewport_data)
        """
        # Try Playwright first (best accuracy)
        if PLAYWRIGHT_AVAILABLE:
            try:
                return await self._fetch_with_playwright(url)
            except Exception as e:
                logger.warning(f"Playwright failed for {url}: {str(e)}, trying requests-html")

        # Try requests-html (good accuracy, lighter)
        if REQUESTS_HTML_AVAILABLE:
            try:
                return await self._fetch_with_requests_html(url)
            except Exception as e:
                logger.warning(f"requests-html failed for {url}: {str(e)}, falling back to aiohttp")

        # Last resort: aiohttp (no JS execution)
        return await self._fetch_with_aiohttp(url)

    async def _fetch_with_playwright(self, url: str) -> tuple:
        """Fetch portfolio using Playwright"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Navigate with timeout
                await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=settings.page_load_timeout * 1000
                )

                # Additional wait for React/Vue SPAs to fully render
                await page.wait_for_timeout(2000)

                # Get HTML content
                html_content = await page.content()

                # Test responsiveness
                viewport_data = await self._test_responsiveness(page)

                # Take screenshot if enabled
                screenshot = None
                if settings.enable_screenshot_capture:
                    screenshot_bytes = await page.screenshot(full_page=False)
                    # Here you could upload to S3 or save locally
                    # For now, just note that we have it
                    screenshot = "screenshot_captured"

                await browser.close()
                return html_content, screenshot, viewport_data

            except PlaywrightTimeout:
                logger.warning(f"Timeout loading {url}")
                await browser.close()
                return None, None, {}
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                await browser.close()
                return None, None, {}

    async def _fetch_with_requests_html(self, url: str) -> tuple:
        """
        Fetch portfolio using requests-html (lighter than Playwright)

        Pros:
        - Executes JavaScript (gets full rendered content)
        - Lighter than Playwright (~120MB vs 300MB)
        - Works on Render free tier
        - 85-90% accuracy for JS portfolios

        Returns: (html_content, screenshot_url, viewport_data)
        """
        session = None
        try:
            session = AsyncHTMLSession()
            response = await session.get(url, timeout=settings.page_load_timeout)

            # Render JavaScript (wait for React/Vue to load)
            await response.html.arender(sleep=2, timeout=settings.page_load_timeout)

            html_content = response.html.html

            # Close session
            await session.close()

            # No screenshot or viewport testing with requests-html
            return html_content, None, {}

        except asyncio.TimeoutError:
            logger.warning(f"Timeout loading {url} with requests-html")
            if session:
                await session.close()
            return None, None, {}
        except Exception as e:
            logger.error(f"Error fetching {url} with requests-html: {str(e)}")
            if session:
                await session.close()
            return None, None, {}

    async def _fetch_with_aiohttp(self, url: str) -> tuple:
        """Fetch portfolio using aiohttp (fallback when Playwright unavailable)"""
        try:
            timeout = aiohttp.ClientTimeout(total=settings.page_load_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status != 200:
                        logger.warning(f"Non-200 status code for {url}: {response.status}")
                        return None, None, {}

                    html_content = await response.text()

                    # No screenshot or responsiveness testing with aiohttp
                    return html_content, None, {}

        except asyncio.TimeoutError:
            logger.warning(f"Timeout loading {url} with aiohttp")
            return None, None, {}
        except Exception as e:
            logger.error(f"Error fetching {url} with aiohttp: {str(e)}")
            return None, None, {}

    async def _test_responsiveness(self, page) -> Dict[str, Any]:
        """Test portfolio at multiple viewport sizes"""
        viewports = {
            "mobile": {"width": 375, "height": 667},
            "tablet": {"width": 768, "height": 1024},
            "desktop": {"width": 1920, "height": 1080}
        }

        results = {}
        for device, viewport in viewports.items():
            try:
                await page.set_viewport_size(viewport)
                await page.wait_for_timeout(500)  # Let page adjust

                # Check for horizontal scrollbar
                has_scroll = await page.evaluate(
                    "document.body.scrollWidth > document.body.clientWidth"
                )

                results[device] = {
                    "width": viewport["width"],
                    "has_horizontal_scroll": has_scroll,
                    "passes": not has_scroll
                }
            except Exception as e:
                logger.warning(f"Viewport test failed for {device}: {str(e)}")
                results[device] = {"passes": False, "error": str(e)}

        return results

    async def _run_rubric_analysis(self, html_content: str, url: str) -> Dict[str, Any]:
        """Run rule-based rubric analysis"""
        try:
            checklist = self.rubric_engine.evaluate(html_content, url)
            return {"checklist": checklist}
        except Exception as e:
            logger.error(f"Rubric analysis error: {str(e)}")
            return {"checklist": {}}

    async def _run_ai_analysis(self, html_content: str) -> Dict[str, Any]:
        """Run AI analysis with fallback"""
        try:
            if not settings.enable_ai_analysis:
                return {"analysis": "AI analysis disabled", "provider": "None"}

            result = await self.ai_analyzer.analyze(html_content)
            return result
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            return {"analysis": "AI analysis failed", "provider": "None"}

    async def _run_image_analysis(self, html_content: str) -> Dict[str, Any]:
        """Find and validate profile images"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find potential profile images
            # Look in about section first
            about_keywords = ["about", "profile", "bio"]
            profile_img = None

            for keyword in about_keywords:
                section = soup.find(id=keyword) or soup.find(class_=keyword)
                if section:
                    img = section.find('img')
                    if img and img.get('src'):
                        profile_img = img.get('src')
                        break

            # Fallback: first image on page
            if not profile_img:
                first_img = soup.find('img')
                if first_img and first_img.get('src'):
                    profile_img = first_img.get('src')

            if profile_img:
                # Make absolute URL if relative
                if profile_img.startswith('/'):
                    # Would need base URL here
                    pass

                # Validate image
                validation_result = await self.image_validator.validate_image_url(profile_img)
                return validation_result
            else:
                return {
                    "exists": False,
                    "has_face": False,
                    "details": "No profile image found"
                }

        except Exception as e:
            logger.error(f"Image analysis error: {str(e)}")
            return {"exists": False, "details": str(e)}

    def _calculate_score(self, checklist: Dict[str, Dict]) -> int:
        """
        Calculate percentage score based on checklist
        Returns: 0-100
        """
        if not checklist:
            return 0

        total = len(checklist)
        passed = sum(1 for item in checklist.values() if item.get("pass", False))

        return round((passed / total) * 100) if total > 0 else 0

    def _generate_learning_resources(self, checklist: Dict[str, Dict]) -> List[Dict[str, str]]:
        """
        Generate learning resources based on failed checks
        Helps users understand HOW to improve
        """
        resources = []

        # Mapping of failed checks to learning resources
        resource_map = {
            "about_section": {
                "title": "Creating an Effective About Section",
                "description": "Learn how to write a compelling introduction that showcases your personality and skills.",
                "tips": [
                    "Include your name prominently",
                    "Add a professional photo",
                    "Write 2-3 paragraphs about your background and goals",
                    "Mention your key strengths and what makes you unique"
                ]
            },
            "projects_minimum": {
                "title": "Showcasing Your Projects",
                "description": "Quality projects are crucial. Aim for at least 3 well-documented projects.",
                "tips": [
                    "Include project title and clear description",
                    "Add screenshots or demo GIFs",
                    "List technologies used",
                    "Provide both GitHub and live demo links",
                    "Explain the problem your project solves"
                ]
            },
            "responsive_design": {
                "title": "Making Your Portfolio Responsive",
                "description": "Ensure your portfolio works on all devices with responsive design.",
                "tips": [
                    "Use CSS media queries for different screen sizes",
                    "Consider using frameworks like Tailwind CSS or Bootstrap",
                    "Test on mobile (375px), tablet (768px), and desktop (1920px)",
                    "Use relative units (%, rem, em) instead of fixed pixels"
                ]
            },
            "skills_highlighted": {
                "title": "Highlighting Your Skills",
                "description": "Make your technical skills easy to scan and visually appealing.",
                "tips": [
                    "Use icons for programming languages and tools",
                    "Group skills by category (Frontend, Backend, Tools, etc.)",
                    "Consider using progress bars or proficiency levels",
                    "Include both technical and soft skills"
                ]
            },
            "contact_section": {
                "title": "Making It Easy to Contact You",
                "description": "Recruiters need multiple ways to reach you.",
                "tips": [
                    "Add links to LinkedIn, GitHub, and Email",
                    "Consider adding a contact form",
                    "Include your location (city/country)",
                    "Ensure all social links open in new tabs"
                ]
            }
        }

        # Find failed checks and add relevant resources
        for key, value in checklist.items():
            if not value.get("pass", False):
                # Map specific checks to resource categories
                resource_key = None
                if key.startswith("about_"):
                    resource_key = "about_section"
                elif key.startswith("projects_"):
                    if key == "projects_minimum":
                        resource_key = "projects_minimum"
                    else:
                        resource_key = "projects_minimum"  # Same resource
                elif key.startswith("skills_"):
                    resource_key = "skills_highlighted"
                elif key.startswith("contact_"):
                    resource_key = "contact_section"
                elif key == "responsive_design":
                    resource_key = "responsive_design"

                if resource_key and resource_key in resource_map:
                    resource = resource_map[resource_key]
                    if resource not in resources:  # Avoid duplicates
                        resources.append(resource)

        # Limit to top 3 most important resources
        return resources[:3]

    def _error_result(self, message: str) -> Dict[str, Any]:
        """Return error result structure"""
        return {
            "error": True,
            "message": message,
            "checklist": {},
            "score": 0,
            "analysis_time": 0
        }

    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all analysis providers"""
        return {
            "ai_providers": self.ai_analyzer.get_provider_status(),
            "face_detection": self.image_validator.get_status(),
            "caching": {
                "enabled": settings.enable_caching,
                **(await cache_service.get_cache_stats())
            }
        }
