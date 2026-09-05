"""
ATS Guard - Text Extraction Module
Combines PDFMiner + OCR for robust text extraction
"""
try:
    import pytesseract
except ImportError:
    pytesseract = None

from pdfminer.high_level import extract_text
from PIL import Image
import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

def extract_resume_text(pdf_path: str) -> str:
    """
    Extract text from PDF using multiple methods for robustness.
    
    Args:
        pdf_path: Absolute path to PDF file
        
    Returns:
        Combined text from PDFMiner + OCR
    """
    text = ""
    
    # Method 1: PDFMiner (fast, works for text-based PDFs)
    try:
        text = extract_text(pdf_path) or ""
    except Exception as e:
        logger.warning(f"PDFMiner extraction failed: {e}")

    # Method 2: OCR fallback (for images / scanned PDFs)
    ocr_text = ""
    if len(text.strip()) < 100:
        logger.info(f"PDFMiner extracted only {len(text.strip())} chars. Running OCR fallback...")
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                if pytesseract:
                    ocr_text += pytesseract.image_to_string(img)
                else:
                    logger.warning("Pytesseract not installed. Skipping OCR layer.")
            doc.close()
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
    else:
        logger.info(f"PDFMiner extraction successful ({len(text.strip())} chars). Skipping OCR.")

    # Combine and clean, ensuring safe encoding for Windows console
    combined = "\n".join([text.strip(), ocr_text.strip()])
    
    # 2026 Fix: Ensure valid UTF-8 and remove unprintable chars that crash Windows console
    try:
        combined = combined.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        pass
        
    return combined.strip()
