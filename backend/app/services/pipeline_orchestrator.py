# pyright: reportMissingImports=false
"""
Pipeline Orchestrator
Manages the complete 10-stage agent pipeline execution
"""
import logging
import json
import httpx # type: ignore
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import select # type: ignore
from sqlalchemy.orm import selectinload # type: ignore
from app.models import ( # type: ignore
    Application, Candidate, Job, AgentRun, Credential, ReviewCase, Blacklist,
    AgentRunStatus, PipelineStatus, ApplicationStatus
)
from app.config import settings # type: ignore
from app.passport import sign_credential # type: ignore
from app.agent_client import AgentClient # type: ignore

log = logging.getLogger("uvicorn.error")

class PipelineOrchestrator:
    """Orchestrates the complete agent pipeline"""
    
    # Agent service URLs from settings
    SERVICES = {
        "ATS": settings.ATS_AGENT_URL,
        "GITHUB": settings.GITHUB_AGENT_URL,
        "LEETCODE": settings.LEETCODE_AGENT_URL,
        "CODEFORCES": settings.CODEFORCES_AGENT_URL,
        "LINKEDIN": settings.LINKEDIN_AGENT_URL,
        "SKILLS": settings.SKILL_AGENT_URL,
        "TEST": settings.TEST_AGENT_URL,
        "BIAS": settings.BIAS_AGENT_URL,
        "MATCHING": settings.MATCH_AGENT_URL,
        "PASSPORT": settings.PASSPORT_AGENT_URL,
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.state: Dict[str, Any] = {}
        self.agent_client = AgentClient()

    def _ensure_stage(self, stage: str):
        """Ensure stage exists in state"""
        self.state["stage_runs"].setdefault(stage, {
            "status": "queued",
            "attempts": 0,
            "started_at": None,
            "ended_at": None,
            "duration_ms": None,
            "agent_run_id": None,
            "error": None,
            "output_ref": None
        })

    def _stage_ok(self, stage: str) -> bool:
        """Check if stage completed successfully"""
        return self.state["stage_runs"].get(stage, {}).get("status") == "ok"
    
    async def call_agent(self, service_name: str, endpoint: str, payload: Dict) -> Dict:
        """Call an agent service using AgentClient which handles Zynd routing"""
        mapping = {
            "ATS": "ats",
            "GITHUB": "github",
            "LEETCODE": "leetcode",
            "CODEFORCES": "codeforces",
            "LINKEDIN": "linkedin",
            "SKILLS": "skill",
            "TEST": "skill", # TEST usually goes to skill server with a specialized endpoint
            "BIAS": "bias",
            "MATCHING": "matching",
            "PASSPORT": "passport",
        }
        agent_key = mapping.get(service_name, service_name.lower())
        
        self._ensure_stage(service_name)
        log.info(f"[PIPELINE] Calling {service_name} via AgentClient ({agent_key})")
        
        try:
            return await self.agent_client.call_agent(agent_key, endpoint, payload)
        except Exception as e:
            log.error(f"[PIPELINE] {service_name} call failed: {str(e)}")
            raise
    
    async def log_agent_run(
        self,
        application_id: int,
        agent_name: str,
        input_payload: Dict,
        output_payload: Optional[Dict] = None,
        status: AgentRunStatus = AgentRunStatus.pending
    ) -> AgentRun:
        """Log an agent run to the database"""
        run = AgentRun(
            application_id=application_id,
            agent_name=agent_name,
            input_payload=input_payload,
            output_payload=output_payload,
            status=status
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        
        # update state with run id
        self._ensure_stage(agent_name)
        self.state["stage_runs"][agent_name]["agent_run_id"] = run.id
        
        return run
    
    async def save_credential_state(self, application_id: int, state: Dict):
        """Save or update credential state"""
        import copy
        from sqlalchemy.orm.attributes import flag_modified

        # Check if credential exists
        q = await self.db.execute(
            select(Credential)
            .where(Credential.application_id == application_id)
            .order_by(Credential.issued_at.desc())
        )
        cred = q.scalar_one_or_none()
        
        # Get application for candidate_id
        app_q = await self.db.execute(
            select(Application).where(Application.id == application_id)
        )
        app = app_q.scalar_one()
        
        clean_state = copy.deepcopy(state)
        h, sig = sign_credential(clean_state)

        if cred:
            # Update existing
            cred.credential_json = clean_state
            flag_modified(cred, "credential_json")
            cred.hash_sha256 = h
            cred.signature_b64 = sig
        else:
            # Create new
            cred = Credential(
                candidate_id=app.candidate_id,
                application_id=application_id,
                credential_json=clean_state,
                hash_sha256=h,
                signature_b64=sig
            )
            self.db.add(cred)
        
        await self.db.commit()
        return cred
    
    async def execute_pipeline(
        self,
        application_id: int,
        resume_text: str,
        resume_path: str,
        github_url: Optional[str],
        leetcode_url: Optional[str],
        codeforces_url: Optional[str],
        linkedin_pdf_path: Optional[str],
        linkedin_text: Optional[str],
        linkedin_url: Optional[str] = None
    ) -> Dict:
        """
        Execute the complete 10-stage pipeline
        
        Returns pipeline state or raises exception on critical failure
        """
        # Get application and candidate (eager-load job to avoid greenlet issues)
        app_q = await self.db.execute(
            select(Application)
            .where(Application.id == application_id)
            .options(selectinload(Application.job))
        )
        app = app_q.scalar_one()
        
        cand_q = await self.db.execute(
            select(Candidate).where(Candidate.id == app.candidate_id)
        )
        cand = cand_q.scalar_one()
        
        # Try to load existing state from Credential table
        q = await self.db.execute(
            select(Credential)
            .where(Credential.application_id == application_id)
            .order_by(Credential.issued_at.desc())
        )
        existing_cred = q.scalars().first()
        
        if existing_cred and existing_cred.credential_json and existing_cred.credential_json.get("schema_version") == 1:
            log.info(f"[PIPELINE] Loading existing state for application {application_id}")
            self.state = existing_cred.credential_json
            self.state["pipeline_status"] = "running"
            self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        else:
            # Initialize New StageState
            self.state = {
                "schema_version": 1,
                "application_id": application_id,
                "candidate_id": cand.id,
                "job_id": app.job_id,
                "pipeline_status": "running",
                "application_status": "processing",
                "current_stage": "INIT",
                "stages_completed": [],
                "started_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "stage_runs": {},
                "evidence": {
                    "ats": None,
                    "github": None,
                    "leetcode": None,
                    "codeforces": None,
                    "linkedin": None,
                    "skills": None,
                    "bias": None,
                    "matching": None,
                    "passport": None
                },
                "derived": {
                    "verified_skills": [],
                    "confidence": None,
                    "signal_strength": None,
                    "test_required": False,
                    "match_score": None,
                    "matched_skills": [],
                    "missing_skills": []
                },
                "flags": [],
                "review_case_id": None,
                "credential_id": None
            }
        
        # Save initial state
        await self.save_credential_state(application_id, self.state)
        
        try:
            # STAGE 1: ATS (FRAUD DETECTION)
            stage = "ATS"
            self._ensure_stage(stage)
            
            if self._stage_ok(stage):
                log.info(f"[PIPELINE] Skipping {stage} (already completed)")
            else:
                log.info(f"[PIPELINE] Stage 1: ATS - application_id={application_id}")
                self.state["current_stage"] = stage
                self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                app.status = ApplicationStatus.processing
                app.pipeline_status = PipelineStatus.in_progress
                await self.db.commit()
                
                await self.save_credential_state(application_id, self.state)
                
                ats_input = {
                    "application_id": application_id,
                    "resume_text": resume_text,
                    "resume_path": resume_path
                }
                
                run = await self.log_agent_run(application_id, stage, ats_input, status=AgentRunStatus.running)
                self.state["stage_runs"][stage]["started_at"] = datetime.now(timezone.utc).isoformat()
                
                start_time = datetime.now()
                try:
                    ats_result = await self.call_agent("ATS", "/run", ats_input)
                    duration = (datetime.now() - start_time).total_seconds() * 1000

                    # agent_client wraps response: { "success": bool, "data": {...}, "status_code": int }
                    # The actual ATS payload lives inside "data"
                    ats_data = ats_result.get("data", ats_result)

                    # DEBUG: Log ATS output
                    skills_found = ats_data.get("skills", [])
                    log.info(f"[PIPELINE-DEBUG] ATS Stage Complete. Skills found: {len(skills_found)}")
                    if skills_found:
                        log.info(f"[PIPELINE-DEBUG] First 3 skills: {skills_found[:3]}")
                    else:
                        log.warning(f"[PIPELINE-DEBUG] ATS returned NO SKILLS. Check extraction logic.")
                        if "evidence" in ats_data:
                            log.info(f"[PIPELINE-DEBUG] ATS Evidence keys: {list(ats_data['evidence'].keys())}")

                    run.output_payload = ats_data
                    run.status = AgentRunStatus.completed
                    run.execution_time_ms = duration

                    self.state["evidence"]["ats"] = ats_data
                    self.state["stage_runs"][stage].update({
                        "status": "ok",
                        "ended_at": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": duration,
                        "output_ref": "evidence.ats"
                    })

                    # Check for blacklist/rejection (from Guard OR legacy LLM)
                    # Read from ats_data (unwrapped), not the outer wrapper
                    action = ats_data.get("action", "")
                    legacy_action = ats_data.get("evidence", {}).get("final_action", "") if isinstance(ats_data.get("evidence"), dict) else ""

                    if action in ["BLACKLIST", "REJECTED"] or legacy_action in ["blacklist", "BLACKLIST", "BLACKLISTED", "rejected", "REJECTED"]:
                        log.warning(f"[PIPELINE] ATS blacklisted application {application_id}. Action={action}")

                        # Build human-readable fraud reason listing detected attack types
                        fraud_flags = ats_data.get("flags", [])
                        manipulation_patterns = ats_data.get("manipulation_signals", {}).get("patterns", [])
                        all_flags = list(set(fraud_flags + manipulation_patterns))

                        flag_descriptions = []
                        for f in all_flags:
                            if "white_text" in f.lower():
                                flag_descriptions.append("white hidden text")
                            elif "injection" in f.lower() or "prompt" in f.lower():
                                flag_descriptions.append("prompt injection")
                            elif "fraud" in f.lower() or "manipulation" in f.lower():
                                flag_descriptions.append("resume manipulation/fraud")
                            elif "bot" in f.lower() or "generated" in f.lower():
                                flag_descriptions.append("AI-generated content")
                            elif "invisible" in f.lower() or "hidden" in f.lower():
                                flag_descriptions.append("hidden content layer")
                            else:
                                flag_descriptions.append(f)

                        # Deduplicate and build reason string
                        unique_descriptions = list(dict.fromkeys(flag_descriptions))
                        base_reason = ats_data.get("reason", ats_data.get("fraud_reason", ""))
                        if unique_descriptions:
                            fraud_reason = f"Resume rejected: detected {', '.join(unique_descriptions)}."
                            if base_reason:
                                fraud_reason += f" Detail: {base_reason}"
                        else:
                            fraud_reason = base_reason or ats_data.get("evidence", {}).get("human_review_reason", "ATS fraud detection")

                        # Blacklist candidate
                        blacklist = Blacklist(
                            candidate_id=app.candidate_id,
                            reason=fraud_reason
                        )
                        self.db.add(blacklist)

                        # Create Review Case so reviewer can see the blacklist
                        review = ReviewCase(
                            application_id=application_id,
                            job_id=app.job_id,
                            candidate_id=app.candidate_id,
                            triggered_by=stage,
                            severity="critical",
                            reason=fraud_reason,
                            evidence=ats_data
                        )
                        self.db.add(review)

                        app.status = ApplicationStatus.rejected
                        app.pipeline_status = PipelineStatus.failed
                        app.pipeline_error = fraud_reason
                        self.state["pipeline_status"] = "rejected"
                        self.state["blacklist_reason"] = fraud_reason
                        self.state["blacklist_flags"] = unique_descriptions

                        await self.db.commit()
                        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                        await self.save_credential_state(application_id, self.state)

                        log.warning(f"[PIPELINE] Pipeline STOPPED. Reason: {fraud_reason}")
                        return self.state

                    # Check for review
                    if action in ["NEEDS_REVIEW", "REVIEW"] or legacy_action in ["review", "REVIEW", "PENDING_HUMAN_REVIEW", "NEEDS_REVIEW"]:
                        log.info(f"[PIPELINE] ATS flagged application {application_id} for review")

                        review = ReviewCase(
                            application_id=application_id,
                            job_id=app.job_id,
                            candidate_id=app.candidate_id,
                            triggered_by=stage,
                            severity=ats_data.get("severity", "medium"),
                            reason=ats_data.get("reason", "ATS flagged for review"),
                            evidence=ats_data
                        )
                        self.db.add(review)

                        app.pipeline_status = PipelineStatus.completed
                        self.state["pipeline_status"] = "needs_review"

                        await self.db.commit()
                        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                        await self.save_credential_state(application_id, self.state)

                        return self.state

                    self.state["stages_completed"].append(stage)
                    
                except Exception as e:
                    run.status = AgentRunStatus.failed
                    run.error_message = str(e)
                    log.error(f"[PIPELINE] ATS failed: {str(e)}")
                    
                    self.state["stage_runs"][stage].update({
                        "status": "failed",
                        "error": str(e),
                    })
                    # Retain partial evidence state and proceed with subsequent stages
                    
                await self.db.commit()
                self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.save_credential_state(application_id, self.state)
            
            # STAGE 2: GITHUB
            if github_url:
                stage = "GITHUB"
                self._ensure_stage(stage)
                
                if self._stage_ok(stage):
                    log.info(f"[PIPELINE] Skipping {stage} (already completed)")
                else:
                    log.info(f"[PIPELINE] Stage 2: GitHub - application_id={application_id}")
                    self.state["current_stage"] = stage
                    self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                    await self.save_credential_state(application_id, self.state)
                    
                    github_input = {
                        "github_url": github_url,
                        "application_id": application_id
                    }
                    
                    run = await self.log_agent_run(application_id, stage, github_input, status=AgentRunStatus.running)
                    self.state["stage_runs"][stage]["started_at"] = datetime.now(timezone.utc).isoformat()
                    
                    start_time = datetime.now()
                    try:
                        github_result = await self.call_agent("GITHUB", "/scrape", github_input)
                        duration = (datetime.now() - start_time).total_seconds() * 1000
                        
                        run.output_payload = github_result
                        run.status = AgentRunStatus.completed
                        run.execution_time_ms = duration
                        
                        self.state["evidence"]["github"] = github_result
                        self.state["stage_runs"][stage].update({
                            "status": "ok",
                            "ended_at": datetime.now(timezone.utc).isoformat(),
                            "duration_ms": duration,
                            "output_ref": "evidence.github"
                        })
                        self.state["stages_completed"].append(stage)
                        
                    except Exception as e:
                        run.status = AgentRunStatus.failed
                        run.error_message = str(e)
                        log.error(f"[PIPELINE] GitHub failed: {str(e)}")
                        
                        self.state["stage_runs"][stage].update({
                            "status": "failed",
                            "error": str(e),
                            "ended_at": datetime.now(timezone.utc).isoformat()
                        })
                    
                    await self.db.commit()
                    self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                    await self.save_credential_state(application_id, self.state)
            
            # STAGE 3: LEETCODE
            if leetcode_url:
                stage = "LEETCODE"
                self._ensure_stage(stage)
                
                if self._stage_ok(stage):
                    log.info(f"[PIPELINE] Skipping {stage} (already completed)")
                else:
                    log.info(f"[PIPELINE] Stage 3: LeetCode - application_id={application_id}")
                    self.state["current_stage"] = stage
                    self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                    await self.save_credential_state(application_id, self.state)
                    
                    leetcode_input = {
                        "username": leetcode_url,
                        "application_id": application_id
                    }
                    
                    run = await self.log_agent_run(application_id, stage, leetcode_input, status=AgentRunStatus.running)
                    self.state["stage_runs"][stage]["started_at"] = datetime.now(timezone.utc).isoformat()
                    
                    start_time = datetime.now()
                    try:
                        leetcode_result = await self.call_agent("LEETCODE", "/scrape", leetcode_input)
                        duration = (datetime.now() - start_time).total_seconds() * 1000
                        
                        run.output_payload = leetcode_result
                        run.status = AgentRunStatus.completed
                        run.execution_time_ms = duration
                        
                        self.state["evidence"]["leetcode"] = leetcode_result
                        self.state["stage_runs"][stage].update({
                            "status": "ok",
                            "ended_at": datetime.now(timezone.utc).isoformat(),
                            "duration_ms": duration,
                            "output_ref": "evidence.leetcode"
                        })
                        self.state["stages_completed"].append(stage)
                        
                    except Exception as e:
                        run.status = AgentRunStatus.failed
                        run.error_message = str(e)
                        log.error(f"[PIPELINE] LeetCode failed: {str(e)}")
                        
                        self.state["stage_runs"][stage].update({
                            "status": "failed",
                            "error": str(e),
                            "ended_at": datetime.now(timezone.utc).isoformat()
                        })
                    
                    await self.db.commit()
                    self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                    await self.save_credential_state(application_id, self.state)
            
            # STAGE 4: CODEFORCES
            if codeforces_url:
                stage = "CODEFORCES"
                self._ensure_stage(stage)
                
                if self._stage_ok(stage):
                    log.info(f"[PIPELINE] Skipping {stage} (already completed)")
                else:
                    log.info(f"[PIPELINE] Stage 4: Codeforces - application_id={application_id}")
                    self.state["current_stage"] = stage
                    self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                    await self.save_credential_state(application_id, self.state)
                    
                    codeforces_input = {
                        "handle": codeforces_url,
                        "application_id": application_id
                    }
                    
                    run = await self.log_agent_run(application_id, stage, codeforces_input, status=AgentRunStatus.running)
                    self.state["stage_runs"][stage]["started_at"] = datetime.now(timezone.utc).isoformat()
                    
                    start_time = datetime.now()
                    try:
                        codeforces_result = await self.call_agent("CODEFORCES", "/scrape", codeforces_input)
                        duration = (datetime.now() - start_time).total_seconds() * 1000
                        
                        run.output_payload = codeforces_result
                        run.status = AgentRunStatus.completed
                        run.execution_time_ms = duration
                        
                        self.state["evidence"]["codeforces"] = codeforces_result
                        self.state["stage_runs"][stage].update({
                            "status": "ok",
                            "ended_at": datetime.now(timezone.utc).isoformat(),
                            "duration_ms": duration,
                            "output_ref": "evidence.codeforces"
                        })
                        self.state["stages_completed"].append(stage)
                        
                    except Exception as e:
                        run.status = AgentRunStatus.failed
                        run.error_message = str(e)
                        log.error(f"[PIPELINE] Codeforces failed: {str(e)}")
                        
                        self.state["stage_runs"][stage].update({
                            "status": "failed",
                            "error": str(e),
                            "ended_at": datetime.now(timezone.utc).isoformat()
                        })
                    
                    await self.db.commit()
                    self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                    await self.save_credential_state(application_id, self.state)
            
            # STAGE 5: LINKEDIN
            target_linkedin = linkedin_url or linkedin_pdf_path
            if target_linkedin:
                stage = "LINKEDIN"
                self._ensure_stage(stage)
                
                if self._stage_ok(stage):
                    log.info(f"[PIPELINE] Skipping {stage} (already completed)")
                else:
                    log.info(f"[PIPELINE] Stage 5: LinkedIn - application_id={application_id}, target={target_linkedin}")
                    self.state["current_stage"] = stage
                    self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                    await self.save_credential_state(application_id, self.state)
                    
                    linkedin_input = {
                        "linkedin_url": target_linkedin,
                        "linkedin_text": linkedin_text or "",
                        "linkedin_path": linkedin_pdf_path or "",
                        "application_id": application_id
                    }
                    
                    run = await self.log_agent_run(application_id, stage, linkedin_input, status=AgentRunStatus.running)
                    self.state["stage_runs"][stage]["started_at"] = datetime.now(timezone.utc).isoformat()
                    
                    start_time = datetime.now()
                    try:
                        # If target_linkedin is a web URL, scrape via Bright Data client directly or through agent
                        if "linkedin.com" in target_linkedin or target_linkedin.startswith("http"):
                            try:
                                from app.services.brightdata_service import brightdata_client
                                linkedin_result = await brightdata_client.scrape_profile(target_linkedin)
                            except Exception as bd_err:
                                log.warning(f"[PIPELINE] Direct Bright Data call failed: {bd_err}, falling back to agent")
                                linkedin_result = await self.call_agent("LINKEDIN", "/parse", linkedin_input)
                        else:
                            linkedin_result = await self.call_agent("LINKEDIN", "/parse", linkedin_input)

                        duration = (datetime.now() - start_time).total_seconds() * 1000
                        
                        run.output_payload = linkedin_result
                        run.status = AgentRunStatus.completed
                        run.execution_time_ms = duration
                        
                        self.state["evidence"]["linkedin"] = linkedin_result
                        self.state["stage_runs"][stage].update({
                            "status": "ok",
                            "ended_at": datetime.now(timezone.utc).isoformat(),
                            "duration_ms": duration,
                            "output_ref": "evidence.linkedin"
                        })
                        self.state["stages_completed"].append(stage)
                        
                    except Exception as e:
                        run.status = AgentRunStatus.failed
                        run.error_message = str(e)
                        log.error(f"[PIPELINE] LinkedIn failed: {str(e)}")
                        
                        self.state["stage_runs"][stage].update({
                            "status": "failed",
                            "error": str(e),
                            "ended_at": datetime.now(timezone.utc).isoformat()
                        })
                    
                    await self.db.commit()
                    self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                    await self.save_credential_state(application_id, self.state)
            
            # STAGE 6: SKILL VERIFICATION
            stage = "SKILLS"
            self._ensure_stage(stage)
            
            if self._stage_ok(stage):
                log.info(f"[PIPELINE] Skipping {stage} (already completed)")
            else:
                log.info(f"[PIPELINE] Stage 6: Skill Verification - application_id={application_id}")
                self.state["current_stage"] = stage
                self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.save_credential_state(application_id, self.state)
                
                log.info(f"[PIPELINE-DEBUG] Evidence Keys: {list(self.state['evidence'].keys())}")
                if "ATS" in self.state["evidence"]:
                    log.info(f"[PIPELINE-DEBUG] ATS result skills: {len(self.state['evidence']['ATS'].get('skills', []))}")
                
                skills_input = {
                    "required_skills": app.job.required_skills if app.job else [],
                    "evidence": self.state["evidence"], # Pass all collected evidence
                    "application_id": application_id
                }
                
                run = await self.log_agent_run(application_id, stage, skills_input, status=AgentRunStatus.running)
                self.state["stage_runs"][stage]["started_at"] = datetime.now(timezone.utc).isoformat()
                
                start_time = datetime.now()
                try:
                    skills_result = await self.call_agent("SKILLS", "/verify", skills_input)
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    
                    run.output_payload = skills_result
                    run.status = AgentRunStatus.completed
                    run.execution_time_ms = duration
                    
                    self.state["evidence"]["skills"] = skills_result

                    # Unwrap {success, data, status_code} wrapper, then drill into "output"
                    skills_data = skills_result.get("data", skills_result)
                    output_envelope = skills_data.get("output", skills_data)
                    output = output_envelope.get("output", output_envelope) if isinstance(output_envelope, dict) else skills_data
                    
                    verified_skills = output.get("verified_skills", [])
                    self.state["derived"]["verified_skills"] = verified_skills
                    self.state["derived"]["test_required"] = output.get("test_required", False)
                    # FIX: Map skill_confidence to derived.confidence
                    self.state["derived"]["confidence"] = output.get("skill_confidence")
                    self.state["derived"]["signal_strength"] = output.get("signal_strength")
                    
                    # Update application feedback early so skills are visible immediately
                    if not app.feedback_json:
                        app.feedback_json = {}
                    
                    # Store verified_skills in feedback_json for UI visibility
                    app.feedback_json["verified_skills"] = self.state["derived"]["verified_skills"]
                    app.feedback_json["recommendation"] = "Technical signatures detected. Matching in progress..."
                    
                    await self.db.commit()
                    
                    self.state["stage_runs"][stage].update({
                        "status": "ok",
                        "ended_at": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": duration,
                        "output_ref": "evidence.skills"
                    })
                    
                    # Pause for test
                    if skills_result.get("test_required"):
                        log.info(f"[PIPELINE] Skill verification requires test for application {application_id}")
                        app.pipeline_status = PipelineStatus.completed # Finished initial scan
                        self.state["pipeline_status"] = "awaiting_test"
                        
                        await self.db.commit()
                        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                        await self.save_credential_state(application_id, self.state)
                        
                        return self.state
                    
                    self.state["stages_completed"].append(stage)
                    
                except Exception as e:
                    run.status = AgentRunStatus.failed
                    run.error_message = str(e)
                    log.error(f"[PIPELINE] Skill Verification failed: {str(e)}")
                    
                    self.state["stage_runs"][stage].update({
                        "status": "failed",
                        "error": str(e),
                        "ended_at": datetime.now(timezone.utc).isoformat()
                    })
                
                await self.db.commit()
                self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.save_credential_state(application_id, self.state)
            
            # STAGE 7: CONDITIONAL TEST
            # This stage is handled separately when user submits test
            # We skip it here as no test is required
            
            # STAGE 8: BIAS DETECTION
            stage = "BIAS"
            self._ensure_stage(stage)
            
            if self._stage_ok(stage):
                log.info(f"[PIPELINE] Skipping {stage} (already completed)")
            else:
                log.info(f"[PIPELINE] Stage 8: Bias Detection - application_id={application_id}")
                self.state["current_stage"] = stage
                self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.save_credential_state(application_id, self.state)
                
                bias_input = {
                    "credential": {
                        "identity": {
                            "candidate_id": cand.id,
                            "application_id": application_id
                        },
                        "skills": self.state["derived"].get("verified_skills", []),
                        "evidence": self.state["evidence"]
                    },
                    "metadata": {
                        "resume_text": resume_text,
                        "linkedin_text": linkedin_text
                    },
                    "mode": "realtime"
                }
                
                run = await self.log_agent_run(application_id, stage, bias_input, status=AgentRunStatus.running)
                self.state["stage_runs"][stage]["started_at"] = datetime.now(timezone.utc).isoformat()
                
                start_time = datetime.now()
                try:
                    bias_result = await self.call_agent("BIAS", "/run", bias_input)
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    
                    run.output_payload = bias_result
                    run.status = AgentRunStatus.completed
                    run.execution_time_ms = duration
                    
                    self.state["evidence"]["bias"] = bias_result
                    self.state["stage_runs"][stage].update({
                        "status": "ok",
                        "ended_at": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": duration,
                        "output_ref": "evidence.bias"
                    })
                    
                    # Check for high/critical severity
                    if bias_result.get("severity") in ["high", "critical"]:
                        log.warning(f"[PIPELINE] Bias detected (severity={bias_result.get('severity')})")
                        
                        review = ReviewCase(
                            application_id=application_id,
                            job_id=app.job_id,
                            candidate_id=app.candidate_id,
                            triggered_by=stage,
                            severity=bias_result.get("severity"),
                            reason="Bias detection flagged systemic issues",
                            evidence=bias_result
                        )
                        self.db.add(review)
                    
                    self.state["stages_completed"].append(stage)
                    
                except Exception as e:
                    run.status = AgentRunStatus.failed
                    run.error_message = str(e)
                    log.error(f"[PIPELINE] Bias Detection failed: {str(e)}")
                    
                    self.state["stage_runs"][stage].update({
                        "status": "failed",
                        "error": str(e),
                        "ended_at": datetime.now(timezone.utc).isoformat()
                    })
                
                await self.db.commit()
                self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.save_credential_state(application_id, self.state)

            # STAGE 9: MATCHING
            stage = "MATCHING"
            self._ensure_stage(stage)
            
            if self._stage_ok(stage):
                log.info(f"[PIPELINE] Skipping {stage} (already completed)")
            else:
                log.info(f"[PIPELINE] Stage 9: Matching - application_id={application_id}")
                self.state["current_stage"] = stage
                self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.save_credential_state(application_id, self.state)
                
                jd_data = app.job.required_skills if (app.job and app.job.required_skills) else {}
                
                # Normalize jd_data to dictionary if provided as a skill list
                if isinstance(jd_data, list):
                    jd_data = {
                        "skills": jd_data,
                        "strict_requirements": [],
                        "matching_philosophy": {"learning_velocity_weight": 0.2},
                        "problem_solving": {"required": False}
                    }

                # Ensure defaults for critical fields
                if "strict_requirements" not in jd_data:
                    jd_data["strict_requirements"] = [] # type: ignore
                if "languages" not in jd_data:
                    jd_data["languages"] = [] # type: ignore
                if "matching_philosophy" not in jd_data:
                    jd_data["matching_philosophy"] = {"learning_velocity_weight": 0.2} # type: ignore
                if "problem_solving" not in jd_data:
                    jd_data["problem_solving"] = {"required": False} # type: ignore

                # Pull actual data from evidence if available
                # Evidence is stored as {success, data, status_code} wrappers — unwrap .data
                github_results_raw = self.state["evidence"].get("github", {}) or {}
                github_results = github_results_raw.get("data", github_results_raw)
                github_score = 0.5
                if isinstance(github_results, dict):
                    sig = github_results.get("credibility_signal", {})
                    github_score = sig.get("score", 50) / 100.0 if "score" in sig else 0.5

                skills_results = self.state["evidence"].get("skills", {})
                verified_skills = self.state["derived"].get("verified_skills", [])

                # Adapt payload schema for matching agent v2
                # Gather raw experience from ATS as primary source of narrative evidence
                ats_evidence_raw = self.state["evidence"].get("ats", {}) or {}
                ats_data = ats_evidence_raw.get("data", ats_evidence_raw)
                # ATS agent nests experience/identity under "evidence" key
                ats_evidence = ats_data.get("evidence", ats_data)
                experience = ats_evidence.get("experience", [])
                identity = ats_evidence.get("identity", {})
                
                # Update identity with current application info
                if not identity: identity = {}
                identity["candidate_id"] = cand.id # type: ignore
                identity["application_id"] = application_id # type: ignore
                
                # Populate public links based on completed stages
                public_links = identity.get("public_links", [])
                if self._stage_ok("GITHUB"): public_links.append("github_present")
                if self._stage_ok("LEETCODE"): public_links.append("leetcode_present")
                if self._stage_ok("LINKEDIN"): public_links.append("linkedin_present")
                identity["public_links"] = list(set(public_links)) # type: ignore

                # 2. Flatten verified_skills from Stage 6 (Dictionary of categories)
                flat_skills = []
                if isinstance(verified_skills, dict):
                    for tier, sks in verified_skills.items():
                        for s in sks:
                            flat_skills.append({"skill": s, "tier": tier})
                elif isinstance(verified_skills, list):
                    flat_skills = [{"skill": s} for s in verified_skills]
                
                # Use flattened list for MatchNormalizer compatibility
                skills_to_pass = flat_skills

                # 3. Handle failed job extraction (error object in required_skills)
                if isinstance(jd_data, dict) and "error" in jd_data:
                    log.warning(f"[PIPELINE] Job {app.job_id} has extraction error, using empty requirements fallback")
                    jd_data = {
                        "strict_requirements": [],
                        "languages": [],
                        "matching_philosophy": {"learning_velocity_weight": 0.2}
                    }

                matching_input = {
                    "credential": {
                        "identity": identity,
                        "skills": skills_to_pass,
                        "verified_skills": verified_skills, # Keep original as well
                        "experience": experience,
                        "github_score": github_score,
                        "cp_activity": any("competitive" in str(s).lower() for s in (flat_skills if flat_skills else verified_skills)),
                        "learning_velocity": 0.5
                    },
                    "job_description": {
                        "title": app.job.title if app.job else "Technical Role",
                        "description": app.job.description if app.job else "",
                        **jd_data
                    }
                }
                
                run = await self.log_agent_run(application_id, stage, matching_input, status=AgentRunStatus.running)
                self.state["stage_runs"][stage]["started_at"] = datetime.now(timezone.utc).isoformat()
                
                start_time = datetime.now()
                try:
                    matching_result = await self.call_agent("MATCHING", "/run", matching_input)
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    
                    run.output_payload = matching_result
                    run.status = AgentRunStatus.completed
                    run.execution_time_ms = duration
                    
                    self.state["evidence"]["matching"] = matching_result

                    # Unwrap {success, data, status_code} wrapper from agent_client
                    matching_data = matching_result.get("data", matching_result)
                    output = matching_data.get("output", matching_data)
                    analysis = output.get("analysis", {}) or {}

                    self.state["derived"]["match_score"] = output.get("match_score", 0)
                    self.state["derived"]["matched_skills"] = analysis.get("matched_skills", [])
                    self.state["derived"]["missing_skills"] = analysis.get("missing_skills", [])

                    self.state["stage_runs"][stage].update({
                        "status": "ok",
                        "ended_at": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": duration,
                        "output_ref": "evidence.matching"
                    })
                    self.state["stages_completed"].append(stage)

                    # Update application with match score
                    app.match_score = output.get("match_score", 0)

                    # Flatten feedback for frontend
                    app.feedback_json = {
                        "breakdown": output.get("breakdown"),
                        "matched_skills": analysis.get("matched_skills", []),
                        "missing_skills": analysis.get("missing_skills", []),
                        "verified_skills": self.state["derived"].get("verified_skills", []),
                        "recommendation": output.get("decision_reason") or "Verification complete: Technical alignment confirmed.",
                        "message": output.get("decision_reason") or "Verification complete: Technical alignment confirmed."
                    }
                    
                except Exception as e:
                    run.status = AgentRunStatus.failed
                    run.error_message = str(e)
                    log.error(f"[PIPELINE] Matching failed: {str(e)}")
                    
                    self.state["stage_runs"][stage].update({
                        "status": "failed",
                        "error": str(e),
                        "ended_at": datetime.now(timezone.utc).isoformat()
                    })
                
                await self.db.commit()
                self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.save_credential_state(application_id, self.state)

            # STAGE 10: PASSPORT ISSUANCE
            stage = "PASSPORT"
            self._ensure_stage(stage)
            
            if self._stage_ok(stage):
                log.info(f"[PIPELINE] Skipping {stage} (already completed)")
            else:
                log.info(f"[PIPELINE] Stage 10: Passport Issuance - application_id={application_id}")
                self.state["current_stage"] = stage
                self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.save_credential_state(application_id, self.state)
                
                passport_input = {
                    "candidate_id": cand.id,
                    "application_id": application_id,
                    "evidence": self.state["evidence"],
                    "derived": self.state["derived"]
                }
                
                run = await self.log_agent_run(application_id, stage, passport_input, status=AgentRunStatus.running)
                self.state["stage_runs"][stage]["started_at"] = datetime.now(timezone.utc).isoformat()
                
                start_time = datetime.now()
                try:
                    # sign credential
                    credential_data = {
                        "issuer": "FairHiringPlatform",
                        "issued_at": datetime.now(timezone.utc).isoformat(),
                        "candidate": {
                            "id": cand.id,
                            "email": cand.email,
                            "name": cand.name
                        },
                        "job_id": app.job_id,
                        "verified_skills": self.state["derived"]["verified_skills"],
                        "match_score": self.state["derived"]["match_score"],
                        # simplified hash for demo
                        "evidence_hash": str(hash(json.dumps(self.state["evidence"], sort_keys=True)))
                    }
                    
                    # Sign
                    h, signature = sign_credential(credential_data)
                    credential_data["signature"] = signature
                    credential_data["hash"] = h
                    
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    
                    run.output_payload = credential_data
                    run.status = AgentRunStatus.completed
                    run.execution_time_ms = duration
                    
                    self.state["evidence"]["passport"] = credential_data
                    self.state["stage_runs"][stage].update({
                        "status": "ok",
                        "ended_at": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": duration,
                        "output_ref": "evidence.passport"
                    })
                    self.state["stages_completed"].append(stage)
                    
                    # Store Credential Record
                    # Using existing credential (already saved in save_credential_state)
                    # Just update the state reference
                    existing_q = await self.db.execute(
                        select(Credential)
                        .where(Credential.application_id == application_id)
                        .order_by(Credential.issued_at.desc())
                    )
                    existing_cred = existing_q.scalars().first()
                    if existing_cred:
                        self.state["credential_id"] = existing_cred.id
                    
                except Exception as e:
                    run.status = AgentRunStatus.failed
                    run.error_message = str(e)
                    log.error(f"[PIPELINE] Passport Issuance failed: {str(e)}")
                    
                    self.state["stage_runs"][stage].update({
                        "status": "failed",
                        "error": str(e),
                        "ended_at": datetime.now(timezone.utc).isoformat()
                    })
                
                await self.db.commit()
                self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.save_credential_state(application_id, self.state)
                
            # Final Status Update
            # Accumulate newly verified skills into candidate's master profile
            verified_skills = self.state["derived"].get("verified_skills", [])
            if verified_skills:
                existing_skills = list(cand.skills or [])
                updated = False
                for s in verified_skills:
                    s_name = s.get("name") if isinstance(s, dict) else str(s)
                    if s_name and s_name not in existing_skills:
                        existing_skills.append(s_name)
                        updated = True
                if updated:
                    cand.skills = existing_skills
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(cand, "skills")
                    log.info(f"[PIPELINE] Updated candidate {cand.id} cumulative skills: {existing_skills}")

            app.status = ApplicationStatus.matched
            app.pipeline_status = PipelineStatus.completed
            self.state["pipeline_status"] = "completed"
            self.state["application_status"] = "matched"
            self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
            await self.db.commit()
            await self.save_credential_state(application_id, self.state)
            
            return self.state
            
        except Exception as e:
            log.error(f"[PIPELINE] Pipeline failed: {str(e)}")
            
            app.status = ApplicationStatus.pending
            app.pipeline_status = PipelineStatus.failed
            self.state["pipeline_status"] = "failed"
            self.state["error"] = str(e)
            
            await self.db.commit()
            self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
            await self.save_credential_state(application_id, self.state)
            
            raise
