from typing import Dict, Any
import logging
# Add language_tool_python for grammar checking
try:
    import language_tool_python
    tool = language_tool_python.LanguageTool('en-US')
except ImportError:
    tool = None
    logging.warning("language_tool_python not installed. Grammar checking will be skipped.")

logger = logging.getLogger(__name__)

class PortfolioScorer:
    def __init__(self):
        # Define scoring criteria with weights (total = 100%)
        self.criteria = {
            "sections": {
                "weight": 10,  # 10%
                "description": "Required sections (About, Skills, Projects, Contact)",
                "max_score": 10,
                "check": lambda results: 10 if results["basic_sections"]["has_all_sections"] else 0
            },
            "about_section": {
                "weight": 10,  # 10%
                "description": "About section completeness (name, photo, introduction)",
                "max_score": 10,
                "check": lambda results: 10 if results["about_section"]["is_complete"] else 0
            },
            "projects": {
                "weight": 20,  # 20%
                "description": "Projects section quality (count, details, links)",
                "max_score": 20,
                "check": lambda results: min(20, results["projects_section"]["project_count"] * 5)
            },
            "skills": {
                "weight": 10,  # 10%
                "description": "Skills section completeness",
                "max_score": 10,
                "check": lambda results: 10 if results["skills_section"]["is_complete"] else 0
            },
            "contact": {
                "weight": 10,  # 10%
                "description": "Contact section with social links",
                "max_score": 10,
                "check": lambda results: 10 if results["contact_section"]["is_complete"] else 0
            },
            "links": {
                "weight": 5,  # 5%
                "description": "Working links",
                "max_score": 5,
                "check": lambda results: 5 if results["links"]["is_complete"] else 0
            },
            "responsiveness": {
                "weight": 10,  # 10%
                "description": "Mobile and tablet responsiveness",
                "max_score": 10,
                "check": lambda results: 10 if results["responsiveness"]["is_responsive"] else 0
            },
            "url_professionalism": {
                "weight": 5,  # 5%
                "description": "Professional URL",
                "max_score": 5,
                "check": lambda results: 5 if results["url_professionalism"]["is_professional"] else 0
            },
            "design": {
                "weight": 10,  # 10%
                "description": "Clean design without issues",
                "max_score": 10,
                "check": lambda results: 10 if results["design"]["is_complete"] else 0
            },
            "external_links": {
                "weight": 10,  # 10%
                "description": "External links open in new tabs",
                "max_score": 10,
                "check": lambda results: 10 if results["external_links"]["is_complete"] else 0
            }
        }

    def generate_detailed_report(self, validation_results: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Generate a detailed report with scores for each criterion."""
        scores = {}
        total_score = 0
        total_weight = 0

        # Calculate scores for each criterion
        for criterion, details in self.criteria.items():
            score = details["check"](validation_results)
            weighted_score = (score / details["max_score"]) * details["weight"]
            scores[criterion] = {
                "score": score,
                "max_score": details["max_score"],
                "weight": details["weight"],
                "weighted_score": weighted_score,
                "description": details["description"]
            }
            total_score += weighted_score
            total_weight += details["weight"]

        # Calculate overall percentage
        overall_percentage = (total_score / total_weight) * 100

        # Generate suggestions
        suggestions = self.generate_suggestions(validation_results)

        # Generate detailed report
        report = {
            "portfolio_url": url,
            "scores": scores,
            "overall_score": {
                "raw_score": total_score,
                "max_score": total_weight,
                "percentage": overall_percentage
            },
            "summary": self._generate_summary(validation_results, scores),
            "suggestions": suggestions
        }

        return report

    def generate_suggestions(self, validation_results: Dict[str, Any]) -> list:
        suggestions = []
        # Sections
        if not validation_results["basic_sections"]["has_all_sections"]:
            suggestions.append("Add all required sections: About, Skills, Projects, and Contact.")
        # About
        about = validation_results["about_section"]
        if not about["has_name"]:
            suggestions.append("Include your name in the About section.")
        if not about["has_photo"]:
            suggestions.append("Add a clear, professional photo of yourself in the About or Home section.")
        if not about["has_intro"]:
            suggestions.append("Write a catchy introduction about yourself in the About section.")
        # Projects
        projects = validation_results["projects_section"]
        if not projects["is_complete"] or projects["project_count"] < 2:
            suggestions.append("Showcase at least two of your best projects with summaries, images, and tech stacks.")
        # Skills
        skills = validation_results["skills_section"]
        if not skills["is_complete"]:
            suggestions.append("Highlight your skills and tech stacks in a dedicated section.")
        # Contact
        contact = validation_results["contact_section"]
        if not contact["has_linkedin"]:
            suggestions.append("Add your LinkedIn profile to the Contact section.")
        if not contact["has_github"]:
            suggestions.append("Add your GitHub profile to the Contact section.")
        # Links
        links = validation_results["links"]
        if not links["is_complete"]:
            suggestions.append("Fix all broken or incorrect links in your portfolio.")
        # Responsiveness
        responsiveness = validation_results["responsiveness"]
        if not responsiveness["is_responsive"]:
            suggestions.append("Make your portfolio responsive for mobile and tablet devices.")
        # URL
        url = validation_results["url_professionalism"]
        if not url["is_professional"]:
            suggestions.append("Use a professional and clean URL for your portfolio (consider a custom domain).")
        # Design
        design = validation_results["design"]
        if not design["is_complete"]:
            issues = []
            if not design["has_navbar"]: issues.append("navbar")
            if design["has_font_issues"]: issues.append("font usage")
            if design["has_padding_issues"]: issues.append("spacing/padding")
            if design["has_animation_issues"]: issues.append("animations")
            if issues:
                suggestions.append(f"Fix design issues: {', '.join(issues)}.")
        # External links
        external = validation_results["external_links"]
        if not external["is_complete"]:
            suggestions.append("Ensure all external links open in a new tab (target='_blank').")
        # Grammar/Spell Check (About and Projects)
        if tool:
            about_text = self._extract_about_text(validation_results)
            if about_text:
                matches = tool.check(about_text)
                if matches:
                    suggestions.append("Check grammar and spelling in your About section.")
            for proj in validation_results.get("projects_section", {}).get("project_details", []):
                matches = tool.check(proj)
                if matches:
                    suggestions.append("Check grammar and spelling in your project summaries.")
        else:
            suggestions.append("(Optional) Install 'language_tool_python' for grammar and spell checking.")
        return suggestions

    def _extract_about_text(self, validation_results: Dict[str, Any]) -> str:
        # This is a placeholder; ideally, About text should be extracted from the HTML, but here we use summary fields
        about = validation_results.get("about_section", {})
        # If you have a way to get the actual text, use it here
        return ""

    def _generate_summary(self, validation_results: Dict[str, Any], scores: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the portfolio evaluation."""
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
            summary.append("✅ About section includes name, photo, and introduction.")
        else:
            missing = []
            if not about["has_name"]: missing.append("name")
            if not about["has_photo"]: missing.append("photo")
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