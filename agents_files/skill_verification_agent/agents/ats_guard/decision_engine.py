"""
ATS Guard - Trust-Based Decision Engine
Graduated scoring system for final verdict (Production Grade)
"""
import logging

logger = logging.getLogger(__name__)

def decide(flags: list) -> dict:
    """
    Make final ATS decision based on accumulated flags.
    
    Production-grade trust scoring (0-100 integer):
    - Critical: Immediate 0 (short-circuit)
    - High: -25
    - Medium: -15
    - Low: -5
    
    Args:
        flags: List of flag dictionaries from all guards
        
    Returns:
        Decision dictionary with security_status, trust score (0-100), and flags
    """
    trust = 100
    has_critical = False
    
    # Short-circuit on critical flags (FIX #2: No severity stacking)
    for flag in flags:
        severity = flag.get("severity", "unknown")
        if severity == "critical":
            has_critical = True
            trust = 0
            break  # Immediate rejection, no further processing
        elif severity == "high":
            trust -= 25
        elif severity == "medium":
            trust -= 15
        elif severity == "low":
            trust -= 5
    
    # Floor at 0
    trust = max(0, trust)
    
    # Determine security_status (renamed from "status")
    if trust >= 75:
        security_status = "PASSED"
    elif trust >= 50:
        security_status = "REVIEW"
    else:
        security_status = "REJECTED"
    
    # Build response
    result = {
        "security_status": security_status,  # FIX #5: Renamed from "status"
        "trust_score": trust,  # FIX #4: Now 0-100 integer
        "flags": flags,
        "flag_count": len(flags),
        "has_critical": has_critical,
        "reason": f"Trust score: {trust}" if flags else "No issues detected"
    }
    
    # Add critical flag details if present
    if has_critical:
        critical_flags = [f for f in flags if f.get("severity") == "critical"]
        result["critical_flags"] = critical_flags
        result["reason"] = "Critical ATS manipulation detected"
    
    return result
