"""
LangGraph State Schema

Defines the shared state that flows through all agents.
"""
from typing import TypedDict, Dict, List, Optional, Literal
from datetime import datetime


class HiringState(TypedDict):
    """
    Complete state schema for the Fair Hiring workflow
    
    This state flows through all agents in the pipeline.
    Each agent reads what it needs and writes its output.
    """
    
    # INPUT DATA
    # Raw application data
    raw_application: Dict
    job_description: str
    job_requirements: Dict
    
    # AGENT 1: COMPANY FAIRNESS
    company_id: Optional[str]
    company_fairness_score: int
    company_status: Literal["Approved", "Rejected", "Pending"]
    company_flags: List[Dict]
    company_suggestions: List[str]
    
    # AGENT 2: SKILL VERIFICATION
    candidate_id: str  # Anonymous ID
    anonymized_data: Dict  # PII stripped
    portfolio_result: Dict
    manipulation_detected: bool
    verified_skills: List[str]
    skill_confidence: int
    signal_strength: Literal["strong", "weak"]
    skill_credential: Dict
    
    # AGENT 3: BIAS DETECTION
    # Accumulated for batch processing
    candidates_buffer: List[Dict]
    bias_report: Optional[Dict]
    bias_detected: bool
    bias_severity: Optional[str]
    
    # AGENT 4: MATCHING
    match_scorecard: Dict
    overall_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    recommendation: str
    
    # AGENT 5: PASSPORT
    credential_id: str
    credential_issued: bool
    nfc_payload: Optional[Dict]
    
    # WORKFLOW CONTROL
    current_stage: str
    workflow_status: Literal["in_progress", "completed", "rejected", "error"]
    error_message: Optional[str]
    timestamps: Dict[str, str]
    
    # REDIS EVENTS
    events_published: List[Dict]


def create_initial_state(
    application: Dict,
    job_description: str,
    job_requirements: Dict
) -> HiringState:
    """
    Create initial state for a new hiring workflow
    
    Args:
        application: Raw candidate application
        job_description: Job description text
        job_requirements: Structured job requirements
        
    Returns:
        Initialized HiringState
    """
    return HiringState(
        # Input
        raw_application=application,
        job_description=job_description,
        job_requirements=job_requirements,
        
        # Company Fairness (to be filled)
        company_id=None,
        company_fairness_score=0,
        company_status="Pending",
        company_flags=[],
        company_suggestions=[],
        
        # Skill Verification (to be filled)
        candidate_id="",
        anonymized_data={},
        portfolio_result={},
        manipulation_detected=False,
        verified_skills=[],
        skill_confidence=0,
        signal_strength="weak",
        skill_credential={},
        
        # Bias Detection
        candidates_buffer=[],
        bias_report=None,
        bias_detected=False,
        bias_severity=None,
        
        # Matching (to be filled)
        match_scorecard={},
        overall_score=0,
        matched_skills=[],
        missing_skills=[],
        recommendation="",
        
        # Passport (to be filled)
        credential_id="",
        credential_issued=False,
        nfc_payload=None,
        
        # Workflow control
        current_stage="start",
        workflow_status="in_progress",
        error_message=None,
        timestamps={
            "started_at": datetime.now().isoformat()
        },
        events_published=[]
    )
