def run(pdf_path: str, extracted_text: str):
    critical_patterns = [
        "ignore previous instructions",
        "ignore all instructions",
        "override evaluation",
        "system prompt",
        "you are an ai",
        "disregard all previous",
        "forget everything"
    ]
    
    lower_text = extracted_text.lower()
    matches = []
    
    for pattern in critical_patterns:
        if pattern in lower_text:
            matches.append(pattern)
            
    if matches:
        return {
            "flag": True,
            "type": "prompt_injection",
            "severity": "critical",
            "confidence": 0.95,
            "evidence": {"patterns": matches}
        }
        
    return {"flag": False}
