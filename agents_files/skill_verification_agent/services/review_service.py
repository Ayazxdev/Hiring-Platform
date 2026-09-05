from models.review_models import HumanReviewQueue, CandidateBlacklist
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib

class ReviewService:
    """
    Manages human review queue and blacklist
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def queue_for_review(
        self,
        evaluation_id: str,
        candidate_email: str,
        detection_type: str,
        severity: str,
        evidence: dict,
        agent_source: str
    ) -> str:
        """
        Add candidate to human review queue
        """
        
        # Hash email for privacy
        candidate_hash = hashlib.sha256(candidate_email.encode()).hexdigest()
        
        # Check if already blacklisted
        if self.is_blacklisted(candidate_hash):
            return "already_blacklisted"
        
        # Create review entry
        review = HumanReviewQueue(
            evaluation_id=evaluation_id,
            candidate_hash=candidate_hash,
            detection_type=detection_type,
            severity=severity,
            evidence=evidence,
            agent_source=agent_source,
            status="pending"
        )
        
        self.db.add(review)
        self.db.commit()
        
        return str(review.review_id)
    
    def is_blacklisted(self, candidate_hash: str) -> bool:
        """
        Check if candidate is blacklisted
        """
        blacklist_entry = self.db.query(CandidateBlacklist).filter(
            CandidateBlacklist.candidate_hash == candidate_hash
        ).first()
        
        if not blacklist_entry:
            return False
        
        # Check if temporary blacklist expired
        if blacklist_entry.expires_at:
            if datetime.utcnow() > blacklist_entry.expires_at:
                # Expired, remove from blacklist
                self.db.delete(blacklist_entry)
                self.db.commit()
                return False
        
        return True
    
    def approve_review(self, review_id: str, reviewer_id: str, notes: str = None):
        """
        Approve flagged candidate (false positive)
        """
        review = self.db.query(HumanReviewQueue).filter(
            HumanReviewQueue.review_id == review_id
        ).first()
        
        if review:
            review.status = "approved"
            review.reviewer_id = reviewer_id
            review.reviewer_notes = notes
            review.reviewed_at = datetime.utcnow()
            self.db.commit()
    
    def reject_and_blacklist(
        self,
        review_id: str,
        reviewer_id: str,
        notes: str = None,
        duration_days: int = None
    ):
        """
        Reject candidate and add to blacklist
        duration_days: None = permanent, int = temporary
        """
        review = self.db.query(HumanReviewQueue).filter(
            HumanReviewQueue.review_id == review_id
        ).first()
        
        if not review:
            return False
        
        # Update review status
        review.status = "rejected"
        review.reviewer_id = reviewer_id
        review.reviewer_notes = notes
        review.reviewed_at = datetime.utcnow()
        
        # Add to blacklist
        expires_at = None
        if duration_days:
            expires_at = datetime.utcnow() + timedelta(days=duration_days)
        
        blacklist_entry = CandidateBlacklist(
            candidate_hash=review.candidate_hash,
            reason=review.detection_type,
            detection_type=review.detection_type,
            evidence_snapshot=review.evidence,
            review_id=review.review_id,
            blacklisted_by=reviewer_id,
            blacklist_duration_days=duration_days,
            expires_at=expires_at
        )
        
        self.db.add(blacklist_entry)
        self.db.commit()
        
        return True
