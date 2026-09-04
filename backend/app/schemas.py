"""
Pydantic Schemas for Fair Hiring System API
Matches frontend expectations exactly
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


# ENUMS

class ApplicationStatusEnum(str, Enum):
    """Application status enum for API"""
    pending = "pending"
    processing = "processing"
    matched = "matched"
    rejected = "rejected"


class PipelineStatusEnum(str, Enum):
    """Pipeline status enum for API"""
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


# CANDIDATE SCHEMAS

class CandidateRegister(BaseModel):
    """Candidate registration request"""
    email: EmailStr
    name: str
    password: str
    gender: Optional[str] = None
    college: Optional[str] = None
    engineer_level: Optional[str] = None


class CandidateLogin(BaseModel):
    """Candidate login request"""
    email: EmailStr
    password: str


class CandidateResponse(BaseModel):
    """Candidate response"""
    id: int
    anon_id: str
    email: str
    name: str
    gender: Optional[str] = None
    college: Optional[str] = None
    engineer_level: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateStats(BaseModel):
    """Candidate statistics"""
    total_applications: int
    matched_applications: int
    pending_applications: int
    average_match_score: float


class TokenResponse(BaseModel):
    """Token response"""
    token: str
    candidate: CandidateResponse


# JOB SCHEMAS

class JobCreate(BaseModel):
    """Job creation request"""
    company_id: str
    title: str
    description: str
    required_skills: Any
    fairness_score: Optional[float] = None
    fairness_status: Optional[str] = None
    fairness_findings: Optional[Dict[str, Any]] = None
    published: bool = False
    max_participants: Optional[int] = None
    application_deadline: Optional[datetime] = None


class JobResponse(BaseModel):
    """Job response"""
    id: int
    company_id: str
    title: str
    description: str
    required_skills: Any
    fairness_score: Optional[float] = None
    fairness_status: Optional[str] = None
    fairness_findings: Optional[Any] = None
    published: bool
    max_participants: Optional[int] = None
    application_deadline: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True



class JobListItem(BaseModel):
    """Single job item in list response"""
    id: int
    title: str
    company_name: str
    description: str
    required_skills: Any
    application_deadline: Optional[datetime] = None

class JobListResponse(BaseModel):
    """Job list response wrapper"""
    success: bool
    jobs: List[Dict[str, Any]]
    total: int


# APPLICATION SCHEMAS

class ApplicationCreate(BaseModel):
    """Application creation request"""
    anon_id: str
    job_id: int
    resume_text: str
    github_url: Optional[str] = None
    leetcode_url: Optional[str] = None
    codeforces_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedin_text: Optional[str] = None
    run_pipeline: bool = True


class ApplicationResponse(BaseModel):
    """Application response"""
    success: bool
    application_id: int
    candidate_id: int
    job_id: int
    job_title: str
    company_name: str
    status: str
    pipeline_status: str
    created_at: str

    class Config:
        from_attributes = True


class ApplicationDetailResponse(BaseModel):
    """Application detail response with job and credential info"""
    success: bool
    application_id: int
    candidate_id: int
    job_id: int
    job_title: str
    company_name: str
    status: str
    pipeline_status: str
    match_score: Optional[float] = None
    feedback_json: Optional[Dict[str, Any]] = None
    pipeline_error: Optional[str] = None
    created_at: str
    updated_at: str


class ApplicationListItem(BaseModel):
    """Application list item for candidate"""
    application_id: int
    job_id: int
    job_title: str
    company_name: str
    status: str
    match_score: Optional[float] = None
    feedback: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class ApplicationListResponse(BaseModel):
    """Application list response for candidate"""
    success: bool
    candidate_id: int
    anon_id: str
    applications: List[ApplicationListItem]
    total: int


class ApplicationStatusUpdate(BaseModel):
    """Application status update request"""
    status: ApplicationStatusEnum
    feedback: Optional[str] = None


# CREDENTIAL SCHEMAS

class CredentialResponse(BaseModel):
    """Credential response for frontend"""
    success: bool
    credential: Dict[str, Any]
    hash: str
    signature: str
    issued_at: str


# PIPELINE SCHEMAS

class PipelineRunRequest(BaseModel):
    """Pipeline run request"""
    application_id: int


class AgentResult(BaseModel):
    """Agent execution result"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PipelineRunResponse(BaseModel):
    """Pipeline run response"""
    success: bool
    application_id: int
    credential: Optional[Dict[str, Any]] = None
    match_score: Optional[float] = None
    pipeline_results: Optional[Dict[str, Any]] = None


class PipelineResultResponse(BaseModel):
    """Pipeline result response"""
    application_id: int
    credential: Optional[Dict[str, Any]] = None
    match_score: Optional[float] = None
    feedback: Optional[Dict[str, Any]] = None


class PipelineStatusResponse(BaseModel):
    """Pipeline status response"""
    success: bool
    application_id: int
    pipeline_status: str
    application_status: str
    match_score: Optional[float] = None
    pipeline_error: Optional[str] = None
    agent_runs: List[Dict[str, Any]] = []


# REVIEW SCHEMAS

class ReviewCaseCreate(BaseModel):
    """Review case creation request"""
    application_id: int
    job_id: int
    candidate_id: int
    triggered_by: str
    severity: str
    reason: str
    evidence: Dict[str, Any]


class ReviewCaseResponse(BaseModel):
    """Review case response"""
    id: int
    application_id: int
    job_id: int
    candidate_id: int
    triggered_by: str
    severity: str
    reason: str
    evidence: Dict[str, Any]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ERROR SCHEMAS

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None


# ALIASES FOR BACKWARD COMPATIBILITY
# Routers use "Request" suffix, so we create aliases

CandidateRegisterRequest = CandidateRegister
CandidateLoginRequest = CandidateLogin
CandidateStatsResponse = CandidateStats
JobCreateRequest = JobCreate
ApplicationCreateRequest = ApplicationCreate
ApplicationStatusUpdateRequest = ApplicationStatusUpdate

# Add ReviewSeverity enum for pipeline service
class ReviewSeverity(str, Enum):
    """Review severity enum"""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"