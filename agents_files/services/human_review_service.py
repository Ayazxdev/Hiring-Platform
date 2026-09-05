import json
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

# Root dir is parent of 'services'
ROOT_DIR = Path(__file__).parent.parent
QUEUE_FILE = str(ROOT_DIR / "human_review_queue.json")

class HumanReviewService:
    """
    Centralized service for managing Human Review Events.
    Implements the 'One Queue, Many Entry Points' architecture.
    """
    
    def __init__(self, queue_file: str = QUEUE_FILE):
        self.queue_file = queue_file
        self._ensure_queue_exists()

    def _ensure_queue_exists(self):
        # Create file with empty list if not exists
        if not os.path.exists(self.queue_file):
            with open(self.queue_file, 'w') as f:
                json.dump([], f)

    def load_queue(self) -> List[Dict]:
        try:
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load queue: {e}")
            return []

    def _save_queue(self, queue: List[Dict]):
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2)

    def submit_review_request(self, 
                              candidate_id: str,
                              triggered_by: str,
                              severity: str,
                              reason: str,
                              system_action_taken: str,
                              evidence: Dict = {},
                              job_id: str = "unknown_job") -> str:
        """
        Submit a new event to the Human Review Queue.
        Returns the review_id.
        """
        
        review_id = f"review_{uuid.uuid4().hex[:6]}"
        
        event = {
            "review_id": review_id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "triggered_by": triggered_by,
            "severity": severity,
            "reason": reason,
            "evidence": evidence,
            "system_action_taken": system_action_taken,
            "status": "PENDING",
            "human_decision": None,
            "reviewer_notes": None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Load, Append, Save
        queue = self.load_queue()
        queue.append(event)
        self._save_queue(queue)
        
        import sys
        sys.stderr.write(f"🚨 HUMAN REVIEW REQUESTED: [{severity.upper()}] {reason}\n")
        sys.stderr.write(f"   action_taken: {system_action_taken}\n")
        sys.stderr.write(f"   review_id: {review_id}\n")
        
        return review_id

    def get_pending_reviews(self) -> List[Dict]:
        queue = self.load_queue()
        return [q for q in queue if q["status"] == "PENDING"]
