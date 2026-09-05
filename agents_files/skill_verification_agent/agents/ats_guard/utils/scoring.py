WEIGHTS = {
    "prompt_injection": 1.0,
    "white_text": 0.9,
    "hidden_layer": 0.8,
    "unicode_attack": 0.6,
}

def compute_risk_score(guard_results):
    risk_score = 0

    for g in guard_results:
        confidence = g.get("confidence", 1.0)
        if g.get("severity") == "critical":
            risk_score += 0.6 * confidence
        elif g.get("severity") == "medium":
            risk_score += 0.3 * confidence
        elif g.get("severity") == "high":
            # For backwards compatibility with standard severity
            risk_score += 0.45 * confidence

    return min(risk_score, 1.0)
