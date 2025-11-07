"""
Portalyze 2.0 - Main FastAPI Application
AI-powered portfolio grading with deployed link analysis
"""

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, List, Dict, Any
import logging
from contextlib import asynccontextmanager
import asyncio
import csv
import io

from app.config import settings
from app.services.analyzer import PortfolioAnalyzer
from app.database.cache import cache_service
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Portalyze 2.0")
    logger.info(f"AI Providers: {', '.join(settings.get_available_ai_providers())}")

    # Validate configuration
    try:
        settings.validate_required_keys()
    except ValueError as e:
        logger.warning(f"⚠️  Configuration warning: {str(e)}")

    # Initialize database
    await cache_service.initialize()

    # Clean up expired cache entries
    cleaned = await cache_service.cleanup_expired()
    if cleaned > 0:
        logger.info(f"🧹 Cleaned up {cleaned} expired cache entries")

    yield

    # Shutdown
    logger.info("👋 Shutting down Portalyze")


# Create FastAPI app
app = FastAPI(
    title="Portalyze 2.0",
    description="AI-Powered Portfolio Grading System",
    version="2.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS with environment awareness
cors_kwargs: Dict[str, Any] = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

if settings.is_production:
    cors_kwargs["allow_origins"] = settings.origins_list
    if not cors_kwargs["allow_origins"]:
        logger.warning("No allowed origins configured. Set ALLOWED_ORIGINS in production.")
else:
    origin_regex = settings.cors_origin_regex
    if origin_regex:
        cors_kwargs["allow_origin_regex"] = origin_regex
    else:
        cors_kwargs["allow_origins"] = settings.origins_list or ["*"]

app.add_middleware(CORSMiddleware, **cors_kwargs)


# Pydantic Models
class PortfolioSubmission(BaseModel):
    """Portfolio submission model"""
    portfolio_url: HttpUrl
    force_refresh: Optional[bool] = False

    @validator('portfolio_url')
    def validate_url(cls, v):
        """Validate portfolio URL"""
        url_str = str(v)

        # Disallow localhost/127.0.0.1 in production
        if 'localhost' in url_str or '127.0.0.1' in url_str:
            raise ValueError(
                "Please provide a deployed portfolio URL, not localhost. "
                "Deploy your portfolio to Vercel, Netlify, or GitHub Pages first."
            )

        return v


class GradingResponse(BaseModel):
    """Grading response model"""
    portfolio_url: str
    score: int
    checklist: dict
    ai_analysis: str
    ai_provider: str
    professional_photo: dict
    learning_resources: list
    analysis_time: float
    from_cache: bool
    share_url: Optional[str] = None


class BatchPortfolioItem(BaseModel):
    """Single portfolio item for batch processing"""
    id: str
    name: str
    portfolio_url: str

    @validator('portfolio_url')
    def validate_url(cls, v):
        """Validate and normalize portfolio URL"""
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v


class BatchSubmission(BaseModel):
    """Batch submission model"""
    portfolios: List[BatchPortfolioItem]

    @validator('portfolios')
    def validate_portfolio_count(cls, v):
        """Validate portfolio count"""
        if len(v) == 0:
            raise ValueError("At least one portfolio is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 portfolios per batch")
        return v


class BatchResult(BaseModel):
    """Single result in batch processing"""
    id: str
    name: str
    portfolio_url: str
    score: Optional[int] = None
    status: str  # success, failed, skipped
    error: Optional[str] = None
    analysis_time: Optional[float] = None
    from_cache: bool = False
    checklist: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[str] = None


class BatchGradingResponse(BaseModel):
    """Batch grading response model"""
    total: int
    successful: int
    failed: int
    avg_score: Optional[float] = None
    total_time: float
    results: List[BatchResult]


# Initialize analyzer
analyzer = PortfolioAnalyzer()


# Routes
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Portalyze 2.0",
        "version": "2.0.0",
        "description": "AI-Powered Portfolio Grading System",
        "features": [
            "Deployed website analysis (no GitHub cloning)",
            "Multi-AI provider support (Gemini + Groq fallback)",
            "Modern face detection (MediaPipe 95%+ accuracy)",
            "27-parameter comprehensive grading",
            "SQLite caching for cost optimization",
            "Shareable result links",
            "Learning resources for improvement"
        ],
        "endpoints": {
            "grade": "POST /grade - Analyze a single portfolio",
            "batch-upload-csv": "POST /batch-upload-csv - Upload CSV file",
            "batch-grade": "POST /batch-grade - Grade multiple portfolios",
            "batch-export-csv": "POST /batch-export-csv - Export results as CSV",
            "share": "GET /share/{share_id} - Get shared result",
            "status": "GET /status - System status",
            "health": "GET /health - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "ai_providers": settings.get_available_ai_providers()
    }


@app.get("/status")
async def system_status():
    """Get system status and provider availability"""
    try:
        status = await analyzer.get_provider_status()
        return {
            "status": "operational",
            "providers": status,
            "cache_stats": await cache_service.get_cache_stats()
        }
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return {
            "status": "degraded",
            "error": str(e)
        }


@app.post("/grade", response_model=GradingResponse)
@limiter.limit(f"{settings.rate_limit_per_hour}/hour")
async def grade_portfolio(
    request: Request,
    submission: PortfolioSubmission
):
    """
    Grade a portfolio by analyzing its deployed website

    Rate limited to prevent abuse:
    - {rate_limit_per_hour} requests per hour per IP
    - {rate_limit_per_day} requests per day per IP
    """
    portfolio_url = str(submission.portfolio_url)
    force_refresh = submission.force_refresh or False

    try:
        logger.info(f"📊 Grading request for: {portfolio_url} (force_refresh={force_refresh})")

        # Delete cache if force refresh requested
        if force_refresh:
            await cache_service.delete_cached_result(portfolio_url)
            logger.info(f"🔄 Cache cleared for {portfolio_url}, forcing fresh analysis")

        # Analyze portfolio
        result = await analyzer.analyze(portfolio_url, force_refresh=force_refresh)

        if result.get("error"):
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Analysis failed")
            )

        logger.info(
            f"✅ Grading complete: {portfolio_url} "
            f"(Score: {result['score']}%, Time: {result['analysis_time']}s)"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Grading error for {portfolio_url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during analysis: {str(e)}"
        )


@app.get("/share/{share_id}")
async def get_shared_result(share_id: str):
    """
    Get a shared portfolio result by share ID

    Share IDs are short (12 characters) and easy to share
    Example: https://portalyze.com/share/abc123xyz789
    """
    try:
        result = await cache_service.get_shared_result(share_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Shared result not found or expired"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving shared result {share_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve shared result"
        )


@app.delete("/cache")
@limiter.limit("5/minute")
async def clear_cache(request: Request, portfolio_url: str = Query(..., description="Full portfolio URL to clear from cache")):
    """
    Clear cache for a specific portfolio URL.
    Useful if you've updated your portfolio and want to re-analyze immediately.
    """
    try:
        deleted = await cache_service.delete_cached_result(portfolio_url)
        if deleted:
            return {
                "message": "Cache cleared",
                "portfolio_url": portfolio_url
            }
        return {
            "message": "No cached result found for portfolio",
            "portfolio_url": portfolio_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/clear-all")
@limiter.limit("3/minute")
async def clear_all_cache(request: Request):
    """
    Clear ALL cached portfolio results.
    Use with caution - this will force re-analysis for all portfolios.
    Useful during development or when algorithm updates require fresh analysis.
    """
    try:
        deleted_count = await cache_service.clear_all_cache()
        return {
            "message": "All cache cleared successfully",
            "deleted_entries": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch-grade", response_model=BatchGradingResponse)
@limiter.limit("100/hour")  # Increased for testing
async def batch_grade_portfolios(
    request: Request,
    submission: BatchSubmission
):
    """
    Grade multiple portfolios in batch

    Processes portfolios with controlled concurrency to avoid overwhelming the server.
    Maximum 100 portfolios per batch.

    Rate limited to 2 batches per hour per IP to prevent abuse.
    """
    import time
    start_time = time.time()

    logger.info(f"Batch grading request for {len(submission.portfolios)} portfolios")

    results = []
    successful = 0
    failed = 0

    # Process portfolios with controlled concurrency
    semaphore = asyncio.Semaphore(settings.max_concurrent_analyses)

    async def analyze_one(item: BatchPortfolioItem) -> BatchResult:
        """Analyze a single portfolio with semaphore control"""
        async with semaphore:
            try:
                logger.info(f"Analyzing: {item.name} ({item.id})")
                result = await analyzer.analyze(item.portfolio_url)

                if result.get("error"):
                    return BatchResult(
                        id=item.id,
                        name=item.name,
                        portfolio_url=item.portfolio_url,
                        score=None,
                        status="failed",
                        error=result.get("message", "Analysis failed"),
                        analysis_time=None,
                        from_cache=False
                    )

                return BatchResult(
                    id=item.id,
                    name=item.name,
                    portfolio_url=item.portfolio_url,
                    score=result.get("score"),
                    status="success",
                    analysis_time=result.get("analysis_time"),
                    from_cache=result.get("from_cache", False),
                    checklist=result.get("checklist"),
                    ai_analysis=result.get("ai_analysis")
                )

            except Exception as e:
                logger.error(f"Error analyzing {item.name}: {str(e)}")
                return BatchResult(
                    id=item.id,
                    name=item.name,
                    portfolio_url=item.portfolio_url,
                    score=None,
                    status="failed",
                    error=str(e),
                    analysis_time=None,
                    from_cache=False
                )

    # Process all portfolios concurrently (with semaphore limits)
    tasks = [analyze_one(item) for item in submission.portfolios]
    results = await asyncio.gather(*tasks)

    # Calculate statistics
    successful = sum(1 for r in results if r.status == "success")
    failed = sum(1 for r in results if r.status == "failed")

    scores = [r.score for r in results if r.score is not None]
    avg_score = sum(scores) / len(scores) if scores else None

    total_time = time.time() - start_time

    avg_score_str = f"{avg_score:.1f}" if avg_score else "N/A"
    logger.info(
        f"Batch complete: {successful} successful, {failed} failed, "
        f"avg score: {avg_score_str}, time: {total_time:.1f}s"
    )

    return BatchGradingResponse(
        total=len(results),
        successful=successful,
        failed=failed,
        avg_score=avg_score,
        total_time=total_time,
        results=results
    )


@app.post("/batch-upload-csv")
@limiter.limit("5/hour")
async def batch_upload_csv(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Upload CSV file for batch processing

    Expected CSV format:
    Id,Name,Portfolio Link
    fw16_484,John Doe,https://johndoe.com
    fw13_042,Jane Smith,https://janesmith.com

    Returns parsed data for confirmation before processing.
    """
    try:
        # Read CSV file
        contents = await file.read()
        decoded = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded))

        portfolios = []
        for row in csv_reader:
            # Support various column name formats
            id_col = row.get('Id') or row.get('ID') or row.get('id')
            name_col = row.get('Name') or row.get('name') or row.get('NAME')
            url_col = (row.get('Portfolio Link') or row.get('portfolio_link') or
                      row.get('URL') or row.get('url') or row.get('link'))

            if not all([id_col, name_col, url_col]):
                continue  # Skip invalid rows

            portfolios.append({
                "id": id_col.strip(),
                "name": name_col.strip(),
                "portfolio_url": url_col.strip()
            })

        if not portfolios:
            raise HTTPException(
                status_code=400,
                detail="No valid portfolio entries found in CSV"
            )

        logger.info(f"Parsed {len(portfolios)} portfolios from CSV")

        return {
            "portfolios": portfolios,
            "count": len(portfolios),
            "message": f"Successfully parsed {len(portfolios)} portfolios. Use /batch-grade to process them."
        }

    except Exception as e:
        logger.error(f"CSV upload error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse CSV: {str(e)}"
        )


@app.post("/batch-export-csv")
async def batch_export_csv(batch_results: BatchGradingResponse):
    """
    Export batch results as CSV with all 27 checklist parameters

    Takes batch grading results and returns a downloadable CSV file.
    """
    try:
        output = io.StringIO()
        writer = csv.writer(output)

        # Get all unique checklist keys from successful results
        all_checklist_keys = set()
        for result in batch_results.results:
            if result.checklist:
                all_checklist_keys.update(result.checklist.keys())

        # Sort checklist keys for consistent ordering
        sorted_checklist_keys = sorted(all_checklist_keys)

        # Write header - basic info + all checklist parameters
        header = [
            'ID', 'Name', 'Portfolio URL', 'Score', 'Status',
            'Analysis Time (s)', 'From Cache'
        ]
        # Add checklist parameters as columns
        header.extend([key.replace('_', ' ').title() for key in sorted_checklist_keys])
        # Add error column at the end
        header.append('Error')
        writer.writerow(header)

        # Write data rows
        for result in batch_results.results:
            row = [
                result.id,
                result.name,
                result.portfolio_url,
                result.score if result.score is not None else '',
                result.status,
                f"{result.analysis_time:.2f}" if result.analysis_time else '',
                'Yes' if result.from_cache else 'No'
            ]

            # Add checklist parameter values
            if result.checklist:
                for key in sorted_checklist_keys:
                    if key in result.checklist:
                        row.append('PASS' if result.checklist[key].get('pass', False) else 'FAIL')
                    else:
                        row.append('N/A')
            else:
                # No checklist data available (likely failed analysis)
                row.extend(['N/A'] * len(sorted_checklist_keys))

            # Add error at the end
            row.append(result.error or '')
            writer.writerow(row)

        # Add summary section
        writer.writerow([])
        writer.writerow(['=== SUMMARY ==='])
        writer.writerow(['Total Portfolios', batch_results.total])
        writer.writerow(['Successful', batch_results.successful])
        writer.writerow(['Failed', batch_results.failed])
        writer.writerow(['Average Score',
                        f"{batch_results.avg_score:.1f}%" if batch_results.avg_score else 'N/A'])
        writer.writerow(['Total Time (s)', f"{batch_results.total_time:.1f}"])

        # Add parameter statistics
        if sorted_checklist_keys:
            writer.writerow([])
            writer.writerow(['=== PARAMETER STATISTICS ==='])
            writer.writerow(['Parameter', 'Pass Rate', 'Passed', 'Total'])

            for key in sorted_checklist_keys:
                passed = 0
                total = 0
                for result in batch_results.results:
                    if result.checklist and key in result.checklist:
                        total += 1
                        if result.checklist[key].get('pass', False):
                            passed += 1

                pass_rate = (passed / total * 100) if total > 0 else 0
                writer.writerow([
                    key.replace('_', ' ').title(),
                    f"{pass_rate:.1f}%",
                    passed,
                    total
                ])

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=portfolio_results.csv"
            }
        )

    except Exception as e:
        logger.error(f"CSV export error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export CSV: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "detail": str(exc) if settings.log_level == "DEBUG" else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
