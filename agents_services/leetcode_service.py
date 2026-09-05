"""
LeetCode Scraper Service
FastAPI service that scrapes LeetCode profiles.
Port: 8006
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

leetcode_scraper = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize LeetCode scraper on startup"""
    global leetcode_scraper
    try:
        from skill_verification_agent.scraper.leetcode_tool import analyze_leetcode_profile
        class LeetCodeScraper:
            def scrape_profile(self, username: str):
                return analyze_leetcode_profile(f"https://leetcode.com/{username}")
        leetcode_scraper = LeetCodeScraper()
        logger.info("LeetCode scraper initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LeetCode scraper: {str(e)}")
    yield

app = FastAPI(title="LeetCode Scraper Service", version="1.0.0", lifespan=lifespan)


class LeetCodeRequest(BaseModel):
    username: Optional[str] = None
    leetcode_url: Optional[str] = None


class LeetCodeResponse(BaseModel):
    username: str
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    ranking: Optional[int] = None
    acceptance_rate: Optional[float] = None
    submission_stats: Optional[dict] = None


@app.post("/scrape", response_model=LeetCodeResponse)
async def scrape_leetcode(request: LeetCodeRequest):
    """
    Scrape LeetCode profile for problem-solving stats
    """
    global leetcode_scraper
    
    try:
        username = request.username
        if request.leetcode_url and not username:
            username = request.leetcode_url.rstrip('/').split('/')[-1]
        
        if not username:
            raise HTTPException(status_code=400, detail="Username or leetcode_url required")
        
        # Lazy initialization
        if leetcode_scraper is None:
            from skill_verification_agent.scraper.leetcode_tool import analyze_leetcode_profile
            class LeetCodeScraper:
                def scrape_profile(self, username: str):
                    return analyze_leetcode_profile(f"https://leetcode.com/{username}")
            leetcode_scraper = LeetCodeScraper()
        
        # Scrape LeetCode
        result = leetcode_scraper.scrape_profile(username)
        
        return LeetCodeResponse(
            username=username,
            total_solved=result.get("problems_solved", 0),
            easy_solved=0, # Simplified
            medium_solved=0,
            hard_solved=0,
            ranking=int(result.get("rank", 0)) if result.get("rank") else None,
            acceptance_rate=None,
            submission_stats=result
        )
    
    except Exception as e:
        logger.error(f"LeetCode scraping failed for {request.username}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"LeetCode scraping failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "leetcode_scraper",
        "scraper_loaded": leetcode_scraper is not None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)
