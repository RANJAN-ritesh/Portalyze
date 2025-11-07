from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class GradingResult(BaseModel):
    # Section presence
    has_required_sections: bool
    sections_present: Dict[str, bool]
    
    # About section
    about_section: Dict[str, bool]
    
    # Projects section
    projects_section: Dict[str, Any]
    
    # Skills section
    skills_section: Dict[str, bool]
    
    # Contact section
    contact_section: Dict[str, bool]
    
    # Links
    links: Dict[str, Any]
    
    # Design
    responsiveness: Dict[str, Any]
    design_issues: Dict[str, Any]
    
    # Overall score
    score: float
    feedback: List[str]
    
    @classmethod
    def combine_results(cls, github_results: Dict[str, Any], website_results: Dict[str, Any]) -> 'GradingResult':
        """Combine results from GitHub and website analysis."""
        # Initialize feedback list
        feedback = []
        
        # Check required sections
        sections_present = website_results.get("sections", {})
        has_required_sections = all(sections_present.values())
        
        if not has_required_sections:
            missing_sections = [section for section, present in sections_present.items() if not present]
            feedback.append(f"Missing required sections: {', '.join(missing_sections)}")
        
        # About section analysis
        about_section = website_results.get("about", {})
        if about_section.get("exists"):
            if not about_section.get("has_photo"):
                feedback.append("About section is missing a photo")
            if not about_section.get("has_name"):
                feedback.append("About section is missing your name")
            if not about_section.get("has_intro"):
                feedback.append("About section is missing an introduction")
        
        # Projects section analysis
        projects_section = website_results.get("projects", {})
        if projects_section.get("exists"):
            if projects_section.get("count", 0) < 3:
                feedback.append("Projects section should have at least 3 projects")
            
            for i, project in enumerate(projects_section.get("details", [])):
                if not project.get("has_summary"):
                    feedback.append(f"Project {i+1} is missing a summary")
                if not project.get("has_hero_image"):
                    feedback.append(f"Project {i+1} is missing a hero image")
                if not project.get("has_tech_stack"):
                    feedback.append(f"Project {i+1} is missing tech stack information")
                if not project.get("has_deployed_link"):
                    feedback.append(f"Project {i+1} is missing a deployed link")
        
        # Skills section analysis
        skills_section = website_results.get("skills", {})
        if skills_section.get("exists") and not skills_section.get("has_visual_presentation"):
            feedback.append("Skills section should have visual presentation (icons or cards)")
        
        # Contact section analysis
        contact_section = website_results.get("contact", {})
        if contact_section.get("exists"):
            if not contact_section.get("has_linkedin"):
                feedback.append("Contact section is missing LinkedIn link")
            if not contact_section.get("has_github"):
                feedback.append("Contact section is missing GitHub link")
            if not contact_section.get("has_form"):
                feedback.append("Contact section is missing a contact form")
        
        # Links analysis
        links = website_results.get("links", {})
        if links.get("external", 0) > 0:
            external_links_new_tab = links.get("external_new_tab", 0)
            if external_links_new_tab < links.get("external", 0):
                feedback.append("Some external links don't open in new tab")
        
        # Check for broken links
        broken_links = [link for link in links.get("working", []) 
                       if link.get("status") != 200]
        if broken_links:
            feedback.append(f"Found {len(broken_links)} broken links")
        
        # Responsiveness analysis
        responsiveness = website_results.get("responsiveness", {})
        for viewport, results in responsiveness.items():
            if results.get("has_horizontal_scroll"):
                feedback.append(f"Website has horizontal scroll at {viewport} viewport")
        
        # Design issues
        design_issues = website_results.get("design_issues", {})
        if design_issues.get("console_errors"):
            feedback.append(f"Found {len(design_issues['console_errors'])} JavaScript errors")
        if design_issues.get("broken_images", 0) > 0:
            feedback.append(f"Found {design_issues['broken_images']} broken images")
        
        # Calculate score
        score = cls._calculate_score(
            has_required_sections,
            about_section,
            projects_section,
            skills_section,
            contact_section,
            links,
            responsiveness,
            design_issues
        )
        
        return cls(
            has_required_sections=has_required_sections,
            sections_present=sections_present,
            about_section=about_section,
            projects_section=projects_section,
            skills_section=skills_section,
            contact_section=contact_section,
            links=links,
            responsiveness=responsiveness,
            design_issues=design_issues,
            score=score,
            feedback=feedback
        )
    
    @staticmethod
    def _calculate_score(
        has_required_sections: bool,
        about_section: Dict[str, bool],
        projects_section: Dict[str, Any],
        skills_section: Dict[str, bool],
        contact_section: Dict[str, bool],
        links: Dict[str, Any],
        responsiveness: Dict[str, Any],
        design_issues: Dict[str, Any]
    ) -> float:
        """Calculate overall score based on all criteria."""
        score = 0.0
        total_criteria = 0
        
        # Required sections (20%)
        if has_required_sections:
            score += 20
        total_criteria += 20
        
        # About section (15%)
        if about_section.get("exists"):
            about_score = 0
            if about_section.get("has_photo"): about_score += 5
            if about_section.get("has_name"): about_score += 5
            if about_section.get("has_intro"): about_score += 5
            score += about_score
        total_criteria += 15
        
        # Projects section (25%)
        if projects_section.get("exists"):
            projects_score = 0
            project_count = projects_section.get("count", 0)
            if project_count >= 3: projects_score += 10
            
            for project in projects_section.get("details", []):
                if project.get("has_summary"): projects_score += 1
                if project.get("has_hero_image"): projects_score += 1
                if project.get("has_tech_stack"): projects_score += 1
                if project.get("has_deployed_link"): projects_score += 1
            
            score += min(projects_score, 15)
        total_criteria += 25
        
        # Skills section (10%)
        if skills_section.get("exists"):
            if skills_section.get("has_visual_presentation"):
                score += 10
        total_criteria += 10
        
        # Contact section (15%)
        if contact_section.get("exists"):
            contact_score = 0
            if contact_section.get("has_linkedin"): contact_score += 5
            if contact_section.get("has_github"): contact_score += 5
            if contact_section.get("has_form"): contact_score += 5
            score += contact_score
        total_criteria += 15
        
        # Links (5%)
        if links.get("external", 0) > 0:
            if links.get("external_new_tab", 0) == links.get("external", 0):
                score += 5
        total_criteria += 5
        
        # Responsiveness (5%)
        responsive_score = 5
        for viewport, results in responsiveness.items():
            if results.get("has_horizontal_scroll"):
                responsive_score -= 1
        score += max(responsive_score, 0)
        total_criteria += 5
        
        # Design issues (5%)
        design_score = 5
        if design_issues.get("console_errors"):
            design_score -= len(design_issues["console_errors"]) * 0.5
        if design_issues.get("broken_images", 0) > 0:
            design_score -= design_issues["broken_images"] * 0.5
        score += max(design_score, 0)
        total_criteria += 5
        
        # Calculate final percentage
        return (score / total_criteria) * 100 