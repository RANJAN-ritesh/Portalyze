"""
Main Portfolio Analyzer
Coordinates all analysis services: web scraping, AI, rubrics, face detection
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup

# No browser dependencies needed - using cloud rendering!

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
        Smart portfolio fetcher:
        - Uses aiohttp (0MB, instant)
        - Detects JS-only sites automatically
        - Uses Google Rendertron (free cloud service) for JS rendering
        - No local browser needed!

        Returns: (html_content, screenshot_url, viewport_data)
        """
        return await self._fetch_with_aiohttp(url)

    async def _fetch_with_aiohttp(self, url: str) -> tuple:
        """
        Smart aiohttp fetcher with JS detection and cloud rendering fallback

        Strategy:
        1. Fetch with aiohttp (fast, 0MB)
        2. Detect if JS-only (empty <body> or just <div id="root">)
        3. If JS-only, use free cloud rendering service
        4. If static HTML, return as-is
        """
        try:
            timeout = aiohttp.ClientTimeout(total=settings.page_load_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try normal fetch first
                async with session.get(url, allow_redirects=True) as response:
                    if response.status != 200:
                        logger.warning(f"Non-200 status code for {url}: {response.status}")
                        return None, None, {}

                    html_content = await response.text()

                    # Detect if this is a JS-only site (React/Vue/Next.js skeleton)
                    if self._is_js_only_site(html_content):
                        logger.info(f"Detected JS-only site: {url}, trying smart extraction methods")

                        # Method 1: Check for SSR data (Next.js, Nuxt, etc.) - FASTEST & BEST
                        ssr_html = self._extract_ssr_data(html_content)
                        if ssr_html:
                            logger.info(f"Successfully extracted SSR data for {url}")
                            return ssr_html, None, {}

                        # Method 2: Extract from JS bundles - SLOWER but works for CSR
                        logger.info(f"No SSR data found, extracting from JS bundles")
                        enhanced_html = await self._extract_from_js_bundles(html_content, url, session, timeout)
                        if enhanced_html:
                            logger.info(f"Successfully extracted content from JS bundles for {url}")
                            return enhanced_html, None, {}
                        else:
                            logger.warning(f"Could not extract JS content, using skeleton HTML")

                    # Return original HTML (either static or fallback if rendering failed)
                    return html_content, None, {}

        except asyncio.TimeoutError:
            logger.warning(f"Timeout loading {url} with aiohttp")
            return None, None, {}
        except Exception as e:
            logger.error(f"Error fetching {url} with aiohttp: {str(e)}")
            return None, None, {}

    def _is_js_only_site(self, html: str) -> bool:
        """
        Detect if a site is JS-only (React/Vue/Next.js)

        Indicators:
        - Very short HTML (<2000 chars)
        - Has <div id="root"> or <div id="app">
        - Has <script src="...main.js">
        - Body has almost no content
        """
        if len(html) > 5000:
            return False  # Likely has content

        html_lower = html.lower()

        # Check for common JS framework patterns
        js_indicators = [
            '<div id="root"',
            '<div id="app"',
            '<div id="__next"',  # Next.js
            'react-root',
            'vue-app',
            '/static/js/main.',
            '/static/js/bundle.'
        ]

        has_js_indicator = any(indicator in html_lower for indicator in js_indicators)

        # Check if body is basically empty
        body_start = html_lower.find('<body')
        body_end = html_lower.find('</body>')

        if body_start > 0 and body_end > body_start:
            body_content = html_lower[body_start:body_end]
            # Remove scripts and links
            body_content = body_content.replace('<script', '').replace('<link', '')
            body_text_length = len(body_content.strip())

            # If body is less than 500 chars after removing scripts/links, it's probably JS-only
            is_empty_body = body_text_length < 500

            return has_js_indicator and is_empty_body

        return has_js_indicator

    def _extract_ssr_data(self, html: str) -> str:
        """
        Extract Server-Side Rendered data from HTML

        Many modern frameworks embed data in the HTML:
        - Next.js: <script id="__NEXT_DATA__">
        - Nuxt: <script>window.__NUXT__=
        - React: window.__INITIAL_STATE__
        - Vue: window.__VUE_SSR_CONTEXT__

        This is MUCH better than parsing JS bundles!
        """
        import json
        import re

        try:
            # Method 1: Next.js __NEXT_DATA__ (most common)
            next_data_pattern = r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>'
            match = re.search(next_data_pattern, html, re.DOTALL)

            if match:
                try:
                    data = json.loads(match.group(1))
                    logger.info("Found Next.js SSR data!")
                    return self._build_html_from_nextjs_data(html, data)
                except:
                    pass

            # Method 2: Nuxt __NUXT__ data
            nuxt_pattern = r'window\.__NUXT__\s*=\s*({.*?});'
            match = re.search(nuxt_pattern, html, re.DOTALL)

            if match:
                try:
                    data = json.loads(match.group(1))
                    logger.info("Found Nuxt SSR data!")
                    return self._build_html_from_nuxt_data(html, data)
                except:
                    pass

            # Method 3: Generic __INITIAL_STATE__
            state_pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
            match = re.search(state_pattern, html, re.DOTALL)

            if match:
                try:
                    data = json.loads(match.group(1))
                    logger.info("Found React SSR data!")
                    return self._build_html_from_state_data(html, data)
                except:
                    pass

            # Method 4: Check for script tags with type="application/json"
            json_pattern = r'<script[^>]*type="application/json"[^>]*>(.*?)</script>'
            matches = re.findall(json_pattern, html, re.DOTALL)

            for json_str in matches:
                try:
                    data = json.loads(json_str)
                    if isinstance(data, dict) and len(data) > 0:
                        logger.info("Found embedded JSON data!")
                        return self._build_html_from_generic_data(html, data)
                except:
                    continue

            return None

        except Exception as e:
            logger.error(f"Error extracting SSR data: {str(e)}")
            return None

    def _build_html_from_nextjs_data(self, html: str, data: dict) -> str:
        """Build HTML from Next.js __NEXT_DATA__"""
        try:
            # Next.js structure: data.props.pageProps usually has content
            page_props = data.get('props', {}).get('pageProps', {})

            # Extract any text content from the data
            all_text = self._extract_text_from_dict(page_props)

            if all_text:
                return self._build_synthetic_html(html, all_text)

            return None
        except:
            return None

    def _build_html_from_nuxt_data(self, html: str, data: dict) -> str:
        """Build HTML from Nuxt __NUXT__ data"""
        try:
            all_text = self._extract_text_from_dict(data)

            if all_text:
                return self._build_synthetic_html(html, all_text)

            return None
        except:
            return None

    def _build_html_from_state_data(self, html: str, data: dict) -> str:
        """Build HTML from generic state data"""
        try:
            all_text = self._extract_text_from_dict(data)

            if all_text:
                return self._build_synthetic_html(html, all_text)

            return None
        except:
            return None

    def _build_html_from_generic_data(self, html: str, data: dict) -> str:
        """Build HTML from generic JSON data"""
        return self._build_html_from_state_data(html, data)

    def _extract_text_from_dict(self, obj, depth=0, max_depth=10) -> list:
        """Recursively extract meaningful text from nested dict/list"""
        if depth > max_depth:
            return []

        texts = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                # Key itself might be meaningful
                if isinstance(key, str) and len(key) > 3:
                    texts.append(key)

                # Recurse into value
                texts.extend(self._extract_text_from_dict(value, depth+1, max_depth))

        elif isinstance(obj, list):
            for item in obj:
                texts.extend(self._extract_text_from_dict(item, depth+1, max_depth))

        elif isinstance(obj, str):
            # Keep meaningful strings only
            if len(obj) > 5 and not obj.startswith('http') and not obj.startswith('/'):
                # Filter out code/technical strings
                if not any(bad in obj.lower() for bad in ['function', 'return', 'import', '=>', 'const']):
                    texts.append(obj)

        return texts

    async def _extract_from_js_bundles(self, html: str, base_url: str, session, timeout) -> str:
        """
        Extract content from JavaScript bundles for React/Vue/Next.js sites

        Strategy:
        1. Find all <script src="..."> tags
        2. Fetch the JS bundles
        3. Extract text content using regex
        4. Build synthetic HTML with extracted content

        This works because React/Vue apps have all content embedded in JS bundles!
        """
        try:
            from urllib.parse import urljoin
            import re

            # Find all script tags
            script_pattern = r'<script[^>]+src="([^"]+)"'
            script_urls = re.findall(script_pattern, html)

            all_content = []

            # Fetch and parse each JS bundle
            for script_url in script_urls[:5]:  # Limit to first 5 scripts
                try:
                    full_url = urljoin(base_url, script_url)
                    logger.info(f"Fetching JS bundle: {full_url}")

                    async with session.get(full_url, timeout=timeout) as js_response:
                        if js_response.status == 200:
                            js_content = await js_response.text()

                            # Extract text content from JS
                            extracted = self._parse_js_content(js_content)
                            all_content.extend(extracted)

                except Exception as e:
                    logger.warning(f"Error fetching JS bundle {script_url}: {str(e)}")
                    continue

            if not all_content:
                return None

            # Build synthetic HTML with extracted content
            synthetic_html = self._build_synthetic_html(html, all_content)
            return synthetic_html

        except Exception as e:
            logger.error(f"Error extracting from JS bundles: {str(e)}")
            return None

    def _parse_js_content(self, js_code: str) -> list:
        """
        Extract meaningful text content from JavaScript code

        Looks for:
        - String literals with actual content
        - Object properties that look like content
        - Text between quotes that's longer than 10 chars
        """
        import re

        extracted = []

        # Pattern 1: Find strings in quotes (common in JSX)
        # Matches: "About Me", "My Projects", "Contact", etc.
        string_pattern = r'["\']([A-Z][a-zA-Z0-9\s,.\-!?()]{10,200})["\']'
        matches = re.findall(string_pattern, js_code)

        for match in matches:
            # Filter out code-looking strings
            if not any(bad in match for bad in ['function', 'return', 'import', 'export', 'const', 'var', 'let', '=>']):
                extracted.append(match.strip())

        # Pattern 2: Find URLs (linkedin, github, etc.)
        url_pattern = r'https?://[a-zA-Z0-9\-\.]+\.[a-z]{2,}(?:/[^\s"\']*)?'
        urls = re.findall(url_pattern, js_code)
        extracted.extend(urls)

        # Pattern 3: Find email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, js_code)
        extracted.extend(emails)

        # Remove duplicates and very short strings
        unique_content = list(set([x for x in extracted if len(x) > 5]))

        return unique_content[:100]  # Limit to avoid memory issues

    def _build_synthetic_html(self, original_html: str, extracted_content: list) -> str:
        """
        Build a synthetic HTML document with extracted content

        This creates sections based on keywords found in the content
        """
        # Categorize content
        about_content = []
        project_content = []
        skill_content = []
        contact_content = []
        other_content = []

        about_keywords = ['about', 'developer', 'engineer', 'designer', 'student', 'graduate', 'experience']
        project_keywords = ['project', 'built', 'created', 'developed', 'application', 'website', 'app']
        skill_keywords = ['react', 'javascript', 'python', 'java', 'css', 'html', 'node', 'angular', 'vue', 'typescript']
        contact_keywords = ['linkedin', 'github', 'email', 'contact', '@', 'https://']

        for content in extracted_content:
            content_lower = content.lower()

            if any(kw in content_lower for kw in contact_keywords):
                contact_content.append(content)
            elif any(kw in content_lower for kw in skill_keywords):
                skill_content.append(content)
            elif any(kw in content_lower for kw in project_keywords):
                project_content.append(content)
            elif any(kw in content_lower for kw in about_keywords):
                about_content.append(content)
            else:
                other_content.append(content)

        # Build synthetic HTML
        synthetic_body = ['<div id="root">']

        if about_content:
            synthetic_body.append('<section id="about" class="about-section">')
            for text in about_content[:5]:
                synthetic_body.append(f'<p>{text}</p>')
            synthetic_body.append('</section>')

        if project_content:
            synthetic_body.append('<section id="projects" class="projects-section">')
            for text in project_content[:10]:
                synthetic_body.append(f'<div class="project"><h3>{text}</h3></div>')
            synthetic_body.append('</section>')

        if skill_content:
            synthetic_body.append('<section id="skills" class="skills-section">')
            for text in skill_content[:15]:
                synthetic_body.append(f'<span class="skill">{text}</span>')
            synthetic_body.append('</section>')

        if contact_content:
            synthetic_body.append('<section id="contact" class="contact-section">')
            for text in contact_content[:10]:
                if 'http' in text:
                    synthetic_body.append(f'<a href="{text}" target="_blank">{text}</a>')
                else:
                    synthetic_body.append(f'<p>{text}</p>')
            synthetic_body.append('</section>')

        synthetic_body.append('</div>')

        # Replace the empty body in original HTML
        body_html = '\n'.join(synthetic_body)
        enhanced_html = original_html.replace('<div id="root"></div>', body_html)

        return enhanced_html

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
