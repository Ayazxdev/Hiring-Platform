"""
ATS Guard - Main Pipeline
Orchestrates all guard modules for comprehensive resume security analysis
"""
import logging
from pathlib import Path

from .extractor import extract_resume_text
from .structure_guard import check_structure
from .injection_guard import detect_prompt_injection
from .semantic_guard import semantic_consistency_check
from .decision_engine import decide

logger = logging.getLogger(__name__)

def run_ats_guard(pdf_path: str, github_age_years: float = None) -> dict:
    """
    Run complete ATS guard pipeline on a resume.
    
    Pipeline:
    1. Extract text (PDFMiner + OCR)
    2. Check structure (white text, tiny fonts)
    3. Detect prompt injection (critical + semantic)
    4. Check semantic consistency (experience inflation)
    5. Make final decision (trust-based scoring)
    
    Args:
        pdf_path: Absolute path to PDF resume
        github_age_years: GitHub account age (optional, for consistency check)
        
    Returns:
        Decision dictionary with security_status, trust_score (0-100), and flags
    """
    logger.info(f"Running ATS Guard on: {pdf_path}")
    
    # Validate file exists
    if not Path(pdf_path).exists():
        return {
            "security_status": "ERROR",
            "reason": f"File not found: {pdf_path}",
            "trust_score": 0,
            "flags": [],
            "guard_version": "v1"
        }

    # Step 1: Extract text
    try:
        text = extract_resume_text(pdf_path)
        if not text or len(text.strip()) < 50:
            return {
                "security_status": "ERROR",
                "reason": "Could not extract sufficient text from PDF",
                "trust_score": 0,
                "flags": [],
                "guard_version": "v1"
            }
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return {
            "security_status": "ERROR",
            "reason": f"Text extraction failed: {str(e)}",
            "trust_score": 0,
            "flags": [],
            "guard_version": "v1"
        }

    # Step 2-4: Accumulate flags from all guards
    flags = []
    
    try:
        flags += check_structure(pdf_path)
    except Exception as e:
        logger.error(f"Structure check failed: {e}")
    
    try:
        flags += detect_prompt_injection(text)
    except Exception as e:
        logger.error(f"Injection detection failed: {e}")
    
    try:
        flags += semantic_consistency_check(text, github_age_years)
    except Exception as e:
        logger.error(f"Semantic check failed: {e}")

    # Step 5: Make final decision
    decision = decide(flags)
    
    # Add guard version
    decision["guard_version"] = "v1"
    
    logger.info(f"ATS Guard Decision: {decision['security_status']} (trust: {decision['trust_score']})")
    
    return decision

from .guards import run_all_guards
from .utils.scoring import compute_risk_score

def run_ats_guard_v2(pdf_path, extracted_text):
    guard_results = run_all_guards(pdf_path, extracted_text)

    risk_score = compute_risk_score(guard_results)

    # Final Decision (MULTI-SIGNAL)
    if risk_score >= 0.85:
        action = "BLOCKED"
    elif risk_score >= 0.5:
        action = "NEEDS_REVIEW"
    else:
        action = "ALLOW"

    # Convert to structured dict
    guard_analysis = {g["type"]: g for g in guard_results}

    return {
        "action": action,
        "risk_score": risk_score,
        "guard_analysis": guard_analysis
    }
