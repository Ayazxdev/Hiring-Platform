import base64, hashlib
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from app.config import settings

def _b64decode(s: str) -> bytes:
    s_clean = s.strip()
    # Support 64-char hex strings (32 raw bytes for Ed25519)
    if len(s_clean) == 64 and all(c in "0123456789abcdefABCDEF" for c in s_clean):
        return bytes.fromhex(s_clean)
    return base64.b64decode(s_clean.encode())

def _b64encode(b: bytes) -> str:
    return base64.b64encode(b).decode()

def get_private_key() -> Ed25519PrivateKey:
    raw = _b64decode(settings.SIGNING_PRIVATE_KEY_B64)
    return Ed25519PrivateKey.from_private_bytes(raw)

def get_public_key() -> Ed25519PublicKey:
    raw = _b64decode(settings.SIGNING_PUBLIC_KEY_B64)
    return Ed25519PublicKey.from_public_bytes(raw)

def canonical_json(data: dict) -> bytes:
    # Use standard json with sort_keys=True and no whitespace for canonical representation
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')

def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()

def sign_credential(credential: dict) -> tuple[str, str]:
    payload = canonical_json(credential)
    h = sha256_hex(payload)
    sig = get_private_key().sign(payload)
    return h, _b64encode(sig)

def verify_credential(credential: dict, signature_b64: str) -> bool:
    payload = canonical_json(credential)
    try:
        # Handle Hex signature (starts with 0x) - common in some agent implementations
        if signature_b64.startswith("0x"):
            sig = bytes.fromhex(signature_b64[2:])
        else:
            sig = base64.b64decode(signature_b64)
            
        pk = get_public_key()
        pk.verify(sig, payload)
        return True
    except Exception:
        return False
