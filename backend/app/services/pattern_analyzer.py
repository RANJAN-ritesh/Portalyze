from typing import Dict, Any, List, Set
from bs4 import BeautifulSoup
import re
from collections import defaultdict

class PortfolioPatternAnalyzer:
    def __init__(self):
        # Umbrella section patterns (primary detection)
        self.umbrella_sections = {
            'about': {
                'ids': {
                    'about', 'about-me', 'aboutdiv', 'about_me', 'about_me2',
                    'about-section', 'about-container', 'about-wrapper',
                    'about-content', 'about-details', 'about-info',
                    'bio', 'biography', 'profile', 'personal-info'
                },
                'classes': {
                    'about', 'about-section', 'about-details', 'about-details-mobile',
                    'about-container', 'about-wrapper', 'about-content',
                    'about-info', 'about-text', 'about-description',
                    'bio', 'biography', 'profile', 'personal-info',
                    'about-me', 'about-myself', 'about-page'
                },
                'headings': {
                    'about', 'about me', 'about myself', 'hi, i\'m', 'hello, i\'m',
                    'welcome', 'introduction', 'who am i', 'my story',
                    'biography', 'profile', 'personal info', 'get to know me',
                    'about myself', 'my background', 'my journey'
                }
            },
            'intro': {
                'ids': {
                    'home', 'home-content', 'intro', 'introduction',
                    'hero', 'hero-section', 'main', 'main-content',
                    'welcome', 'welcome-section', 'landing', 'landing-page',
                    'header', 'header-content', 'banner', 'banner-section'
                },
                'classes': {
                    'home', 'intro', 'introduction', 'hero',
                    'hero-section', 'main', 'main-content',
                    'welcome', 'welcome-section', 'landing',
                    'landing-page', 'header', 'header-content',
                    'banner', 'banner-section', 'hero-container'
                },
                'headings': {
                    'hi, i\'m', 'hello, i\'m', 'welcome', 'introduction',
                    'hi there', 'hello there', 'greetings', 'welcome to my portfolio',
                    'i am', 'my name is', 'welcome to my site',
                    'full stack developer', 'software engineer', 'web developer'
                }
            },
            'skills': {
                'ids': {
                    'skills', 'skillAbout', 'tech-stack', 'technologies',
                    'expertise', 'capabilities', 'abilities', 'competencies',
                    'tech-skills', 'technical-skills', 'core-skills',
                    'frontend', 'backend', 'fullstack', 'tools'
                },
                'classes': {
                    'skills', 'skill-section', 'tech-stack', 'technologies',
                    'expertise', 'capabilities', 'abilities', 'competencies',
                    'tech-skills', 'technical-skills', 'core-skills',
                    'frontend', 'backend', 'fullstack', 'tools',
                    'skill-container', 'skill-wrapper', 'skill-grid',
                    'tech-stack-container', 'technologies-container'
                },
                'headings': {
                    'skills', 'my skills', 'technical skills', 'tech stack',
                    'technologies', 'expertise', 'capabilities', 'abilities',
                    'what i do', 'my expertise', 'core competencies',
                    'frontend skills', 'backend skills', 'full stack skills',
                    'tools & technologies', 'tech stack & tools'
                }
            },
            'projects': {
                'ids': {
                    'projects', 'projectsdiv', 'project-sec', 'portfolio',
                    'work', 'works', 'showcase', 'showcase-section',
                    'portfolio-section', 'portfolio-container',
                    'my-work', 'my-projects', 'project-showcase',
                    'recent-work', 'featured-projects'
                },
                'classes': {
                    'projects', 'project-section', 'portfolio', 'projects-grid',
                    'work', 'works', 'showcase', 'showcase-section',
                    'portfolio-section', 'portfolio-container',
                    'my-work', 'my-projects', 'project-showcase',
                    'recent-work', 'featured-projects',
                    'project-container', 'project-wrapper',
                    'project-grid', 'project-list'
                },
                'headings': {
                    'projects', 'my projects', 'portfolio', 'work',
                    'my work', 'showcase', 'featured projects',
                    'recent projects', 'selected works',
                    'what i\'ve built', 'my portfolio',
                    'project showcase', 'recent work',
                    'featured work', 'selected projects'
                }
            },
            'contact': {
                'ids': {
                    'contact', 'contact-email', 'contact-phone', 'get-in-touch',
                    'contact-section', 'contact-container', 'contact-form',
                    'contact-info', 'contact-details', 'reach-out',
                    'connect', 'connect-section', 'message', 'message-section'
                },
                'classes': {
                    'contact', 'contact-section', 'get-in-touch',
                    'contact-container', 'contact-wrapper',
                    'contact-form', 'contact-info', 'contact-details',
                    'reach-out', 'connect', 'connect-section',
                    'message', 'message-section', 'contact-grid',
                    'contact-box', 'contact-card'
                },
                'headings': {
                    'contact', 'contact me', 'get in touch', 'reach out',
                    'connect', 'let\'s connect', 'get in contact',
                    'send a message', 'drop a message', 'say hello',
                    'contact information', 'contact details',
                    'let\'s talk', 'reach me at', 'connect with me'
                }
            }
        }
        
        # Detailed patterns (secondary detection)
        self.section_patterns = defaultdict(set)
        self.project_patterns = defaultdict(set)
        self.skill_patterns = defaultdict(set)
        self.contact_patterns = defaultdict(set)
        
        # Content quality metrics
        self.content_metrics = {
            'min_section_length': 50,  # Minimum characters for a valid section
            'min_project_description': 100,  # Minimum characters for project description
            'min_skill_count': 5,  # Minimum number of skills to be considered valid
            'required_sections': {'about', 'projects', 'skills', 'contact'}
        }
        
        # Technical stack patterns
        self.tech_stack_patterns = {
            'frontend': {
                'frameworks': {'react', 'vue', 'angular', 'svelte'},
                'libraries': {'jquery', 'bootstrap', 'tailwind', 'material-ui'},
                'build_tools': {'webpack', 'vite', 'parcel', 'rollup'}
            },
            'backend': {
                'frameworks': {'express', 'django', 'flask', 'spring', 'rails'},
                'databases': {'mongodb', 'postgresql', 'mysql', 'redis'},
                'apis': {'rest', 'graphql', 'grpc'}
            }
        }
        
    def analyze_portfolio(self, html_content: str) -> Dict[str, Any]:
        """Analyze a single portfolio to extract patterns and quality metrics."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # First pass: Try to find sections using umbrella terms
            sections = self._find_umbrella_sections(soup)
            
            # Second pass: If sections not found, use detailed pattern analysis
            if not any(sections.values()):
                self._analyze_section_patterns(soup)
                self._analyze_project_patterns(soup)
                self._analyze_skill_patterns(soup)
                self._analyze_contact_patterns(soup)
            
            # Analyze content quality
            quality_metrics = self._analyze_content_quality(soup, sections)
            
            # Analyze technical stack
            tech_stack = self._analyze_technical_stack(soup)
            
            # Get base patterns
            patterns = self.get_patterns()
            
            # Add quality metrics and tech stack to patterns
            patterns.update({
                'quality_metrics': quality_metrics,
                'tech_stack': tech_stack
            })
            
            return patterns
        except Exception as e:
            print(f"Error in pattern analysis: {str(e)}")
            return self.get_patterns()
    
    def _find_umbrella_sections(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Find sections using umbrella terms."""
        sections = {}
        
        for section_name, patterns in self.umbrella_sections.items():
            # Look for sections by ID
            for section_id in patterns['ids']:
                element = soup.find(id=re.compile(section_id, re.I))
                if element:
                    sections[section_name] = element
                    break
            
            # If not found by ID, look by class
            if section_name not in sections:
                for section_class in patterns['classes']:
                    element = soup.find(class_=re.compile(section_class, re.I))
                    if element:
                        sections[section_name] = element
                        break
            
            # If still not found, look by heading
            if section_name not in sections:
                for heading_text in patterns['headings']:
                    heading = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], 
                                     string=re.compile(heading_text, re.I))
                    if heading:
                        # Get the parent section
                        section = heading.find_parent(['section', 'div', 'article'])
                        if section:
                            sections[section_name] = section
                            break
        
        return sections
    
    def _analyze_section_patterns(self, soup: BeautifulSoup):
        """Extract patterns for section identification (fallback method)."""
        try:
            # Look for section containers
            for section in soup.find_all(['section', 'div', 'article']):
                # Check IDs
                if section.get('id'):
                    self.section_patterns['ids'].add(section.get('id'))
                
                # Check classes
                if section.get('class'):
                    self.section_patterns['classes'].update(section.get('class'))
                
                # Check headings
                heading = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if heading:
                    self.section_patterns['headings'].add(heading.get_text().strip().lower())
        except Exception as e:
            print(f"Error in section pattern analysis: {str(e)}")
    
    def _analyze_project_patterns(self, soup: BeautifulSoup):
        """Extract patterns for project identification."""
        try:
            # Look for project containers
            for container in soup.find_all(['div', 'article']):
                # Check if it looks like a project
                if self._looks_like_project(container):
                    # Check IDs
                    if container.get('id'):
                        self.project_patterns['ids'].add(container.get('id'))
                    
                    # Check classes
                    if container.get('class'):
                        self.project_patterns['classes'].update(container.get('class'))
                    
                    # Check structure
                    self._analyze_project_structure(container)
        except Exception as e:
            print(f"Error in project pattern analysis: {str(e)}")
    
    def _analyze_project_structure(self, container: BeautifulSoup):
        """Analyze the structure of a project container."""
        try:
            # Title patterns
            title = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if title and title.get('class'):
                self.project_patterns['title_classes'].add(title.get('class')[0])
            
            # Description patterns
            desc = container.find(['p', 'div'], class_=re.compile(r'description|summary|about', re.I))
            if desc and desc.get('class'):
                self.project_patterns['description_classes'].add(desc.get('class')[0])
            
            # Link patterns
            links = container.find_all('a')
            for link in links:
                href = link.get('href', '')
                if 'github.com' in href and link.get('class'):
                    self.project_patterns['github_link_classes'].add(link.get('class')[0])
                elif any(x in href for x in ['netlify', 'vercel', 'heroku']) and link.get('class'):
                    self.project_patterns['deploy_link_classes'].add(link.get('class')[0])
        except Exception as e:
            print(f"Error in project structure analysis: {str(e)}")
    
    def _analyze_skill_patterns(self, soup: BeautifulSoup):
        """Extract patterns for skill identification."""
        try:
            # Look for skill containers
            for container in soup.find_all(['div', 'ul', 'li']):
                if self._looks_like_skill(container):
                    # Check IDs
                    if container.get('id'):
                        self.skill_patterns['ids'].add(container.get('id'))
                    
                    # Check classes
                    if container.get('class'):
                        self.skill_patterns['classes'].update(container.get('class'))
                    
                    # Check structure
                    self._analyze_skill_structure(container)
        except Exception as e:
            print(f"Error in skill pattern analysis: {str(e)}")
    
    def _analyze_skill_structure(self, container: BeautifulSoup):
        """Analyze the structure of a skill container."""
        try:
            # Icon patterns
            icon = container.find('img')
            if icon and icon.get('class'):
                self.skill_patterns['icon_classes'].add(icon.get('class')[0])
            
            # Text patterns
            text = container.find(['span', 'p', 'div'])
            if text and text.get('class'):
                self.skill_patterns['text_classes'].add(text.get('class')[0])
        except Exception as e:
            print(f"Error in skill structure analysis: {str(e)}")
    
    def _analyze_contact_patterns(self, soup: BeautifulSoup):
        """Extract patterns for contact section identification."""
        try:
            # Look for contact containers
            for container in soup.find_all(['div', 'section', 'form']):
                if self._looks_like_contact(container):
                    # Check IDs
                    if container.get('id'):
                        self.contact_patterns['ids'].add(container.get('id'))
                    
                    # Check classes
                    if container.get('class'):
                        self.contact_patterns['classes'].update(container.get('class'))
                    
                    # Check structure
                    self._analyze_contact_structure(container)
        except Exception as e:
            print(f"Error in contact pattern analysis: {str(e)}")
    
    def _analyze_contact_structure(self, container: BeautifulSoup):
        """Analyze the structure of a contact container."""
        try:
            # Form patterns
            form = container.find('form')
            if form and form.get('class'):
                self.contact_patterns['form_classes'].add(form.get('class')[0])
            
            # Social link patterns
            social_links = container.find_all('a', href=re.compile(r'linkedin|github|twitter', re.I))
            for link in social_links:
                if link.get('class'):
                    self.contact_patterns['social_link_classes'].add(link.get('class')[0])
        except Exception as e:
            print(f"Error in contact structure analysis: {str(e)}")
    
    def _looks_like_project(self, container: BeautifulSoup) -> bool:
        """Check if a container looks like a project."""
        try:
            # Must have a title
            title = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if not title:
                return False
            
            # Must have at least two of: description, image, or links
            has_description = bool(container.find(['p', 'div'], class_=re.compile(r'description|summary|about', re.I)))
            has_image = bool(container.find('img'))
            has_links = bool(container.find('a', href=re.compile(r'github|netlify|vercel|heroku', re.I)))
            
            return sum([has_description, has_image, has_links]) >= 2
        except Exception:
            return False
    
    def _looks_like_skill(self, container: BeautifulSoup) -> bool:
        """Check if a container looks like a skill."""
        try:
            # Must have either an icon or text
            has_icon = bool(container.find('img'))
            has_text = bool(container.find(['span', 'p', 'div']))
            
            return has_icon or has_text
        except Exception:
            return False
    
    def _looks_like_contact(self, container: BeautifulSoup) -> bool:
        """Check if a container looks like a contact section."""
        try:
            # Must have either a form or social links
            has_form = bool(container.find('form'))
            has_social = bool(container.find('a', href=re.compile(r'linkedin|github|twitter', re.I)))
            
            return has_form or has_social
        except Exception:
            return False
    
    def get_patterns(self) -> Dict[str, Any]:
        """Get all discovered patterns."""
        def convert_sets_to_lists(d: Dict[str, Any]) -> Dict[str, Any]:
            """Convert all sets in a dictionary to lists."""
            result = {}
            for k, v in d.items():
                if isinstance(v, set):
                    result[k] = list(v)
                elif isinstance(v, dict):
                    result[k] = convert_sets_to_lists(v)
                else:
                    result[k] = v
            return result
        
        return convert_sets_to_lists({
            "umbrella_sections": self.umbrella_sections,
            "section_patterns": dict(self.section_patterns),
            "project_patterns": dict(self.project_patterns),
            "skill_patterns": dict(self.skill_patterns),
            "contact_patterns": dict(self.contact_patterns)
        })
    
    def _analyze_content_quality(self, soup: BeautifulSoup, sections: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the quality of content in each section."""
        quality_metrics = {
            'section_coverage': 0,
            'content_quality': {},
            'accessibility': {},
            'performance': {}
        }
        
        # Check section coverage
        found_sections = set(sections.keys())
        quality_metrics['section_coverage'] = len(found_sections.intersection(self.content_metrics['required_sections'])) / len(self.content_metrics['required_sections'])
        
        # Analyze each section
        for section_name, section in sections.items():
            section_metrics = {
                'length': len(section.get_text().strip()),
                'has_images': bool(section.find_all('img')),
                'has_links': bool(section.find_all('a')),
                'heading_structure': self._analyze_heading_structure(section),
                'accessibility_score': self._analyze_accessibility(section)
            }
            quality_metrics['content_quality'][section_name] = section_metrics
        
        return quality_metrics
    
    def _analyze_heading_structure(self, section: BeautifulSoup) -> Dict[str, Any]:
        """Analyze the heading structure of a section."""
        headings = section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        structure = {
            'has_main_heading': False,
            'heading_levels': set(),
            'heading_count': len(headings)
        }
        
        for heading in headings:
            level = int(heading.name[1])
            structure['heading_levels'].add(level)
            if level == 1:
                structure['has_main_heading'] = True
        
        return structure
    
    def _analyze_accessibility(self, section: BeautifulSoup) -> Dict[str, Any]:
        """Analyze accessibility features of a section."""
        accessibility = {
            'has_aria_labels': bool(section.find(attrs={'aria-label': True})),
            'has_alt_text': bool(section.find('img', alt=True)),
            'has_semantic_elements': bool(section.find(['article', 'nav', 'main', 'aside'])),
            'color_contrast_issues': self._check_color_contrast(section)
        }
        return accessibility
    
    def _check_color_contrast(self, section: BeautifulSoup) -> List[str]:
        """Check for potential color contrast issues."""
        issues = []
        # This is a simplified check - in production, use a proper color contrast analyzer
        text_elements = section.find_all(['p', 'span', 'div', 'a'])
        for element in text_elements:
            style = element.get('style', '')
            if 'color:' in style and 'background-color:' not in style:
                issues.append(f"Potential contrast issue: {element.get_text()[:30]}...")
        return issues
    
    def _analyze_technical_stack(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze the technical stack used in the portfolio."""
        tech_stack = {
            'frontend': {'frameworks': set(), 'libraries': set(), 'build_tools': set()},
            'backend': {'frameworks': set(), 'databases': set(), 'apis': set()}
        }
        
        # Check for script tags and their sources
        scripts = soup.find_all('script')
        for script in scripts:
            src = script.get('src', '')
            for category, patterns in self.tech_stack_patterns.items():
                for tech_type, techs in patterns.items():
                    for tech in techs:
                        if tech.lower() in src.lower():
                            tech_stack[category][tech_type].add(tech)
        
        # Check for CSS framework classes
        for element in soup.find_all(class_=True):
            classes = ' '.join(element['class']).lower()
            for tech in self.tech_stack_patterns['frontend']['libraries']:
                if tech.lower() in classes:
                    tech_stack['frontend']['libraries'].add(tech)
        
        return tech_stack 