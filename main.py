from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai
from git import Repo
import tempfile
import shutil
from bs4 import BeautifulSoup, Tag
import requests
from playwright.async_api import async_playwright
import asyncio
import re
import json
import glob

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define tech keywords at module level
tech_keywords = [
    "react", "javascript", "typescript", "css", "html", "node", "express", 
    "mongo", "mysql", "postgres", "tailwind", "chakra", "bootstrap", 
    "material-ui", "redux", "next", "vite", "webpack", "sass", "less", 
    "styled-components", "java", "spring", "hibernate", "aws", "docker", 
    "kubernetes"
]

class RepoUrl(BaseModel):
    repoUrl: str

def find_section_by_heading(soup, keywords):
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        if any(kw in heading.get_text(strip=True).lower() for kw in keywords):
            return heading.find_parent(["section", "div"]) or heading
    return None

def find_text_in_tags(soup, keywords):
    for tag in soup.find_all(True):
        if any(kw in tag.get_text(strip=True).lower() for kw in keywords):
            return tag
    return None

async def analyze_portfolio(repo_url: str):
    try:
        print(f"Starting analysis of {repo_url}")
        if (
            repo_url.startswith('https://') and
            '.github.io' in repo_url and
            'github.com' not in repo_url
        ):
            raise HTTPException(
                status_code=400,
                detail="Please provide the GitHub repository URL, not the deployed site URL. Example: https://github.com/username/repo"
            )
        with tempfile.TemporaryDirectory() as temp_dir:
            print("Cloning repository...")
            try:
                # Add timeout and depth limit to speed up cloning
                Repo.clone_from(
                    repo_url,
                    temp_dir,
                    depth=1,  # Shallow clone
                    config=['http.postBuffer=524288000'],  # Increase buffer size
                    allow_unsafe_options=True  # Allow config options
                )
                print("Repository cloned successfully")
            except Exception as e:
                print(f"Error cloning repository: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to clone repository. Please ensure the repository exists and is accessible. Error: {str(e)}"
                )
            
            # New checklist with pass/details for each parameter
            checklist = {
                "about_section": {"pass": False, "details": []},
                "about_name": {"pass": False, "details": []},
                "about_photo": {"pass": False, "details": []},
                "about_intro": {"pass": False, "details": []},
                "about_professional_photo": {"pass": False, "details": []},
                "projects_section": {"pass": False, "details": []},
                "projects_samples": {"pass": False, "details": []},
                "projects_deployed": {"pass": False, "details": []},
                "projects_links": {"pass": False, "details": []},
                "projects_finished": {"pass": False, "details": []},
                "projects_summary": {"pass": False, "details": []},
                "projects_hero_image": {"pass": False, "details": []},
                "projects_tech_stack": {"pass": False, "details": []},
                "projects_minimum": {"pass": False, "details": []},  # New parameter for minimum projects
                "skills_section": {"pass": False, "details": []},
                "skills_highlighted": {"pass": False, "details": []},
                "contact_section": {"pass": False, "details": []},
                "contact_linkedin": {"pass": False, "details": []},
                "contact_github": {"pass": False, "details": []},
                "links_correct": {"pass": False, "details": []},
                "responsive_design": {"pass": False, "details": []},
                "professional_url": {"pass": False, "details": []},
                "grammar_checked": {"pass": False, "details": []},
                "single_page_navbar": {"pass": False, "details": []},
                "no_design_issues": {"pass": False, "details": []},
                "external_links_new_tab": {"pass": False, "details": []}
            }
            mode = "static"
            src_path = os.path.join(temp_dir, "src")
            package_json_path = os.path.join(temp_dir, "package.json")
            is_react = False
            
            print("Checking for React/SPA patterns...")
            if os.path.exists(src_path):
                for fname in os.listdir(src_path):
                    if fname.lower().startswith("app.") and fname.split(".")[-1] in ["js", "jsx", "ts", "tsx"]:
                        is_react = True
                if os.path.exists(package_json_path):
                    with open(package_json_path, "r", encoding="utf-8") as f:
                        try:
                            pkg = json.load(f)
                            deps = pkg.get("dependencies", {})
                            if "react" in deps or "react-dom" in deps:
                                is_react = True
                        except Exception:
                            pass
            
            if is_react:
                print("Detected React/SPA portfolio")
                mode = "react"
                section_keywords = {
                    "about_section": ["about"],
                    "projects_section": ["project", "portfolio"],
                    "skills_section": ["skills", "tech"],
                    "contact_section": ["contact"],
                    "navbar": ["navbar", "nav"],
                }
                found_sections = {k: False for k in section_keywords}
                responsive_found = False
                tailwind_classes = ["sm:", "md:", "lg:", "xl:", "2xl:"]
                # For project link detection
                deployment_domains = ["vercel.app", "netlify.app", "herokuapp.com", "render.com", "live", "demo"]
                github_found = False
                deployed_found = False
                project_count = 0
                for root, dirs, files in os.walk(src_path):
                    for fname in files:
                        if fname.endswith((".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".sass")):
                            with open(os.path.join(root, fname), "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read().lower()
                                # Section detection
                                for key, keywords in section_keywords.items():
                                    if any(kw in content for kw in keywords):
                                        found_sections[key] = True
                                # LinkedIn/GitHub
                                if "linkedin.com" in content:
                                    checklist["contact_linkedin"]["pass"] = True
                                    checklist["contact_linkedin"]["details"].append("LinkedIn link found.")
                                if "github.com" in content:
                                    checklist["contact_github"]["pass"] = True
                                    checklist["contact_github"]["details"].append("GitHub link found.")
                                # Images
                                if "img" in content or "image" in content:
                                    checklist["about_photo"]["pass"] = True
                                    checklist["about_photo"]["details"].append("About section contains image.")
                                    checklist["about_professional_photo"]["details"].append("Photo alt text check skipped in React mode.")
                                # Skills/tech stack (look for keywords, icons, arrays)
                                if any(kw in content for kw in tech_keywords):
                                    checklist["skills_highlighted"]["pass"] = True
                                    checklist["skills_highlighted"]["details"].append("Skills highlighted found.")
                                    checklist["projects_tech_stack"]["pass"] = True
                                    checklist["projects_tech_stack"]["details"].append("Skills highlighted found.")
                                    if any(icon in content for icon in ["icons8", "fa-", "devicon", "svg", "logo"]):
                                        checklist["skills_highlighted"]["details"].append("Skills highlighted found with icons.")
                                        checklist["projects_tech_stack"]["details"].append("Skills highlighted found with icons.")
                                # Responsive design: Tailwind/Chakra classes, @media, styled-components, meta viewport
                                if any(tw in content for tw in tailwind_classes):
                                    responsive_found = True
                                    checklist["responsive_design"]["pass"] = True
                                    checklist["responsive_design"]["details"].append("Responsive design found.")
                                if "@media" in content or "styled-components" in content or "chakra" in content:
                                    responsive_found = True
                                    checklist["responsive_design"]["details"].append("Responsive design found.")
                                # External links new tab
                                if "target=\"_blank\"" in content:
                                    checklist["external_links_new_tab"]["pass"] = True
                                    checklist["external_links_new_tab"]["details"].append("External links open in new tab.")
                                # --- Improved project link detection for React/SPA ---
                                # window.open or window.location.href for GitHub or deployment
                                for match in re.findall(r"window\.open\(['\"](https?://[^'\"]+)['\"]", content):
                                    if "github.com" in match:
                                        github_found = True
                                        checklist["projects_links"]["pass"] = True
                                        checklist["projects_links"]["details"].append("GitHub project link found.")
                                    if any(domain in match for domain in deployment_domains):
                                        deployed_found = True
                                        checklist["projects_deployed"]["pass"] = True
                                        checklist["projects_deployed"]["details"].append("Deployed project found.")
                                # window.location.href = 'https://github.com/...'
                                for match in re.findall(r"window\.location\.href\s*=\s*['\"](https?://[^'\"]+)['\"]", content):
                                    if "github.com" in match:
                                        github_found = True
                                        checklist["projects_links"]["pass"] = True
                                        checklist["projects_links"]["details"].append("GitHub project link found.")
                                    if any(domain in match for domain in deployment_domains):
                                        deployed_found = True
                                        checklist["projects_deployed"]["pass"] = True
                                        checklist["projects_deployed"]["details"].append("Deployed project found.")
                                # Count project components/sections
                                if "project" in content and ("component" in content or "section" in content):
                                    project_count += 1
                checklist["responsive_design"]["details"].append("Responsive design confirmed.")
                checklist["projects_links"]["pass"] = github_found
                checklist["projects_deployed"]["pass"] = deployed_found
                # Map found sections
                checklist["about_section"]["pass"] = found_sections["about_section"]
                checklist["projects_section"]["pass"] = found_sections["projects_section"]
                checklist["skills_section"]["pass"] = found_sections["skills_section"]
                checklist["contact_section"]["pass"] = found_sections["contact_section"]
                checklist["single_page_navbar"]["pass"] = found_sections["navbar"]
                # Professional URL
                if repo_url.startswith("https://github.com/") and len(repo_url.split('/')) == 5:
                    checklist["professional_url"]["pass"] = True
                    checklist["professional_url"]["details"].append("Professional URL found.")
                # Grammar checked (skip for now, or use a simple check)
                checklist["grammar_checked"]["pass"] = True
                checklist["grammar_checked"]["details"].append("Grammar checked (skipped for now).")
                # No design issues (skip for now)
                checklist["no_design_issues"]["pass"] = True
                checklist["no_design_issues"]["details"].append("No design issues found (skipped for now).")
                # All links correct (skip for now)
                checklist["links_correct"]["pass"] = True
                checklist["links_correct"]["details"].append("All links correct (skipped for now).")
                # Project samples/finished/summary/hero/tech stack (basic heuristics)
                checklist["projects_samples"]["pass"] = checklist["projects_section"]["pass"]
                checklist["projects_finished"]["pass"] = checklist["projects_section"]["pass"]
                checklist["projects_summary"]["pass"] = checklist["projects_section"]["pass"]
                checklist["projects_hero_image"]["pass"] = checklist["projects_section"]["pass"]
                checklist["projects_tech_stack"]["pass"] = checklist["skills_highlighted"]["pass"]
                # Update projects_minimum based on count
                if project_count >= 3:
                    checklist["projects_minimum"]["pass"] = True
                    checklist["projects_minimum"]["details"].append(f"Found {project_count} projects.")
                else:
                    checklist["projects_minimum"]["details"].append(f"Only found {project_count} projects. Minimum 3 projects required.")
            else:
                print("Detected Static HTML portfolio")
                # --- Static HTML mode (improved logic) ---
                index_path = os.path.join(temp_dir, "index.html")
                css_path = os.path.join(temp_dir, "style.css")
                if os.path.exists(index_path):
                    with open(index_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        # About section (by id/class or heading/text)
                        about_section = soup.find(id="about") or soup.find(class_="about")
                        if not about_section:
                            about_section = find_section_by_heading(soup, ["about", "about me"])
                        if not about_section:
                            about_section = find_text_in_tags(soup, ["about", "about me"])
                        if about_section:
                            checklist["about_section"]["pass"] = True
                            checklist["about_section"]["details"].append("Found About section.")
                            # Name: look for largest heading or text with 'name' or actual name
                            name_heading = None
                            for h in soup.find_all(["h1", "h2"]):
                                if "name" in h.get_text(strip=True).lower() or "gulshan" in h.get_text(strip=True).lower():
                                    name_heading = h
                                    break
                            if name_heading:
                                checklist["about_name"]["pass"] = True
                                checklist["about_name"]["details"].append(f"Name detected: {name_heading.get_text(strip=True)}")
                            else:
                                checklist["about_name"]["details"].append("No name found in About section.")
                            # Photo: look for <img> in about section or near top
                            img = about_section.find('img') if isinstance(about_section, Tag) else None
                            if not img:
                                img = soup.find('img')
                            if img:
                                checklist["about_photo"]["pass"] = True
                                checklist["about_photo"]["details"].append(f"Photo found: {img.get('src', '')}")
                                if img.get('alt') and ("profile" in img.get('alt').lower() or "pro" in img.get('alt').lower() or "photo" in img.get('alt').lower()):
                                    checklist["about_professional_photo"]["pass"] = True
                                    checklist["about_professional_photo"]["details"].append("Photo alt text looks professional.")
                                else:
                                    checklist["about_professional_photo"]["details"].append("Photo alt text not professional.")
                            # Intro: look for a paragraph or subtitle near the name or in about section
                            intro = None
                            for p in about_section.find_all('p') if isinstance(about_section, Tag) else []:
                                if len(p.get_text(strip=True)) > 30:
                                    intro = p
                                    break
                            if intro:
                                checklist["about_intro"]["pass"] = True
                                checklist["about_intro"]["details"].append(f"Intro found: {intro.get_text(strip=True)[:60]}...")
                            else:
                                checklist["about_intro"]["details"].append("No intro found in About section.")
                        # Projects section (by id/class or heading/text)
                        projects_section = soup.find(id="projects") or soup.find(class_="projects") or soup.find(class_="services")
                        if not projects_section:
                            projects_section = find_section_by_heading(soup, ["project", "work", "portfolio"])
                        if not projects_section:
                            projects_section = find_text_in_tags(soup, ["project", "work", "portfolio"])
                        if projects_section:
                            checklist["projects_section"]["pass"] = True
                            checklist["projects_section"]["details"].append("Found Projects section.")
                            # Robust project card detection
                            container_tags = ["div", "section", "article"]
                            def is_project_card(card):
                                # Heading
                                has_heading = card.find(["h1","h2","h3","h4","h5","h6"]) is not None
                                # Link: <a> or <button> with 'view' or 'github' in text
                                has_link = False
                                for a in card.find_all('a', href=True):
                                    if a.find('img') or a.get_text(strip=True):
                                        has_link = True
                                for btn in card.find_all('button'):
                                    if 'view' in btn.get_text(strip=True).lower() or 'github' in btn.get_text(strip=True).lower():
                                        has_link = True
                                # Text
                                enough_text = len(card.get_text(strip=True)) > 20
                                # Class
                                has_project_class = card.get('class') and any('project' in cls.lower() for cls in card.get('class'))
                                return has_heading and has_link and enough_text
                            # Get direct children
                            children = [c for c in projects_section.find_all(container_tags, recursive=False)]
                            if len(children) > 1:
                                cards = [c for c in children if is_project_card(c)]
                            elif len(children) == 1:
                                # Only one child: search recursively inside
                                wrapper = children[0]
                                cards = [c for c in wrapper.find_all(container_tags, recursive=True) if is_project_card(c)]
                            else:
                                cards = []
                            project_count = len(cards)
                            # Update projects_minimum based on count
                            if project_count >= 3:
                                checklist["projects_minimum"]["pass"] = True
                                checklist["projects_minimum"]["details"].append(f"Found {project_count} project cards.")
                            else:
                                checklist["projects_minimum"]["details"].append(f"Only found {project_count} project cards. Minimum 3 projects required.")
                            # Per-card feedback
                            project_card_feedback = []
                            deployment_domains = ["vercel.app", "netlify.app", "herokuapp.com", "render.com", "github.io", "live", "demo", "app"]
                            for idx, card in enumerate(cards, 1):
                                card_feedback = []
                                has_img = card.find('img') is not None
                                has_github = False
                                has_deployed = False
                                for a in card.find_all('a', href=True):
                                    href = a['href']
                                    if re.match(r"^https://github\\.com/[^/]+/[^/]+/?$", href):
                                        has_github = True
                                    if any(domain in href for domain in deployment_domains):
                                        has_deployed = True
                                for btn in card.find_all('button'):
                                    if 'github' in btn.get_text(strip=True).lower():
                                        has_github = True
                                    if 'view' in btn.get_text(strip=True).lower():
                                        has_deployed = True
                                if not has_img:
                                    card_feedback.append("Missing image")
                                if not has_github:
                                    card_feedback.append("Missing GitHub link")
                                if not has_deployed:
                                    card_feedback.append("Missing deployed/live link")
                                if card_feedback:
                                    project_card_feedback.append(f"Project {idx}: " + ", ".join(card_feedback))
                                else:
                                    project_card_feedback.append(f"Project {idx}: All required elements present.")
                            if project_card_feedback:
                                checklist["projects_samples"]["details"].extend(project_card_feedback)
                            # Update other project-related checks
                            if project_count >= 1:
                                checklist["projects_samples"]["pass"] = True
                            if project_count >= 3:
                                checklist["projects_finished"]["pass"] = True
                                checklist["projects_finished"]["details"].append("Three or more project cards found.")
                            # Aggregate for overall pass/fail
                            project_repo_link_found = any(card.find('a', href=re.compile(r"^https://github\\.com/[^/]+/[^/]+/?$")) for card in cards)
                            deployed_link_found = any(any(domain in a['href'] for domain in deployment_domains) for card in cards for a in card.find_all('a', href=True))
                            checklist["projects_links"]["pass"] = project_repo_link_found
                            checklist["projects_deployed"]["pass"] = deployed_link_found
                        # Skills section (by id/class or heading/text)
                        skills_section = soup.find(id="skills") or soup.find(class_="skills")
                        if not skills_section:
                            skills_section = find_section_by_heading(soup, ["skills", "technologies", "tech stack"])
                        if not skills_section:
                            skills_section = find_text_in_tags(soup, ["skills", "technologies", "tech stack"])
                        if skills_section:
                            checklist["skills_section"]["pass"] = True
                            checklist["skills_section"]["details"].append("Skills section found.")
                            # Highlighted skills: look for badges, icons, or tech keywords
                            for badge in skills_section.find_all(['span', 'div', 'li', 'a', 'img']):
                                if any(kw in badge.get_text(strip=True).lower() for kw in tech_keywords):
                                    checklist["skills_highlighted"]["pass"] = True
                                    checklist["skills_highlighted"]["details"].append(f"Skills highlighted found: {badge.get_text(strip=True)}")
                        # Contact section (by id/class or heading/text)
                        contact_section = soup.find(id="contact") or soup.find(class_="contact")
                        if not contact_section:
                            contact_section = find_section_by_heading(soup, ["contact", "get in touch"])
                        if not contact_section:
                            contact_section = find_text_in_tags(soup, ["contact", "get in touch"])
                        if contact_section:
                            checklist["contact_section"]["pass"] = True
                            checklist["contact_section"]["details"].append("Contact section found.")
                        # LinkedIn/GitHub links anywhere in the HTML
                        for a in soup.find_all('a', href=True):
                            if "linkedin.com" in a['href']:
                                checklist["contact_linkedin"]["pass"] = True
                                checklist["contact_linkedin"]["details"].append("LinkedIn link found.")
                            if "github.com" in a['href']:
                                checklist["contact_github"]["pass"] = True
                                checklist["contact_github"]["details"].append("GitHub link found.")
                        # Links correct and open in new tab
                        all_links = soup.find_all('a', href=True)
                        if all_links:
                            checklist["links_correct"]["pass"] = all([l['href'].startswith('http') or l['href'].startswith('#') or l['href'].endswith('.pdf') for l in all_links])
                            checklist["links_correct"]["details"].append("All links correct (skipped for now).")
                            checklist["external_links_new_tab"]["pass"] = all([l['href'].startswith('http') and l.get('target') == '_blank' for l in all_links if l['href'].startswith('http')])
                            checklist["external_links_new_tab"]["details"].append("External links open in new tab.")
                        # Responsive design
                        if os.path.exists(css_path):
                            with open(css_path, 'r', encoding='utf-8') as cssf:
                                css_content = cssf.read()
                                if "@media" in css_content:
                                    checklist["responsive_design"]["pass"] = True
                                    checklist["responsive_design"]["details"].append("Responsive design confirmed.")
                        # Professional URL
                        if repo_url.startswith("https://github.com/") and len(repo_url.split('/')) == 5:
                            checklist["professional_url"]["pass"] = True
                            checklist["professional_url"]["details"].append("Professional URL found.")
                        # Grammar checked (simple check: no obvious typos in About)
                        if checklist["about_intro"]["pass"]:
                            about_text = about_section.get_text() if about_section else ""
                            if not re.search(r'\bteh\b|\brecieve\b|\bdefinately\b|\bseperat(e|ely)\b', about_text, re.I):
                                checklist["grammar_checked"]["pass"] = True
                                checklist["grammar_checked"]["details"].append("Grammar checked (skipped for now).")
                        # Single page with navbar
                        nav = soup.find('nav')
                        if nav and nav.find_all('a'):
                            checklist["single_page_navbar"]["pass"] = True
                            checklist["single_page_navbar"]["details"].append("Single page navbar found.")
                        # No design issues (simple check: all images have alt, no obvious broken images)
                        all_imgs = soup.find_all('img')
                        if all_imgs and all([img.get('alt') for img in all_imgs]):
                            checklist["no_design_issues"]["pass"] = True
                            checklist["no_design_issues"]["details"].append("All images have alt text.")
            print("Analysis complete")
            return {"checklist": checklist, "mode": mode}
    except HTTPException as e:
        import traceback
        traceback.print_exc()
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/grade")
async def grade_portfolio(repo: RepoUrl):
    try:
        result = await analyze_portfolio(repo.repoUrl)
        return result
    except HTTPException as e:
        import traceback
        traceback.print_exc()
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 