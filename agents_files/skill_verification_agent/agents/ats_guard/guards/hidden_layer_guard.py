def run(pdf_path: str, extracted_text: str):
    try:
        import fitz
        doc = fitz.open(pdf_path)
    except Exception:
        return {"flag": False}

    tiny_chars = 0
    total_chars = 0

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    size = span.get("size", 10)
                    total_chars += len(text)
                    if size < 2:
                        tiny_chars += len(text)
    doc.close()

    ratio = tiny_chars / total_chars if total_chars else 0

    if ratio > 0.15:
        return {
            "flag": True,
            "type": "hidden_layer",
            "severity": "critical",
            "confidence": min(1.0, ratio + 0.3),
            "evidence": {"hidden_ratio": ratio}
        }

    return {"flag": False}
