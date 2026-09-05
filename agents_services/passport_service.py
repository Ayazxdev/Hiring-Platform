"""
Passport Credential Service
FastAPI service for issuing and verifying skill credentials.
Port: 8010
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os
import logging
import json
import hashlib
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', ))
# Also add skill_verification_agent to path for utils imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', 'skill_verification_agent'))

logger = logging.getLogger("uvicorn.error")

passport_agent = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize passport agent on startup"""
    global passport_agent
    try:
        from passport_agent.agents.passport_agent import PassportAgent
        passport_agent = PassportAgent()
        logger.info("Passport agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize passport agent: {str(e)}")
    yield

app = FastAPI(title="Passport Credential Service", version="1.0.0", lifespan=lifespan)


class CredentialRequest(BaseModel):
    application_id: int
    credential_data: dict
    match_score: int
    anon_id: Optional[str] = None


class CredentialResponse(BaseModel):
    credential_id: str
    hash: str
    signature: str
    public_key: str
    verification_url: str
    issued_at: str
    expires_at: str
    payload: Dict[str, Any]


class VerificationRequest(BaseModel):
    credential_id: str
    payload: dict
    signature: str


class VerificationResponse(BaseModel):
    valid: bool
    credential_id: str
    issued_at: Optional[str] = None
    expires_at: Optional[str] = None
    reason: Optional[str] = None


@app.post("/issue", response_model=CredentialResponse)
async def issue_credential(request: CredentialRequest):
    """
    Issue a signed skill credential (passport)
    
    Creates a cryptographically signed credential that proves:
    - Skills were verified
    - Bias was checked
    - Job match was calculated
    - All evidence is authentic
    """
    global passport_agent
    
    try:
        # Lazy initialization
        if passport_agent is None:
            from passport_agent.agents.passport_agent import PassportAgent
            passport_agent = PassportAgent()
        
        # Prepare credential payload
        issued_at = datetime.utcnow()
        expires_at = issued_at + timedelta(days=365)  # 1 year validity
        
        credential_payload = {
            "type": "SkillPassport",
            "version": "1.0",
            "application_id": request.application_id,
            "anon_id": request.anon_id,
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "match_score": request.match_score,
            "verified_skills": request.credential_data.get("verified_skills", []),
            "confidence": request.credential_data.get("skill_confidence", request.credential_data.get("confidence", 0)),
            "signal_strength": request.credential_data.get("signal_strength", "weak"),
            "evidence": {
                "ats_verified": bool(request.credential_data.get("ats")),
                "github_verified": bool(request.credential_data.get("github")),
                "leetcode_verified": bool(request.credential_data.get("leetcode")),
                "codeforces_verified": bool(request.credential_data.get("codeforces")),
                "linkedin_verified": bool(request.credential_data.get("linkedin")),
                "bias_checked": bool(request.credential_data.get("bias"))
            }
        }
        
        # Issue passport
        result = passport_agent.issue_passport(credential_payload)
        
        # Generate credential ID
        credential_id = f"cred_{hashlib.sha256(json.dumps(credential_payload, sort_keys=True).encode()).hexdigest()[:16]}"
        
        # Generate verification URL
        verification_url = f"{os.getenv('PASSPORT_VERIFY_BASE_URL', 'https://yourdomain.com')}/verify/{credential_id}"
        
        return CredentialResponse(
            credential_id=credential_id,
            hash=result.get("hash", ""),
            signature=result.get("signature", ""),
            public_key=result.get("public_key", ""),
            verification_url=verification_url,
            issued_at=issued_at.isoformat(),
            expires_at=expires_at.isoformat(),
            payload=credential_payload
        )
    
    except Exception as e:
        logger.error(f"Credential issuance failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Credential issuance failed: {str(e)}"
        )


@app.post("/verify", response_model=VerificationResponse)
async def verify_credential(request: VerificationRequest):
    """
    Verify a skill credential's authenticity
    
    Checks:
    - Signature is valid
    - Credential hasn't been tampered with
    - Credential hasn't expired
    """
    global passport_agent
    
    try:
        # Lazy initialization
        if passport_agent is None:
            from passport_agent.agents.passport_agent import PassportAgent
            passport_agent = PassportAgent()
        
        # Verify signature
        is_valid = passport_agent.verify_passport(
            payload=request.payload,
            signature=request.signature
        )
        
        if not is_valid:
            return VerificationResponse(
                valid=False,
                credential_id=request.credential_id,
                reason="Invalid signature"
            )
        
        # Check expiration
        expires_at = request.payload.get("expires_at")
        if expires_at:
            expires_dt = datetime.fromisoformat(expires_at)
            if datetime.utcnow() > expires_dt:
                return VerificationResponse(
                    valid=False,
                    credential_id=request.credential_id,
                    issued_at=request.payload.get("issued_at"),
                    expires_at=expires_at,
                    reason="Credential expired"
                )
        
        return VerificationResponse(
            valid=True,
            credential_id=request.credential_id,
            issued_at=request.payload.get("issued_at"),
            expires_at=expires_at
        )
    
    except Exception as e:
        logger.error(f"Credential verification failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Credential verification failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "passport_credential",
        "agent_loaded": passport_agent is not None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8008))
    uvicorn.run(app, host="0.0.0.0", port=port)
