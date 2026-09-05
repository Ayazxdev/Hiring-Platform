import json
from typing import Any, Dict, Tuple

def parse_json_content(content: str) -> Dict[str, Any]:
    """Parse message.content which is expected to be JSON string."""
    if content is None:
        return {}
    if isinstance(content, (dict, list)):
        return content
    try:
        return json.loads(content)
    except Exception:
        # allow "prefix: {json}"
        try:
            idx = content.find("{")
            if idx != -1:
                return json.loads(content[idx:])
        except Exception:
            pass
    return {"raw": content}

def dump_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return json.dumps({"error":"non-serializable response"})
