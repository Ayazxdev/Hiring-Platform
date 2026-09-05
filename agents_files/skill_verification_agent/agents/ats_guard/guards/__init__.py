from .white_text_guard import run as white_text
from .prompt_injection_guard import run as prompt_injection
from .hidden_layer_guard import run as hidden_layer
from .unicode_attack_guard import run as unicode_attack
from .ocr_diff_guard import run as ocr_diff


def run_all_guards(pdf_path, extracted_text):
    results = []

    for guard in [white_text, prompt_injection, hidden_layer, unicode_attack, ocr_diff]:
        try:
            res = guard(pdf_path, extracted_text)
            if res and res.get("flag"):
                results.append(res)
        except Exception:
            continue

    return results
