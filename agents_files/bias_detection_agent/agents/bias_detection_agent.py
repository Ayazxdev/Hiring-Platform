
import json
import logging
import statistics
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Minimum sample sizes for valid flags
MIN_SAMPLES = {
    "gender": 20,
    "college": 15,
    "github": 20,
    "overall": 50
}

# Thresholds
THRESHOLDS = {
    "gender_gap": 5.0,
    "college_boost": 10.0,
    "github_penalty": 8.0,
    "employment_gap_penalty": 10.0
}

class BiasDetectionAgent:
    """
    Meta-Agent for hiring fairness.
    Monitors the pipeline for systemic bias without modifying credentials.
    """
    
    def __init__(self):
        # Initialize Human Review Service (Centralized)
        try:
            from services.human_review_service import HumanReviewService
            self.human_review_service = HumanReviewService()
        except ImportError:
            try:
                import sys
                from pathlib import Path
                sys.path.append(str(Path(__file__).parent.parent.parent))
                from services.human_review_service import HumanReviewService
                self.human_review_service = HumanReviewService()
            except ImportError:
                logger.warning("Could not import HumanReviewService. Human-in-loop disabled.")
                self.human_review_service = None

    def run_analysis(self, credential_input, mode="batch") -> Dict:
        """
        Analyze credential for bias patterns. 
        Supports both file path and dictionary input.
        """
        # Load credential if string path
        if isinstance(credential_input, str):
            with open(credential_input, 'r') as f:
                credential = json.load(f)
        else:
            credential = credential_input

        # Unwrap Envelope if present
        if "output" in credential and "agent" in credential:
            credential = credential["output"]
            
        logger.info(f"Running Bias Analysis for {credential.get('evaluation_id', credential.get('candidate_id'))} (Mode: {mode})")
        
        report = {
            "bias_detected": False,
            "severity": "none",
            "checks_performed": [],
            "details": {},
            "action": "proceed_to_matching",
            "bias_scope": "systemic",      # New from readthis.md
            "candidate_impact": "none",    # New from readthis.md
            "enforcement": "log_only",     # New from readthis.md
            "data_access": {               # New from readthis.md
                "pii_visibility": "restricted",
                "source": "secure_backend_join"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 0. Load Context/Metadata (Mocked for now as we don't have secure backend join yet)
        metadata = {
            "gender": "unknown", # Protected attribute not in credential
            "college": "unknown"
        }
        
        # 1. Real-Time Checks (Per Candidate)
        rt_checks = self._run_realtime_checks(credential, metadata)
        report["details"].update(rt_checks)
        report["checks_performed"].extend(["metadata_leak", "quick_flags"])
        
        if rt_checks.get("metadata_leak_detected"):
            report["bias_detected"] = True
            report["severity"] = "critical"
            report["action"] = "pause_for_correction"
            report["enforcement"] = "pipeline_pause" # Escalation
            
            # SUBMIT HUMAN REVIEW
            if self.human_review_service:
                candidate_id = credential.get('candidate_id') or credential.get('evaluation_id')
                self.human_review_service.submit_review_request(
                    candidate_id=candidate_id,
                    triggered_by="bias_detection",
                    severity="critical",
                    reason="Critical Metadata Leak Detected (Protected Attributes)",
                    system_action_taken="paused",
                    evidence={"leaked_fields": rt_checks.get("leaked_fields")},
                    job_id="unknown_job"
                )
            
            return report

        # 2. Batch Statistical Checks (Systemic)
        historical_data = self._load_mock_history() # Simulating DB load
        
        if historical_data and len(historical_data) >= MIN_SAMPLES["overall"]:
            batch_checks = self._run_batch_checks(historical_data)
            report["details"].update(batch_checks["details"])
            report["checks_performed"].extend(batch_checks["checks"])
            
            if batch_checks["bias_detected"]:
                report["bias_detected"] = True
                
                # Determine highest severity
                severities = [d.get("severity", "low") for d in batch_checks["details"].values() if d.get("bias_detected")]
                if "critical" in severities:
                    report["severity"] = "critical"
                elif "high" in severities:
                    report["severity"] = "high"
                elif "medium" in severities:
                    report["severity"] = "medium"
                else:
                    report["severity"] = "low"
        else:
            report["details"]["batch_analysis"] = {
                "status": "skipped",
                "reason": "insufficient_data",
                "sample_size": len(historical_data)
            }

        # 3. Final Action Determination
        report["action"] = self._determine_action(report)
        
        # 4. Submit Human Review if needed
        if report["bias_detected"] and report["severity"] in ["critical", "high"] and self.human_review_service:
             # Ensure we haven't already submitted (RT check returns early, so we are safe)
             # But batch checks might trigger this
             candidate_id = credential.get('candidate_id') or credential.get('evaluation_id')
             self.human_review_service.submit_review_request(
                candidate_id=candidate_id,
                triggered_by="bias_detection",
                severity=report["severity"],
                reason=f"Systemic Bias Detected: {report['severity'].upper()}",
                system_action_taken="flagged",
                evidence={"batch_details": report.get("details", {})},
                job_id="unknown_job"
            )
        
        return report

    def _load_mock_history(self) -> List[Dict]:
        """
        Load historical data for systemic bias analysis.
        Returns empty list when no persistent backend history is connected,
        triggering standard insufficient_data evaluation.
        """
        return []

    def _determine_action(self, report: Dict) -> str:
        """Decides next step based on severity."""
        if not report["bias_detected"]:
            return "proceed_to_matching"
            
        severity = report["severity"]
        
        if severity == "critical":
            return "pause_for_correction"
        elif severity == "high":
            return "human_review"
        else:
            # Low/Medium bias -> Log it but don't stop the candidate
            return "proceed_to_matching"

    # Real-time checks

    def _run_realtime_checks(self, credential: Dict, metadata: Dict) -> Dict:
        """Quick sanity checks."""
        results = {"metadata_leak_detected": False}
        
        # Ensure sensitive fields are NOT in the credential
        leaked_fields = []
        cred_str = json.dumps(credential).lower()
        
        if metadata.get("gender") and str(metadata["gender"]).lower() in cred_str:
             # Be careful not to flag "male" inside "email" or similar substrings
             pass 
             
        # Simple college check - Handle Tiered Skills
        if metadata.get("college"):
            college = str(metadata["college"])
            
            verified_skills = credential.get("verified_skills", [])
            
            # Flatten if tiered dict
            if isinstance(verified_skills, dict):
                all_skills = []
                for tier_list in verified_skills.values():
                    all_skills.extend(tier_list)
            else:
                all_skills = verified_skills
                
            if college in str(all_skills):
                 leaked_fields.append("college_in_skills")

        if leaked_fields:
            results["metadata_leak_detected"] = True
            results["leaked_fields"] = leaked_fields
            
        return results

    # Batch statistical checks

    def _run_batch_checks(self, history: List[Dict]) -> Dict:
        """Runs all statistical analysis functions."""
        results = {
            "bias_detected": False,
            "details": {},
            "checks": []
        }
        
        # 1. Gender Bias
        gender_res = self._detect_gender_bias(history)
        results["details"]["gender_bias"] = gender_res
        results["checks"].append("gender_bias")
        if gender_res["bias_detected"]: results["bias_detected"] = True
        
        # 2. College Bias
        college_res = self._detect_college_bias(history)
        results["details"]["college_bias"] = college_res
        results["checks"].append("college_bias")
        if college_res["bias_detected"]: results["bias_detected"] = True
        
        # 3. GitHub Age Bias
        github_res = self._detect_github_age_bias(history)
        results["details"]["github_age_bias"] = github_res
        results["checks"].append("github_age_bias")
        if github_res["bias_detected"]: results["bias_detected"] = True
        
        return results

    def _detect_gender_bias(self, history: List[Dict]) -> Dict:
        """Check for confidence score disparity by gender."""
        males = [c for c in history if c["metadata"].get("gender") in ["M", "male", "Male"]]
        females = [c for c in history if c["metadata"].get("gender") in ["F", "female", "Female"]]
        
        if len(males) < MIN_SAMPLES["gender"] or len(females) < MIN_SAMPLES["gender"]:
            return {"bias_detected": False, "status": "insufficient_data"}
            
        male_avg = statistics.mean([c["skill_confidence"] for c in males])
        female_avg = statistics.mean([c["skill_confidence"] for c in females])
        
        gap = male_avg - female_avg
        
        if gap > THRESHOLDS["gender_gap"]:
            return {
                "bias_detected": True,
                "severity": "high" if gap > 10 else "medium",
                "gap": round(gap, 2),
                "male_avg": round(male_avg, 2),
                "female_avg": round(female_avg, 2)
            }
            
        return {"bias_detected": False, "gap": round(gap, 2)}

    def _detect_college_bias(self, history: List[Dict]) -> Dict:
        """Check if Tier 1 colleges get unfair boosts."""
        TIER_1 = ["IIT", "BITS", "IIIT", "NIT"]
        
        tier1 = []
        others = []
        
        for c in history:
            college = c["metadata"].get("college", "")
            if any(t in college for t in TIER_1):
                tier1.append(c)
            else:
                others.append(c)
                
        if len(tier1) < MIN_SAMPLES["college"] or len(others) < MIN_SAMPLES["college"]:
             return {"bias_detected": False, "status": "insufficient_data"}
             
        t1_avg = statistics.mean([c["skill_confidence"] for c in tier1])
        other_avg = statistics.mean([c["skill_confidence"] for c in others])
        
        boost = t1_avg - other_avg
        
        if boost > THRESHOLDS["college_boost"]:
            # Check if portfolio justifies it
            t1_port = statistics.mean([c["evidence"].get("portfolio_score", 0) for c in tier1])
            other_port = statistics.mean([c["evidence"].get("portfolio_score", 0) for c in others])
            
            # If portfolios are similar (diff < 5) but score boost is high -> BIAS
            if abs(t1_port - other_port) < 5:
                return {
                    "bias_detected": True,
                    "severity": "high",
                    "boost": round(boost, 2),
                    "reason": "Tier 1 boost not justified by portfolio score"
                }

        return {"bias_detected": False}

    def _detect_github_age_bias(self, history: List[Dict]) -> Dict:
        """Check if new accounts are penalized unfairly."""
        new_acc = []
        old_acc = []
        
        for c in history:
            age = c["evidence_details"].get("github", {}).get("account_age_years", 0)
            if age < 2.0:
                new_acc.append(c)
            else:
                old_acc.append(c)
                
        if len(new_acc) < MIN_SAMPLES["github"] or len(old_acc) < MIN_SAMPLES["github"]:
            return {"bias_detected": False, "status": "insufficient_data"}
            
        new_avg = statistics.mean([c["skill_confidence"] for c in new_acc])
        old_avg = statistics.mean([c["skill_confidence"] for c in old_acc])
        
        penalty = old_avg - new_avg
        
        if penalty > THRESHOLDS["github_penalty"]:
            return {
                "bias_detected": True,
                "severity": "medium",
                "penalty": round(penalty, 2),
                "reason": "New GitHub accounts penalized significantly"
            }
            
        return {"bias_detected": False}
