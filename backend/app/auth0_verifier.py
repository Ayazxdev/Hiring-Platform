"""
Auth0 JWT Verification for Fair Hiring Network
Provides a FastAPI dependency that validates Auth0 access tokens using JWKS.
"""
import os
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.environ.get("AUTH0_AUDIENCE", "https://fair-hiring-api")

# Cache for JWKS keys
_jwks_cache: Optional[dict] = None

security = HTTPBearer(auto_error=False)


async def _get_jwks() -> dict:
    """Fetch and cache the Auth0 JWKS public keys."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    if not AUTH0_DOMAIN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AUTH0_DOMAIN is not configured on the server.",
        )

    url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache


async def verify_auth0_token(token: str) -> dict:
    """
    Validate an Auth0 JWT access token.
    Returns the decoded claims on success, raises HTTPException on failure.
    """
    try:
        jwks = await _get_jwks()
        unverified_header = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to parse token header.",
        )

    rsa_key = {}
    for key in jwks.get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n":   key["n"],
                "e":   key["e"],
            }
            break

    if not rsa_key:
        # JWKS refresh: if no key found, clear the cache and retry once
        global _jwks_cache
        _jwks_cache = None
        try:
            jwks = await _get_jwks()
            for key in jwks.get("keys", []):
                if key.get("kid") == unverified_header.get("kid"):
                    rsa_key = {
                        "kty": key["kty"], "kid": key["kid"],
                        "use": key["use"], "n": key["n"], "e": key["e"],
                    }
                    break
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"[auth0_verifier] JWKS refresh failed: {e}")

    if not rsa_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"No matching public key found in JWKS. kid={unverified_header.get('kid')}",
        )

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except JWTError as e:
        import logging
        logging.getLogger(__name__).error(
            f"[auth0_verifier] JWT decode failed. domain={AUTH0_DOMAIN!r} "
            f"kid={unverified_header.get('kid')!r} err={e}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
        )

    return payload


async def get_current_user_claims(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    FastAPI dependency — extract and verify the Bearer token from the request.
    Usage:  claims: dict = Depends(get_current_user_claims)
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or malformed.",
        )
    return await verify_auth0_token(credentials.credentials)


async def get_optional_user_claims(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    Optional version — returns None if no token is supplied (for public routes
    that can also return richer data when authenticated).
    """
    if credentials is None or not credentials.credentials:
        return None
    try:
        return await verify_auth0_token(credentials.credentials)
    except HTTPException:
        return None
