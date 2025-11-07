from typing import Dict, Any, List, Tuple
import re
from bs4 import BeautifulSoup
import aiohttp
from urllib.parse import urlparse, urljoin
import os
import requests
from dotenv import load_dotenv
import asyncio

# Try to import Playwright (optional dependency)
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not available - using aiohttp fallback for web scraping")

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
        use_playwright = PLAYWRIGHT_AVAILABLE and os.getenv('USE_PLAYWRIGHT', 'true').lower() == 'true'

        if use_playwright:
            return await self._analyze_with_playwright()
        else:
            return await self._analyze_with_aiohttp()

    async def _analyze_with_aiohttp(self) -> Dict[str, Any]:
        """Analyze website using aiohttp (Playwright-free fallback)."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Fetch linked files concurrently
                    css_files, js_files = await self._fetch_linked_files(soup)

                    # Combine content efficiently
                    combined_content = f"{html_content}\n\nCSS Files:\n{''.join(css_files)}\n\nJS Files:\n{''.join(js_files)}"

                    # Run analyses
                    ai_analysis = self.analyze_with_ai(combined_content)

                    # Basic analysis without Playwright-specific features
                    return {
                        "ai_analysis": ai_analysis,
                        "html_content": html_content,
                        "soup": str(soup)[:1000]  # Limited soup representation
                    }
        except Exception as e:
            print(f"Error in aiohttp analysis: {str(e)}")
            return {"error": str(e)}

    async def _analyze_with_playwright(self) -> Dict[str, Any]:
        """Analyze website using Playwright (requires playwright package)."""
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

                # Run AI analysis
                ai_analysis = self.analyze_with_ai(combined_content)

                return {
                    "ai_analysis": ai_analysis,
                    "html_content": html_content
                }

            finally:
                await self.browser.close()
