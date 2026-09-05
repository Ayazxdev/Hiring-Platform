from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import secrets

from app.database import get_db
from app.models import Candidate, Company
from app.schemas import (
    CandidateRegister, CandidateLogin, CandidateResponse
)
from app.auth_utils import hash_password, verify_password
from app.auth0_verifier import get_current_user_claims
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

def _new_anon_id() -> str:
    return "ANON-" + secrets.token_hex(6).upper()

@router.post("/candidate/signup", response_model=CandidateResponse)
async def candidate_signup(
    payload: CandidateRegister,
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(
        select(Candidate).where(Candidate.email == payload.email.lower().strip())
    )
    if q.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        pw_hash = hash_password(payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cand = Candidate(
        anon_id=_new_anon_id(),
        email=payload.email.lower().strip(),
        password_hash=pw_hash,
        name=payload.name,
        gender=payload.gender,
        college=payload.college,
        engineer_level=payload.engineer_level,
    )

    db.add(cand)
    await db.commit()
    await db.refresh(cand)

    return CandidateResponse(
        id=cand.id,
        anon_id=cand.anon_id,
        email=cand.email,
        name=cand.name,
        gender=cand.gender,
        college=cand.college,
        engineer_level=cand.engineer_level,
        created_at=cand.created_at
    )

@router.post("/candidate/login", response_model=CandidateResponse)
async def candidate_login(payload: CandidateLogin, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(Candidate).where(Candidate.email == payload.email.lower().strip()))
    cand = q.scalar_one_or_none()
    
    logger.info(f"Candidate login attempt for: {payload.email}")
    if not cand:
        logger.warning(f"Candidate not found: {payload.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, cand.password_hash):
        logger.warning(f"Password verification failed for: {payload.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    logger.info(f"Candidate login successful: {payload.email}")

    return CandidateResponse(
        id=cand.id,
        anon_id=cand.anon_id,
        email=cand.email,
        name=cand.name,
        gender=cand.gender,
        college=cand.college,
        engineer_level=cand.engineer_level,
        created_at=cand.created_at
    )


# COMPANY AUTH

@router.post("/company/signup")
async def company_signup(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Company signup with proper password hashing.
    Expects: {name, email, password}
    """
    email = payload.get("email", "").lower().strip()
    name = payload.get("name", "").strip()
    password = payload.get("password", "")

    if not email or not name or not password:
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Check if company already exists
    q = await db.execute(select(Company).where(Company.email == email))
    existing = q.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Company with this email already exists")

    try:
        pw_hash = hash_password(password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate deterministic company_id from email
    company_id = email.replace("@", "_").replace(".", "_")

    company = Company(
        id=company_id,
        name=name,
        email=email,
        password_hash=pw_hash,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)

    logger.info(f"Company signup successful: {email}")
    return {
        "company_id": company.id,
        "name": company.name,
        "email": company.email
    }


@router.post("/company/login")
async def company_login(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Company login with proper password verification.
    Expects: {email, password}
    """
    email = payload.get("email", "").lower().strip()
    password = payload.get("password", "")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Missing required fields")

    q = await db.execute(select(Company).where(Company.email == email))
    company = q.scalar_one_or_none()

    logger.info(f"Company login attempt for: {email}")
    if not company:
        logger.warning(f"Company not found: {email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Handle existing companies that were created without password_hash
    if company.password_hash is None:
        logger.warning(f"Company {email} has no password set — re-register via /auth/company/signup")
        raise HTTPException(
            status_code=401,
            detail="This company account has no password set. Please sign up again to set a password."
        )

    if not verify_password(password, company.password_hash):
        logger.warning(f"Company password verification failed for: {email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    logger.info(f"Company login successful: {email}")
    return {
        "company_id": company.id,
        "name": company.name,
        "email": company.email
    }


# AUTH0 INTEGRATION

@router.post("/candidate/auth0-sync", response_model=CandidateResponse)
async def candidate_auth0_sync(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Auth0 Sync Endpoint.
    Called by the frontend immediately after Auth0 login.
    Accepts {sub, email, name} from the Auth0 user object (already authenticated client-side).
    Creates or retrieves the Candidate DB row and returns the anon_id.
    """
    auth0_id: str = payload.get("sub", "")
    email: str = payload.get("email", "").lower().strip()
    name: str = payload.get("name") or email.split("@")[0] or "candidate"

    if not auth0_id:
        raise HTTPException(status_code=400, detail="Missing 'sub' field")

    # 1. Try to find by auth0_id first (most accurate)
    q = await db.execute(select(Candidate).where(Candidate.auth0_id == auth0_id))
    cand = q.scalar_one_or_none()

    # 2. Fallback: find by email (links existing old-system accounts to Auth0)
    if not cand and email:
        q = await db.execute(select(Candidate).where(Candidate.email == email))
        cand = q.scalar_one_or_none()
        if cand and cand.auth0_id is None:
            cand.auth0_id = auth0_id
            await db.commit()
            await db.refresh(cand)

    # 3. Create new candidate if not found
    if not cand:
        anon_id = "ANON-" + secrets.token_hex(6).upper()
        cand = Candidate(
            anon_id=anon_id,
            auth0_id=auth0_id,
            email=email,
            name=name,
            password_hash=None,
        )
        db.add(cand)
        try:
            await db.commit()
            await db.refresh(cand)
        except IntegrityError:
            await db.rollback()
            q = await db.execute(select(Candidate).where(Candidate.auth0_id == auth0_id))
            cand = q.scalar_one()

    return CandidateResponse(
        id=cand.id,
        anon_id=cand.anon_id,
        email=cand.email,
        name=cand.name,
        gender=cand.gender,
        college=cand.college,
        engineer_level=cand.engineer_level,
        created_at=cand.created_at,
    )
