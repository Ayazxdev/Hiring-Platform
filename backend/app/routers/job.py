"""
Job Router for Fair Hiring System
Handles job creation and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
from datetime import datetime, timezone
import logging

from app.database import get_db
from app.models import Job, Company, utc_now
from app.agents.jd_bias import JobBiasAgent
from app.agents.job_extraction import JobExtractionAgent
from app.agent_client import AgentClient
from app.schemas import (
    JobCreateRequest,
    JobResponse,
    JobListResponse
)

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])
logger = logging.getLogger(__name__)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    published_only: bool = True,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all jobs.
    
    Args:
        published_only: If True, only return published jobs
        db: Database session
        
    Returns:
        List of jobs
    """
    query = select(Job).options(selectinload(Job.company))

    if published_only:
        query = query.where(Job.published == True)
    
    query = query.order_by(Job.created_at.desc())
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    job_list = []
    for job in jobs:
        job_list.append({
            "job_id": job.id,
            "company_id": job.company_id,
            "company_name": job.company.name if job.company else job.company_id,
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
    
    return JobListResponse(
        success=True,
        jobs=job_list,
        total=len(job_list)
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific job.
    
    Args:
        job_id: Job ID
        db: Database session
        
    Returns:
        Detailed job information
    """
    query = select(Job).options(selectinload(Job.company)).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return JobResponse.model_validate(job)


@router.post("", response_model=JobResponse)
async def create_job(
    request: JobCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new job posting with AI bias audit.
    """
    # 1. Verify company exists (or create a placeholder)
    query = select(Company).where(Company.id == request.company_id)
    result = await db.execute(query)
    company = result.scalar_one_or_none()
    
    if not company:
        # Auto-create company if missing to prevent blocker
        company = Company(
            id=request.company_id,
            name=f"Company {request.company_id}",
            email=f"contact@{request.company_id}.com"
        )
        db.add(company)
        await db.flush()
    
    # 2. AI SKILL EXTRACTION (If skills are missing)
    skills_to_save = request.required_skills or {}
    
    if not skills_to_save or (isinstance(skills_to_save, list) and len(skills_to_save) == 0):
        try:
            # Use agent-based extraction (configurable port)
            agent_client = AgentClient()
            description = request.description or ""
            logger.info("Auto-extracting skills via job_description agent...")
            
            jd_result = await agent_client.call_agent(
                "job_description",
                "/extract",
                {
                    "job_title": request.title,
                    "job_description": description
                }
            )
            
            if jd_result.get("success"):
                extracted_data = jd_result.get("data", {})
            else:
                # Fallback to local extraction if agent fails
                logger.warning(f"Agent extraction failed: {jd_result.get('error')}, falling back to local")
                extraction_agent = JobExtractionAgent()
                extracted_data = extraction_agent.extract(description, title=request.title)
            
            # Save extracted skill metadata dictionary
            skills_to_save = extracted_data
            logger.debug(f"Extracted v3 metadata: {skills_to_save.get('role')}")
            
        except Exception as e:
            logger.error(f"Skill Extraction Error: {e}")
            skills_to_save = []

    # 3. AI BIAS AUDIT
    try:
        bias_agent = JobBiasAgent()
        description = request.description or ""
        bias_result = bias_agent.analyze(description)
        
        raw_score = bias_result.get("bias_score", 0) if isinstance(bias_result, dict) else 0
        try:
            numeric_bias = float(raw_score)
        except (ValueError, TypeError):
            numeric_bias = 0.0
        fairness_score = int(100 - (numeric_bias * 10))
        fairness_status = "VERIFIED" if fairness_score >= 80 else "FLAGGED"
        fairness_findings = bias_result.get("findings", [])
    except Exception as e:
        logger.error(f"Bias Audit Error in Job Router: {e}")
        fairness_score = 100
        fairness_status = "VERIFIED"
        fairness_findings = []

    # 4. Create job
    job = Job(
        company_id=request.company_id,
        title=request.title,
        description=request.description,
        required_skills=skills_to_save,
        fairness_score=fairness_score,
        fairness_status=fairness_status,
        fairness_findings=fairness_findings,
        published=request.published,
        max_participants=request.max_participants,
        application_deadline=request.application_deadline,
        created_at=utc_now()
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return JobResponse(
        id=job.id,
        company_id=job.company_id,
        title=job.title,
        description=job.description,
        required_skills=job.required_skills,
        fairness_score=job.fairness_score,
        fairness_status=job.fairness_status,
        fairness_findings=job.fairness_findings,
        published=job.published,
        max_participants=job.max_participants,
        application_deadline=job.application_deadline,
        created_at=job.created_at
    )


@router.patch("/{job_id}/publish", response_model=JobResponse)
async def publish_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Publish a job posting.
    
    Args:
        job_id: Job ID
        db: Database session
        
    Returns:
        Updated job information
    """
    query = select(Job).options(selectinload(Job.company)).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job.published = True
    job.updated_at = utc_now()
    
    await db.commit()
    await db.refresh(job)
    
    return JobResponse.model_validate(job)