import logging
import os

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    import pytesseract
    import numpy as np
    from pathlib import Path
    
    # DEFINITIVE FIX: Hard-wire Tesseract path for Windows
    TESSERACT_PATH = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

    if TESSERACT_PATH.exists():
        pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)
        logger.info(f"Tesseract definitively configured at: {TESSERACT_PATH}")
    else:
        # Fallback to fuzzy search if the primary path fails (to keep it robust)
        tesseract_paths = [
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe'
        ]
        tesseract_found = False
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                tesseract_found = True
                logger.info(f"Tesseract found via fallback at: {path}")
                break
        
        if not tesseract_found:
            logger.warning("Tesseract binary not found at expected path. Image scanning may fail.")

except ImportError as e:
    Image = None
    pytesseract = None
    np = None
    logger.warning(f"Image processing dependencies not installed: {e}")

class ImageInjectionDetector:
    """
    2026 Defense: Detect hidden text in uploaded images
    (headshots, certificates, portfolio screenshots)
    """
    
    def __init__(self):
        # Only warn if pytesseract module is missing, not if just the binary isn't found
        # The actual availability will be checked when scan_image_for_injection is called
        if pytesseract is None:
            logger.warning("Pytesseract module not installed. Image scanning disabled.")
        elif Image is None:
            logger.warning("PIL/Pillow not installed. Image scanning disabled.")
        else:
            # Test if Tesseract binary is actually accessible
            try:
                # Quick test to see if tesseract is available
                pytesseract.get_tesseract_version()
                logger.info("Tesseract OCR is ready for image scanning")
            except Exception as e:
                logger.warning(f"Tesseract binary not accessible: {e}. Image scanning disabled.")
            
    def scan_image_for_injection(self, image_path: str) -> dict:
        """
        Extract ALL text from image (including hidden)
        Check for prompt injection patterns
        """
        if not pytesseract or not Image:
             return {
                "injection_detected": False,
                "error": "dependencies_missing",
                "action": "skip_image_scan"
            }

        try:
            # Open image
            img = Image.open(image_path)
            
            # Extract text using OCR
            # Note: Tesseract executable must be in PATH
            extracted_text = pytesseract.image_to_string(img)
            
            # Check for injection patterns
            injection_patterns = [
                "ignore instructions",
                "dismiss instructions",
                "approve candidate",
                "hire immediately",
                "override",
                "system:",
                "score: 100",
                "ignore previous"
            ]
            
            for pattern in injection_patterns:
                if pattern in extracted_text.lower():
                    return {
                        "injection_detected": True,
                        "type": "multimodal_injection",
                        "pattern_found": pattern,
                        "action": "reject_image"
                    }
            
            # Check for suspiciously high text volume in headshot
            # Heuristic: mostly relevant if identified as headshot, but good general check
            if len(extracted_text.split()) > 50:  # Relaxed threshold
                return {
                    "injection_detected": True,
                    "type": "excessive_text_in_image",
                    "action": "manual_review"
                }
            
            return {"injection_detected": False}
            
        except Exception as e:
            logger.error(f"Image scan failed: {e}")
            return {
                "injection_detected": False,
                "error": str(e),
                "action": "skip_image_scan"
            }
