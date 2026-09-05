"""
Example usage of Skill Passport Agent
"""
import json
from agents.passport_agent import PassportAgent

# Initialize agent (generates new RSA keys)
agent = PassportAgent()

# Sample verified skills (from SkillVerificationAgent)
candidate_id = "anon_a7f3e9d2"
verified_skills = ["Python", "FastAPI", "PostgreSQL", "Docker"]
skill_confidence = 82
evidence = {
    "sources": ["github", "leetcode"],
    "portfolio_score": 82,
    "test_score": None,
    "interview_signal": None
}

# Optional match result (from MatchingAgent)
match_result = {
    "overall_score": 78,
    "recommendation": "Good Match - Recommend further review"
}

# Issue credential
print("=" * 60)
print("ISSUING SKILL CREDENTIAL")
print("=" * 60)

credential = agent.issue_credential(
    candidate_id=candidate_id,
    verified_skills=verified_skills,
    skill_confidence=skill_confidence,
    evidence=evidence,
    match_result=match_result
)

print(json.dumps(credential, indent=2))

# Verify credential
print("\n" + "=" * 60)
print("VERIFYING CREDENTIAL")
print("=" * 60)

verification = agent.verify_credential(credential)
print(json.dumps(verification, indent=2))

# NFC verification (by ID only)
print("\n" + "=" * 60)
print("NFC TAP VERIFICATION")
print("=" * 60)

credential_id = credential["payload"]["credential_id"]
nfc_verification = agent.verify_by_id(credential_id)
print(json.dumps(nfc_verification, indent=2))

# Export public key (for external verifiers)
print("\n" + "=" * 60)
print("PUBLIC KEY FOR EXTERNAL VERIFICATION")
print("=" * 60)
print(agent.export_public_key())
