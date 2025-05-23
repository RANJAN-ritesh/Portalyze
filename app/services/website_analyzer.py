from playwright.async_api import async_playwright
from typing import Dict, Any, List, Tuple
import re
from bs4 import BeautifulSoup
import aiohttp
from urllib.parse import urlparse, urljoin
import os
import requests
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

class WebsiteAnalyzer:
    def __init__(self, url):
        self.url = url
        self.base_url = url
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
        self.browser = None
        self.page = None
        self.timeout = 30  # Set timeout in seconds
        
        # Comprehensive section keywords
        self.section_keywords = {
            "about": [
                "about", "about me", "about-me", "bio", "biography", "introduction", 
                "profile", "who am i", "whoami", "personal", "background"
            ],
            "skills": [
                "skills", "tech stack", "tech-stack", "technologies", "expertise",
                "proficiency", "tools", "languages", "frameworks", "stack",
                "technical skills", "technical expertise", "what i know"
            ],
            "projects": [
                "projects", "project", "portfolio", "work", "case studies",
                "my work", "my projects", "my portfolio", "recent work",
                "showcase", "applications", "apps", "websites"
            ],
            "contact": [
                "contact", "contact me", "contact-me", "get in touch",
                "reach out", "connect", "social", "social media",
                "social links", "connect with me", "let's talk"
            ]
        }
        
        # Common skill names to exclude from projects
        self.skill_names = set([
            # MERN & Web
            'html', 'css', 'js', 'javascript', 'node.js', 'node', 'express', 'expressjs', 
            'react', 'redux', 'next.js', 'nextjs', 'angular', 'vue', 'svelte', 'bootstrap', 
            'material-ui', 'tailwind', 'mui', 'chakra', 'jquery',
            # Databases
            'mongodb', 'mongo', 'mongoose', 'mysql', 'postgresql', 'postgres', 'sqlite', 
            'redis', 'database', 'firebase', 'nosql', 'sql',
            # AI/ML/Data
            'python', 'pandas', 'numpy', 'scipy', 'scikit-learn', 'sklearn', 'tensorflow', 
            'keras', 'pytorch', 'openai', 'opencv', 'matplotlib', 'seaborn', 'jupyter', 
            'jupyter notebook', 'deep learning', 'machine learning', 'data engineering', 
            'data analysis', 'data analytics', 'ai', 'ml', 'web-scrapping',
            # Business/Data Analysis
            'powerbi', 'tableau', 'excel', 'statistics', 'metabase', 'looker', 'superset',
            # Testing
            'jest', 'mocha', 'chai', 'cypress', 'selenium', 'pytest', 'unittest', 'testing',
            # DevOps/Cloud
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'netlify', 
            'vercel', 'heroku', 'digitalocean', 'cloud',
            # Other
            'rest', 'graphql', 'api', 'git', 'github', 'bitbucket', 'gitlab', 
            'software development', 'software testing', 'business analysis', 'metabase', 
            'powerbi', 'tableau', 'jupyter notebook', 'firebase', 'aws', 'cloud'
        ])
        
        # Project detection patterns
        self.project_patterns = {
            'container_classes': [
                'project', 'portfolio', 'work', 'case-study', 'card', 'item',
                'project-card', 'portfolio-item', 'work-item'
            ],
            'title_classes': [
                'title', 'name', 'heading', 'project-title', 'portfolio-title',
                'work-title', 'case-study-title'
            ],
            'description_classes': [
                'description', 'summary', 'about', 'info', 'project-description',
                'portfolio-description', 'work-description'
            ],
            'tech_stack_classes': [
                'tech', 'stack', 'technology', 'tools', 'languages', 'frameworks',
                'tech-stack', 'project-tech', 'portfolio-tech'
            ],
            'link_classes': [
                'link', 'url', 'github', 'demo', 'live', 'deployed', 'project-link',
                'portfolio-link', 'work-link', 'case-study-link'
            ]
        }
        
    async def _fetch_linked_files(self, soup) -> Tuple[List[str], List[str]]:
        """Fetch linked CSS and JS files with timeout."""
        css_files = []
        js_files = []
        async with aiohttp.ClientSession() as session:
            # Fetch CSS files
            css_tasks = []
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                if href:
                    css_tasks.append(self._fetch_file(session, href))
            
            # Fetch JS files
            js_tasks = []
            for script in soup.find_all('script', src=True):
                src = script.get('src')
                if src:
                    js_tasks.append(self._fetch_file(session, src))
            
            # Wait for all tasks to complete with timeout
            css_results, js_results = await asyncio.gather(
                asyncio.gather(*css_tasks, return_exceptions=True),
                asyncio.gather(*js_tasks, return_exceptions=True)
            )
            
            # Filter out failed requests
            css_files = [r for r in css_results if isinstance(r, str)]
            js_files = [r for r in js_results if isinstance(r, str)]
            
        return css_files, js_files
    
    async def _fetch_file(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch a single file with timeout."""
        try:
            # Handle relative URLs
            full_url = urljoin(self.base_url, url)
            async with session.get(full_url, timeout=self.timeout) as response:
                if response.status == 200:
                    return await response.text()
                return ""
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return ""
    
    def analyze_with_ai(self, html_content: str) -> Dict[str, Any]:
        """Analyze content with AI using a focused prompt."""
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Focused prompt for essential parameters
        prompt = (
            "Analyze this portfolio and provide a concise assessment of:\n"
            "1. Required sections (About, Skills, Projects, Contact)\n"
            "2. Project details (deployment links, tech stack)\n"
            "3. Contact information (LinkedIn, GitHub)\n"
            "4. Grammar and spelling\n"
            "5. Design issues\n\n"
            f"HTML: {html_content}"
        )
        
        data = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': prompt
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                f'{self.gemini_api_url}?key={self.gemini_api_key}',
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            print(f"Error in AI analysis: {str(e)}")
            return {}
    
    async def analyze(self) -> Dict[str, Any]:
        """Analyze a deployed website for portfolio grading."""
        async with async_playwright() as p:
            self.browser = await p.chromium.launch()
            self.page = await self.browser.new_page()
            
            try:
                # Navigate to the page with timeout
                await self.page.goto(self.url, wait_until="networkidle", timeout=self.timeout * 1000)
                
                # Fetch HTML content
                html_content = await self.page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Fetch linked files concurrently
                css_files, js_files = await self._fetch_linked_files(soup)
                
                # Combine content efficiently
                combined_content = f"{html_content}\n\nCSS Files:\n{''.join(css_files)}\n\nJS Files:\n{''.join(js_files)}"
                
                # Run analyses concurrently
                ai_analysis_task = asyncio.create_task(self._run_ai_analysis(combined_content))
                other_analyses_task = asyncio.create_task(self._run_analyses())
                
                # Wait for both tasks to complete
                ai_results, other_results = await asyncio.gather(ai_analysis_task, other_analyses_task)
                
                # Combine results
                return {**other_results, "ai_analysis": ai_results}
                
            finally:
                await self.browser.close()
    
    async def _run_ai_analysis(self, content: str) -> Dict[str, Any]:
        """Run AI analysis in a separate task."""
        return self.analyze_with_ai(content)
    
    async def _run_analyses(self) -> Dict[str, Any]:
        """Run all website analyses concurrently."""
        analyses = [
            self._analyze_sections(),
            self._analyze_responsiveness(),
            self._analyze_links(),
            self._analyze_about_section(),
            self._analyze_projects_section(),
            self._analyze_skills_section(),
            self._analyze_contact_section(),
            self._analyze_design_issues()
        ]
        
        results = {}
        for analysis in analyses:
            result = await analysis
            results.update(result)
            
        return results
    
    async def _analyze_sections(self) -> Dict[str, Any]:
        """Analyze the presence and content of main sections."""
        content = await self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        sections = {
            "about": self._find_section(soup, "about") is not None,
            "skills": self._find_section(soup, "skills") is not None,
            "projects": self._find_section(soup, "projects") is not None,
            "contact": self._find_section(soup, "contact") is not None
        }
        
        return {"sections": sections}
    
    async def _analyze_responsiveness(self) -> Dict[str, Any]:
        """Test website responsiveness at different viewport sizes."""
        viewports = [
            {"width": 375, "height": 667},  # Mobile
            {"width": 768, "height": 1024},  # Tablet
            {"width": 1440, "height": 900}   # Desktop
        ]
        
        results = {}
        for viewport in viewports:
            await self.page.set_viewport_size(viewport)
            await self.page.wait_for_load_state("networkidle")
            
            # Check for horizontal scrollbar
            has_horizontal_scroll = await self.page.evaluate("""
                () => document.documentElement.scrollWidth > document.documentElement.clientWidth
            """)
            
            # Check for media queries
            has_media_queries = await self.page.evaluate("""
                () => {
                    const styleSheets = Array.from(document.styleSheets);
                    return styleSheets.some(sheet => {
                        try {
                            return Array.from(sheet.cssRules).some(rule => 
                                rule instanceof CSSMediaRule
                            );
                        } catch (e) {
                            return false;
                        }
                    });
                }
            """)
            
            results[f"viewport_{viewport['width']}"] = {
                "has_horizontal_scroll": has_horizontal_scroll,
                "has_media_queries": has_media_queries
            }
        
        return {"responsiveness": results}
    
    async def _analyze_links(self) -> Dict[str, Any]:
        """Analyze all links on the page."""
        links = await self.page.evaluate("""
            () => {
                const links = Array.from(document.getElementsByTagName('a'));
                return links.map(link => ({
                    href: link.href,
                    text: link.textContent,
                    target: link.target,
                    is_external: link.hostname !== window.location.hostname
                }));
            }
        """)
        
        # Check if external links open in new tab
        external_links = [link for link in links if link["is_external"]]
        external_links_new_tab = [link for link in external_links if link["target"] == "_blank"]
        
        # Check if links are working
        working_links = []
        async with aiohttp.ClientSession() as session:
            for link in links:
                try:
                    async with session.head(link["href"]) as response:
                        working_links.append({
                            "url": link["href"],
                            "status": response.status
                        })
                except:
                    working_links.append({
                        "url": link["href"],
                        "status": "error"
                    })
        
        return {
            "links": {
                "total": len(links),
                "external": len(external_links),
                "external_new_tab": len(external_links_new_tab),
                "working": working_links
            }
        }
    
    async def _analyze_about_section(self) -> Dict[str, Any]:
        """Analyze the About section."""
        content = await self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        about_section = self._find_section(soup, "about")
        
        if not about_section:
            return {"about": {"exists": False}}
        
        # Check for photo
        photo = about_section.find('img')
        has_photo = bool(photo)
        
        # Check for name
        name = about_section.find(['h1', 'h2', 'h3'])
        has_name = bool(name)
        
        # Check for introduction
        intro = about_section.find(['p', 'div'], class_=re.compile(r'intro|about-text|bio'))
        has_intro = bool(intro)
        
        return {
            "about": {
                "exists": True,
                "has_photo": has_photo,
                "has_name": has_name,
                "has_intro": has_intro
            }
        }
    
    async def _analyze_projects_section(self) -> Dict[str, Any]:
        """Analyze the Projects section with enhanced detection."""
        content = await self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        projects_section = self._find_section(soup, "projects")
        
        if not projects_section:
            return {"projects": {"exists": False}}
        
        # Find project containers using multiple strategies
        project_containers = []
        
        # Strategy 1: Direct class match
        for class_name in self.project_patterns['container_classes']:
            containers = projects_section.find_all(['div', 'article'], 
                class_=re.compile(class_name, re.I))
            project_containers.extend(containers)
        
        # Strategy 2: Look for project cards with specific structure
        if not project_containers:
            # Look for divs that contain both a title and project content
            potential_containers = projects_section.find_all('div', class_=re.compile(r'project|card|item', re.I))
            for container in potential_containers:
                # Check if it has a title and either description or links
                has_title = bool(container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
                has_content = bool(container.find(['p', 'div'], class_=re.compile(r'description|content|about', re.I)))
                has_links = bool(container.find('a', href=True))
                
                if has_title and (has_content or has_links):
                    project_containers.append(container)
        
        # Strategy 3: Look for project cards by structure
        if not project_containers:
            # Find all divs that might be project cards
            all_divs = projects_section.find_all('div')
            for div in all_divs:
                # Check if this div looks like a project card
                if self._looks_like_project(div):
                    project_containers.append(div)
        
        # Process found projects
        projects = []
        for container in project_containers:
            project_info = self._extract_project_info(container)
            if project_info:
                projects.append(project_info)
        
        # If still no projects found, try one last strategy
        if not projects:
            # Look for any div that contains both a title and project-related content
            all_divs = projects_section.find_all('div')
            for div in all_divs:
                title = div.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title:
                    title_text = title.get_text().strip()
                    # Skip if it's a section title or skill
                    if title_text.lower() in self.skill_names or title_text.lower() in ['projects', 'my projects', 'portfolio']:
                        continue
                    
                    # Check for project-like content
                    has_content = bool(div.find(['p', 'div'], string=re.compile(r'description|about|summary', re.I)))
                    has_links = bool(div.find('a', href=re.compile(r'github|netlify|vercel|heroku', re.I)))
                    
                    if has_content or has_links:
                        project_info = self._extract_project_info(div)
                        if project_info:
                            projects.append(project_info)
        
        return {
            "projects": {
                "exists": True,
                "count": len(projects),
                "details": projects
            }
        }

    def _looks_like_project(self, container: Any) -> bool:
        """Check if a container looks like a project card."""
        # Must have a title
        title = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not title:
            return False
            
        title_text = title.get_text().strip().lower()
        
        # Skip if it's a section title or skill
        if title_text in self.skill_names or title_text in ['projects', 'my projects', 'portfolio']:
            return False
            
        # Must have at least two of: description, image, or links
        has_description = bool(container.find(['p', 'div'], class_=re.compile(r'description|summary|about|content', re.I)))
        has_image = bool(container.find('img'))
        has_links = bool(container.find('a', href=re.compile(r'github|netlify|vercel|heroku', re.I)))
        
        # Count how many project-like features it has
        feature_count = sum([has_description, has_image, has_links])
        return feature_count >= 2

    def _extract_project_info(self, container: Any) -> Dict[str, Any]:
        """Extract project information from a container."""
        # Get title
        title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not title_elem:
            return None
            
        title = title_elem.get_text().strip()
        
        # Skip if title matches a skill name or is a section title
        if title.lower() in self.skill_names or title.lower() in ['projects', 'my projects', 'portfolio']:
            return None
        
        # Get project details with more flexible selectors
        description = container.find(['p', 'div'], class_=re.compile(r'description|summary|about|content', re.I))
        if not description:
            description = container.find(['p', 'div'], string=re.compile(r'description|about|summary', re.I))
            
        tech_stack = container.find(['p', 'div'], class_=re.compile(r'tech|stack|technology', re.I))
        if not tech_stack:
            tech_stack = container.find(['p', 'div'], string=re.compile(r'tech|stack|technology', re.I))
            
        github_link = container.find('a', href=re.compile(r'github.com', re.I))
        deployed_link = container.find('a', href=re.compile(r'netlify|vercel|heroku|firebase', re.I))
        image = container.find('img')
        
        return {
            "name": title,
            "has_summary": bool(description),
            "has_hero_image": bool(image),
            "has_tech_stack": bool(tech_stack),
            "has_deployed_link": bool(deployed_link),
            "has_github_link": bool(github_link)
        }
    
    async def _analyze_skills_section(self) -> Dict[str, Any]:
        """Analyze the Skills section."""
        content = await self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        skills_section = self._find_section(soup, "skills")
        
        if not skills_section:
            return {"skills": {"exists": False}}
        
        # Check for visual presentation
        has_icons = bool(skills_section.find('img', class_=re.compile(r'icon|skill')))
        has_cards = bool(skills_section.find(class_=re.compile(r'card|item|skill')))
        
        return {
            "skills": {
                "exists": True,
                "has_visual_presentation": has_icons or has_cards
            }
        }
    
    async def _analyze_contact_section(self) -> Dict[str, Any]:
        """Analyze the Contact section."""
        content = await self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        contact_section = self._find_section(soup, "contact")
        
        if not contact_section:
            return {"contact": {"exists": False}}
        
        # Check for social links
        has_linkedin = bool(contact_section.find('a', href=re.compile(r'linkedin.com')))
        has_github = bool(contact_section.find('a', href=re.compile(r'github.com')))
        
        # Check for contact form
        has_form = bool(contact_section.find('form'))
        
        return {
            "contact": {
                "exists": True,
                "has_linkedin": has_linkedin,
                "has_github": has_github,
                "has_form": has_form
            }
        }
    
    async def _analyze_design_issues(self) -> Dict[str, Any]:
        """Analyze potential design issues."""
        # Check for console errors
        console_errors = await self.page.evaluate("""
            () => {
                const errors = [];
                const originalConsoleError = console.error;
                console.error = (...args) => {
                    errors.push(args.join(' '));
                    originalConsoleError.apply(console, args);
                };
                return errors;
            }
        """)
        
        # Check for broken images
        broken_images = await self.page.evaluate("""
            () => {
                const images = Array.from(document.getElementsByTagName('img'));
                return images.filter(img => !img.complete || img.naturalHeight === 0).length;
            }
        """)
        
        return {
            "design_issues": {
                "console_errors": console_errors,
                "broken_images": broken_images
            }
        }
    
    def _find_section(self, soup: BeautifulSoup, section_name: str) -> Any:
        """
        Find a section using multiple strategies:
        1. Direct ID/class match
        2. Heading text match
        3. Section content analysis
        4. AI fallback
        """
        section = None
        keywords = self.section_keywords.get(section_name, [section_name])
        
        # Strategy 1: Direct ID/class match
        for keyword in keywords:
            # Try ID
            section = soup.find(id=re.compile(f'{keyword}|{keyword}-section', re.I))
            if section:
                print(f"Found {section_name} section by ID: {section.get('id')}")
                return section
                
            # Try class
            section = soup.find(class_=re.compile(f'{keyword}|{keyword}-section', re.I))
            if section:
                print(f"Found {section_name} section by class: {section.get('class')}")
                return section
        
        # Strategy 2: Heading text match
        for keyword in keywords:
            heading = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], 
                              string=re.compile(keyword, re.I))
            if heading:
                # Get the parent section or container
                section = heading.find_parent(['section', 'div', 'article'])
                if section:
                    print(f"Found {section_name} section by heading: {heading.get_text()}")
                    return section
        
        # Strategy 3: Section content analysis
        for keyword in keywords:
            # Look for sections containing the keyword in their text
            sections = soup.find_all(['section', 'div', 'article'])
            for s in sections:
                text = s.get_text().lower()
                if keyword.lower() in text:
                    # Verify it's not a false positive
                    if self._verify_section_content(s, section_name):
                        print(f"Found {section_name} section by content analysis")
                        return s
        
        # Strategy 4: AI fallback
        if not section:
            print(f"Using AI to find {section_name} section")
            section = self._find_section_with_ai(soup, section_name)
        
        return section

    def _verify_section_content(self, section: Any, section_name: str) -> bool:
        """Verify if a section contains expected content for its type."""
        if section_name == "about":
            return bool(section.find(['p', 'div'], string=re.compile(r'about|bio|introduction', re.I)))
        elif section_name == "skills":
            return bool(section.find(['div', 'ul', 'li'], class_=re.compile(r'skill|tech|technology', re.I)))
        elif section_name == "projects":
            return bool(section.find(['div', 'article'], class_=re.compile(r'project|portfolio|work', re.I)))
        elif section_name == "contact":
            return bool(section.find(['a', 'form'], href=re.compile(r'mailto|linkedin|github', re.I)))
        return False

    def _find_section_with_ai(self, soup: BeautifulSoup, section_name: str) -> Any:
        """Use AI to find a section when traditional methods fail."""
        # Extract relevant HTML for AI analysis
        html_content = str(soup)
        
        # Create a focused prompt for the AI
        prompt = f"""
        Analyze this HTML and identify the {section_name} section.
        Look for:
        1. Section with {section_name}-related content
        2. Common patterns for {section_name} sections
        3. Relevant headings and content
        
        Return the section's HTML if found.
        """
        
        try:
            response = self.analyze_with_ai(html_content)
            # Process AI response and extract section
            # This is a placeholder - implement actual AI response processing
            return None
        except Exception as e:
            print(f"AI section detection failed: {str(e)}")
            return None 