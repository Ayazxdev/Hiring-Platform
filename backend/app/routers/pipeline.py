"""
Pipeline Router for Fair Hiring System
Handles pipeline execution and status queries
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db
from app.services.pipeline_service import PipelineService
from app.schemas import (
    PipelineRunRequest,
    PipelineRunResponse,
    PipelineStatusResponse,
    CredentialResponse
)

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(
    request: PipelineRunRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Run the complete hiring pipeline for an application.
    
    This endpoint:
    1. Validates the application exists
    2. Runs all agent services in sequence
    3. Stores results in the database
    4. Returns the final credential
    
    Args:
        request: Pipeline run request with application_id
        db: Database session
        
    Returns:
        Pipeline execution results with credential
    """
    pipeline_service = PipelineService(db)
    
    try:
        result = await pipeline_service.run_pipeline(request.application_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Pipeline execution failed")
            )
        
        return PipelineRunResponse(
            success=True,
            application_id=result["application_id"],
            credential=result["credential"],
            match_score=result.get("match_score"),
            pipeline_results=result.get("pipeline_results")
        )
        
    finally:
        await pipeline_service.close()


@router.get("/status/{application_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    application_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get pipeline status for an application.
    
    Args:
        application_id: Application ID
        db: Database session
        
    Returns:
        Pipeline status information
    """
    pipeline_service = PipelineService(db)
    
    try:
        result = await pipeline_service.get_pipeline_status(application_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Application not found")
            )
        
        return PipelineStatusResponse(
            success=True,
            application_id=result["application_id"],
            pipeline_status=result["pipeline_status"],
            application_status=result["application_status"],
            match_score=result.get("match_score"),
            pipeline_error=result.get("pipeline_error"),
            agent_runs=result.get("agent_runs", [])
        )
        
    finally:
        await pipeline_service.close()


@router.get("/credential/{application_id}", response_model=CredentialResponse)
async def get_credential(
    application_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get credential for an application.
    
    Args:
        application_id: Application ID
        db: Database session
        
    Returns:
        Credential data with hash and signature
    """
    pipeline_service = PipelineService(db)
    
    try:
        result = await pipeline_service.get_credential(application_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Credential not found")
            )
        
        return CredentialResponse(
            success=True,
            credential=result["credential"],
            hash=result["hash"],
            signature=result["signature"],
            issued_at=result["issued_at"]
        )
        
    finally:
        await pipeline_service.close()