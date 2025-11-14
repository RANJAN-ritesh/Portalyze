"""
Rubric Engine - Rule-based grading system
27 parameters across 5 categories with detailed feedback
"""

import logging
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class RubricEngine:
    """
    Comprehensive rubric-based grading system
    Evaluates portfolios against 27 specific parameters
    """

    def __init__(self):
        self.tech_keywords = [
            "react", "javascript", "typescript", "css", "html", "node", "express",
            "mongo", "mysql", "postgres", "tailwind", "chakra", "bootstrap",
            "material-ui", "redux", "next", "vite", "webpack", "sass", "vue",
            "angular", "python", "django", "flask", "java", "spring", "docker",
            "kubernetes", "aws", "azure", "gcp"
        ]

        self.section_keywords = {
            "about": ["about", "aboutme", "about-me", "about_me", "bio", "biography", "introduction", "intro", "profile", "whoami", "who-am-i"],
            "projects": ["project", "projects", "portfolio", "work", "works", "case", "cases", "showcase", "my-work", "mywork", "my-projects"],
            "skills": ["skill", "skills", "tech", "techstack", "tech-stack", "stack", "expertise", "technologies", "technology", "toolset", "abilities"],
            "contact": ["contact", "contacts", "reach", "reachout", "reach-out", "connect", "getintouch", "get-in-touch", "social", "touch", "contactme", "contact-me"]
        }

    def evaluate(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Main evaluation method - runs all 27 checks

        Returns:
            Complete checklist with pass/fail and details for each parameter
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Initialize checklist structure
        checklist = self._initialize_checklist()

        # Run all evaluations
        self._evaluate_about_section(soup, checklist)
        self._evaluate_projects_section(soup, checklist)
        self._evaluate_skills_section(soup, checklist)
        self._evaluate_contact_section(soup, checklist)
        self._evaluate_technical(soup, html_content, url, checklist)

        return checklist

    def _initialize_checklist(self) -> Dict[str, Dict]:
        """Initialize checklist with all 27 parameters"""
        params = [
            # About (5)
            "about_section", "about_name", "about_photo", "about_intro",
            "about_professional_photo",
            # Projects (9)
            "projects_section", "projects_minimum", "projects_samples",
            "projects_deployed", "projects_links", "projects_finished",
            "projects_summary", "projects_hero_image", "projects_tech_stack",
            # Skills (2)
            "skills_section", "skills_highlighted",
            # Contact (3)
            "contact_section", "contact_linkedin", "contact_github",
            # Technical (8)
            "links_correct", "responsive_design", "professional_url",
            "grammar_checked", "single_page_navbar", "no_design_issues",
            "external_links_new_tab"
        ]

        return {param: {"pass": False, "details": []} for param in params}

    def _evaluate_about_section(self, soup: BeautifulSoup, checklist: Dict):
        """Evaluate About section (5 parameters)"""
        # Find about section
        about_section = self._find_section(soup, self.section_keywords["about"])

        if about_section:
            checklist["about_section"]["pass"] = True
            checklist["about_section"]["details"].append("[PASS] About section found")

            # Check for name (look for h1, h2, or name mention)
            name_found = False
            for heading in soup.find_all(["h1", "h2"]):
                text = heading.get_text(strip=True)
                # Check if looks like a name (2-4 words, capitalized)
                words = text.split()
                if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                    checklist["about_name"]["pass"] = True
                    checklist["about_name"]["details"].append(f"[PASS] Name found: {text}")
                    name_found = True
                    break

            if not name_found:
                checklist["about_name"]["details"].append("[FAIL] Name not clearly displayed")

            # Check for photo - EXPANDED: Search multiple sections thoroughly
            # Step 1: Search priority sections (about, header, hero, main)
            priority_sections = []

            # Add about section if exists
            if isinstance(about_section, Tag):
                priority_sections.append(about_section)

            # Add header/hero sections
            for section_name in ['header', 'hero', 'main', 'banner', 'intro', 'top']:
                section = soup.find(['header', 'section', 'div'], class_=re.compile(section_name, re.I))
                if section:
                    priority_sections.append(section)
                section = soup.find(['header', 'section', 'div'], id=re.compile(section_name, re.I))
                if section:
                    priority_sections.append(section)

            # Collect all images from priority sections
            priority_imgs = []
            for section in priority_sections:
                priority_imgs.extend(section.find_all('img'))

            # Step 2: If no images in priority sections, search entire page
            all_imgs = priority_imgs if priority_imgs else soup.find_all('img')

            # Score images based on how likely they are to be profile photos
            profile_candidates = []
            for img in all_imgs:
                alt = img.get('alt', '').lower()
                src = img.get('src', '').lower()
                score = 0

                # Positive indicators
                if any(word in alt for word in ['profile', 'photo', 'picture', 'portrait', 'avatar', 'headshot', 'me', 'myself', 'author', 'face']):
                    score += 3
                if any(word in src for word in ['profile', 'photo', 'avatar', 'headshot', 'portrait', 'me', 'about', 'author', 'person', 'face', 'user']):
                    score += 2
                if alt and len(alt) > 3:  # Has meaningful alt text
                    score += 1

                # Check parent classes for profile indicators
                parent = img.find_parent(['div', 'figure', 'section'])
                if parent:
                    parent_class = ' '.join(parent.get('class', [])).lower()
                    if any(word in parent_class for word in ['profile', 'photo', 'avatar', 'about', 'hero', 'author']):
                        score += 2

                # Negative indicators (decorative/UI elements)
                if any(word in (alt + src) for word in ['icon', 'logo', 'decoration', 'background', 'banner', 'pattern']):
                    score -= 3
                # Less aggressive on project images - only reduce if explicitly project-related
                if any(word in (alt + src) for word in ['project-', 'work-', 'portfolio-item', 'screenshot']):
                    score -= 1

                profile_candidates.append((score, img))

            # Sort by score and take best candidate
            profile_candidates.sort(key=lambda x: x[0], reverse=True)

            # Accept best scored image with more lenient threshold
            best_img = None
            search_location = "priority sections" if priority_imgs else "entire page"

            if profile_candidates:
                # Accept if score is positive OR if we have no better option
                if profile_candidates[0][0] > -1:  # Very lenient: even slightly negative scores accepted
                    best_img = profile_candidates[0][1]
                elif len(all_imgs) > 0:
                    # Fallback: accept first image from the first 3 images
                    for score, img in profile_candidates[:3]:
                        img_src = img.get('src', '').lower()
                        # Skip only if it's clearly a project screenshot or work sample
                        if not any(word in img_src for word in ['project-screenshot', 'work-sample', 'case-study-img']):
                            best_img = img
                            break
                    if not best_img and all_imgs:
                        best_img = all_imgs[0]  # Last resort: take first image

            if best_img:
                checklist["about_photo"]["pass"] = True
                src = best_img.get('src', '')[:80] + '...' if len(best_img.get('src', '')) > 80 else best_img.get('src', '')
                checklist["about_photo"]["details"].append(f"[PASS] Photo found: {src}")

                # Check alt text for professionalism - more lenient
                alt = best_img.get('alt', '').lower()
                if any(word in alt for word in ['profile', 'photo', 'picture', 'portrait', 'avatar', 'headshot']):
                    checklist["about_professional_photo"]["pass"] = True
                    checklist["about_professional_photo"]["details"].append(
                        "[PASS] Professional photo alt text detected"
                    )
                elif alt and len(alt) > 3:  # Has some alt text
                    checklist["about_professional_photo"]["pass"] = True
                    checklist["about_professional_photo"]["details"].append(
                        "[PASS] Profile image found with description"
                    )
                else:
                    checklist["about_professional_photo"]["details"].append(
                        "[WARNING] Photo alt text could be more descriptive"
                    )
            else:
                checklist["about_photo"]["details"].append(f"[FAIL] No photo found (searched {search_location})")

            # Check for introduction paragraph
            paragraphs = about_section.find_all('p') if isinstance(about_section, Tag) else soup.find_all('p')
            intro_found = False
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 50:  # Substantial intro
                    checklist["about_intro"]["pass"] = True
                    preview = text[:80] + "..." if len(text) > 80 else text
                    checklist["about_intro"]["details"].append(f"[PASS] Introduction: {preview}")
                    intro_found = True
                    break

            if not intro_found:
                checklist["about_intro"]["details"].append(
                    "[FAIL] No substantial introduction paragraph found"
                )
        else:
            checklist["about_section"]["details"].append("[FAIL] About section not found")

    def _evaluate_projects_section(self, soup: BeautifulSoup, checklist: Dict):
        """Evaluate Projects section (9 parameters)"""
        projects_section = self._find_section(soup, self.section_keywords["projects"])

        if projects_section:
            checklist["projects_section"]["pass"] = True
            checklist["projects_section"]["details"].append("[PASS] Projects section found")

            # Detect project cards
            project_cards = self._find_project_cards(
                projects_section if isinstance(projects_section, Tag) else soup
            )
            project_count = len(project_cards)

            checklist["projects_section"]["details"].append(
                f"Found {project_count} project card(s)"
            )

            # Check minimum 3 projects
            if project_count >= 3:
                checklist["projects_minimum"]["pass"] = True
                checklist["projects_minimum"]["details"].append(
                    f"[PASS] Has {project_count} projects (requirement: ≥3)"
                )
            else:
                checklist["projects_minimum"]["details"].append(
                    f"[FAIL] Only {project_count} project(s) found. Add at least {3 - project_count} more."
                )

            # Evaluate each project card
            has_samples = project_count > 0
            has_deployed = False
            has_github = False
            has_images = False
            has_descriptions = False
            has_tech_stack = False

            for idx, card in enumerate(project_cards, 1):
                card_analysis = self._analyze_project_card(card, idx)

                if card_analysis["has_image"]:
                    has_images = True
                if card_analysis["has_description"]:
                    has_descriptions = True
                if card_analysis["has_github"]:
                    has_github = True
                if card_analysis["has_deployed"]:
                    has_deployed = True
                if card_analysis["has_tech_stack"]:
                    has_tech_stack = True

                # Add per-project feedback
                checklist["projects_samples"]["details"].append(card_analysis["feedback"])

            # Update checklist based on findings
            checklist["projects_samples"]["pass"] = has_samples
            checklist["projects_hero_image"]["pass"] = has_images
            checklist["projects_summary"]["pass"] = has_descriptions
            checklist["projects_links"]["pass"] = has_github
            checklist["projects_deployed"]["pass"] = has_deployed
            checklist["projects_tech_stack"]["pass"] = has_tech_stack
            checklist["projects_finished"]["pass"] = has_deployed and has_descriptions

            # Summary messages
            if has_images:
                checklist["projects_hero_image"]["details"].append("[PASS] Projects have images")
            else:
                checklist["projects_hero_image"]["details"].append("[FAIL] Add images to projects")

            if has_github:
                checklist["projects_links"]["details"].append("[PASS] GitHub links found")
            else:
                checklist["projects_links"]["details"].append("[FAIL] Add GitHub repository links")

            if has_deployed:
                checklist["projects_deployed"]["details"].append("[PASS] Deployed links found")
            else:
                checklist["projects_deployed"]["details"].append("[FAIL] Add deployed/live links")

            if has_tech_stack:
                checklist["projects_tech_stack"]["details"].append("[PASS] Tech stack mentioned")
            else:
                checklist["projects_tech_stack"]["details"].append("[FAIL] List tech stack for projects")

        else:
            checklist["projects_section"]["details"].append("[FAIL] Projects section not found")

    def _evaluate_skills_section(self, soup: BeautifulSoup, checklist: Dict):
        """Evaluate Skills section (2 parameters)"""
        skills_section = self._find_section(soup, self.section_keywords["skills"])

        if skills_section:
            checklist["skills_section"]["pass"] = True
            checklist["skills_section"]["details"].append("[PASS] Skills section found")

            # Check if skills are highlighted (icons, badges, cards) - MORE LENIENT
            section_elem = skills_section if isinstance(skills_section, Tag) else soup
            has_icons = bool(section_elem.find_all(['svg', 'i', 'img']))
            has_badges = bool(section_elem.find_all(class_=re.compile(r'badge|tag|chip|skill|tech')))
            has_tech_keywords = any(
                kw in section_elem.get_text().lower()
                for kw in self.tech_keywords
            )

            # Count how many skill items (lists, divs, spans) are present
            skill_items = section_elem.find_all(['li', 'div', 'span'], class_=re.compile(r'skill|tech', re.I))
            has_multiple_items = len(skill_items) >= 3

            # Also check for any structured lists
            has_list = bool(section_elem.find_all(['ul', 'ol']))

            # More lenient: pass if ANY of these conditions are met
            if has_icons or has_badges or has_tech_keywords or has_multiple_items or has_list:
                checklist["skills_highlighted"]["pass"] = True
                highlights = []
                if has_icons:
                    highlights.append("icons")
                if has_badges:
                    highlights.append("badges")
                if has_tech_keywords:
                    highlights.append("tech keywords")
                if has_multiple_items:
                    highlights.append(f"{len(skill_items)} skill items")
                if has_list:
                    highlights.append("structured list")
                checklist["skills_highlighted"]["details"].append(
                    f"[PASS] Skills highlighted with {', '.join(highlights)}"
                )
            else:
                checklist["skills_highlighted"]["details"].append(
                    "[FAIL] Skills not visually highlighted. Consider adding icons or badges."
                )
        else:
            checklist["skills_section"]["details"].append("[FAIL] Skills section not found")

    def _evaluate_contact_section(self, soup: BeautifulSoup, checklist: Dict):
        """Evaluate Contact section (3 parameters)"""
        contact_section = self._find_section(soup, self.section_keywords["contact"])

        if contact_section:
            checklist["contact_section"]["pass"] = True
            checklist["contact_section"]["details"].append("[PASS] Contact section found")
        else:
            checklist["contact_section"]["details"].append("[FAIL] Contact section not found")

        # Check for LinkedIn and GitHub links (anywhere in page)
        all_links = soup.find_all('a', href=True)

        linkedin_found = False
        github_found = False

        for link in all_links:
            href = link.get('href', '').lower()
            if 'linkedin.com' in href:
                linkedin_found = True
            if 'github.com' in href and '/repos/' not in href:
                github_found = True

        if linkedin_found:
            checklist["contact_linkedin"]["pass"] = True
            checklist["contact_linkedin"]["details"].append("[PASS] LinkedIn profile link found")
        else:
            checklist["contact_linkedin"]["details"].append("[FAIL] Add LinkedIn profile link")

        if github_found:
            checklist["contact_github"]["pass"] = True
            checklist["contact_github"]["details"].append("[PASS] GitHub profile link found")
        else:
            checklist["contact_github"]["details"].append("[FAIL] Add GitHub profile link")

    def _evaluate_technical(
        self,
        soup: BeautifulSoup,
        html_content: str,
        url: str,
        checklist: Dict
    ):
        """Evaluate technical aspects (8 parameters)"""
        # Links correctness - with specific invalid link details
        all_links = soup.find_all('a', href=True)
        if all_links:
            invalid_links = []
            for link in all_links:
                href = link['href'].strip()

                # Skip empty links
                if not href:
                    link_text = link.get_text(strip=True)[:40]
                    link_display = f"'(empty)' (text: {link_text})" if link_text else "'(empty)'"
                    invalid_links.append(link_display)
                    continue

                # Check if link is potentially invalid
                # Valid patterns:
                # - http/https (external links)
                # - # (anchors)
                # - mailto:/tel: (special protocols)
                # - / (absolute paths)
                # - ./ or ../ (relative paths)
                # - any other relative path (e.g., "about.html", "projects")
                # Invalid patterns:
                # - javascript: (should use onclick instead)
                # - void(0) or similar
                is_valid = (
                    href.startswith(('http://', 'https://')) or  # External links
                    href.startswith('#') or  # Anchors
                    href.startswith(('mailto:', 'tel:')) or  # Special protocols
                    href.startswith('/') or  # Absolute paths
                    href.startswith(('./', '../')) or  # Relative paths with .
                    (not href.startswith(('javascript:', 'void')))  # Not JS or void
                )

                if not is_valid:
                    # Get link text for context
                    link_text = link.get_text(strip=True)[:40]
                    link_display = f"'{href}' (text: {link_text})" if link_text else f"'{href}'"
                    invalid_links.append(link_display)

            if len(invalid_links) == 0:
                checklist["links_correct"]["pass"] = True
                checklist["links_correct"]["details"].append("[PASS] All links appear valid")
            else:
                # Show warning with specific links inline for better visibility
                if len(invalid_links) == 1:
                    checklist["links_correct"]["details"].append(
                        f"[WARNING] 1 link may be invalid: {invalid_links[0]}"
                    )
                else:
                    checklist["links_correct"]["details"].append(
                        f"[WARNING] {len(invalid_links)} links may be invalid:"
                    )
                    # Show up to 5 invalid links
                    for invalid_link in invalid_links[:5]:
                        checklist["links_correct"]["details"].append(f"  • {invalid_link}")
                    if len(invalid_links) > 5:
                        checklist["links_correct"]["details"].append(f"  • ... and {len(invalid_links) - 5} more")

        # External links open in new tab - with specific link details
        external_links = [
            l for l in all_links
            if l['href'].startswith(('http', 'https'))
            and urlparse(l['href']).netloc != urlparse(url).netloc
        ]
        if external_links:
            links_without_target = [l for l in external_links if l.get('target') != '_blank']
            if len(links_without_target) == 0:
                checklist["external_links_new_tab"]["pass"] = True
                checklist["external_links_new_tab"]["details"].append(
                    "[PASS] External links open in new tab"
                )
            else:
                # Show warning with specific links for better visibility
                if len(links_without_target) == 1:
                    link = links_without_target[0]
                    href = link['href'][:60] + '...' if len(link['href']) > 60 else link['href']
                    link_text = link.get_text(strip=True)[:30]
                    display = f"'{href}' (text: {link_text})" if link_text else f"'{href}'"
                    checklist["external_links_new_tab"]["details"].append(
                        f"[WARNING] 1 external link missing target='_blank': {display}"
                    )
                else:
                    checklist["external_links_new_tab"]["details"].append(
                        f"[WARNING] {len(links_without_target)} external links missing target='_blank':"
                    )
                    # Show up to 5 links missing target
                    for link in links_without_target[:5]:
                        href = link['href'][:60] + '...' if len(link['href']) > 60 else link['href']
                        link_text = link.get_text(strip=True)[:30]
                        display = f"'{href}' (text: {link_text})" if link_text else f"'{href}'"
                        checklist["external_links_new_tab"]["details"].append(f"  • {display}")
                    if len(links_without_target) > 5:
                        checklist["external_links_new_tab"]["details"].append(
                            f"  • ... and {len(links_without_target) - 5} more"
                        )

        # Responsive design indicators
        responsive_indicators = [
            '@media' in html_content.lower(),
            'viewport' in html_content.lower(),
            bool(soup.find('meta', attrs={'name': 'viewport'})),
            any(cls in html_content for cls in ['sm:', 'md:', 'lg:', 'xl:', '2xl:'])  # Tailwind
        ]
        if any(responsive_indicators):
            checklist["responsive_design"]["pass"] = True
            checklist["responsive_design"]["details"].append("[PASS] Responsive design indicators found")
        else:
            checklist["responsive_design"]["details"].append(
                "[FAIL] No responsive design indicators. Add media queries or responsive framework."
            )

        # Professional URL
        parsed = urlparse(url)
        is_professional = (
            parsed.scheme == 'https'
            and not parsed.netloc.startswith('127.0.0.1')
            and not parsed.netloc.startswith('localhost')
        )
        checklist["professional_url"]["pass"] = is_professional
        if is_professional:
            checklist["professional_url"]["details"].append(f"[PASS] Professional URL: {url}")
        else:
            checklist["professional_url"]["details"].append(
                "[WARNING] Consider deploying to a professional URL (HTTPS)"
            )

        # Single page with navbar
        nav = soup.find(['nav', 'header'])
        if nav and nav.find_all('a'):
            checklist["single_page_navbar"]["pass"] = True
            nav_links = len(nav.find_all('a'))
            checklist["single_page_navbar"]["details"].append(
                f"[PASS] Navigation bar with {nav_links} link(s)"
            )
        else:
            checklist["single_page_navbar"]["details"].append(
                "[FAIL] Add navigation bar for better UX"
            )

        # Design issues (check for alt text on images)
        images = soup.find_all('img')
        if images:
            with_alt = [img for img in images if img.get('alt')]
            if len(with_alt) == len(images):
                checklist["no_design_issues"]["pass"] = True
                checklist["no_design_issues"]["details"].append("[PASS] All images have alt text")
            else:
                missing = len(images) - len(with_alt)
                checklist["no_design_issues"]["details"].append(
                    f"[WARNING] {missing} image(s) missing alt text (accessibility issue)"
                )
        else:
            checklist["no_design_issues"]["pass"] = True
            checklist["no_design_issues"]["details"].append("No images to check")

        # Grammar check (basic)
        text_content = soup.get_text()
        common_typos = ['teh', 'recieve', 'definately', 'seperate']
        found_typos = [typo for typo in common_typos if typo in text_content.lower()]
        if not found_typos:
            checklist["grammar_checked"]["pass"] = True
            checklist["grammar_checked"]["details"].append("[PASS] No obvious typos detected")
        else:
            checklist["grammar_checked"]["details"].append(
                f"[WARNING] Possible typos found: {', '.join(found_typos)}"
            )

    def _find_section(self, soup: BeautifulSoup, keywords: List[str]) -> Any:
        """Find section by keywords using improved, flexible strategies"""
        # Strategy 1: Exact ID match (most reliable)
        for keyword in keywords:
            section = soup.find(id=keyword)
            if section:
                return section

        # Strategy 2: Exact class match
        for keyword in keywords:
            section = soup.find(class_=keyword)
            if section:
                return section

        # Strategy 3: ID/class contains keyword
        for keyword in keywords:
            section = soup.find(id=re.compile(keyword, re.I))
            if section:
                return section
            section = soup.find(class_=re.compile(keyword, re.I))
            if section:
                return section

        # Strategy 4: Heading text match (reliable)
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text(strip=True).lower()
            # Exact or close match
            for kw in keywords:
                if kw in heading_text or heading_text in kw:
                    # Return parent container if it exists
                    parent = heading.find_parent(['section', 'div', 'article', 'main'])
                    if parent and len(parent.get_text(strip=True)) > len(heading_text) * 2:
                        return parent
                    return heading

        # Strategy 5: Look for sections with semantic HTML5 tags
        for keyword in keywords:
            # Check data attributes
            section = soup.find(attrs={'data-section': keyword})
            if section:
                return section

        # Strategy 6: Text content in larger containers (least reliable, last resort)
        for tag in soup.find_all(['section', 'div', 'article'], recursive=False):
            tag_text = tag.get_text().lower()
            # Only match if keyword appears prominently (first 200 chars)
            first_part = tag_text[:200]
            if any(kw in first_part for kw in keywords):
                return tag

        return None

    def _find_project_cards(self, container: Tag) -> List[Tag]:
        """Find project cards using improved, flexible heuristics"""
        cards = []
        seen_cards = set()

        # Strategy 1: Look for common project card class patterns
        class_patterns = [
            r'project[-_]?card', r'project[-_]?item', r'project',
            r'card', r'portfolio[-_]?item', r'work[-_]?item',
            r'case[-_]?study', r'item', r'project[-_]?box', r'col'
        ]

        for pattern in class_patterns:
            potential_cards = container.find_all(
                ['div', 'article', 'section', 'li'],
                class_=re.compile(pattern, re.I)
            )

            for card in potential_cards:
                # Skip if already found
                card_id = id(card)
                if card_id in seen_cards:
                    continue

                # Validate it's likely a project card - VERY LENIENT
                has_heading = bool(card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
                has_link = bool(card.find('a', href=True))
                has_image = bool(card.find('img'))
                has_content = len(card.get_text(strip=True)) > 15

                # Very flexible: needs ANY of these combinations
                if has_content and (has_heading or has_link or has_image):
                    cards.append(card)
                    seen_cards.add(card_id)

        # Strategy 2: Look for repeated structures (likely project cards)
        # Find all divs with images and links inside project section
        if len(cards) < 2:
            divs_with_content = container.find_all(['div', 'article', 'li'])
            content_structures = []

            for div in divs_with_content:
                if id(div) in seen_cards:
                    continue

                has_image = bool(div.find('img'))
                has_link = bool(div.find('a', href=True))
                has_heading = bool(div.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
                text_length = len(div.get_text(strip=True))

                # More lenient: accept if has reasonable content and ANY structural element
                if 20 < text_length < 2000 and (has_image or has_link or has_heading):
                    content_structures.append(div)

            # If we found multiple similar structures, they're likely projects
            if len(content_structures) >= 2:
                for struct in content_structures:
                    if id(struct) not in seen_cards:
                        cards.append(struct)
                        seen_cards.add(id(struct))

        # Strategy 3: Look in grid/flex containers
        if len(cards) < 2:
            grid_containers = container.find_all(['div', 'section'], class_=re.compile(r'grid|flex|row|container|columns', re.I))

            for grid in grid_containers:
                direct_children = [child for child in grid.children if hasattr(child, 'name') and child.name]

                # If container has 2-10 similar children, they're likely projects
                if 2 <= len(direct_children) <= 10:
                    for child in direct_children:
                        if id(child) in seen_cards:
                            continue

                        has_link = bool(child.find('a', href=True))
                        text_length = len(child.get_text(strip=True))

                        if has_link and text_length > 30:
                            cards.append(child)
                            seen_cards.add(id(child))

        # Strategy 4: Look for any container with heading + link combination
        # This catches many custom-structured projects
        if len(cards) < 2:
            all_headings = container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in all_headings:
                # Find the parent container (could be div, article, section, li, etc.)
                parent = heading.find_parent(['div', 'article', 'section', 'li', 'figure'])
                if not parent or id(parent) in seen_cards:
                    continue

                # Check if this parent has project-like features
                has_link = bool(parent.find('a', href=True))
                has_image = bool(parent.find('img'))
                has_button = bool(parent.find(['button', 'a'], string=re.compile(r'demo|live|github|view', re.I)))
                text_length = len(parent.get_text(strip=True))

                # Accept if it has a heading and at least one other project feature
                if 20 < text_length < 3000 and (has_link or has_image or has_button):
                    cards.append(parent)
                    seen_cards.add(id(parent))

        # Strategy 5: Look for anchor tags that link to github/deployed projects
        # Sometimes projects are structured as simple link lists
        if len(cards) < 2:
            project_links = container.find_all('a', href=re.compile(r'github\.com|netlify|vercel|herokuapp|render\.com|github\.io', re.I))
            for link in project_links:
                # Get the parent container
                parent = link.find_parent(['div', 'li', 'article', 'section'])
                if not parent or id(parent) in seen_cards:
                    continue

                # Check if this looks like a project entry
                has_heading = bool(parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
                has_image = bool(parent.find('img'))
                text_length = len(parent.get_text(strip=True))

                # Accept if it has reasonable content
                if text_length > 20 and (has_heading or has_image):
                    cards.append(parent)
                    seen_cards.add(id(parent))

        return cards[:10]  # Limit to 10 projects max

    def _analyze_project_card(self, card: Tag, index: int) -> Dict[str, Any]:
        """Analyze individual project card"""
        analysis = {
            "has_image": bool(card.find('img')),
            "has_description": len(card.get_text(strip=True)) > 50,
            "has_github": False,
            "has_deployed": False,
            "has_tech_stack": False,
            "feedback": f"Project {index}: "
        }

        # Check links
        links = card.find_all('a', href=True)
        deployment_domains = ['vercel.app', 'netlify.app', 'herokuapp.com', 'render.com', 'github.io']

        for link in links:
            href = link.get('href', '')
            if 'github.com' in href and '/repos/' not in href:
                analysis["has_github"] = True
            if any(domain in href for domain in deployment_domains):
                analysis["has_deployed"] = True

        # Check for tech stack mention
        card_text = card.get_text().lower()
        if any(tech in card_text for tech in self.tech_keywords):
            analysis["has_tech_stack"] = True

        # Generate feedback
        issues = []
        if not analysis["has_image"]:
            issues.append("missing image")
        if not analysis["has_github"]:
            issues.append("missing GitHub link")
        if not analysis["has_deployed"]:
            issues.append("missing deployed link")
        if not analysis["has_tech_stack"]:
            issues.append("missing tech stack")

        if issues:
            analysis["feedback"] += ", ".join(issues)
        else:
            analysis["feedback"] += "[PASS] Complete"

        return analysis
