"""
ATS Fraud Detection Service
FastAPI service that wraps the ATS fraud detection agent.
Port: 8004
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os
import logging

import re
from collections import Counter

# Add agents path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', ))
# Also add skill_verification_agent to path for utils imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', 'skill_verification_agent'))

# Pre-import detector modules so they're cached when ats.py tries to import them
try:
    from utils.pdf_layer_extractor import WhiteTextDetector
    from utils.manipulation_detector import PromptInjectionDefender
    from utils.image_text_extractor import ImageInjectionDetector
    from utils.evasion_detector import SophisticatedEvasionDetector
except ImportError as e:
    logging.warning(f"Some detectors not available: {e}")

# Import ATS Guard (new multi-layer security system)
try:
    from skill_verification_agent.agents.ats_guard import run_ats_guard
    ATS_GUARD_AVAILABLE = True
    logging.info("ATS Guard system loaded successfully")
except ImportError as e:
    ATS_GUARD_AVAILABLE = False
    logging.warning(f"ATS Guard not available, falling back to basic checks: {e}")

logger = logging.getLogger("uvicorn.error")

# Global agent instance
ats_agent = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize ATS agent on startup"""
    global ats_agent
    try:
        from skill_verification_agent.agents.ats import ATSEvidenceAgent
        ats_agent = ATSEvidenceAgent(llm=None) # Start with None, will be fallback or lazy loaded
        logger.info("ATS Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ATS agent: {str(e)}")
        # Fallback to lazy initialization on first request
    yield

app = FastAPI(title="ATS Fraud Detection Service", version="1.0.0", lifespan=lifespan)


class ATSRequest(BaseModel):
    application_id: Optional[int] = None
    resume_text: str
    resume_path: Optional[str] = None
    deep_check: bool = True

class ATSResponse(BaseModel):
    schema_version: str = "ats_evidence_v1"
    action: str  # "OK" | "NEEDS_REVIEW" | "BLACKLIST"
    status: Optional[str] = None
    
    fraud_detected: bool = False
    fraud_reason: Optional[str] = None
    manipulation_detected: bool = False
    
    needs_review: Optional[bool] = None
    reason: Optional[str] = None
    severity: str = "none"
    flags: list = []
    analysis: dict = {}
    manipulation_signals: dict 
    evidence: Optional[dict] = None


@app.post("/run", response_model=ATSResponse)
@app.post("/analyze", response_model=ATSResponse)
async def analyze_resume(request: ATSRequest):
    """
    Analyze resume for fraud and manipulation attempts
    """
    global ats_agent
    
    try:
        flags = []
        severity = "none"
        reason = None
        action = "OK"
        text = request.resume_text

        # ATS GUARD: Multi-Layer Security Pre-Check
        guard_result = None
        if ATS_GUARD_AVAILABLE and request.resume_path:
            try:
                logger.info(f"Running ATS Guard on: {request.resume_path}")
                guard_result = run_ats_guard(
                    pdf_path=request.resume_path,
                    github_age_years=None  # Will be populated later if available
                )
                
                logger.info(f"ATS Guard Result: {guard_result['security_status']} (trust: {guard_result['trust_score']})")  
                
                # Early rejection for critical attacks
                if guard_result["security_status"] == "REJECTED":
                    logger.warning(f"ATS Guard REJECTED resume: {guard_result['reason']}")
                    
                    manipulation_confidence = min(1.0, (100 - guard_result["trust_score"]) / 100)
                    
                    return ATSResponse(
                        schema_version="ats_evidence_v1",
                        action="BLACKLIST",
                        fraud_detected=True,
                        fraud_reason=guard_result["reason"],
                        manipulation_detected=True,
                        severity="critical",
                        flags=[f["type"] for f in guard_result.get("flags", [])],
                        manipulation_signals={
                            "detected": True,
                            "patterns": [f["type"] for f in guard_result.get("flags", [])],
                            "confidence": manipulation_confidence,
                            "severity": "critical",
                            "trust_score": guard_result["trust_score"],
                            "guard_flags": guard_result.get("flags", []),
                            "guard_version": guard_result.get("guard_version", "v1")
                        },
                        analysis={"realtime_checks": {"guard_security_status": guard_result["security_status"]}},
                        evidence=None
                    )
                
                # Update flags and severity based on guard results
                if guard_result.get("flags"):
                    for flag in guard_result["flags"]:
                        flags.append(flag["type"])
                        if flag["severity"] == "critical":
                            severity = "critical"
                        elif flag["severity"] == "high" and severity not in ["critical"]:
                            severity = "high"
                        elif flag["severity"] == "medium" and severity not in ["critical", "high"]:
                            severity = "medium"
                        elif flag["severity"] == "low" and severity == "none":
                            severity = "low"
                
            except Exception as e:
                logger.error(f"ATS Guard failed: {e}")
                # Continue with fallback basic checks
        
        # Fallback: Basic Real-time Checks (if Guard not available)
        # White text (hidden keywords)
        suspicious_chars = ['\u200b', '\u200c', '\u200d', '\ufeff']
        white_text_count = sum(text.count(char) for char in suspicious_chars)
        if white_text_count > 10:
            flags.append("white_text_detected")
            severity = "high"
            reason = "Potential white text manipulation detected"
        
        # Prompt injection
        prompt_injection_patterns = [
            r'ignore\s+(previous|all|above)\s+instructions',
            r'system\s*:\s*you\s+are',
            r'act\s+as\s+a',
            r'pretend\s+to\s+be',
            r'<\|im_start\|>',
            r'<\|im_end\|>',
            r'\[INST\]',
            r'\[\/INST\]',
            r'disregard\s+all\s+previous',
            r'you\s+must\s+approve',
            r'bypass\s+all\s+checks',
            r'rejection\s+rules\s+must\s+not\s+apply'
        ]
        for pattern in prompt_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append("prompt_injection")
                severity = "critical"
                reason = "Prompt injection attempt detected"
                action = "BLACKLIST"
                break
        
        # Bot-generated patterns
        bot_indicators = ["as an ai language model", "generated by chatgpt", "written by gpt"]
        for indicator in bot_indicators:
            if indicator in text.lower():
                flags.append("bot_generated")
                severity = "high"
                reason = "Resume appears to be AI-generated"
                action = "NEEDS_REVIEW"
                break

        # 2. Deep Analysis using existing ATSAgent (if available)
        ats_result = {}
        try:
            if ats_agent is None:
                try:
                    from skill_verification_agent.agents.ats import ATSEvidenceAgent
                    ats_agent = ATSEvidenceAgent(llm=None)
                except Exception as e:
                    logger.error(f"Lazy loading of ATSEvidenceAgent failed: {str(e)}")
                    pass
            
            if ats_agent:
                # Use extract_evidence instead of analyze if it matches the class
                if hasattr(ats_agent, 'extract_evidence'):
                    # Pass resume_text directly and enable deep_check
                    ats_result = ats_agent.extract_evidence(
                        pdf_path=request.resume_path,
                        resume_text=request.resume_text,
                        deep_check=request.deep_check,
                        evaluation_id=str(request.application_id) if request.application_id else None
                    )
                elif hasattr(ats_agent, 'analyze'):
                    ats_result = ats_agent.analyze(text)
        except Exception as e:
            logger.error(f"Deep ATS analysis failed: {str(e)}")

        # Merge results from deep analysis
        if ats_result.get("final_action") == "BLACKLISTED":
            action = "BLACKLIST"
            reason = ats_result.get("reason", reason)
        elif ats_result.get("final_action") == "PENDING_HUMAN_REVIEW":
            action = "NEEDS_REVIEW"
            reason = ats_result.get("reason", reason)

        if action == "OK" and severity in ["high", "critical"]:
            action = "NEEDS_REVIEW"

        # Build manipulation signals (explicit, never null)
        # Include ATS Guard trust score if available
        manipulation_signals = {
            "detected": len(flags) > 0 or severity in ["high", "critical"],
            "patterns": flags,
            "confidence": 0.8 if severity == "critical" else (0.5 if severity == "high" else 0.0),
            "severity": severity
        }
        
        # Enhance with ATS Guard data if available
        if guard_result:
            manipulation_signals["trust_score"] = guard_result["trust_score"]
            manipulation_signals["guard_flags"] = guard_result.get("flags", [])
            manipulation_signals["guard_status"] = guard_result["security_status"]
            # Update confidence based on trust score (0-100 scale)
            if guard_result["trust_score"] < 100:
                manipulation_signals["confidence"] = max(
                    manipulation_signals["confidence"],
                    (100 - guard_result["trust_score"]) / 100  # Convert to 0.0-1.0
                )
        
        # Separate analysis metadata from raw extracted evidence
        
        # 1. Extract analysis components from ats_result
        semantic_flags = []
        consistency_checks = {}
        
        # Prepare evidence object (mutable copy)
        final_evidence = None
        
        if isinstance(ats_result, dict):
            # Extract flags and checks
            semantic_flags = ats_result.get("semantic_flags", [])
            consistency_checks = ats_result.get("consistency_checks", {})
            
            # Create cleaner evidence object by REMOVING analysis fields
            # We copy to avoid modifying original if it's used elsewhere (though here it's local)
            if "source" in ats_result:
                final_evidence = ats_result.copy()
                # Remove analysis fields from evidence
                final_evidence.pop("semantic_flags", None)
                final_evidence.pop("consistency_checks", None)
                final_evidence.pop("flags", None) 
                final_evidence.pop("human_review_reason", None)
        
        # Build response payload
        return ATSResponse(
            schema_version="ats_evidence_v1",
            action=action,
            status=action,
            fraud_detected=action == "BLACKLIST",
            fraud_reason=reason if action == "BLACKLIST" else None,
            manipulation_detected=manipulation_signals["detected"],
            
            needs_review=action == "NEEDS_REVIEW",
            reason=reason or ats_result.get("human_review_reason"),
            severity=severity,
            flags=flags + ats_result.get("flags", []),
            
            # ANALYSIS: All reasoning, detection, and validation logic
            analysis={
                "realtime_checks": {
                    "white_text_count": white_text_count,
                    "bot_detected": "bot_generated" in flags
                },
                "semantic_analysis": {
                    "flags": semantic_flags,
                    "consistency_checks": consistency_checks
                }
            },
            
            manipulation_signals=manipulation_signals,
            
            # EVIDENCE: Pure extracted facts only
            evidence=final_evidence
        )
    
    except Exception as e:
        logger.error(f"ATS analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ATS fraud detection failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ats_fraud_detection",
        "agent_loaded": ats_agent is not None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
