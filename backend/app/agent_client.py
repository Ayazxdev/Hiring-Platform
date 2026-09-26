"""
Agent Client for Fair Hiring System
Handles communication with all agent services
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment from root and backend .env
_root_env = Path(__file__).resolve().parent.parent.parent / ".env"
_backend_env = Path(__file__).resolve().parent.parent / ".env"
if _root_env.exists():
    load_dotenv(_root_env)
if _backend_env.exists():
    load_dotenv(_backend_env)

import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json

USE_ZYND = os.getenv('USE_ZYND', '0') == '1'

def _get_zynd_orchestrator():
    """Lazily import and return the Zynd orchestrator. Returns None on failure."""
    try:
        from .zynd_orchestrator import get_orchestrator
        return get_orchestrator()
    except Exception as e:
        logger.warning(f"Zynd orchestrator unavailable, falling back to direct HTTP: {e}")
        return None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentClient:
    """
    Client for communicating with agent services.
    All agent services run as separate FastAPI apps on different ports.
    """
    
    def __init__(self, timeout: float = 500.0):
        """
        Initialize agent client.
        """
        self.timeout = timeout
        
        # Check for unified agents URL (useful for deployment)
        unified_url = os.getenv("UNIFIED_AGENTS_URL")
        
        # Agent service endpoints - Authoritative Map
        # These defaults match agents_services/ and start_all_complete.py
        # Set USE_ZYND=1 to route via Zynd orchestrator instead (ports 5101-5109)
        if unified_url:
            unified_url = unified_url.rstrip('/')
            self.endpoints = {
                "matching": f"{unified_url}/matching",
                "bias": f"{unified_url}/bias",
                "skill": f"{unified_url}/skill",
                "ats": f"{unified_url}/ats",
                "github": f"{unified_url}/github",
                "leetcode": f"{unified_url}/leetcode",
                "linkedin": f"{unified_url}/linkedin",
                "passport": f"{unified_url}/passport",
                "job_description": f"{unified_url}/job_description",
                "codeforces": f"{unified_url}/codeforces",
            }
        else:
            self.endpoints = {
                "matching": os.getenv("MATCHING_SERVICE_URL", "http://localhost:8001"),
                "bias": os.getenv("BIAS_SERVICE_URL", "http://localhost:8002"),
                "skill": os.getenv("SKILL_SERVICE_URL", "http://localhost:8003"),
                "ats": os.getenv("ATS_SERVICE_URL", "http://localhost:8004"),
                "github": os.getenv("GITHUB_SERVICE_URL", "http://localhost:8005"),
                "leetcode": os.getenv("LEETCODE_SERVICE_URL", "http://localhost:8006"),
                "linkedin": os.getenv("LINKEDIN_SERVICE_URL", "http://localhost:8007"),
                "passport": os.getenv("PASSPORT_SERVICE_URL", "http://localhost:8008"),
                "job_description": os.getenv("JOB_DESCRIPTION_SERVICE_URL", "http://localhost:8009"),
                "codeforces": os.getenv("CODEFORCES_SERVICE_URL", "http://localhost:8010"),
            }
    
        # Load unified agents in-memory if available
        self.internal_agents_app = None
        try:
            import sys
            from pathlib import Path
            root_dir = Path(__file__).resolve().parent.parent.parent
            agents_dir = root_dir / "agents_services"
            for d in [str(root_dir), str(agents_dir)]:
                if d not in sys.path:
                    sys.path.insert(0, d)
            from agents_services.agents_aggregator import app as agents_app
            self.internal_agents_app = agents_app
            logger.info("AgentClient: in-memory unified agents loaded successfully.")
        except Exception as e:
            logger.warning(f"AgentClient: in-memory agents not loaded ({e}), using HTTP endpoints.")
    
    async def close(self):
        """No persistent sessions to close for now."""
        pass
    
    async def call_agent(self, agent_name: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an agent service with retry logic and exponential backoff.
        
        Args:
            agent_name: Name of the agent to call
            endpoint: API endpoint (e.g., "/run", "/extract")
            payload: Request payload
        """
        if agent_name not in self.endpoints:
            raise ValueError(f"Unknown agent: {agent_name}")

        # In-memory ASGI dispatch when unified agents are available
        if self.internal_agents_app is not None and not USE_ZYND:
            try:
                transport = httpx.ASGITransport(app=self.internal_agents_app)
                async with httpx.AsyncClient(transport=transport, base_url="http://agents", timeout=httpx.Timeout(self.timeout)) as client:
                    target_path = f"/{agent_name}{endpoint}"
                    logger.info(f"Calling internal agent '{agent_name}' at {target_path}")
                    response = await client.post(target_path, json=payload)
                    response.raise_for_status()
                    data = response.json() if response.status_code != 204 else {}
                    return {
                        "success": True,
                        "data": data,
                        "status_code": response.status_code
                    }
            except Exception as e:
                logger.warning(f"Internal call to '{agent_name}' failed: {e}. Falling back to network endpoints.")

        # Zynd mode: discover + call remote agent via /webhook/sync
        ZYND_AGENTS = ["matching", "bias", "skill", "ats", "passport", "github", "linkedin", "leetcode", "codeforces"]
        if USE_ZYND and agent_name in ZYND_AGENTS:
            orch = _get_zynd_orchestrator()
            if orch is not None:
                capability_map = {
                    "matching": ["fair_hiring", "matching"],
                    "bias": ["fair_hiring", "bias_detection"],
                    "skill": ["fair_hiring", "skill_verification"],
                    "ats": ["fair_hiring", "ats"],
                    "passport": ["fair_hiring", "passport"],
                    "github": ["fair_hiring", "github_analysis"],
                    "leetcode": ["fair_hiring", "leetcode_analysis"],
                    "codeforces": ["fair_hiring", "codeforces_analysis"],
                }
                caps = capability_map.get(agent_name, [agent_name])
                found = orch.discover(caps, top_k=5)
                if not found:
                    logger.warning(f"No Zynd agents found for {agent_name} capabilities={caps}. Falling back to direct call.")
                else:
                    logger.info(f"[zynd-orch] Discovered {agent_name}: {found[0]}")
                    result = orch.call_sync(found[0], payload)
                    # FIX: Normalize Zynd response to match direct HTTP structure (data + success)
                    return {
                        "success": True,
                        "data": result,
                        "status_code": 200
                    }
        url = f"{self.endpoints[agent_name]}{endpoint}"
        timeout = httpx.Timeout(self.timeout)
        retries = 3

        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    logger.info(f"Calling {agent_name} at {url} (attempt {attempt})")
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    
                    data = response.json()
                    return {
                        "success": True,
                        "data": data,
                        "status_code": response.status_code
                    }

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(f"Agent '{agent_name}' attempt {attempt} failed: {str(e)}")
                if attempt == retries:
                    logger.error(f"Agent '{agent_name}' failed after {retries} attempts.")
                    return {
                        "success": False,
                        "error": str(e),
                        "status_code": getattr(e.response, "status_code", 500) if hasattr(e, "response") else 500
                    }
                import asyncio
                await asyncio.sleep(2 ** attempt)  # exponential backoff
        
        return {
            "success": False,
            "error": "Unknown failure in call_agent",
            "status_code": 500
        }
    
    async def run_ats(
        self,
        application_id: int,
        resume_text: str,
        resume_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run ATS fraud detection agent."""
        payload = {
            "application_id": application_id,
            "resume_text": resume_text,
            "resume_path": resume_path
        }
        return await self.call_agent("ats", "/run", payload)
    
    async def scrape_github(
        self,
        github_url: str
    ) -> Dict[str, Any]:
        """Scrape GitHub profile."""
        payload = {"github_url": github_url}
        return await self.call_agent("github", "/scrape", payload)
    
    async def scrape_leetcode(
        self,
        leetcode_url: str
    ) -> Dict[str, Any]:
        """Scrape LeetCode profile."""
        payload = {"leetcode_url": leetcode_url}
        return await self.call_agent("leetcode", "/scrape", payload)
    
    async def scrape_codeforces(
        self,
        codeforces_url: str
    ) -> Dict[str, Any]:
        """Scrape Codeforces profile."""
        payload = {"codeforces_url": codeforces_url}
        return await self.call_agent("codeforces", "/scrape", payload)
    
    async def scrape_linkedin(
        self,
        linkedin_url: str
    ) -> Dict[str, Any]:
        """Parse LinkedIn profile (via URL as path placeholder)."""
        payload = {"linkedin_url": linkedin_url}
        return await self.call_agent("linkedin", "/parse", payload)
    
    async def verify_skills(
        self,
        application_id: int,
        anon_id: str,
        resume_text: str,
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify skills using skill verification agent."""
        payload = {
            "application_id": application_id,
            "anon_id": anon_id,
            "resume_text": resume_text,
            "evidence": evidence
        }
        return await self.call_agent("skill", "/run", payload)
    
    async def analyze_bias(
        self,
        credential: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze bias in credential."""
        payload = {
            "credential": credential,
            "metadata": {},
            "mode": "realtime"
        }
        return await self.call_agent("bias", "/run", payload)
    
    async def match_candidate(
        self,
        credential: Dict[str, Any],
        job_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Match candidate to job requirements."""
        payload = {
            "credential": credential,
            "job_description": job_description
        }
        return await self.call_agent("matching", "/run", payload)
    
    async def generate_passport(
        self,
        application_id: int,
        anon_id: str,
        credential_data: Dict[str, Any],
        match_score: int
    ) -> Dict[str, Any]:
        """Generate skill passport credential."""
        payload = {
            "application_id": application_id,
            "anon_id": anon_id,
            "credential_data": credential_data,
            "match_score": match_score
        }
        return await self.call_agent("passport", "/issue", payload)
    
    async def run_full_pipeline(
        self,
        application_id: int,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline with all agents in the requested order:
        ATS -> GitHub -> Coding Platforms -> LinkedIn -> Matching -> Bias -> Passport
        """
        results: Dict[str, Any] = {
            "pipeline_id": f"PIPE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "agents": {},
            "final_credential": None,
            "success": True,
            "errors": []
        }
        
        try:
            # Step 1: ATS
            logger.info("Step 1: Running ATS analysis")
            resume_path = candidate_data.get("resume_path")
            ats_result = await self.run_ats(
                application_id, 
                candidate_data.get("resume_text", ""),
                resume_path=resume_path
            )
            results["agents"]["ats"] = ats_result
            
            # Security Gate: Stop if BLACKLIST
            if ats_result.get("success") and ats_result.get("data", {}).get("action") == "BLACKLIST":
                 logger.warning("ATS Security Gate: BLACKLIST detected. Stopping pipeline.")
                 results["success"] = False
                 results["errors"].append("Security violation: Resume blacklisted by ATS")
                 return results
            
            # Step 2-4: Scrapers (GitHub first, then others)
            if candidate_data.get("github_url"):
                results["agents"]["github"] = await self.scrape_github(candidate_data["github_url"])
            if candidate_data.get("leetcode_url"):
                results["agents"]["leetcode"] = await self.scrape_leetcode(candidate_data["leetcode_url"])
            if candidate_data.get("codeforces_url"):
                results["agents"]["codeforces"] = await self.scrape_codeforces(candidate_data["codeforces_url"])
            
            # Step 5: LinkedIn
            if candidate_data.get("linkedin_url"):
                results["agents"]["linkedin"] = await self.scrape_linkedin(candidate_data["linkedin_url"])

            # Evidence aggregation for Skill Verification
            evidence = {
                "ats": results["agents"].get("ats", {}).get("data"),
                "github": results["agents"].get("github", {}).get("data"),
                "leetcode": results["agents"].get("leetcode", {}).get("data"),
                "codeforces": results["agents"].get("codeforces", {}).get("data"),
                "linkedin": results["agents"].get("linkedin", {}).get("data"),
            }
            
            # Step 6: Skill Verification
            logger.info("Step 6: Verifying skills")
            skill_result = await self.verify_skills(
                application_id=application_id,
                anon_id=candidate_data.get("anon_id", "ANON"),
                resume_text=candidate_data.get("resume_text", ""),
                evidence=evidence
            )
            results["agents"]["skill"] = skill_result
            if not skill_result["success"]:
                 results["success"] = False
                 results["errors"].append(f"Skill verification failed: {skill_result.get('error')}")
                 return results

            # Step 7: Matching stage (evaluates candidate evidence against job requirements)
            
            # Extract actual credential data
            skill_envelope = skill_result.get("data", {}).get("output", {})
            actual_credential = skill_envelope.get("output", skill_envelope)
            
            # Schema adaptation for Matching Agent
            
            # 1. Flatten verified_skills (tiered dict) into 'skills' list for MatchNormalizer
            if "skills" not in actual_credential and "verified_skills" in actual_credential:
                verified_skills = actual_credential.get("verified_skills", {})
                flat_skills = []
                
                if isinstance(verified_skills, dict):
                    for tier, skills in verified_skills.items():
                        for skill in skills:
                            flat_skills.append({"skill": skill, "tier": tier})
                elif isinstance(verified_skills, list):
                    # Fallback if it's already a list (from V1 arg)
                    flat_skills = [{"skill": s} for s in verified_skills]
                    
                actual_credential["skills"] = flat_skills
                
            # 2. Add Identity (required by Matching Agent Service wrapper)
            if "identity" not in actual_credential:
                actual_credential["identity"] = {
                    "anon_id": candidate_data.get("anon_id"),
                    "public_links": []
                }
                # Check for GitHub presence in generic sense
                if candidate_data.get("github_url"):
                     actual_credential["identity"]["public_links"].append("github_present")
            
            # Add explicit evidence flags for Passport Agent based on agent success
            actual_credential["ats"] = results["agents"].get("ats", {}).get("success", False)
            actual_credential["github"] = results["agents"].get("github", {}).get("success", False)
            actual_credential["leetcode"] = results["agents"].get("leetcode", {}).get("success", False)
            actual_credential["codeforces"] = results["agents"].get("codeforces", {}).get("success", False)
            actual_credential["linkedin"] = results["agents"].get("linkedin", {}).get("success", False)

            # Pull experience & projects into actual_credential from ATS if not present
            ats_data = results["agents"].get("ats", {}).get("data", {})
            if "experience" not in actual_credential and isinstance(ats_data, dict):
                actual_credential["experience"] = ats_data.get("experience", [])
            if "projects" not in actual_credential and isinstance(ats_data, dict):
                actual_credential["projects"] = ats_data.get("projects", [])
                
            # Pull experience_years from LinkedIn or ATS
            if not actual_credential.get("experience_years"):
                linkedin_data = results["agents"].get("linkedin", {}).get("data", {})
                if isinstance(linkedin_data, dict) and linkedin_data.get("experience_years"):
                    actual_credential["experience_years"] = linkedin_data.get("experience_years")
                elif isinstance(ats_data, dict) and ats_data.get("experience"):
                    actual_credential["experience_years"] = len(ats_data.get("experience", [])) * 1.0

            # Pull github_score from GitHub scraping if available
            github_data = results["agents"].get("github", {}).get("data", {})
            if isinstance(github_data, dict):
                cred_signal = github_data.get("credibility_signal", {})
                if cred_signal and "score" in cred_signal:
                    actual_credential["github_score"] = cred_signal.get("score", 0) / 100.0

            logger.info("Step 7: Matching candidate to job")
            match_result = await self.match_candidate(
                credential=actual_credential,
                job_description=job_data
            )
            results["agents"]["matching"] = match_result
            
            # Step 8: Bias Analysis
            logger.info("Step 8: Analyzing bias")
            bias_result = await self.analyze_bias(actual_credential)
            results["agents"]["bias"] = bias_result
            actual_credential["bias"] = bias_result.get("success", False)
            
            # Step 9: Generate Passport
            logger.info("Step 9: Generating passport")
            passport_result = await self.generate_passport(
                application_id=application_id,
                anon_id=candidate_data.get("anon_id", ""),
                credential_data=actual_credential,
                match_score=match_result.get("data", {}).get("match_score", 0)
            )
            results["agents"]["passport"] = passport_result
            if passport_result["success"]:
                results["final_credential"] = passport_result.get("data")
            
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed with exception: {str(e)}", exc_info=True)
            results["success"] = False
            results["errors"].append(f"Pipeline exception: {str(e)}")
            return results