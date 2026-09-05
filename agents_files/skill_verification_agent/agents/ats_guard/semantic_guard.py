"""
ATS Guard - Semantic Consistency Checker
Detects experience inflation and credential fraud
"""
import re
import logging

logger = logging.getLogger(__name__)

def extract_years_claimed(text: str) -> int:
    """
    Extract maximum years of experience claimed in resume.
    
    Args:
        text: Resume text
        
    Returns:
        Maximum years claimed
    """
    matches = re.findall(r'(\d+)\+?\s*years', text.lower())
    return max([int(m) for m in matches], default=0)

def semantic_consistency_check(text: str, github_age_years: float = None) -> list:
    """
    Check semantic consistency between claims and evidence.
    
    Args:
        text: Resume text
        github_age_years: GitHub account age (if available)
        
    Returns:
        List of flag dictionaries
    """
    flags = []
    claimed_years = extract_years_claimed(text)

    # Check GitHub age vs. claimed experience
    if github_age_years is not None and claimed_years >= 5 and github_age_years < 1:
        flags.append({
            "type": "experience_inflation",
            "severity": "medium",
            "reason": f"Claims {claimed_years} years experience but GitHub account is {github_age_years:.1f} years old",
            "claimed_years": claimed_years,
            "github_age": github_age_years
        })

    # Check for excessive self-assessment language
    self_assessment_patterns = [
        "exceptional", "outstanding", "world-class", 
        "best-in-class", "unparalleled", "unmatched"
    ]
    
    count = sum(1 for pattern in self_assessment_patterns if pattern in text.lower())
    if count >= 3:
        flags.append({
            "type": "credential_inflation",
            "severity": "low",
            "reason": f"Excessive self-assessment language detected ({count} instances)",
            "count": count
        })

    return flags
