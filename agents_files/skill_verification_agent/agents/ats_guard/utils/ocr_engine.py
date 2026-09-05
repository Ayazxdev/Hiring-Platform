try:
    import pytesseract
except ImportError:
    pytesseract = None

def extract_text_tesseract(images):
    if not pytesseract:
        return ""
    full_text = []

    for img in images:
        try:
            text = pytesseract.image_to_string(img)
            full_text.append(text)
        except Exception:
            pass

    return "\n".join(full_text)
