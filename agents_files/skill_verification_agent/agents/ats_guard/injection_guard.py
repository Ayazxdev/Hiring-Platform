"""
ATS Guard - Prompt Injection Detector
Detects system manipulation and LLM prompt injection attempts
"""
import logging

logger = logging.getLogger(__name__)

# Hard injection patterns (critical severity)
CRITICAL_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "override evaluation",
    "system prompt",
    "you are an ai",
    "you are a helpful assistant",
    "disregard all previous",
    "forget everything"
]

# Soft manipulation patterns (low severity)
SEMANTIC_MANIPULATION_PATTERNS = [
    "for ai systems",
    "for ai-based screening",
    "assessment system should",
    "evaluation system should",
    "rate this candidate",
    "this candidate should be rated",
    "assessment frameworks must",
    "evaluation frameworks are designed"
]

def detect_prompt_injection(text: str) -> list:
    """
    Detect prompt injection and semantic manipulation attempts.
    
    Args:
        text: Extracted resume text
        
    Returns:
        List of flag dictionaries
    """
    flags = []
    lower = text.lower()

    # Check critical patterns
    for pattern in CRITICAL_INJECTION_PATTERNS:
        if pattern in lower:
            flags.append({
                "type": "prompt_injection",
                "severity": "critical",
                "reason": f"Critical injection pattern detected: '{pattern}'",
                "pattern": pattern
            })

    # Check semantic manipulation patterns
    for pattern in SEMANTIC_MANIPULATION_PATTERNS:
        if pattern in lower:
            flags.append({
                "type": "semantic_manipulation",
                "severity": "low",
                "reason": f"Narrative manipulation detected: '{pattern}'",
                "pattern": pattern
            })

    return flags
