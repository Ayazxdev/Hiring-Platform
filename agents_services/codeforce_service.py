"""
Codeforces Scraper Service
FastAPI service that scrapes Codeforces profiles.
Port: 8007
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', ))
# Also add skill_verification_agent to path for utils imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', 'skill_verification_agent'))

logger = logging.getLogger("uvicorn.error")

codeforces_scraper = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Codeforces scraper on startup"""
    global codeforces_scraper
    try:
        from skill_verification_agent.scraper.codeforce_tool import analyze_codeforces_profile
        class CodeforceScraper:
            def scrape_profile(self, handle: str):
                return analyze_codeforces_profile(handle)
        codeforces_scraper = CodeforceScraper()
        logger.info("Codeforces scraper initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Codeforces scraper: {str(e)}")
    yield

app = FastAPI(title="Codeforces Scraper Service", version="1.0.0", lifespan=lifespan)


class CodeforcesRequest(BaseModel):
    handle: Optional[str] = None
    codeforces_url: Optional[str] = None


class CodeforcesResponse(BaseModel):
    handle: str
    rating: int
    max_rating: int
    rank: str
    max_rank: str
    contests_participated: int
    problems_solved: Optional[int] = None


@app.post("/scrape", response_model=CodeforcesResponse)
async def scrape_codeforces(request: CodeforcesRequest):
    """
    Scrape Codeforces profile for competitive programming stats
    """
    global codeforces_scraper
    
    try:
        handle = request.handle or request.codeforces_url
        if handle:
            handle = str(handle).rstrip('/').split('/')[-1].strip()
        
        if not handle:
            raise HTTPException(status_code=400, detail="Handle or codeforces_url required")
        
        # Lazy initialization
        if codeforces_scraper is None:
            from skill_verification_agent.scraper.codeforce_tool import analyze_codeforces_profile
            class CodeforceScraper:
                def scrape_profile(self, handle: str):
                    return analyze_codeforces_profile(handle)
            codeforces_scraper = CodeforceScraper()
        
        # Scrape Codeforces
        result = codeforces_scraper.scrape_profile(handle)
        
        return CodeforcesResponse(
            handle=handle,
            rating=result.get("rating", 0),
            max_rating=result.get("max_rating", 0),
            rank=result.get("rank", "Unrated"),
            max_rank=result.get("max_rank", "Unrated"),
            contests_participated=0, # Simplified
            problems_solved=result.get("problems_solved")
        )
    
    except Exception as e:
        logger.error(f"Codeforces scraping failed for {request.handle}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Codeforces scraping failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "codeforces_scraper",
        "scraper_loaded": codeforces_scraper is not None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8011))
    uvicorn.run(app, host="0.0.0.0", port=port)
