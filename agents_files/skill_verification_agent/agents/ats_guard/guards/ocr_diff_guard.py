from ..utils.pdf_to_image import pdf_to_images
from ..utils.ocr_engine import extract_text_tesseract

def normalize(text):
    return set(word.lower() for word in text.split() if len(word) > 2)

def run(pdf_path, extracted_text):
    # Only run OCR when needed
    if len(extracted_text) < 50:
        return {"flag": False}

    try:
        images = pdf_to_images(pdf_path)
        ocr_text = extract_text_tesseract(images)

        parser_words = normalize(extracted_text)
        ocr_words = normalize(ocr_text)

        if not parser_words:
            return {"flag": False}

        hidden_words = parser_words - ocr_words
        mismatch_ratio = len(hidden_words) / len(parser_words)

        # FIXED LOGIC: Make OCR guard non-aggressive + Confidence Damping
        if mismatch_ratio > 0.5 and len(hidden_words) > 40:
            return {
                "flag": True,
                "type": "ocr_mismatch",
                "severity": "medium",   # ⚠️ NOT critical
                "confidence": mismatch_ratio * 0.7, # 0.7 damping included
                "evidence": {
                    "mismatch_ratio": mismatch_ratio,
                    "hidden_sample": list(hidden_words)[:10]
                }
            }

        return {"flag": False}

    except Exception as e:
        return {"flag": False, "error": str(e)}
