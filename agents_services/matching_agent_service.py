"""
Matching Agent Wrapper Service (v2 Gold Standard - Hardened)
FastAPI service that wraps the matching agent with precision exposure.
Port: 8003
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matching_service")

# Paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', ))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', 'skill_verification_agent'))

app = FastAPI(title="Matching Agent Service (v2 Hardened)", version="2.1.0")

class MatchAgentRequest(BaseModel):
    credential: Dict[str, Any]
    job_description: Dict[str, Any]

class MatchAgentResponse(BaseModel):
    match_score: int              # 0-100 Legacy
    match_score_raw: float        # 0.0-1.0 Canonical Precision
    match_status: str             # Machine-safe Enum (e.g. MATCHED)
    decision_reason: str          # Machine-safe Enum (e.g. STRONG_MATCH)
    breakdown: Dict[str, Any]
    analysis: Optional[Dict[str, Any]] = None

@app.post("/run", response_model=MatchAgentResponse)
async def run_matching(request: MatchAgentRequest):
    """
    Run the deterministic 4-pillar matching algorithm with precision exposure.
    """
    jd = request.job_description
    cand = request.credential

    # 1. Early Schema Validation & Normalization
    if "strict_requirements" not in jd:
        jd["strict_requirements"] = []
    if "languages" not in jd:
        jd["languages"] = []
    if "matching_philosophy" not in jd:
        jd["matching_philosophy"] = {"learning_velocity_weight": 0.2}

    if "identity" not in cand:
        cand["identity"] = {"anon_id": "ANON", "public_links": []}
    if "skills" not in cand:
        cand["skills"] = []

    # 2. Execute Match
    try:
        from matching_agent.agents.matching_agent import MatchingAgent
        agent = MatchingAgent()
        
        # Debug logging
        logger.info(f"JD keys: {list(jd.keys())}")
        logger.info(f"JD types: {[(k, type(v).__name__) for k, v in jd.items()]}")
        logger.info(f"Candidate keys: {list(cand.keys())}")
        logger.info(f"Candidate types: {[(k, type(v).__name__) for k, v in cand.items()]}")
        
        result = agent.match(jd=jd, candidate=cand)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return MatchAgentResponse(
            match_score=result["match_score"],
            match_score_raw=result["final_score"],
            match_status=result["match_status"],
            decision_reason=result["decision_reason"],
            breakdown=result["breakdown"],
            analysis=result["analysis"]
        )
    
    except Exception as e:
        logger.error(f"Matching Engine Crash: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Matching Engine Failure: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "matching_agent_v2_hardened"}

if __name__ == "__main__":
    import uvicorn, os
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
