import os
import tempfile
from git import Repo
from bs4 import BeautifulSoup
import aiohttp
from typing import Dict, Any
import re

class GitHubAnalyzer:
    def __init__(self):
        self.temp_dir = None
        
    async def analyze(self, github_url: str) -> Dict[str, Any]:
        """Analyze a GitHub repository for portfolio grading."""
        try:
            # Clone repository to temporary directory
            self.temp_dir = tempfile.mkdtemp()
            repo = Repo.clone_from(github_url, self.temp_dir)
            
            results = {
                "sections": await self._check_sections(),
                "projects": await self._analyze_projects(),
                "readme": await self._analyze_readme(),
                "tech_stack": await self._analyze_tech_stack(),
                "structure": await self._analyze_structure()
            }
            
            return results
            
        finally:
            # Cleanup
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
    
    async def _check_sections(self) -> Dict[str, bool]:
        """Check for required sections in HTML files."""
        sections = {
            "about": False,
            "skills": False,
            "projects": False,
            "contact": False
        }
        
        # Look for main HTML file
        html_files = self._find_html_files()
        
        for html_file in html_files:
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                
                # Check for sections using various methods
                for section in sections.keys():
                    if self._find_section(soup, section):
                        sections[section] = True
        
        return sections
    
    async def _analyze_projects(self) -> Dict[str, Any]:
        """Analyze project section and individual projects."""
        projects = []
        html_files = self._find_html_files()
        
        for html_file in html_files:
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                project_section = self._find_section(soup, "projects")
                
                if project_section:
                    # Find project cards/elements
                    project_elements = project_section.find_all(['div', 'article'], class_=re.compile(r'project|card|item'))
                    
                    for project in project_elements:
                        project_info = {
                            "summary": self._extract_project_summary(project),
                            "hero_image": self._extract_hero_image(project),
                            "tech_stack": self._extract_project_tech_stack(project),
                            "deployed_link": self._extract_deployed_link(project)
                        }
                        projects.append(project_info)
        
        return {
            "count": len(projects),
            "projects": projects
        }
    
    async def _analyze_readme(self) -> Dict[str, Any]:
        """Analyze README.md file."""
        readme_path = os.path.join(self.temp_dir, "README.md")
        if not os.path.exists(readme_path):
            return {"exists": False}
            
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {
            "exists": True,
            "length": len(content),
            "has_description": bool(re.search(r'##\s*Description|#\s*About', content, re.I))
        }
    
    async def _analyze_tech_stack(self) -> Dict[str, Any]:
        """Analyze tech stack from various configuration files."""
        tech_stack = set()
        
        # Check package.json
        package_json = os.path.join(self.temp_dir, "package.json")
        if os.path.exists(package_json):
            import json
            with open(package_json, 'r') as f:
                data = json.load(f)
                if "dependencies" in data:
                    tech_stack.update(data["dependencies"].keys())
                if "devDependencies" in data:
                    tech_stack.update(data["devDependencies"].keys())
        
        return {
            "technologies": list(tech_stack)
        }
    
    async def _analyze_structure(self) -> Dict[str, bool]:
        """Analyze project structure and organization."""
        return {
            "has_public_dir": os.path.exists(os.path.join(self.temp_dir, "public")),
            "has_src_dir": os.path.exists(os.path.join(self.temp_dir, "src")),
            "has_assets_dir": os.path.exists(os.path.join(self.temp_dir, "assets")),
            "has_css_dir": os.path.exists(os.path.join(self.temp_dir, "css")) or 
                          os.path.exists(os.path.join(self.temp_dir, "styles"))
        }
    
    def _find_html_files(self) -> list:
        """Find all HTML files in the repository."""
        html_files = []
        for root, _, files in os.walk(self.temp_dir):
            for file in files:
                if file.endswith('.html'):
                    html_files.append(os.path.join(root, file))
        return html_files
    
    def _find_section(self, soup: BeautifulSoup, section_name: str) -> Any:
        """Find a section using various methods."""
        # Try common section identifiers
        section = soup.find(id=re.compile(f'{section_name}|{section_name}-section', re.I))
        if not section:
            section = soup.find(class_=re.compile(f'{section_name}|{section_name}-section', re.I))
        if not section:
            section = soup.find('section', string=re.compile(section_name, re.I))
        return section
    
    def _extract_project_summary(self, project_element: Any) -> str:
        """Extract project summary from project element."""
        summary = project_element.find(class_=re.compile(r'summary|description|content'))
        return summary.get_text().strip() if summary else ""
    
    def _extract_hero_image(self, project_element: Any) -> str:
        """Extract hero image URL from project element."""
        img = project_element.find('img')
        return img.get('src', '') if img else ""
    
    def _extract_project_tech_stack(self, project_element: Any) -> list:
        """Extract tech stack from project element."""
        tech_stack = []
        tech_elements = project_element.find_all(class_=re.compile(r'tech|stack|technology'))
        for tech in tech_elements:
            tech_stack.append(tech.get_text().strip())
        return tech_stack
    
    def _extract_deployed_link(self, project_element: Any) -> str:
        """Extract deployed link from project element."""
        link = project_element.find('a', href=True)
        return link.get('href', '') if link else "" 