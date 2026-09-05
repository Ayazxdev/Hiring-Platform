from sqlalchemy import Column, String, DateTime, JSON, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class HumanReviewQueue(Base):
    """
    Queue for flagged candidates requiring human review
    """
    __tablename__ = "human_review_queue"
    
    review_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(String, nullable=False, unique=True, index=True)
    candidate_hash = Column(String, nullable=False, index=True)  # SHA256(email)
    
    detection_type = Column(
        Enum(
            "white_text",
            "prompt_injection",
            "timeline_fraud",
            "skill_mismatch",
            "experience_inflation",
            name="detection_type"
        ),
        nullable=False
    )
    
    severity = Column(
        Enum("low", "medium", "high", "critical", name="severity_level"),
        nullable=False
    )
    
    evidence = Column(JSON, nullable=False)
    agent_source = Column(String, nullable=False)  # Which agent flagged it
    
    status = Column(
        Enum("pending", "approved", "rejected", "escalated", name="review_status"),
        default="pending",
        nullable=False
    )
    
    reviewer_id = Column(String, nullable=True)
    reviewer_notes = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)


class CandidateBlacklist(Base):
    """
    Permanent blacklist for candidates caught cheating
    """
    __tablename__ = "candidate_blacklist"
    
    blacklist_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_hash = Column(String, nullable=False, unique=True, index=True)
    
    reason = Column(String, nullable=False)
    detection_type = Column(String, nullable=False)
    evidence_snapshot = Column(JSON, nullable=False)
    
    review_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("human_review_queue.review_id"),
        nullable=True
    )
    
    blacklisted_by = Column(String, default="system")
    blacklist_duration_days = Column(Integer, nullable=True)  # None = permanent
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
