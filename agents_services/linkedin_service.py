"""
LinkedIn Parser Service
FastAPI service that parses LinkedIn profile PDFs.
Port: 8008
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import sys
import os
import logging
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', ))
# Also add skill_verification_agent to path for utils imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents_files', 'skill_verification_agent'))

# Import ATS Guard for security checks on LinkedIn PDFs
try:
    from skill_verification_agent.agents.ats_guard import run_ats_guard
    ATS_GUARD_AVAILABLE = True
    logging.info("✅ ATS Guard security system loaded for LinkedIn PDFs")
except ImportError as e:
    ATS_GUARD_AVAILABLE = False
    logging.warning(f"⚠️ ATS Guard not available for LinkedIn PDFs: {e}")

logger = logging.getLogger("uvicorn.error")

linkedin_parser = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize LinkedIn parser on startup"""
    global linkedin_parser
    try:
        from skill_verification_agent.agents.linkedin_parser import LinkedInPDFParser
        linkedin_parser = LinkedInPDFParser()
        logger.info("LinkedIn parser initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LinkedIn parser: {str(e)}")
    yield

app = FastAPI(title="LinkedIn Parser Service", version="1.0.0", lifespan=lifespan)


class LinkedInRequest(BaseModel):
    pdf_path: Optional[str] = None  # Path to uploaded PDF
    linkedin_url: Optional[str] = None  # For future scraping


class LinkedInResponse(BaseModel):
    identity: dict
    profile_signals: dict
    experience_signals: dict
    skills_signals: dict
    activity_signals: dict
    credibility_flags: dict
    confidence_score: float
    experience: dict
    education: list
    # Security fields (from ATS Guard)
    security_status: str = "OK"  # "OK" | "NEEDS_REVIEW" | "BLACKLIST"
    security_flags: list = []
    fraud_detected: bool = False
    manipulation_detected: bool = False


@app.post("/parse", response_model=LinkedInResponse)
async def parse_linkedin(request: Optional[LinkedInRequest] = None, file: Optional[UploadFile] = File(None)):
    """
    Parse LinkedIn profile from uploaded PDF or file path
    """
    global linkedin_parser
    
    try:
        # Lazy initialization
        if linkedin_parser is None:
            from skill_verification_agent.agents.linkedin_parser import LinkedInPDFParser
            linkedin_parser = LinkedInPDFParser()
        
        tmp_path = None
        
        if file and file.filename:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
        elif request and request.pdf_path:
            tmp_path = request.pdf_path
        elif request and request.linkedin_url:
            # Check if this is a web URL to scrape via Bright Data
            linkedin_url_str = str(request.linkedin_url).strip()
            if "linkedin.com" in linkedin_url_str or linkedin_url_str.startswith("http"):
                logger.info(f"🌐 Scraping LinkedIn profile URL via Bright Data: {linkedin_url_str}")
                try:
                    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    backend_dir = os.path.join(repo_root, 'backend')
                    if backend_dir not in sys.path:
                        sys.path.insert(0, backend_dir)
                    from app.services.brightdata_service import brightdata_client
                    
                    scraped = await brightdata_client.scrape_profile(linkedin_url_str)
                    return LinkedInResponse(
                        identity=scraped.get("identity", {}),
                        profile_signals=scraped.get("profile_signals", {}),
                        experience_signals={"positions": scraped.get("experience", {}).get("positions", [])},
                        skills_signals={"skills": scraped.get("skills", [])},
                        activity_signals={"connections": scraped.get("profile_signals", {}).get("connections", 500)},
                        credibility_flags={"scraped_via_brightdata": True},
                        confidence_score=scraped.get("confidence_score", 0.9),
                        experience=scraped.get("experience", {}),
                        education=scraped.get("education", []),
                        security_status="OK",
                        security_flags=[],
                        fraud_detected=False,
                        manipulation_detected=False
                    )
                except Exception as e:
                    logger.error(f"❌ Bright Data scraping failed in service: {str(e)}", exc_info=True)
            
            # Otherwise support local filepath passed via linkedin_url parameter
            tmp_path = request.linkedin_url
        
        if not tmp_path or not os.path.exists(tmp_path):
             return LinkedInResponse(
                 identity={},
                 profile_signals={},
                 experience_signals={},
                 skills_signals={},
                 activity_signals={},
                 credibility_flags={},
                 confidence_score=0.0,
                 experience={},
                 education=[]
             )

        try:
            # SECURITY CHECK: Run ATS Guard on LinkedIn PDF (same as resume PDFs)
            security_status = "OK"
            security_flags = []
            fraud_detected = False
            manipulation_detected = False
            
            if ATS_GUARD_AVAILABLE:
                try:
                    # Extract text for security analysis
                    import pypdf
                    with open(tmp_path, 'rb') as f:
                        reader = pypdf.PdfReader(f)
                        pdf_text = ""
                        for page in reader.pages:
                            pdf_text += page.extract_text() or ""
                    
                    # Run ATS Guard security checks
                    guard_result = run_ats_guard(pdf_path=tmp_path, text=pdf_text)
                    
                    security_status = guard_result.get("action", "OK")
                    security_flags = guard_result.get("flags", [])
                    fraud_detected = guard_result.get("fraud_detected", False)
                    manipulation_detected = guard_result.get("manipulation_detected", False)
                    
                    # If BLACKLIST, reject immediately
                    if security_status == "BLACKLIST":
                        logger.warning(f"🚨 LinkedIn PDF BLACKLISTED: {security_flags}")
                        return LinkedInResponse(
                            identity={},
                            profile_signals={},
                            experience_signals={},
                            skills_signals={},
                            activity_signals={},
                            credibility_flags={"blacklisted": True},
                            confidence_score=0.0,
                            experience={},
                            education=[],
                            security_status="BLACKLIST",
                            security_flags=security_flags,
                            fraud_detected=fraud_detected,
                            manipulation_detected=manipulation_detected
                        )
                    
                    logger.info(f"✅ LinkedIn PDF security check: {security_status}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ ATS Guard check failed for LinkedIn PDF: {e}")
                    # Continue with parsing even if security check fails
            
            # Parse LinkedIn PDF
            result = linkedin_parser.parse(tmp_path)
            
            # Map parsed dictionary fields with safe defaults
            return LinkedInResponse(
                identity=result.get("identity", {}),
                profile_signals=result.get("profile_signals", {}),
                experience_signals=result.get("experience_signals", {}),
                skills_signals=result.get("skills_signals", {}),
                activity_signals=result.get("activity_signals", {}),
                credibility_flags=result.get("credibility_flags", {}),
                confidence_score=result.get("confidence_score", 0.0),
                experience=result.get("experience", {}) if isinstance(result.get("experience"), dict) else {},
                education=result.get("education", []),
                # Add security status
                security_status=security_status,
                security_flags=security_flags,
                fraud_detected=fraud_detected,
                manipulation_detected=manipulation_detected
            )
        finally:
            # Clean up temp file ONLY if we created it
            if file and file.filename and tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        logger.error(f"LinkedIn parsing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"LinkedIn parsing failed: {str(e)}"
        )


@app.post("/parse-path", response_model=LinkedInResponse)
async def parse_linkedin_path(request: LinkedInRequest):
    """
    Parse LinkedIn profile from file path
    (Alternative endpoint if file is already on server)
    """
    global linkedin_parser
    
    try:
        if not request.pdf_path:
            raise HTTPException(status_code=400, detail="pdf_path required")
        
        if not os.path.exists(request.pdf_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Lazy initialization
        if linkedin_parser is None:
            from skill_verification_agent.agents.linkedin_parser import LinkedInPDFParser
            linkedin_parser = LinkedInPDFParser()
        
        # Parse LinkedIn PDF
        result = linkedin_parser.parse(request.pdf_path)
        
        return LinkedInResponse(
            experience=result.get("experience", {}).get("timeline", []),
            education=result.get("education", []),
            skills=result.get("skills", {}).get("claimed", []),
            certifications=result.get("certifications", []),
            summary=result.get("summary")
        )
    
    except Exception as e:
        logger.error(f"LinkedIn parsing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"LinkedIn parsing failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "linkedin_parser",
        "parser_loaded": linkedin_parser is not None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)
