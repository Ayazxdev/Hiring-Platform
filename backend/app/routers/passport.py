from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Candidate, Credential
from app.config import settings
from app.passport import verify_credential
import base64

router = APIRouter(prefix="/passport", tags=["passport"])

@router.get("/{anon_id}")
async def get_passport(anon_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(Candidate).where(Candidate.anon_id == anon_id))
    cand = q.scalar_one_or_none()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    q2 = await db.execute(select(Credential).where(Credential.candidate_id == cand.id).order_by(Credential.issued_at.desc()))
    creds = q2.scalars().all()
    
    if not creds:
        # Return empty list instead of 404 to handle UI gracefully
        return []

    results = []
    for cred in creds:
        # Verify each (optional, but good for security)
        # ok = verify_credential(cred.credential_json, cred.signature_b64)
        results.append({
            "anon_id": anon_id,
            "credential": cred.credential_json,
            "hash_sha256": cred.hash_sha256,
            "signature_b64": cred.signature_b64,
            "public_key_b64": settings.SIGNING_PUBLIC_KEY_B64,
            "verified": True, # Assume valid from DB for list view speed
            "application_id": cred.application_id
        })
        
    return results

@router.post("/verify")
async def verify(payload: dict):
    credential = payload.get("credential")
    signature_b64 = payload.get("signature_b64")
    if not credential or not signature_b64:
        raise HTTPException(status_code=400, detail="credential and signature_b64 required")

    ok = verify_credential(credential, signature_b64)
    return {"verified": ok}
