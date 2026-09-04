"""
Database Models for Fair Hiring System
Fixed version with proper types, enums, and relationships
"""
from datetime import datetime, timezone
from typing import Optional, Any
from enum import Enum

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

from sqlalchemy import ( # type: ignore
    Column, Integer, String, Text, Boolean, Float, DateTime, 
    ForeignKey, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import JSONB  # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore

Base: Any = declarative_base()


# ENUMS

class ApplicationStatus(str, Enum):
    """Application status enum"""
    pending = "pending"
    processing = "processing"
    matched = "matched"
    selected = "selected"
    rejected = "rejected"


class PipelineStatus(str, Enum):
    """Pipeline execution status enum"""
    not_started = "not_started"
    queued = "queued"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class AgentRunStatus(str, Enum):
    """Agent run status enum"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ReviewSeverity(str, Enum):
    """Review case severity enum"""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ReviewStatus(str, Enum):
    """Review case status enum"""
    pending = "pending"
    in_review = "in_review"
    resolved = "resolved"
    dismissed = "dismissed"


# MODELS

class Candidate(Base):
    """Candidate model"""
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    anon_id = Column(String(50), unique=True, index=True, nullable=False)
    # Auth0 subject ID (e.g. "auth0|abc123") — set for Auth0-registered users
    auth0_id = Column(String(255), unique=True, index=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    # Nullable — Auth0 users have no local password
    password_hash = Column(String(255), nullable=True)
    gender = Column(String(50))
    college = Column(String(255))
    engineer_level = Column(String(50))
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    credentials = relationship("Credential", back_populates="candidate", cascade="all, delete-orphan")


class Company(Base):
    """Company model"""
    __tablename__ = "companies"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for existing companies without passwords
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")


class Blacklist(Base):
    """Candidate blacklist model"""
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, unique=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)


class Job(Base):
    """Job model"""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSONB, nullable=False)  # Fixed: JSONB
    fairness_score = Column(Float)
    fairness_status = Column(String(50))
    fairness_findings = Column(JSONB)  # Fixed: JSONB
    published = Column(Boolean, default=False)
    max_participants = Column(Integer)
    application_deadline = Column(DateTime)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class Application(Base):
    """Application model"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    resume_text = Column(Text, nullable=False)
    github_url = Column(String(500))
    leetcode_url = Column(String(500))
    codeforces_url = Column(String(500))
    linkedin_url = Column(String(500))
    linkedin_text = Column(Text)
    
    # Fixed: Use Enum
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.pending, nullable=False)
    match_score = Column(Float)
    feedback_json = Column(JSONB)  # Fixed: JSONB
    test_required = Column(Boolean, default=False)
    
    # Fixed: Use Enum
    pipeline_status = Column(SQLEnum(PipelineStatus), default=PipelineStatus.not_started, nullable=False)
    pipeline_error = Column(Text)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    credential = relationship("Credential", back_populates="application", uselist=False)
    agent_runs = relationship("AgentRun", back_populates="application", cascade="all, delete-orphan")
    review_cases = relationship("ReviewCase", back_populates="application", cascade="all, delete-orphan")


class Credential(Base):
    """Credential (Skill Passport) model"""
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    credential_json = Column(JSONB, nullable=False)
    hash_sha256 = Column(String(64), nullable=False)
    signature_b64 = Column(Text, nullable=False)
    issued_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    candidate = relationship("Candidate", back_populates="credentials")
    application = relationship("Application", back_populates="credential")


class AgentRun(Base):
    """Agent execution run model"""
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    input_payload = Column(JSONB)  # Fixed: JSONB
    output_payload = Column(JSONB)  # Fixed: JSONB
    
    # Fixed: Use Enum
    status = Column(SQLEnum(AgentRunStatus), default=AgentRunStatus.pending, nullable=False)
    error_message = Column(Text)
    execution_time_ms = Column(Float)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    application = relationship("Application", back_populates="agent_runs")


class ReviewCase(Base):
    """Review case for human intervention"""
    __tablename__ = "review_cases"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    triggered_by = Column(String(50), nullable=False)
    
    # Fixed: Use Enum
    severity = Column(SQLEnum(ReviewSeverity), nullable=False)
    reason = Column(String(500), nullable=False)
    evidence = Column(JSONB)  # Fixed: JSONB
    
    # Fixed: Use Enum
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.pending, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    application = relationship("Application", back_populates="review_cases")


class AuditLog(Base):
    """Audit log model for tracking system events"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    meta = Column(JSONB)
    created_at = Column(DateTime, default=utc_now)
