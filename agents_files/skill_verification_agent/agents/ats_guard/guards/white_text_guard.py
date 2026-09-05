def run(pdf_path: str, extracted_text: str):
    try:
        import fitz
        doc = fitz.open(pdf_path)
    except Exception:
        return {"flag": False}

    hidden_chars = 0
    total_chars = 0

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    color = span.get("color", 0)
                    total_chars += len(text)
                    # Detect near-white text (#FFFFFF is 16777215)
                    if color > 16777150:
                        hidden_chars += len(text)
    doc.close()

    ratio = hidden_chars / total_chars if total_chars else 0

    if ratio > 0.1:
        return {
            "flag": True,
            "type": "white_text",
            "severity": "critical",
            "confidence": min(1.0, ratio + 0.3),
            "evidence": {"hidden_ratio": ratio}
        }

    return {"flag": False}
