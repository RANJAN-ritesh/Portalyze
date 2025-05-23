from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional
import asyncio
from .services.github_analyzer import GitHubAnalyzer
from .services.website_analyzer import WebsiteAnalyzer
from .models.grading_result import GradingResult

app = FastAPI(title="Portfolio Grader API")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PortfolioSubmission(BaseModel):
    github_url: HttpUrl
    deployed_url: HttpUrl
    name: Optional[str] = None

@app.post("/grade", response_model=GradingResult)
async def grade_portfolio(submission: PortfolioSubmission):
    try:
        # Initialize analyzers
        github_analyzer = GitHubAnalyzer()
        website_analyzer = WebsiteAnalyzer(url=str(submission.deployed_url))
        
        # Convert HttpUrl to str before passing
        github_url = str(submission.github_url)
        deployed_url = str(submission.deployed_url)
        
        # Run analyses concurrently
        github_task = asyncio.create_task(github_analyzer.analyze(github_url))
        website_task = asyncio.create_task(website_analyzer.analyze())
        
        # Wait for both analyses to complete
        github_results, website_results = await asyncio.gather(github_task, website_task)
        
        # Combine and process results
        final_grade = GradingResult.combine_results(github_results, website_results)
        
        return final_grade
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 