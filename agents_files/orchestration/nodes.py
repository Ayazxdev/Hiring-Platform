"""
LangGraph Node Functions

Each function represents a node in the workflow graph.
Nodes read from state, call agents, and update state.
"""
import sys
import os
import logging
from datetime import datetime
from typing import Dict

# Add parent paths for agent imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import HiringState
from config import COMPANY_FAIRNESS_THRESHOLD, PORTFOLIO_STRONG_THRESHOLD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# NODE 1: VERIFY COMPANY
def verify_company_node(state: HiringState) -> Dict:
    """
    Node: Verify company's job description for fairness
    
    Input: job_description from state
    Output: Updates company_* fields
    """
    logger.info("[NODE] verify_company")
    
    # Import agent
    from company_fairness_agent.agents import CompanyFairnessAgent
    agent = CompanyFairnessAgent()
    
    # Run verification
    result = agent.verify_company(state["job_description"])
    
    # Update state
    return {
        "company_id": result.get("company_id"),
        "company_fairness_score": result.get("fairness_score", 0),
        "company_status": result.get("status", "Rejected"),
        "company_flags": result.get("flags", []),
        "company_suggestions": result.get("suggestions", []),
        "current_stage": "company_verified",
        "timestamps": {
            **state.get("timestamps", {}),
            "company_verified_at": datetime.now().isoformat()
        },
        "events_published": state.get("events_published", []) + [{
            "channel": "company_verified",
            "data": {
                "company_id": result.get("company_id"),
                "score": result.get("fairness_score"),
                "status": result.get("status")
            }
        }]
    }


# NODE 2: ANONYMIZE CANDIDATE
def anonymize_node(state: HiringState) -> Dict:
    """
    Node: Anonymize candidate data (Stage 0)
    
    Input: raw_application from state
    Output: Updates anonymized_data, candidate_id
    """
    logger.info("[NODE] anonymize")
    
    from skill_verification_agent.agents import SkillVerificationAgent
    agent = SkillVerificationAgent()
    
    anonymized = agent.anonymize_candidate(state["raw_application"])
    
    return {
        "candidate_id": anonymized.get("candidate_id"),
        "anonymized_data": anonymized,
        "current_stage": "anonymized",
        "timestamps": {
            **state.get("timestamps", {}),
            "anonymized_at": datetime.now().isoformat()
        }
    }


# NODE 3: PORTFOLIO ANALYSIS
def portfolio_analysis_node(state: HiringState) -> Dict:
    """
    Node: Analyze GitHub/LeetCode/CodeChef portfolio
    
    Input: Platform data from raw_application
    Output: Updates portfolio_result, signal_strength
    """
    logger.info("[NODE] portfolio_analysis")
    
    from skill_verification_agent.agents import SkillVerificationAgent
    agent = SkillVerificationAgent()
    
    # Extract platform data from application
    app = state["raw_application"]
    
    result = agent.analyze_portfolio(
        github_data=app.get("github_data"),
        leetcode_data=app.get("leetcode_data"),
        codechef_data=app.get("codechef_data")
    )
    
    return {
        "portfolio_result": result,
        "signal_strength": result.get("signal_strength", "weak"),
        "current_stage": "portfolio_analyzed",
        "timestamps": {
            **state.get("timestamps", {}),
            "portfolio_analyzed_at": datetime.now().isoformat()
        }
    }


# NODE 4: SKILL TEST (CONDITIONAL)
def skill_test_node(state: HiringState) -> Dict:
    """
    Node: Run skill test (only if portfolio is weak)
    
    This is a placeholder - actual test would be async
    """
    logger.info("[NODE] skill_test (conditional)")
    
    # In production, this would trigger an async coding test
    # For now, we just mark that test was required
    
    return {
        "current_stage": "test_required",
        "timestamps": {
            **state.get("timestamps", {}),
            "test_triggered_at": datetime.now().isoformat()
        }
    }


# NODE 5: AGGREGATE SKILLS
def aggregate_skills_node(state: HiringState) -> Dict:
    """
    Node: Final skill aggregation with LLM
    
    Input: portfolio_result, manipulation check
    Output: Updates verified_skills, skill_confidence
    """
    logger.info("[NODE] aggregate_skills")
    
    from skill_verification_agent.agents import SkillVerificationAgent
    agent = SkillVerificationAgent()
    
    # Detect manipulation
    manipulation = agent.detect_manipulation(
        state["anonymized_data"].get("resume", "")
    )
    
    # Extract skills with LLM
    llm_result = agent.extract_skills_with_llm(
        normalized_data=state["portfolio_result"].get("normalized_data", {}),
        job_requirements=state["job_requirements"]
    )
    
    # Calculate confidence
    base_confidence = state["portfolio_result"].get("portfolio_score", 0)
    if manipulation.get("manipulated"):
        final_confidence = int(base_confidence * 0.7)
    else:
        final_confidence = base_confidence
    
    return {
        "verified_skills": llm_result.get("verified_skills", []),
        "skill_confidence": final_confidence,
        "manipulation_detected": manipulation.get("manipulated", False),
        "current_stage": "skills_verified",
        "timestamps": {
            **state.get("timestamps", {}),
            "skills_verified_at": datetime.now().isoformat()
        },
        "events_published": state.get("events_published", []) + [{
            "channel": "skill_verified",
            "data": {
                "candidate_id": state["candidate_id"],
                "skills": llm_result.get("verified_skills", []),
                "confidence": final_confidence
            }
        }]
    }


# NODE 6: BIAS DETECTION
def bias_detection_node(state: HiringState) -> Dict:
    """
    Node: Run bias detection on accumulated candidates
    
    This runs periodically, not on every candidate
    """
    logger.info("[NODE] bias_detection")
    
    from bias_detection_agent.agents import BiasDetectionAgent
    agent = BiasDetectionAgent()
    
    # Add current candidate to buffer
    buffer = state.get("candidates_buffer", [])
    buffer.append({
        "candidate_id": state["candidate_id"],
        "score": state["skill_confidence"],
        "metadata": state["anonymized_data"].get("metadata", {}),
        "evidence": state["portfolio_result"]
    })
    
    # Run audit
    report = agent.audit_candidates(buffer)
    
    updates = {
        "candidates_buffer": buffer,
        "bias_report": report,
        "bias_detected": report.get("bias_detected", False),
        "bias_severity": report.get("overall_severity"),
        "current_stage": "bias_checked",
        "timestamps": {
            **state.get("timestamps", {}),
            "bias_checked_at": datetime.now().isoformat()
        }
    }
    
    # Publish alert if bias detected
    if report.get("bias_detected"):
        updates["events_published"] = state.get("events_published", []) + [{
            "channel": "bias_alert",
            "data": agent.create_bias_alert(report)
        }]
    
    return updates


# NODE 7: MATCHING
def matching_node(state: HiringState) -> Dict:
    """
    Node: Calculate match score
    
    Input: verified_skills, job_requirements
    Output: Updates match_scorecard, overall_score
    """
    logger.info("[NODE] matching")
    
    from matching_agent.agents import MatchingAgent
    agent = MatchingAgent()
    
    # Build credential for matching (NO bias fields)
    credential = {
        "candidate_id": state["candidate_id"],
        "verified_skills": state["verified_skills"],
        "skill_confidence": state["skill_confidence"],
        "evidence": state["portfolio_result"],
        "signal_strength": state["signal_strength"]
    }
    
    scorecard = agent.match_candidate(
        candidate_credential=credential,
        job_requirements=state["job_requirements"],
        experience_years=state["raw_application"].get("experience_years", 0),
        protocall_result=state["raw_application"].get("protocall_result")
    )
    
    return {
        "match_scorecard": scorecard,
        "overall_score": scorecard.get("overall_score", 0),
        "matched_skills": scorecard.get("matched_skills", []),
        "missing_skills": scorecard.get("missing_skills", []),
        "recommendation": scorecard.get("recommendation", ""),
        "current_stage": "matched",
        "timestamps": {
            **state.get("timestamps", {}),
            "matched_at": datetime.now().isoformat()
        },
        "events_published": state.get("events_published", []) + [{
            "channel": "match_completed",
            "data": {
                "candidate_id": state["candidate_id"],
                "score": scorecard.get("overall_score"),
                "decision": scorecard.get("recommendation")
            }
        }]
    }


# NODE 8: ISSUE PASSPORT
def passport_node(state: HiringState) -> Dict:
    """
    Node: Issue skill credential
    
    Input: All verification data
    Output: Updates credential_id, nfc_payload
    """
    logger.info("[NODE] passport")
    
    from passport_agent.agents import PassportAgent
    agent = PassportAgent()
    
    credential = agent.issue_credential(
        candidate_id=state["candidate_id"],
        verified_skills=state["verified_skills"],
        skill_confidence=state["skill_confidence"],
        evidence={
            "portfolio_score": state["portfolio_result"].get("portfolio_score"),
            "sources": state["portfolio_result"].get("evidence_sources", []),
            "test_score": None,
            "interview_signal": None
        },
        match_result=state["match_scorecard"]
    )
    
    return {
        "credential_id": credential["payload"]["credential_id"],
        "skill_credential": credential,
        "credential_issued": True,
        "nfc_payload": credential.get("nfc"),
        "current_stage": "completed",
        "workflow_status": "completed",
        "timestamps": {
            **state.get("timestamps", {}),
            "credential_issued_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        },
        "events_published": state.get("events_published", []) + [{
            "channel": "credential_issued",
            "data": {
                "credential_id": credential["payload"]["credential_id"],
                "candidate_id": state["candidate_id"]
            }
        }]
    }


# REJECTION NODE
def reject_node(state: HiringState) -> Dict:
    """
    Node: Handle rejection (company failed fairness)
    """
    logger.info("[NODE] reject")
    
    return {
        "workflow_status": "rejected",
        "current_stage": "rejected",
        "error_message": f"Company failed fairness check. Score: {state['company_fairness_score']}",
        "timestamps": {
            **state.get("timestamps", {}),
            "rejected_at": datetime.now().isoformat()
        }
    }


# CONDITIONAL FUNCTIONS
def should_proceed_after_company(state: HiringState) -> str:
    """
    Conditional edge: Check if company passed fairness
    
    Returns: "continue" or "reject"
    """
    if state["company_fairness_score"] >= COMPANY_FAIRNESS_THRESHOLD:
        return "continue"
    return "reject"


def should_require_test(state: HiringState) -> str:
    """
    Conditional edge: Check if skill test is needed
    
    Returns: "skip_test" or "require_test"
    """
    portfolio_score = state["portfolio_result"].get("portfolio_score", 0)
    if portfolio_score >= PORTFOLIO_STRONG_THRESHOLD:
        return "skip_test"
    return "require_test"


def check_bias_status(state: HiringState) -> str:
    """
    Conditional edge: Check if bias was detected
    
    Returns: "proceed" or "review"
    """
    if state.get("bias_detected"):
        return "review"
    return "proceed"
