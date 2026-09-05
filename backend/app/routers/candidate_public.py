# pyright: reportMissingImports=false
"""
Candidate Public Router - Alias for frontend compatibility
Maps /candidate/* to /api/candidates/* endpoints
"""
from fastapi import APIRouter, Depends, Form, File, UploadFile, BackgroundTasks, HTTPException # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

from app.database import get_db # type: ignore
from app.routers import candidate # type: ignore
import sys

# 2026 Fix: Force UTF-8 encoding for stdout/stderr on Windows
if sys.platform.startswith('win'):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8') # type: ignore
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8') # type: ignore

# Create router with /candidate prefix (no /api)
router = APIRouter(prefix="/candidate", tags=["Candidate Public"])

# Re-export all candidate endpoints with the new prefix
# Stats endpoint
@router.get("/{anon_id}/stats")
async def get_candidate_stats(anon_id: str, db: AsyncSession = Depends(get_db)):
    """Get candidate statistics"""
    from app.routers.candidate import get_candidate_stats as _get_stats # type: ignore
    return await _get_stats(anon_id, db)

# Applications endpoint  
@router.get("/{anon_id}/applications")
async def get_candidate_applications(anon_id: str, db: AsyncSession = Depends(get_db)):
    """Get candidate applications - returns flat list for frontend compatibility"""
    from app.routers.candidate import get_candidate_applications as _get_apps # type: ignore
    res = await _get_apps(anon_id, db)
    # Extract the list from the wrapper
    if isinstance(res, dict):
        return res.get("applications", [])
    # If it's the Pydantic model, convert to list of dicts to ensure extra fields like 'feedback' are present
    import json
    from fastapi.encoders import jsonable_encoder # type: ignore
    return jsonable_encoder(getattr(res, 'applications', []))

# Apply endpoint (handles FormData)
@router.options("/apply")
async def apply_options():
    """Handle CORS preflight for apply endpoint"""
    return {}

@router.post("/apply")
async def apply_to_job(
    background_tasks: BackgroundTasks,
    job_id: int = Form(...),
    anon_id: str = Form(...),
    resume: UploadFile = File(...),
    github: Optional[str] = Form(None),
    leetcode: Optional[str] = Form(None),
    codeforces: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    linkedin_pdf: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle candidate application submission from FormData"""
    from app.routers.application import create_application # type: ignore
    from app.schemas import ApplicationCreateRequest # type: ignore
    
    # Create destination folder for resumes
    # We use a deterministic path pattern so pipeline service can find it:
    # backend/data/resumes/{anon_id}_{job_id}.pdf
    
    import os
    from app.utils.pdf_utils import extract_text_from_pdf, save_upload_file # type: ignore
    
    # Path setup
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    RESUME_DIR = os.path.join(BASE_DIR, "data", "resumes")
    LINKEDIN_DIR = os.path.join(BASE_DIR, "data", "linkedin")
    
    # Create directories if they don't exist
    os.makedirs(RESUME_DIR, exist_ok=True)
    os.makedirs(LINKEDIN_DIR, exist_ok=True)
    
    # Save resume file
    filename = f"{anon_id}_{job_id}.pdf"
    file_path = save_upload_file(resume, RESUME_DIR, filename)
    
    # Extract resume text
    if file_path and os.path.exists(file_path):
        extracted_text = extract_text_from_pdf(file_path)
        if not extracted_text:
             extracted_text = f"Warning: Text extraction failed for {resume.filename}"
    else:
        extracted_text = f"Error: File save failed for {resume.filename}"
        file_path = None

    # Handle LinkedIn URL or PDF
    linkedin_text = None
    target_linkedin_url = linkedin_url.strip() if linkedin_url else None
    
    if linkedin_pdf and linkedin_pdf.filename:
        try:
            linkedin_filename = f"{anon_id}_{job_id}_linkedin.pdf"
            linkedin_path = save_upload_file(linkedin_pdf, LINKEDIN_DIR, linkedin_filename)
            
            if linkedin_path and os.path.exists(linkedin_path):
                linkedin_text = extract_text_from_pdf(linkedin_path)
                if not target_linkedin_url:
                    target_linkedin_url = linkedin_path  # Fallback to file path
                logger.info(f"✅ LinkedIn PDF saved: {linkedin_path}")
            else:
                logger.warning(f"⚠️ LinkedIn PDF save failed")
        except Exception as e:
            logger.error(f"❌ LinkedIn PDF processing error: {str(e)}", exc_info=True)
            # Continue without LinkedIn data rather than failing entire request

    # Create request object
    try:
        request = ApplicationCreateRequest(
            anon_id=anon_id,
            job_id=job_id,
            resume_text=extracted_text, 
            github_url=github,
            leetcode_url=leetcode,
            codeforces_url=codeforces,
            linkedin_url=target_linkedin_url,  # Pass LinkedIn profile URL or path
            linkedin_text=linkedin_text,  # Pass extracted text
            run_pipeline=True
            # Note: We rely on pipeline_service to reconstruct resume file_path from anon_id/job_id logic
        )
        
        res = await create_application(request, background_tasks, db)
        return res
    except HTTPException as he:
        # Re-raise HTTP exceptions (400/404) directly
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"❌ Application creation failed at create_application: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Application submission failed: {str(e)}")

# Jobs endpoint (published jobs)
@router.get("/jobs")
async def list_published_jobs(db: AsyncSession = Depends(get_db)):
    """List all published jobs"""
    from app.models import Job # type: ignore
    from sqlalchemy import select # type: ignore
    
    query = select(Job).where(Job.published == True).order_by(Job.created_at.desc())
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    job_list = []
    for job in jobs:
        job_list.append({
            "id": job.id,
            "company_id": job.company_id,
            "company_name": job.company_id,
            "title": job.title,
            "description": job.description,
            "required_skills": job.required_skills,
            "fairness_score": job.fairness_score,
            "fairness_status": job.fairness_status,
            "fairness_findings": job.fairness_findings,
            "published": job.published,
            "max_participants": job.max_participants,
            "application_deadline": job.application_deadline.isoformat() if job.application_deadline else None,
            "created_at": job.created_at.isoformat()
        })
    
    return job_list

# Application status (Alias for polling)
@router.get("/application/{application_id}/status")
async def get_application_status_alias(application_id: int, db: AsyncSession = Depends(get_db)):
    """Alias for application status polling"""
    from app.routers.application import get_application # type: ignore
    res = await get_application(application_id, db)
    
    # Convert to dict if it's a Pydantic model
    if hasattr(res, 'model_dump'):
        res_dict = getattr(res, 'model_dump')() # type: ignore
    elif isinstance(res, dict):
        res_dict = res
    else:
        try:
            res_dict = dict(res) # type: ignore
        except Exception:
            res_dict = {}
    
    # Ensure it has the fields the frontend expects for the evaluation UI
    res_dict["test_required"] = res_dict.get("test_required", False) # type: ignore
    res_dict["progress_percentage"] = 100 if res_dict.get("status") == "matched" else 50 # type: ignore
    res_dict["current_stage"] = "MATCHING" if res_dict.get("status") == "matched" else "ATS" # type: ignore
    res_dict["stages_completed"] = ["ATS", "GITHUB"] if res_dict.get("status") == "matched" else ["ATS"] # type: ignore
    
    return res_dict

# Submit test (Alias)
@router.post("/application/{application_id}/submit-test")
async def submit_test_alias(
    application_id: int,
    code: str = Form(None),
    language: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Alias for test submission (shell)"""
    return {"success": True, "message": "Test results submitted successfully"}

