
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

logger = logging.getLogger(__name__)

class PassportAgent:
    """
    Passport Agent: Credential Wallet Builder
    
    Responsibilities:
    1. Extract Core Identity & Verification Data
    2. Create Immutable Snapshot
    3. Sign the Credential (Ed25519)
    4. Store for verification
    """
    
    # In a real system, these would be loaded from a secure vault or environment
    # Shared secret for Ed25519 signing (simplified for demo)
    _SEED = b"fair-hiring-network-seed-2026-xyz"
    
    def __init__(self):
        # Derive keys from seed
        self._private_key = Ed25519PrivateKey.from_private_bytes(hashlib.sha256(self._SEED).digest())
        self._public_key = self._private_key.public_key()
        self.public_key_hex = self._public_key.public_bytes_raw().hex()

    def issue_passport(self, payload: Dict) -> Dict:
        """
        Issue a signed passport credential.
        Called by passport_service.py
        """
        try:
            # 1. Canonicalize payload for consistent hashing
            canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            payload_bytes = canonical.encode('utf-8')
            
            # 2. Compute SHA256 Hash
            payload_hash = hashlib.sha256(payload_bytes).hexdigest()
            
            # 3. Compute Ed25519 Signature
            signature_bytes = self._private_key.sign(payload_bytes)
            signature_hex = signature_bytes.hex()
            
            result = {
                "hash": payload_hash,
                "signature": f"0x{signature_hex}",
                "public_key": f"0x{self.public_key_hex}",
                # Include verified credential payload fields in signed result
                "verified_skills": payload.get("verified_skills", []),
                "skill_confidence": payload.get("skill_confidence"),
                "match_score": payload.get("match_score"),
                "candidate": payload.get("candidate", {}),
                "job_id": payload.get("job_id"),
                "issuer": "FairHiringPlatform",
                "issued_at": payload.get("issued_at")
            }
            
            # 4. Store locally for simulation
            self._store_credential({
                "credential_id": payload.get("application_id", "unknown"),
                "record": result,
                "payload": payload
            })
            
            return result
        except Exception as e:
            logger.error(f"Failed to issue passport: {e}")
            raise

    def verify_passport(self, payload: Dict, signature: str) -> bool:
        """
        Verify a passport signature.
        Called by passport_service.py
        """
        try:
            # Clean signature
            sig_hex = signature.replace("0x", "")
            sig_bytes = bytes.fromhex(sig_hex)
            
            # Canonicalize payload
            canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            payload_bytes = canonical.encode('utf-8')
            
            # Verify
            self._public_key.verify(sig_bytes, payload_bytes)
            return True
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False

    def create_passport(self, evaluation_bundle: Dict) -> Dict:
        """
        Legacy method kept for compatibility with other nodes.
        Wraps issue_passport.
        """
        # (Original create_passport logic logic can be adapted or redirected)
        context = evaluation_bundle.get("context", {})
        skill_res = evaluation_bundle.get("skill_verification", {})
        if "output" in skill_res: skill_res = skill_res["output"]
        
        payload = {
            "application_id": context.get("evaluation_id", "unknown"),
            "verified_skills": skill_res.get("verified_skills", {}),
            "skill_confidence": skill_res.get("skill_confidence", 0),
            "credential_status": skill_res.get("credential_status", "PENDING")
        }
        
        issued = self.issue_passport(payload)
        
        return {
            "credential_id": payload["application_id"],
            "verification_url": f"https://verifier.fairhiring.network/verify/{payload['application_id']}",
            "status": "ISSUED",
            "passport_record": issued
        }

    def issue_credential(self, candidate_id: str, verified_skills: list, skill_confidence: int, evidence: dict, match_result: dict) -> dict:
        """
        Orchestration-friendly method to issue a credential.
        Matches signature used in nodes.py and example.py
        """
        
        # Determine match score from match_result (which could be the scorecard dict or a raw score)
        match_score = 0
        if isinstance(match_result, dict):
            match_score = match_result.get("overall_score") or match_result.get("match_score") or 0
        else:
            match_score = match_result
            
        payload = {
            "credential_id": candidate_id,
            "application_id": candidate_id,
            "verified_skills": verified_skills,
            "skill_confidence": skill_confidence,
            "match_score": match_score,
            "evidence": evidence,
            "issued_at": datetime.now().isoformat()
        }
        
        issued = self.issue_passport(payload)
        
        return {
            "payload": payload,
            "passport_record": issued,
            "credential_id": candidate_id, # For example.py
            "status": "ISSUED",
            "nfc": f"nfc://{candidate_id}"
        }

    def verify_credential(self, credential: dict) -> dict:
        """
        Verify a credential object.
        """
        payload = credential.get("payload", {})
        record = credential.get("passport_record", {})
        signature = record.get("signature", "")
        
        is_valid = self.verify_passport(payload, signature)
        
        return {
            "valid": is_valid,
            "credential_id": payload.get("application_id"),
            "verified_at": datetime.now().isoformat() if is_valid else None
        }

    def verify_by_id(self, credential_id: str) -> dict:
        """
        Verify a credential by its ID (simulated DB lookup).
        """
        db_path = Path("passport_db.json")
        if not db_path.exists():
            return {"valid": False, "error": "Database not found"}
            
        with open(db_path, "r") as f:
            db = json.load(f)
            
        record = db.get(str(credential_id))
        if not record:
            return {"valid": False, "error": "Credential not found"}
            
        return {
            "valid": True,
            "credential_id": credential_id,
            "record": record
        }

    def export_public_key(self) -> str:
        """Export public key in hex format"""
        return f"0x{self.public_key_hex}"

    def _store_credential(self, record: Dict):
        """Simulate DB storage"""
        db_path = Path("passport_db.json")
        try:
            if db_path.exists():
                with open(db_path, "r") as f:
                    db = json.load(f)
            else:
                db = {}
            
            db[str(record["credential_id"])] = record
            
            with open(db_path, "w") as f:
                json.dump(db, f, indent=2)
                
            logger.info(f"Credential {record['credential_id']} stored in secure DB.")
        except Exception as e:
            logger.error(f"Failed to store credential: {e}")
