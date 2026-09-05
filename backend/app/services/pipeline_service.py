"""
Pipeline Service for Fair Hiring System
Orchestrates agent execution and database storage
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models import (
    Application, Credential, AgentRun, ReviewCase,
    ApplicationStatus, PipelineStatus
)
from app.agent_client import AgentClient
from app.schemas import ReviewSeverity

from app.services.pipeline_orchestrator import PipelineOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineService:
    """
    Service for orchestrating the hiring pipeline.
    Manages agent execution, data storage, and error handling.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize pipeline service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.agent_client = AgentClient()
    
    async def close(self):
        """Close agent client."""
        await self.agent_client.close()
    
    async def run_pipeline(
        self,
        application_id: int
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline for an application.
        
        Args:
            application_id: Application ID
            
        Returns:
            Pipeline execution results
        """
        logger.info(f"Starting pipeline for application {application_id}")
        
        # Fetch application
        application = await self._get_application(application_id)
        if not application:
            return {
                "success": False,
                "error": f"Application {application_id} not found"
            }
        
        try:
            # Prepare candidate data (reconstructs resume_path)
            candidate_data = await self._prepare_candidate_data(application)
            
            # Delegate to Orchestrator
            orch = PipelineOrchestrator(self.db)
            state = await orch.execute_pipeline(
                application_id=application_id,
                resume_text=application.resume_text,
                resume_path=candidate_data.get("resume_path", ""),
                github_url=application.github_url,
                leetcode_url=application.leetcode_url,
                codeforces_url=application.codeforces_url,
                linkedin_pdf_path=candidate_data.get("linkedin_path"), # Matches expected key
                linkedin_text=application.linkedin_text,
                linkedin_url=application.linkedin_url
            )
            
            # Extract match results for backward compatibility with router response
            if not isinstance(state, dict):
                state = {}
            evidence = state.get("evidence") or {}
            matching = evidence.get("matching") or {}
            match_score = matching.get("match_score", 0)
            pipeline_status = state.get("pipeline_status", "unknown")

            logger.info(f"Pipeline completed via Orchestrator for application {application_id}. Status: {pipeline_status}")
            return {
                "success": True,
                "application_id": application_id,
                "state": state,
                "credential": state,
                "match_score": match_score,
                "pipeline_status": pipeline_status
            }
                
        except Exception as e:
            logger.error(f"Pipeline exception for application {application_id}: {str(e)}", exc_info=True)
            await self._update_application_status(
                application_id,
                ApplicationStatus.pending,
                PipelineStatus.failed,
                pipeline_error=str(e)
            )
            return {
                "success": False,
                "application_id": application_id,
                "error": str(e)
            }
    
    async def _get_application(self, application_id: int) -> Optional[Application]:
        """Fetch application with related data."""
        query = select(Application).options(
            selectinload(Application.candidate),
            selectinload(Application.job)
        ).where(Application.id == application_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _prepare_candidate_data(self, application: Application) -> Dict[str, Any]:
        """Prepare candidate data for agent pipeline."""
        # Add resume path if file exists (reconstructed from deterministic pattern)
        # Pattern: backend/data/resumes/{anon_id}_{job_id}.pdf
        import os
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        resume_path = os.path.join(BASE_DIR, "data", "resumes", f"{application.candidate.anon_id}_{application.job_id}.pdf")
        
        linkedin_path = os.path.join(BASE_DIR, "data", "linkedin", f"{application.candidate.anon_id}_{application.job_id}.pdf")
        
        data = {
            "anon_id": application.candidate.anon_id,
            "resume_text": application.resume_text,
            "github_url": application.github_url,
            "leetcode_url": application.leetcode_url,
            "codeforces_url": application.codeforces_url,
            "linkedin_url": application.linkedin_url,
            "linkedin_text": application.linkedin_text,
        }
        
        # Add resume_path if file exists
        if os.path.exists(resume_path):
            data["resume_path"] = resume_path
            logger.info(f"✅ Resume PDF found: {resume_path}")
        else:
            logger.warning(f"⚠️ Resume PDF not found at: {resume_path}")

        # Add linkedin_path if file exists
        if os.path.exists(linkedin_path):
            data["linkedin_path"] = linkedin_path
            logger.info(f"✅ LinkedIn PDF found: {linkedin_path}")
        else:
            logger.warning(f"⚠️ LinkedIn PDF not found at: {linkedin_path}")
            
        return data

    
    async def _prepare_job_data(self, application: Application) -> Dict[str, Any]:
        """Prepare job data for agent pipeline."""
        job = application.job
        # If required_skills is a dict (v3), use it directly as the base
        if isinstance(job.required_skills, dict):
            data = job.required_skills.copy()
            # Safely extract languages field
            languages = data.get("languages", []) if isinstance(data.get("languages"), list) else []
            
            # Ensure matching_philosophy is a dict, not a string
            if "matching_philosophy" not in data or isinstance(data.get("matching_philosophy"), str):
                data["matching_philosophy"] = {
                    "type": "skills_based",
                    "learning_velocity_weight": 0.2,
                    "experience_weight": 0.3,
                    "skill_match_weight": 0.5
                }
            
            data.update({
                "title": job.title,
                "description": job.description,
                "company_id": job.company_id,
                "languages": languages  # Add languages field for matching service
            })
            return data
        
        # Legacy fallback
        return {
            "title": job.title,
            "description": job.description,
            "requirements": job.required_skills,
            "company_id": job.company_id,
        }
    
    async def _update_application_status(
        self,
        application_id: int,
        status: ApplicationStatus,
        pipeline_status: PipelineStatus,
        match_score: Optional[float] = None,
        feedback_json: Optional[Dict[str, Any]] = None,
        pipeline_error: Optional[str] = None
    ):
        """Update application status in database."""
        update_data = {
            "status": status,
            "pipeline_status": pipeline_status,
            "updated_at": datetime.utcnow()
        }
        
        if match_score is not None:
            update_data["match_score"] = match_score
        if feedback_json is not None:
            update_data["feedback_json"] = feedback_json
        if pipeline_error is not None:
            update_data["pipeline_error"] = pipeline_error
        
        query = update(Application).where(Application.id == application_id).values(**update_data)
        await self.db.execute(query)
        await self.db.commit()
    
    async def _store_agent_runs(
        self,
        application_id: int,
        pipeline_results: Dict[str, Any]
    ):
        """Store individual agent run results."""
        agents = pipeline_results.get("agents", {})
        
        for agent_name, agent_result in agents.items():
            agent_run = AgentRun(
                application_id=application_id,
                agent_name=agent_name,
                input_payload={},  # Could store input if needed
                output_payload=agent_result.get("data"),
                status="completed" if agent_result.get("success") else "failed",
                error_message=agent_result.get("error"),
                execution_time_ms=agent_result.get("execution_time_ms"),
                created_at=datetime.utcnow()
            )
            self.db.add(agent_run)
        
        await self.db.commit()
    
    async def _store_credential(
        self,
        application_id: int,
        credential_data: Dict[str, Any]
    ):
        """Store credential in database."""
        application = await self._get_application(application_id)
        
        credential = Credential(
            candidate_id=application.candidate_id,
            application_id=application_id,
            credential_json=credential_data.get("payload", credential_data),
            hash_sha256=credential_data.get("hash", ""),
            signature_b64=credential_data.get("signature", ""),
            issued_at=datetime.utcnow(),
            expires_at=None,  # Could calculate based on policy
            created_at=datetime.utcnow()
        )
        
        self.db.add(credential)
        await self.db.commit()
    
    async def _check_for_review_cases(
        self,
        application_id: int,
        pipeline_results: Dict[str, Any]
    ):
        """Check if any review cases need to be created."""
        application = await self._get_application(application_id)
        review_cases = []
        
        # Check ATS fraud detection
        ats_result = pipeline_results.get("agents", {}).get("ats", {}).get("data", {})
        if ats_result.get("fraud_detected"):
            review_cases.append({
                "triggered_by": "ats_agent",
                "severity": ReviewSeverity.high,
                "reason": "Potential resume fraud detected",
                "evidence": ats_result
            })
        
        # Check bias detection
        bias_result = pipeline_results.get("agents", {}).get("bias", {}).get("data", {})
        if bias_result.get("bias_detected"):
            review_cases.append({
                "triggered_by": "bias_agent",
                "severity": ReviewSeverity.medium,
                "reason": "Potential bias detected in job description",
                "evidence": bias_result
            })
        
        # Check for suspicious GitHub activity
        github_result = pipeline_results.get("agents", {}).get("github", {}).get("data", {})
        if github_result.get("suspicious_activity"):
            review_cases.append({
                "triggered_by": "github_agent",
                "severity": ReviewSeverity.medium,
                "reason": "Suspicious GitHub activity detected",
                "evidence": github_result
            })
        
        # Create review cases
        for case_data in review_cases:
            review_case = ReviewCase(
                application_id=application_id,
                job_id=application.job_id,
                candidate_id=application.candidate_id,
                triggered_by=case_data["triggered_by"],
                severity=case_data["severity"],
                reason=case_data["reason"],
                evidence=case_data["evidence"],
                status="pending",
                created_at=datetime.utcnow()
            )
            self.db.add(review_case)
        
        if review_cases:
            await self.db.commit()
            logger.info(f"Created {len(review_cases)} review cases for application {application_id}")
    
    async def get_pipeline_status(
        self,
        application_id: int
    ) -> Dict[str, Any]:
        """
        Get pipeline status for an application.
        
        Args:
            application_id: Application ID
            
        Returns:
            Pipeline status information
        """
        application = await self._get_application(application_id)
        if not application:
            return {
                "success": False,
                "error": f"Application {application_id} not found"
            }
        
        # Get agent runs
        query = select(AgentRun).where(AgentRun.application_id == application_id)
        result = await self.db.execute(query)
        agent_runs = result.scalars().all()
        
        return {
            "success": True,
            "application_id": application_id,
            "pipeline_status": application.pipeline_status,
            "application_status": application.status,
            "match_score": application.match_score,
            "pipeline_error": application.pipeline_error,
            "agent_runs": [
                {
                    "agent_name": run.agent_name,
                    "status": run.status,
                    "execution_time_ms": run.execution_time_ms,
                    "created_at": run.created_at.isoformat()
                }
                for run in agent_runs
            ]
        }
    
    async def get_credential(
        self,
        application_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get credential for an application.
        
        Args:
            application_id: Application ID
            
        Returns:
            Credential data or None
        """
        query = select(Credential).where(Credential.application_id == application_id)
        result = await self.db.execute(query)
        credential = result.scalar_one_or_none()
        
        if credential:
            return {
                "success": True,
                "credential": credential.credential_json,
                "hash": credential.hash_sha256,
                "signature": credential.signature_b64,
                "issued_at": credential.issued_at.isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Credential not found"
            }