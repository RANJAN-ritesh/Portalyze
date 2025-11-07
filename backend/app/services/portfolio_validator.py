from typing import Dict, Any, List, Set
from bs4 import BeautifulSoup
import re
from app.services.pattern_analyzer import PortfolioPatternAnalyzer
import requests
from urllib.parse import urlparse, urljoin
import asyncio
import logging
from functools import lru_cache

# Try to import Playwright (optional dependency)
try:
    from playwright.async_api import async_playwright, TimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    TimeoutError = TimeoutError  # Use built-in TimeoutError
    print("⚠️  Playwright not available in portfolio_validator")

# Try to import CV2 (optional dependency)
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️  OpenCV not available - face detection disabled")

class PortfolioValidator:
    def __init__(self):
        self.pattern_analyzer = PortfolioPatternAnalyzer()
        self.logger = logging.getLogger(__name__)
        # Load face detection model (if opencv is available)
        if CV2_AVAILABLE:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        else:
            self.face_cascade = None
        
    @lru_cache(maxsize=100)
    def _is_valid_profile_image(self, img_url: str) -> bool:
        """Check if image exists and contains a face (cached)."""
        try:
            # Quick check: HEAD request for existence
            response = requests.head(img_url, timeout=5)
            if response.status_code != 200:
                return False
            
            # If quick check passes, verify with face detection
            response = requests.get(img_url, timeout=5)
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                return False
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces with balanced parameters
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=4,
                minSize=(30, 30)
            )
            
            # Return True if at least one face is detected
            return len(faces) > 0
            
        except Exception as e:
            self.logger.error(f"Error validating image: {str(e)}")
            return False

    async def validate_portfolio(self, url: str) -> Dict[str, Any]:
        """Validate a portfolio against all criteria."""
        try:
            # Fetch and parse portfolio
            content = await self._fetch_portfolio(url)
            soup = BeautifulSoup(content, 'html.parser')
            
            # Run all validations
            validation_results = {
                "basic_sections": self._check_basic_sections(soup),
                "about_section": self._check_about_section(soup, url),
                "projects_section": self._check_projects_section(soup),
                "skills_section": self._check_skills_section(soup),
                "contact_section": self._check_contact_section(soup),
                "links": self._check_links(soup),
                "responsiveness": await self._check_responsiveness(url),
                "url_professionalism": self._check_url_professionalism(url),
                "design": self._check_design(soup),
                "external_links": self._check_external_links(soup)
            }
            
            # Generate summary
            summary = self._generate_summary(validation_results)
            
            return {
                "validation_results": validation_results,
                "summary": summary,
                "score": self._calculate_score(validation_results)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating portfolio: {str(e)}")
            # Return a default structure with empty results
            return {
                "validation_results": {
                    "basic_sections": {"has_all_sections": False, "missing_sections": [], "found_sections": []},
                    "about_section": {"has_name": False, "has_photo": False, "has_intro": False, "is_complete": False},
                    "projects_section": {"is_complete": False, "project_count": 0, "project_details": []},
                    "skills_section": {"is_complete": False, "skill_count": 0, "has_tech_stack": False},
                    "contact_section": {"is_complete": False, "has_linkedin": False, "has_github": False, "has_form": False},
                    "links": {"is_complete": False, "total_links": 0, "broken_links": [], "link_details": []},
                    "responsiveness": {"is_responsive": False, "mobile_ok": False, "tablet_ok": False, "mobile_issues": [], "tablet_issues": []},
                    "url_professionalism": {"is_professional": False, "is_hosting_service": False, "has_professional_path": False},
                    "design": {"is_complete": False, "has_navbar": False, "has_font_issues": False, "has_padding_issues": False, "has_animation_issues": False},
                    "external_links": {"is_complete": False, "total_external_links": 0, "links_without_target": []}
                },
                "summary": f"Error validating portfolio: {str(e)}",
                "score": 0
            }
    
    async def _fetch_portfolio(self, url: str) -> str:
        """Fetch portfolio content using Playwright."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_selector('body', timeout=10000)
                return await page.content()
            finally:
                await browser.close()
    
    def _check_basic_sections(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check if portfolio has all required sections."""
        sections = self.pattern_analyzer.analyze_portfolio(str(soup))
        umbrella_sections = sections.get("umbrella_sections", {})
        
        required_sections = {'about', 'skills', 'projects', 'contact'}
        found_sections = set(umbrella_sections.keys())
        
        return {
            "has_all_sections": required_sections.issubset(found_sections),
            "missing_sections": list(required_sections - found_sections),
            "found_sections": list(found_sections)
        }
    
    def _normalize_text(self, text: str) -> str:
        import unicodedata
        text = unicodedata.normalize('NFKC', text)
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()

    def _find_photo_in_sections(self, soup: BeautifulSoup, section_candidates: list, base_url: str) -> bool:
        """Find photo in given sections."""
        for section in section_candidates:
            if not section:
                continue
                
            # Check for <img> tags
            for img in section.find_all('img'):
                src = img.get('src', '')
                if src:
                    try:
                        # Handle relative URLs
                        if src.startswith('./'):
                            src = src[2:]  # Remove './'
                        if src.startswith('/'):
                            src = src[1:]  # Remove leading '/'
                        photo_url = urljoin(base_url, src)
                        self.logger.info(f"Checking image URL: {photo_url}")
                        if self._is_valid_profile_image(photo_url):
                            self.logger.info(f"Found valid photo in section: {section.get('id', section.get('class', ['unknown']))}")
                            return True
                    except Exception as e:
                        self.logger.error(f"Error processing image URL {src}: {str(e)}")
            
            # Check for background images
            for el in section.find_all(True):
                style = el.get('style', '')
                if 'background-image' in style:
                    match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                    if match:
                        try:
                            bg_url = match.group(1)
                            # Handle relative URLs
                            if bg_url.startswith('./'):
                                bg_url = bg_url[2:]  # Remove './'
                            if bg_url.startswith('/'):
                                bg_url = bg_url[1:]  # Remove leading '/'
                            photo_url = urljoin(base_url, bg_url)
                            self.logger.info(f"Checking background image URL: {photo_url}")
                            if self._is_valid_profile_image(photo_url):
                                self.logger.info(f"Found valid background photo in section: {section.get('id', section.get('class', ['unknown']))}")
                                return True
                        except Exception as e:
                            self.logger.error(f"Error processing background image URL {match.group(1)}: {str(e)}")
        
        return False

    def _check_about_section(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Robustly check about section content."""
        # Try to find home/hero section first
        home_section = None
        for id_or_class in [r'home', r'hero', r'landing', r'main', r'header', r'intro', r'welcome']:
            home_section = soup.find(id=re.compile(id_or_class, re.I))
            if home_section:
                break
            home_section = soup.find(class_=re.compile(id_or_class, re.I))
            if home_section:
                break
        
        # If no home section found by id/class, try to find it by content
        if not home_section:
            for section in soup.find_all(['section', 'div', 'header']):
                text = self._normalize_text(section.get_text())
                if re.search(r'(hi|hello|welcome|i\'m|i am|my name is)', text, re.I):
                    home_section = section
                    break
        
        # Try to find about section
        about_section = None
        for id_or_class in [r'about', r'about-me', r'about_me']:
            about_section = soup.find(id=re.compile(id_or_class, re.I))
            if about_section:
                break
            about_section = soup.find(class_=re.compile(id_or_class, re.I))
            if about_section:
                break
        
        # Fallback: look for section with 'about' in text
        if not about_section:
            for section in soup.find_all(['section', 'div']):
                if re.search(r'about', section.get_text(), re.I):
                    about_section = section
                    break
        
        # Fallback: use body if no sections found
        if not about_section:
            about_section = soup.body

        # Normalize all text in section
        section_text = self._normalize_text(about_section.get_text() if about_section else '')

        # Name: look for any heading, paragraph, or div with a likely name pattern
        has_name = False
        for tag in about_section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div']):
            tag_text = self._normalize_text(tag.get_text())
            if re.search(r"(hello|hi|i'm|i am|my name is|about me)[^a-zA-Z]*[a-zA-Z]{3,}", tag_text):
                has_name = True
                break
        # Fallback: look for a capitalized word sequence in section text
        if not has_name and re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', about_section.get_text()):
            has_name = True

        # Photo: check both home and about sections
        section_candidates = []
        if home_section:
            section_candidates.append(home_section)
        if about_section:
            section_candidates.append(about_section)
        
        # If no sections found, try the first section or header
        if not section_candidates:
            first_section = soup.find(['section', 'header'])
            if first_section:
                section_candidates.append(first_section)
        
        has_photo = self._find_photo_in_sections(soup, section_candidates, base_url)

        # Introduction: any paragraph/div with >50 chars
        has_intro = False
        for tag in about_section.find_all(['p', 'div']):
            tag_text = self._normalize_text(tag.get_text())
            if len(tag_text) > 50:
                has_intro = True
                break
        # Fallback: section text
        if not has_intro and len(section_text) > 50:
            has_intro = True

        return {
            "has_name": has_name,
            "has_photo": has_photo,
            "has_intro": has_intro,
            "is_complete": all([has_name, has_photo, has_intro])
        }
    
    def _check_projects_section(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Robustly check projects section content."""
        # Find projects section
        projects_section = None
        for id_or_class in [r'projects', r'portfolio', r'work', r'showcase']:
            projects_section = soup.find(id=re.compile(id_or_class, re.I))
            if projects_section:
                break
            projects_section = soup.find(class_=re.compile(id_or_class, re.I))
            if projects_section:
                break
        if not projects_section:
            for section in soup.find_all(['section', 'div']):
                if re.search(r'projects|portfolio|work|showcase', section.get_text(), re.I):
                    projects_section = section
                    break
        if not projects_section:
            return {"is_complete": False, "details": "Projects section not found"}

        # Improved project detection
        project_cards = []
        for card in projects_section.find_all(['div', 'article', 'section']):
            # Check if card has project-like content
            has_title = bool(card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            has_description = len(self._normalize_text(card.get_text())) > 50
            has_links = bool(card.find_all('a', href=True))
            has_tech_stack = bool(re.search(r'tech|stack|technologies|built with|using', card.get_text(), re.I))
            
            if has_title and has_description and has_links:
                project_cards.append(card)

        return {
            "is_complete": len(project_cards) >= 2,
            "project_count": len(project_cards),
            "project_details": [self._normalize_text(card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']).get_text())[:60] for card in project_cards[:5]]
        }
    
    def _check_skills_section(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Robustly check skills section content."""
        skills_section = None
        for id_or_class in [r'skills', r'tech-stack', r'technologies', r'expertise']:
            skills_section = soup.find(id=re.compile(id_or_class, re.I))
            if skills_section:
                break
            skills_section = soup.find(class_=re.compile(id_or_class, re.I))
            if skills_section:
                break
        if not skills_section:
            for section in soup.find_all(['section', 'div']):
                if re.search(r'skills|tech|technology|expertise', section.get_text(), re.I):
                    skills_section = section
                    break
        if not skills_section:
            return {"is_complete": False, "details": "Skills section not found"}
        # Accept any list/grid of skills
        items = skills_section.find_all(['li', 'span', 'div'])
        skill_items = [i for i in items if 2 < len(self._normalize_text(i.get_text())) < 40]
        return {
            "is_complete": len(skill_items) >= 3,
            "skill_count": len(skill_items),
            "has_tech_stack": True
        }
    
    def _check_contact_section(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check contact section content."""
        contact_section = soup.find(id=re.compile(r'contact|get-in-touch', re.I))
        if not contact_section:
            contact_section = soup.find(class_=re.compile(r'contact|get-in-touch', re.I))
        
        if not contact_section:
            return {"is_complete": False, "details": "Contact section not found"}
        
        has_linkedin = bool(contact_section.find('a', href=re.compile(r'linkedin.com', re.I)))
        has_github = bool(contact_section.find('a', href=re.compile(r'github.com', re.I)))
        has_form = bool(contact_section.find('form'))
        
        return {
            "is_complete": has_linkedin and has_github,
            "has_linkedin": has_linkedin,
            "has_github": has_github,
            "has_form": has_form
        }
    
    def _check_links(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check if all links are working (robust, tolerant)."""
        links = soup.find_all('a', href=True)
        broken_links = []
        link_details = []
        for link in links:
            href = link['href']
            link_text = link.get_text(strip=True) or href
            section = link.find_parent(['section', 'div', 'nav'])
            section_name = "Unknown"
            if section:
                section_id = section.get('id', '')
                section_class = section.get('class', [])
                if section_id:
                    section_name = section_id
                elif section_class:
                    section_name = section_class[0]
            if href.startswith('http'):
                try:
                    # For LinkedIn, always accept as valid if present
                    if 'linkedin.com' in href:
                        link_details.append({
                            "url": href,
                            "text": link_text,
                            "section": section_name,
                            "status": "assumed working (LinkedIn)"
                        })
                        continue
                    response = requests.head(href, timeout=5, allow_redirects=True)
                    if response.status_code >= 400:
                        broken_links.append(href)
                        link_details.append({
                            "url": href,
                            "text": link_text,
                            "section": section_name,
                            "status": response.status_code
                        })
                except Exception as e:
                    # Only flag as broken if not LinkedIn
                    if 'linkedin.com' not in href:
                        broken_links.append(href)
                        link_details.append({
                            "url": href,
                            "text": link_text,
                            "section": section_name,
                            "error": str(e)
                        })
        return {
            "total_links": len(links),
            "broken_links": broken_links,
            "link_details": link_details,
            "is_complete": len(broken_links) == 0
        }
    
    async def _check_responsiveness(self, url: str) -> Dict[str, Any]:
        """Check if portfolio is responsive."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            try:
                # Check mobile view
                await page.set_viewport_size({"width": 375, "height": 667})
                await page.goto(url)
                mobile_issues = await page.evaluate("""() => {
                    const issues = [];
                    const elements = document.querySelectorAll('*');
                    elements.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 375) {
                            issues.push({
                                element: el.tagName,
                                class: el.className,
                                width: rect.width
                            });
                        }
                    });
                    return issues;
                }""")
                
                # Check tablet view
                await page.set_viewport_size({"width": 768, "height": 1024})
                await page.goto(url)
                tablet_issues = await page.evaluate("""() => {
                    const issues = [];
                    const elements = document.querySelectorAll('*');
                    elements.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 768) {
                            issues.push({
                                element: el.tagName,
                                class: el.className,
                                width: rect.width
                            });
                        }
                    });
                    return issues;
                }""")
                
                return {
                    "is_responsive": len(mobile_issues) == 0 and len(tablet_issues) == 0,
                    "mobile_ok": len(mobile_issues) == 0,
                    "tablet_ok": len(tablet_issues) == 0,
                    "mobile_issues": mobile_issues,
                    "tablet_issues": tablet_issues
                }
            finally:
                await browser.close()
    
    def _check_url_professionalism(self, url: str) -> Dict[str, Any]:
        """Check if portfolio URL is professional."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Accept github.io, netlify.app, vercel.app, etc. if path is professional
        is_hosting_service = any(service in parsed.netloc for service in ['github.io', 'netlify.app', 'vercel.app'])
        has_professional_path = bool(re.match(r'^[a-zA-Z0-9-]+$', path))
        
        return {
            "is_professional": has_professional_path,  # Only check path professionalism
            "is_hosting_service": is_hosting_service,
            "has_professional_path": has_professional_path
        }
    
    def _check_design(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check for design issues."""
        has_navbar = bool(soup.find(['nav', 'header']))
        has_font_issues = bool(soup.find(style=re.compile(r'font-family|font-size', re.I)))
        has_padding_issues = bool(soup.find(style=re.compile(r'padding|margin', re.I)))
        has_animation_issues = bool(soup.find(style=re.compile(r'animation|transition', re.I)))
        
        return {
            "has_navbar": has_navbar,
            "has_font_issues": has_font_issues,
            "has_padding_issues": has_padding_issues,
            "has_animation_issues": has_animation_issues,
            "is_complete": has_navbar and not any([
                has_font_issues,
                has_padding_issues,
                has_animation_issues
            ])
        }
    
    def _check_external_links(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check if external links open in new tab."""
        external_links = soup.find_all('a', href=re.compile(r'^https?://'))
        links_without_target = []
        
        for link in external_links:
            href = link['href']
            link_text = link.get_text(strip=True) or href
            if not link.get('target') == '_blank':
                links_without_target.append({
                    "url": href,
                    "text": link_text,
                    "section": self._get_section_name(link)
                })
        
        return {
            "total_external_links": len(external_links),
            "links_without_target": links_without_target,
            "is_complete": len(links_without_target) == 0
        }
    
    def _get_section_name(self, element) -> str:
        """Get the name of the section containing an element."""
        section = element.find_parent(['section', 'div', 'nav'])
        if section:
            section_id = section.get('id', '')
            section_class = section.get('class', [])
            if section_id:
                return section_id
            elif section_class:
                return section_class[0]
        return "Unknown"
    
    def _generate_summary(self, validation_results: Dict[str, Any]) -> str:
        """Generate a human-readable summary of validation results."""
        summary = []
        
        # Basic sections
        if validation_results["basic_sections"]["has_all_sections"]:
            summary.append("✅ All required sections (About, Skills, Projects, Contact) are present.")
        else:
            missing = ", ".join(validation_results["basic_sections"]["missing_sections"])
            summary.append(f"❌ Missing sections: {missing}")
        
        # About section
        about = validation_results["about_section"]
        if about["is_complete"]:
            summary.append("✅ About section includes name, photo (in home/about), and introduction.")
        else:
            missing = []
            if not about["has_name"]: missing.append("name")
            if not about["has_photo"]: missing.append("photo (in home or about section)")
            if not about["has_intro"]: missing.append("introduction")
            summary.append(f"❌ About section is missing: {', '.join(missing)}")
        
        # Projects section
        projects = validation_results["projects_section"]
        if projects["is_complete"]:
            summary.append(f"✅ Projects section includes {projects['project_count']} projects with required details.")
        else:
            summary.append("❌ Projects section is incomplete or missing.")
        
        # Skills section
        skills = validation_results["skills_section"]
        if skills["is_complete"]:
            summary.append(f"✅ Skills section includes {skills['skill_count']} skills with tech stack.")
        else:
            summary.append("❌ Skills section is incomplete or missing.")
        
        # Contact section
        contact = validation_results["contact_section"]
        if contact["is_complete"]:
            summary.append("✅ Contact section includes LinkedIn and GitHub links.")
        else:
            missing = []
            if not contact["has_linkedin"]: missing.append("LinkedIn")
            if not contact["has_github"]: missing.append("GitHub")
            summary.append(f"❌ Contact section is missing: {', '.join(missing)}")
        
        # Links
        links = validation_results["links"]
        if links["is_complete"]:
            summary.append("✅ All links are working correctly.")
        else:
            summary.append(f"❌ Found {len(links['broken_links'])} broken links:")
            for link in links["link_details"]:
                section_info = f" in {link['section']}" if link['section'] != "Unknown" else ""
                summary.append(f"   - {link['text']} ({link['url']}){section_info}: {link.get('status', link.get('error', 'Unknown error'))}")
        
        # Responsiveness
        responsiveness = validation_results["responsiveness"]
        if responsiveness["is_responsive"]:
            summary.append("✅ Portfolio is responsive on mobile and tablet devices.")
        else:
            if not responsiveness["mobile_ok"]:
                summary.append("❌ Mobile responsiveness issues:")
                for issue in responsiveness["mobile_issues"]:
                    summary.append(f"   - {issue['element']} ({issue['class']}): width {issue['width']}px")
            if not responsiveness["tablet_ok"]:
                summary.append("❌ Tablet responsiveness issues:")
                for issue in responsiveness["tablet_issues"]:
                    summary.append(f"   - {issue['element']} ({issue['class']}): width {issue['width']}px")
        
        # URL
        url = validation_results["url_professionalism"]
        if url["is_professional"]:
            summary.append("✅ Portfolio URL is professional.")
        else:
            summary.append("❌ Portfolio URL path could be more professional.")
        
        # Design
        design = validation_results["design"]
        if design["is_complete"]:
            summary.append("✅ Design is clean with no issues.")
        else:
            issues = []
            if not design["has_navbar"]: issues.append("navbar")
            if design["has_font_issues"]: issues.append("fonts")
            if design["has_padding_issues"]: issues.append("spacing")
            if design["has_animation_issues"]: issues.append("animations")
            summary.append(f"❌ Design issues with: {', '.join(issues)}")
        
        # External links
        external = validation_results["external_links"]
        if external["is_complete"]:
            summary.append("✅ All external links open in new tabs.")
        else:
            summary.append(f"❌ {len(external['links_without_target'])} external links don't open in new tabs:")
            for link in external["links_without_target"]:
                section_info = f" in {link['section']}" if link['section'] != "Unknown" else ""
                summary.append(f"   - {link['text']} ({link['url']}){section_info}")
        
        return "\n".join(summary)
    
    def _calculate_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall portfolio score."""
        weights = {
            "basic_sections": 0.15,
            "about_section": 0.10,
            "projects_section": 0.20,
            "skills_section": 0.10,
            "contact_section": 0.10,
            "links": 0.05,
            "responsiveness": 0.10,
            "url_professionalism": 0.05,
            "design": 0.05,
            "external_links": 0.05
        }
        
        score = 0
        for key, weight in weights.items():
            if validation_results[key].get("is_complete", False):
                score += weight
        
        return round(score * 100, 2) 