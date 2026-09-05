"""
Skill Agent Wrapper Service
FastAPI service that wraps the skill verification agent as an HTTP endpoint.
Port: 8001
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
import sys
import os

# Add agents path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', ))
# Also add skill_verification_agent to path for utils imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', 'skill_verification_agent'))

app = FastAPI(title="Skill Agent Service", version="1.0.0")

class SkillAgentRequest(BaseModel):
    application_id: Optional[int] = 0
    resume_text: Optional[str] = ""
    github_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    codeforces_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    anon_id: Optional[str] = ""
    evidence: Optional[dict] = {}
    required_skills: Optional[Any] = []


class SkillAgentResponse(BaseModel):
    output: dict
    explanation: Optional[str] = None
    flags: list = []


@app.post("/run", response_model=SkillAgentResponse)
@app.post("/verify", response_model=SkillAgentResponse)
async def run_skill_verification(request: SkillAgentRequest):
    """
    Run skill verification agent using 2026 Evidence Graph architecture.
    """
    try:
        from skill_verification_agent.agents.evidence_graph_builder import EvidenceGraphBuilder
        from skill_verification_agent.agents.skill_verification_agent_v2 import SkillVerificationAgentV2
        
        # 1. Build Evidence Graph
        builder = EvidenceGraphBuilder()
        evidence = request.evidence or {}
        
        graph = builder.build_evidence_graph(
            ats_output=evidence.get("ats"),
            linkedin_output=evidence.get("linkedin"),
            github_output=evidence.get("github"),
            leetcode_output=evidence.get("leetcode"),
            codeforces_output=evidence.get("codeforces"),
            evaluation_id=str(request.application_id)
        )
        
        # 2. Issue Credential
        agent = SkillVerificationAgentV2()
        credential = agent.issue_credential(graph)
        
        return SkillAgentResponse(
            output=credential,
            explanation=f"Skill verification complete for application {request.application_id}. Level: {credential.get('experience_level', 'Unknown')}",
            flags=credential.get("flags", [])
        )
    
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").error(f"Skill verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Skill verification failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "skill_agent"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
