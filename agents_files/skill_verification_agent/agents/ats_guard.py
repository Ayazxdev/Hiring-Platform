# pyright: reportMissingImports=false
import logging
import re
from typing import Dict, List, Any, Optional
import os
from ..utils.pdf_layer_extractor import WhiteTextDetector # type: ignore
from ..utils.evasion_detector import SophisticatedEvasionDetector # type: ignore

logger = logging.getLogger(__name__)

# Load LLM-based defender, if we want to use it
try:
    from ..utils.manipulation_detector import PromptInjectionDefender # type: ignore
    DEFENDER_AVAILABLE = True
except ImportError:
    DEFENDER_AVAILABLE = False

def run_ats_guard(pdf_path: str, github_age_years: Optional[float] = None) -> Dict[str, Any]:
    """
    Multi-layer ATS Guard Service Integration.
    Runs fast structural and regex-based checks before deep LLM extraction.
    """
    flags: List[Dict[str, Any]] = []
    trust_score: float = 100.0
    security_status = "PASSED"
    reason = "Passed all checks"
    
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except Exception as e:
        logger.error(f"Failed to read PDF for ATS Guard: {e}")
        return {
            "security_status": "REVIEW",
            "trust_score": 50.0,
            "reason": f"Could not read PDF file: {e}",
            "flags": [],
            "guard_version": "v1"
        }

    # 1. Structural Checks (White text)
    white_text_detector = WhiteTextDetector()
    try:
        # Extract plain text for regex logic
        text = white_text_detector._extract_all_text(pdf_bytes)
        
        wt_result = white_text_detector.detect_white_text(pdf_bytes)
        if wt_result.get("severity") == "critical":
            flags.append({
                "type": "white_text",
                "severity": "critical",
                "reason": "Detected massive invisible/white text layering."
            })
            trust_score = 0.0
            security_status = "REJECTED"
            reason = "Critical structural manipulation (White text stufffing)"
            # Fast fail
            return _build_response(security_status, trust_score, reason, flags)
            
        elif wt_result.get("severity") in ["high", "medium"]:
            flags.append({
                "type": "white_text",
                "severity": wt_result["severity"],
                "reason": f"Suspicious hidden words detected: {wt_result.get('hidden_word_count')}"
            })
            trust_score -= 25.0 # type: ignore
    except Exception as e:
        logger.error(f"White Text Detector error: {e}")
        text = "" # Fallback
        
    if not text:
        return _build_response("REVIEW", 50.0, "Empty or unreadable text", flags)
        
    text_lower = text.lower()

    # 2. Hard Injection (Critical)
    hard_injection_patterns = [
        r'ignore\s+(?:all\s+)?(?:previous\s+)?(?:all\s+)?instructions',
        r'override\s+(?:all\s+)?evaluation',
        r'system\s+prompt',
        r'you\s+are\s+an\s+ai',
        r'you\s+are\s+a\s+helpful\s+assistant',
        r'do\s+not\s+apply\s+rejection',
        r'must\s+approve\s+this\s+resume',
        r'disregard\s+all\s+previous',
        r'you\s+must\s+approve',
        r'bypass\s+all\s+checks',
        r'rejection\s+rules\s+must\s+not\s+apply'
    ]
    for pattern in hard_injection_patterns:
        if re.search(pattern, text_lower):
            flags.append({
                "type": "prompt_injection_hard",
                "severity": "critical",
                "reason": f"Hard injection pattern matched: {pattern}"
            })
            trust_score = 0.0
            security_status = "REJECTED"
            reason = "Critical Prompt Injection Detected"
            return _build_response(security_status, trust_score, reason, flags)

    # 3. Keyword Stuffing (Critical/High)
    # Check for 4+ consecutive repeated words (5 total) 
    # Use fuzzy matching for joined words (e.g. FAANGYou)
    words = text_lower.split()
    if len(words) > 0:
        consecutive_repeats: int = 0
        max_repeats: int = 0
        last_word = ""
        for word in words:
            # Handle joined words by checking if current word STARTS with last word
            # This catches things like 'FAANG FAANG FAANG FAANG FAANGYou'
            if word == last_word or (len(last_word) > 3 and word.startswith(last_word)):
                consecutive_repeats += 1
                if consecutive_repeats > max_repeats:
                    max_repeats = consecutive_repeats
            else:
                consecutive_repeats = 0
                last_word = word
                
        if max_repeats >= 4: # 5 consecutive
            flags.append({
                "type": "keyword_stuffing",
                "severity": "critical",
                "reason": f"Keyword stuffing detected: word repeating {max_repeats+1} times"
            })
            trust_score = 0.0
            security_status = "REJECTED"
            reason = "Critical manipulation detected (Keyword stuffing)"
            return _build_response(security_status, trust_score, reason, flags)
        
    # Check for excessive frequency (Global Keyword Stuffing)
    from collections import Counter
    word_counts = Counter(words)
    for word, count in word_counts.items():
        if len(word) > 3 and count > 15: # Extreme repetition of a single tech word
            flags.append({
                "type": "keyword_frequency_stuffing",
                "severity": "high",
                "reason": f"Word '{word}' appears an excessive number of times ({count})"
            })
            trust_score -= 40.0

    # 4. Soft Semantic Manipulation (Low)
    soft_injection_patterns = [
        r'for\s+ai-based\s+screening',
        r'assessment\s+system\s+should',
        r'evaluation\s+system\s+should',
        r'this\s+candidate\s+should\s+be\s+rated',
        r'assessment\s+frameworks\s+must'
    ]
    for pattern in soft_injection_patterns:
        if re.search(pattern, text_lower):
            flags.append({
                "type": "prompt_injection_soft",
                "severity": "low",
                "reason": f"Soft semantic manipulation matched: {pattern}"
            })
            trust_score -= 10.0 # type: ignore

    # 5. Sophisticated Evasion
    evasion_detector = SophisticatedEvasionDetector()
    semantic_res = evasion_detector.detect_semantic_injection(text)
    if semantic_res.get("detected"):
        sev = semantic_res.get("severity", "medium")
        flags.append({
            "type": "semantic_evasion",
            "severity": sev,
            "reason": "Professional Language Mask detected"
        })
        if sev == "high":
            trust_score -= 30.0 # type: ignore
        else:
            trust_score -= 15.0 # type: ignore

    # 6. Self-Assessment Narrative (Low)
    superlatives = ['exceptional', 'outstanding', 'world-class', 'unmatched']
    superlative_count = sum(text_lower.count(word) for word in superlatives)
    if superlative_count >= 3:
        flags.append({
            "type": "self_assessment_narrative",
            "severity": "low",
            "reason": f"Found {superlative_count} extreme superlatives without evidence"
        })
        trust_score -= 5.0 # type: ignore
        
    # Post-checks adjustment
    trust_score = max(0.0, trust_score)
    
    if trust_score == 0.0:
        security_status = "REJECTED"
        reason = "Multiple manipulation vectors detected"
    elif trust_score < 70.0:
        security_status = "REVIEW"
        reason = "Suspicious signals detected in document"
    else:
        if len(flags) > 0:
            reason = "Minor anomalies detected, conditionally passed"

    return _build_response(security_status, trust_score, reason, flags)


def _build_response(security_status: str, trust_score: float, reason: str, flags: List[Dict]) -> Dict[str, Any]:
    return {
        "security_status": security_status,
        "trust_score": float(trust_score),
        "reason": reason,
        "flags": flags,
        "guard_version": "v1"
    }
