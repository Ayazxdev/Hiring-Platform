"""
Candidate Router for Fair Hiring System
Handles candidate registration, login, and data retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import Candidate, Application, Credential
from app.schemas import (
    CandidateRegisterRequest,
    CandidateLoginRequest,
    CandidateResponse,
    CandidateStatsResponse,
    ApplicationListResponse,
    ApplicationDetailResponse,
    CredentialResponse
)
from app.auth_utils import generate_anon_id, hash_password, verify_password

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])


@router.post("/register", response_model=CandidateResponse)
async def register_candidate(
    request: CandidateRegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> CandidateResponse:
    """
    Register a new candidate.
    
    Args:
        request: Candidate registration data
        db: Database session
        
    Returns:
        Registered candidate information
    """
    # Check if email already exists
    query = select(Candidate).where(Candidate.email == request.email)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate anonymous ID
    anon_id = generate_anon_id()
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create candidate
    candidate = Candidate(
        anon_id=anon_id,
        email=request.email,
        name=request.name,
        password_hash=password_hash,
        gender=request.gender,
        college=request.college,
        engineer_level=request.engineer_level,
        created_at=datetime.utcnow()
    )
    
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    
    return CandidateResponse(
        id=candidate.id,
        anon_id=candidate.anon_id,
        email=candidate.email,
        name=candidate.name,
        gender=candidate.gender,
        college=candidate.college,
        engineer_level=candidate.engineer_level,
        created_at=candidate.created_at
    )


@router.post("/login", response_model=CandidateResponse)
async def login_candidate(
    request: CandidateLoginRequest,
    db: AsyncSession = Depends(get_db)
) -> CandidateResponse:
    """
    Login a candidate.
    
    Args:
        request: Login credentials
        db: Database session
        
    Returns:
        Candidate information if login successful
    """
    # Find candidate by email
    query = select(Candidate).where(Candidate.email == request.email)
    result = await db.execute(query)
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(request.password, candidate.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    return CandidateResponse(
        id=candidate.id,
        anon_id=candidate.anon_id,
        email=candidate.email,
        name=candidate.name,
        gender=candidate.gender,
        college=candidate.college,
        engineer_level=candidate.engineer_level,
        created_at=candidate.created_at
    )


@router.get("/{anon_id}/stats", response_model=CandidateStatsResponse)
async def get_candidate_stats(
    anon_id: str,
    db: AsyncSession = Depends(get_db)
) -> CandidateStatsResponse:
    """
    Get candidate statistics.
    
    Args:
        anon_id: Candidate's anonymous ID
        db: Database session
        
    Returns:
        Candidate statistics
    """
    # Find candidate
    query = select(Candidate).where(Candidate.anon_id == anon_id)
    result = await db.execute(query)
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Get applications
    query = select(Application).where(Application.candidate_id == candidate.id)
    result = await db.execute(query)
    applications = result.scalars().all()
    
    # Calculate stats
    total_applications = len(applications)
    matched_applications = sum(1 for app in applications if app.status == "matched")
    pending_applications = sum(1 for app in applications if app.status == "pending")
    processing_applications = sum(1 for app in applications if app.status == "processing")
    
    # Get average match score
    match_scores = [app.match_score for app in applications if app.match_score is not None]
    avg_match_score = sum(match_scores) / len(match_scores) if match_scores else 0.0
    
    return CandidateStatsResponse(
        total_applications=total_applications,
        matched_applications=matched_applications,
        pending_applications=pending_applications,
        processing_applications=processing_applications,
        average_match_score=round(avg_match_score, 2)
    )


@router.get("/{anon_id}/applications", response_model=ApplicationListResponse)
async def get_candidate_applications(
    anon_id: str,
    db: AsyncSession = Depends(get_db)
) -> ApplicationListResponse:
    """
    Get all applications for a candidate.
    
    Args:
        anon_id: Candidate's anonymous ID
        db: Database session
        
    Returns:
        List of applications
    """
    # Find candidate
    query = select(Candidate).where(Candidate.anon_id == anon_id)
    result = await db.execute(query)
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Get applications with job details
    query = select(Application).options(selectinload(Application.job)).where(Application.candidate_id == candidate.id).order_by(Application.created_at.desc())
    result = await db.execute(query)
    applications = result.scalars().all()
    
    application_list = []
    for app in applications:
        score = app.match_score
        if score is None and app.feedback_json:
            score = app.feedback_json.get("match_score") or (app.feedback_json.get("breakdown", {}).get("overall_score") if isinstance(app.feedback_json.get("breakdown"), dict) else None)
        application_list.append({
            "application_id": app.id,
            "job_id": app.job_id,
            "job_title": app.job.title if app.job else "Unknown",
            "company_name": app.job.company_id if app.job else "Unknown",
            "status": app.status,
            "match_score": score,
            "feedback": app.feedback_json,
            "created_at": app.created_at,
            "updated_at": app.updated_at
        })
    
    return ApplicationListResponse(
        success=True,
        candidate_id=candidate.id,
        anon_id=anon_id,
        applications=application_list,
        total=len(application_list)
    )


@router.get("/{anon_id}/applications/{application_id}", response_model=ApplicationDetailResponse)
async def get_application_detail(
    anon_id: str,
    application_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApplicationDetailResponse:
    """
    Get detailed information about a specific application.
    
    Args:
        anon_id: Candidate's anonymous ID
        application_id: Application ID
        db: Database session
        
    Returns:
        Detailed application information
    """
    # Find candidate
    query = select(Candidate).where(Candidate.anon_id == anon_id)
    result = await db.execute(query)
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Get application
    query = select(Application).options(selectinload(Application.job)).where(
        Application.id == application_id,
        Application.candidate_id == candidate.id
    )
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


@router.get("/{anon_id}/passport", response_model=CredentialResponse)
async def get_candidate_passport(
    anon_id: str,
    job_id: int,
    db: AsyncSession = Depends(get_db)
) -> CredentialResponse:
    """
    Get the skill passport (credential) for a candidate's application.
    
    Args:
        anon_id: Candidate's anonymous ID
        job_id: Job ID
        db: Database session
        
    Returns:
        Credential data
    """
    # Find candidate
    query = select(Candidate).where(Candidate.anon_id == anon_id)
    result = await db.execute(query)
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Get application
    query = select(Application).where(
        Application.candidate_id == candidate.id,
        Application.job_id == job_id
    )
    result = await db.execute(query)
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get credential
    query = select(Credential).where(Credential.application_id == application.id)
    result = await db.execute(query)
    credential = result.scalar_one_or_none()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found. Pipeline may not have completed yet."
        )
    
    return CredentialResponse(
        success=True,
        credential=credential.credential_json,
        hash=credential.hash_sha256,
        signature=credential.signature_b64,
        issued_at=credential.issued_at.isoformat()
    )