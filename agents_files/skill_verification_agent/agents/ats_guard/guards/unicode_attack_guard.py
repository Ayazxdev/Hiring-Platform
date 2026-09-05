import re

def run(pdf_path: str, extracted_text: str):
    # Detect zero-width characters (u200B-u200D, uFEFF)
    zero_width_chars = re.findall(r'[\u200B-\u200D\uFEFF]', extracted_text)
    
    if len(zero_width_chars) > 5:
        return {
            "flag": True,
            "type": "unicode_attack",
            "severity": "medium",
            "confidence": 0.85,
            "evidence": {"zero_width_count": len(zero_width_chars)}
        }
        
    return {"flag": False}
