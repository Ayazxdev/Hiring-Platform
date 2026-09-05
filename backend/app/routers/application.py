"""
Application Router for Fair Hiring System
Handles job applications and status updates
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Dict, Any
from datetime import datetime
import logging

from app.database import get_db
from app.models import Application, Candidate, Job, ApplicationStatus
from app.schemas import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationStatusUpdateRequest,
    ApplicationDetailResponse
)
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/api/applications", tags=["Applications"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ApplicationResponse)
async def create_application(
    request: ApplicationCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new job application.
    
    This endpoint:
    1. Validates candidate and job exist
    2. Creates the application record
    3. Optionally triggers the pipeline in the background
    
    Args:
        request: Application creation data
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Created application information
    """
    # Find candidate
    query = select(Candidate).where(Candidate.anon_id == request.anon_id)
    result = await db.execute(query)
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Find job (eager-load company for name lookup)
    query = select(Job).options(selectinload(Job.company)).where(Job.id == request.job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check if job is published
    if not job.published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not published"
        )
    
    # Check if application deadline has passed
    if job.application_deadline and job.application_deadline < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application deadline has passed"
        )
    
    # Check if candidate already applied
    query = select(Application).where(
        Application.candidate_id == candidate.id,
        Application.job_id == job.id
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing application
        existing.resume_text = request.resume_text
        existing.github_url = request.github_url
        existing.leetcode_url = request.leetcode_url
        existing.linkedin_url = request.linkedin_url
        existing.codeforces_url = request.codeforces_url
        existing.status = ApplicationStatus.pending
        existing.pipeline_status = "not_started"
        existing.updated_at = datetime.utcnow()
        
        # Reset match score and feedback as it's a re-run
        existing.match_score = None
        existing.feedback_json = None
        
        await db.commit()
        await db.refresh(existing)
        application = existing
    else:
        # Create application
        application = Application(
            candidate_id=candidate.id,
            job_id=job.id,
            resume_text=request.resume_text,
            github_url=request.github_url,
            leetcode_url=request.leetcode_url,
            linkedin_url=request.linkedin_url,
            codeforces_url=request.codeforces_url,
            status=ApplicationStatus.pending,
            pipeline_status="not_started",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(application)
        await db.commit()
        await db.refresh(application)
    
    # Trigger pipeline in background if requested
    if request.run_pipeline:
        background_tasks.add_task(run_pipeline_background, application.id)
        application.pipeline_status = "queued"
        await db.commit()
    
    return ApplicationResponse(
        success=True,
        application_id=application.id,
        candidate_id=application.candidate_id,
        job_id=application.job_id,
        job_title=job.title,
        company_name=job.company.name if job.company else job.company_id,
        status=application.status,
        pipeline_status=application.pipeline_status,
        created_at=application.created_at.isoformat()
    )


async def run_pipeline_background(application_id: int):
    """
    Background task to run the pipeline.
    
    Args:
        application_id: Application ID
    """
    from app.database import get_db_context
    
    async with get_db_context() as db:
        pipeline_service = PipelineService(db)
        try:
            await pipeline_service.run_pipeline(application_id)
        except Exception as e:
            # Log error but don't crash
            logger.error(f"Pipeline failed for application {application_id}: {str(e)}")
        finally:
            await pipeline_service.close()


@router.get("/{application_id}", response_model=ApplicationDetailResponse)
async def get_application(
    application_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific application.
    
    Args:
        application_id: Application ID
        db: Database session
        
    Returns:
        Detailed application information
    """
    query = select(Application).options(selectinload(Application.job)).where(Application.id == application_id)
    result = await db.execute(query)
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    return ApplicationDetailResponse(
        success=True,
        application_id=application.id,
        candidate_id=application.candidate_id,
        job_id=application.job_id,
        job_title=application.job.title if application.job else "Unknown",
        company_name=application.job.company_id if application.job else "Unknown",
        status=application.status,
        pipeline_status=application.pipeline_status,
        match_score=application.match_score,
        feedback_json=application.feedback_json,
        pipeline_error=application.pipeline_error,
        created_at=application.created_at.isoformat(),
        updated_at=application.updated_at.isoformat()
    )


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    request: ApplicationStatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update application status.
    
    Args:
        application_id: Application ID
        request: Status update data
        db: Database session
        
    Returns:
        Updated application information
    """
    query = select(Application).options(selectinload(Application.job)).where(Application.id == application_id)
    result = await db.execute(query)
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Update status
    application.status = request.status
    application.updated_at = datetime.utcnow()
    
    # Add feedback if provided
    if request.feedback:
        if not application.feedback_json:
            application.feedback_json = {}
        application.feedback_json["status_update"] = request.feedback
    
    await db.commit()
    await db.refresh(application)
    
    return ApplicationResponse(
        success=True,
        application_id=application.id,
        candidate_id=application.candidate_id,
        job_id=application.job_id,
        job_title=application.job.title if application.job else "Unknown",
        company_name=application.job.company_id if application.job else "Unknown",
        status=application.status,
        pipeline_status=application.pipeline_status,
        created_at=application.created_at.isoformat()
    )


@router.post("/{application_id}/pipeline", response_model=ApplicationResponse)
async def trigger_pipeline(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually trigger the pipeline for an application.
    
    Args:
        application_id: Application ID
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Application information
    """
    query = select(Application).options(selectinload(Application.job)).where(Application.id == application_id)
    result = await db.execute(query)
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check if pipeline is already running
    if application.pipeline_status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pipeline is already running"
        )
    
    # Trigger pipeline in background
    background_tasks.add_task(run_pipeline_background, application_id)
    application.pipeline_status = "queued"
    await db.commit()
    
    return ApplicationResponse(
        success=True,
        application_id=application.id,
        candidate_id=application.candidate_id,
        job_id=application.job_id,
        job_title=application.job.title if application.job else "Unknown",
        company_name=application.job.company_id if application.job else "Unknown",
        status=application.status,
        pipeline_status=application.pipeline_status,
        created_at=application.created_at.isoformat()
    )