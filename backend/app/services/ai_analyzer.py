"""
Multi-AI Provider System for Portfolio Analysis
Supports Gemini (primary) and Groq (backup) with automatic fallback
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import google.generativeai as genai
from groq import Groq
import asyncio
from app.config import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    async def analyze(self, html_content: str, prompt: str) -> Dict[str, Any]:
        """Analyze content with AI"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass


class GeminiProvider(AIProvider):
    """Google Gemini AI Provider"""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    @property
    def name(self) -> str:
        return "Gemini"

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def analyze(self, html_content: str, prompt: str) -> Dict[str, Any]:
        """Analyze with Gemini"""
        try:
            # Limit content size to avoid token limits
            limited_content = html_content[:50000]  # ~50KB should be safe

            full_prompt = f"{prompt}\n\nHTML Content:\n{limited_content}"

            # Generate content with timeout
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(full_prompt)
                ),
                timeout=settings.ai_request_timeout
            )

            return {
                "success": True,
                "provider": self.name,
                "analysis": response.text,
                "raw_response": response
            }

        except asyncio.TimeoutError:
            logger.warning(f"{self.name} request timed out")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(f"{self.name} analysis failed: {str(e)}")
            return {"success": False, "error": str(e)}


class GroqProvider(AIProvider):
    """Groq AI Provider"""

    def __init__(self):
        self.api_key = settings.groq_api_key
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
            self.model = "llama-3.1-70b-versatile"

    @property
    def name(self) -> str:
        return "Groq"

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def analyze(self, html_content: str, prompt: str) -> Dict[str, Any]:
        """Analyze with Groq"""
        try:
            # Limit content size
            limited_content = html_content[:40000]  # Groq has smaller context

            full_prompt = f"{prompt}\n\nHTML Content:\n{limited_content}"

            # Create completion with timeout
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert portfolio analyzer. Provide detailed, actionable feedback."
                            },
                            {
                                "role": "user",
                                "content": full_prompt
                            }
                        ],
                        temperature=0.3,
                        max_tokens=2000
                    )
                ),
                timeout=settings.ai_request_timeout
            )

            return {
                "success": True,
                "provider": self.name,
                "analysis": response.choices[0].message.content,
                "raw_response": response
            }

        except asyncio.TimeoutError:
            logger.warning(f"{self.name} request timed out")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(f"{self.name} analysis failed: {str(e)}")
            return {"success": False, "error": str(e)}


class RuleBasedProvider(AIProvider):
    """Fallback rule-based analyzer when AI is unavailable"""

    @property
    def name(self) -> str:
        return "RuleBased"

    def is_available(self) -> bool:
        return True  # Always available

    async def analyze(self, html_content: str, prompt: str) -> Dict[str, Any]:
        """Simple rule-based analysis"""
        analysis_parts = []

        # Basic content checks
        if len(html_content) < 5000:
            analysis_parts.append("WARNING: Portfolio seems minimal. Consider adding more content.")

        # Section checks
        sections = {
            "about": ["about", "about me", "bio"],
            "projects": ["project", "portfolio", "work"],
            "skills": ["skill", "tech", "stack"],
            "contact": ["contact", "email", "social"]
        }

        missing_sections = []
        for section, keywords in sections.items():
            if not any(kw in html_content.lower() for kw in keywords):
                missing_sections.append(section)

        if missing_sections:
            analysis_parts.append(
                f"Missing sections detected: {', '.join(missing_sections).title()}"
            )

        # Link checks
        if "href=" in html_content:
            if "linkedin.com" not in html_content.lower():
                analysis_parts.append("Consider adding LinkedIn profile link")
            if "github.com" not in html_content.lower():
                analysis_parts.append("Consider adding GitHub profile link")

        # Responsive design
        if "@media" not in html_content.lower() and "responsive" not in html_content.lower():
            analysis_parts.append("Consider adding responsive design for mobile devices")

        if not analysis_parts:
            analysis_parts.append("Basic structure looks good. AI analysis unavailable for detailed feedback.")

        return {
            "success": True,
            "provider": self.name,
            "analysis": "\n".join(analysis_parts),
            "is_fallback": True
        }


class AIAnalyzer:
    """
    Main AI Analyzer with multi-provider support and automatic fallback
    Tries providers in order: Gemini -> Groq -> RuleBased
    """

    def __init__(self):
        self.providers: List[AIProvider] = [
            GeminiProvider(),
            GroqProvider(),
            RuleBasedProvider()
        ]

        # Log available providers
        available = [p.name for p in self.providers if p.is_available()]
        logger.info(f"AI Providers available: {', '.join(available)}")

    async def analyze(self, html_content: str) -> Dict[str, Any]:
        """
        Analyze portfolio with best available AI provider
        Returns structured analysis with provider info
        """
        prompt = self._get_analysis_prompt()

        for provider in self.providers:
            if not provider.is_available():
                continue

            logger.info(f"Attempting analysis with {provider.name}")
            result = await provider.analyze(html_content, prompt)

            if result.get("success"):
                logger.info(f"Analysis successful with {provider.name}")
                return result

            logger.warning(f"{provider.name} failed, trying next provider...")

        # Should never reach here since RuleBased is always available
        return {
            "success": False,
            "provider": "None",
            "analysis": "All providers failed",
            "error": "critical_failure"
        }

    def _get_analysis_prompt(self) -> str:
        """Generate comprehensive analysis prompt for high-quality feedback"""
        return """
You are an expert portfolio reviewer helping students improve their developer portfolios. Analyze this portfolio website and provide detailed, actionable feedback.

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:

## CRITICAL ISSUES (Must Fix Immediately)
List 2-4 critical problems that prevent this portfolio from being job-ready. Be specific about:
- What's wrong (e.g., "Only 1 project shown, need minimum 3")
- Why it matters (e.g., "Employers expect to see multiple projects demonstrating different skills")
- How to fix it (e.g., "Add 2 more complete projects with GitHub repos and live demos")

## QUICK WINS (Easy Improvements, High Impact)
List 3-5 improvements that are easy to implement but significantly boost quality:
- Broken links to fix
- Missing alt text on images
- Social media links to add
- Simple design tweaks
- Content additions

## CONTENT ANALYSIS
**About Section:**
- Does it clearly state who they are and what they do?
- Is there a professional photo with a human face visible?
- Is the introduction compelling and specific (not generic)?

**Projects Section:**
- Count exact number of projects
- For each project, check: title, description, tech stack, GitHub link, live demo link, screenshots
- Are projects complete and polished or look unfinished?
- Do projects demonstrate real-world problem solving?

**Skills Section:**
- Are skills visually highlighted (badges, icons)?
- Is there a good variety (frontend, backend, tools)?

**Contact Section:**
- LinkedIn profile link present and working?
- GitHub profile link present and working?
- Email or contact form available?

## DESIGN & UX ASSESSMENT
- Visual professionalism (modern vs outdated)
- Color scheme and typography quality
- Spacing and layout consistency
- Mobile responsiveness
- Navigation clarity
- Loading performance

## STRENGTHS (What's Working Well)
Identify 2-3 specific things they did right. Be genuine and specific:
- "Clean, modern navbar with smooth scroll functionality"
- "Project cards have excellent hover effects"
- "Strong technical writing in project descriptions"

## ACTIONABLE NEXT STEPS (Prioritized)
Provide 4-6 specific actions ranked by priority:

**Priority 1 (This Week):**
1. [Specific action with clear outcome]
2. [Specific action with clear outcome]

**Priority 2 (Next 2 Weeks):**
3. [Specific action with clear outcome]
4. [Specific action with clear outcome]

**Priority 3 (Polish):**
5. [Specific action with clear outcome]
6. [Specific action with clear outcome]

IMPORTANT GUIDELINES:
- Be specific, not generic ("Add projects" is bad, "Add a full-stack CRUD project using React and Node.js with authentication" is good)
- Give concrete numbers (e.g., "Add 2 more projects" not "Add more projects")
- Mention actual HTML/CSS/JS improvements where visible
- Balance criticism with encouragement
- Focus on what will get them hired
- Keep total response under 800 words
- Use professional tone, no excessive praise or harshness
- If something is excellent, say so specifically

Analyze the HTML content provided and structure your response exactly as above.
"""

    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers"""
        return {
            provider.name: provider.is_available()
            for provider in self.providers
        }
