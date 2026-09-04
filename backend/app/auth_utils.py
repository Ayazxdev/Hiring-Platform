import base64
import hashlib
import hmac
import os
import re
import secrets
import string

PBKDF2_ITERS = 210_000

def generate_anon_id(length: int = 16) -> str:
    """
    Generate a random anonymous ID for candidates.
    
    Args:
        length: Length of the ID (default 16)
        
    Returns:
        Random alphanumeric string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password is required.")

    # Basic strength rules for demo: 8+ chars, upper, lower, digit, symbol
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must include a lowercase letter.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must include an uppercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must include a number.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must include a symbol (e.g. !@#$).")

    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERS, dklen=32)
    return "pbkdf2_sha256$%d$%s$%s" % (
        PBKDF2_ITERS,
        base64.b64encode(salt).decode("utf-8"),
        base64.b64encode(dk).decode("utf-8"),
    )

def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters_s, salt_b64, hash_b64 = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iters = int(iters_s)
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        expected = base64.b64decode(hash_b64.encode("utf-8"))
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters, dklen=len(expected))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False
