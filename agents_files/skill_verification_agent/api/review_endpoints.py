from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.review_service import ReviewService
from models.review_models import HumanReviewQueue, CandidateBlacklist
from pydantic import BaseModel
import logging

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/review", tags=["review"])

# Dependency injection placeholder - User needs to provide actual get_db
def get_db():
    raise NotImplementedError("Database dependency not injected")

class ReviewDecision(BaseModel):
    reviewer_id: str
    notes: str = None
    blacklist_duration_days: int = None  # None = permanent


@router.get("/pending")
def get_pending_reviews(db: Session = Depends(get_db)):
    """
    Get all pending reviews (admin dashboard)
    """
    reviews = db.query(HumanReviewQueue).filter(
        HumanReviewQueue.status == "pending"
    ).order_by(
        HumanReviewQueue.severity.desc(),
        HumanReviewQueue.created_at.desc()
    ).all()
    
    return {"reviews": reviews, "count": len(reviews)}


@router.post("/{review_id}/approve")
def approve_review(
    review_id: str,
    decision: ReviewDecision,
    db: Session = Depends(get_db)
):
    """
    Approve flagged candidate (false positive)
    """
    service = ReviewService(db)
    service.approve_review(review_id, decision.reviewer_id, decision.notes)
    
    return {"status": "approved"}


@router.post("/{review_id}/reject")
def reject_and_blacklist(
    review_id: str,
    decision: ReviewDecision,
    db: Session = Depends(get_db)
):
    """
    Reject candidate and add to blacklist
    """
    service = ReviewService(db)
    success = service.reject_and_blacklist(
        review_id,
        decision.reviewer_id,
        decision.notes,
        decision.blacklist_duration_days
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return {"status": "blacklisted"}


@router.get("/blacklist/check/{candidate_email}")
def check_blacklist(candidate_email: str, db: Session = Depends(get_db)):
    """
    Check if candidate is blacklisted (use before processing)
    """
    import hashlib
    candidate_hash = hashlib.sha256(candidate_email.encode()).hexdigest()
    
    service = ReviewService(db)
    is_blacklisted = service.is_blacklisted(candidate_hash)
    
    return {
        "blacklisted": is_blacklisted,
        "candidate_hash": candidate_hash
    }
