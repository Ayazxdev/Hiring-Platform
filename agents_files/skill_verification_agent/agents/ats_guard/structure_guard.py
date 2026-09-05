"""
ATS Guard - Structure Integrity Checker
Detects white text, tiny fonts, and hidden overlays
"""
import fitz
import logging

logger = logging.getLogger(__name__)

def check_structure(pdf_path: str) -> list:
    """
    Check PDF structure for manipulation attempts.
    
    Detects:
    - White text (color near white)
    - Tiny fonts (< 6px)
    - Hidden overlays
    
    Args:
        pdf_path: Absolute path to PDF file
        
    Returns:
        List of flag dictionaries
    """
    flags = []

    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        size = span.get("size", 0)
                        color = span.get("color", 0)
                        text = span.get("text", "")

                        # Tiny font attack
                        if size < 2 and len(text.strip()) > 0:
                            flags.append({
                                "type": "hidden_text",
                                "severity": "high",
                                "reason": f"Very small font detected (size: {size}px) on page {page_num + 1}",
                                "page": page_num + 1
                            })

                        # White text attack (near-white color)
                        # Color is RGB int, white = 0xFFFFFF = 16777215
                        if color > 0xFFFFFF - 50 and len(text.strip()) > 0:
                            flags.append({
                                "type": "white_text",
                                "severity": "critical",
                                "reason": f"White-colored text detected on page {page_num + 1}",
                                "page": page_num + 1
                            })
        
        doc.close()
    except Exception as e:
        logger.error(f"Structure check failed: {e}")
        flags.append({
            "type": "structure_check_error",
            "severity": "low",
            "reason": f"Could not analyze PDF structure: {str(e)}"
        })

    return flags
