from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.jd_bias import JobBiasAgent

router = APIRouter(
    prefix="/company",
    tags=["Company Agents"],
    responses={404: {"description": "Not found"}},
)

# Initialize agent once (or per request if needed, but once is better for potential caching/setup)
bias_agent = JobBiasAgent()

class AnalyzeJobRequest(BaseModel):
    description: str

@router.post("/analyze_bias")
async def analyze_job_bias(payload: AnalyzeJobRequest):
    if not payload.description:
        raise HTTPException(status_code=400, detail="Description is required")
    
    try:
        # The agent.analyze method returns a dict
        result = bias_agent.analyze(payload.description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
