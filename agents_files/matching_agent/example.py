"""
Example usage of Transparent Matching Agent
"""
import json
from agents.matching_agent import MatchingAgent

# Initialize agent
agent = MatchingAgent()

# Sample candidate credential (from SkillVerificationAgent)
# NOTE: No gender, name, college, age - those are EXCLUDED
candidate_credential = {
    "candidate_id": "anon_a7f3e9d2",
    "verified_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "skill_confidence": 82,
    "evidence": {
        "portfolio_score": 82,
        "test_score": None,
        "interview_signal": None,
        "sources": ["github", "leetcode"]
    },
    "signal_strength": "strong"
}

# Job requirements
job_requirements = {
    "required_skills": ["Python", "FastAPI", "SQL"],
    "preferred_skills": ["Docker", "AWS", "Kubernetes"]
}

# Match single candidate
print("=" * 60)
print("SINGLE CANDIDATE MATCHING")
print("=" * 60)

scorecard = agent.match_candidate(
    candidate_credential=candidate_credential,
    job_requirements=job_requirements,
    experience_years=4,
    protocall_result=None  # Not opted in
)

print(json.dumps(scorecard, indent=2))

# Test with Protocall opted in
print("\n" + "=" * 60)
print("MATCHING WITH PROTOCALL")
print("=" * 60)

scorecard_with_protocall = agent.match_candidate(
    candidate_credential=candidate_credential,
    job_requirements=job_requirements,
    experience_years=4,
    protocall_result={
        "opted_in": True,
        "signal": 85,
        "explanation_clarity": 88,
        "concept_understanding": 82
    }
)

print(json.dumps(scorecard_with_protocall, indent=2))

# Rank multiple candidates
print("\n" + "=" * 60)
print("RANKING MULTIPLE CANDIDATES")
print("=" * 60)

candidates = [
    {
        "credential": {
            "candidate_id": "anon_001",
            "verified_skills": ["Python", "FastAPI", "Docker"],
            "skill_confidence": 85
        },
        "experience_years": 5
    },
    {
        "credential": {
            "candidate_id": "anon_002",
            "verified_skills": ["Python", "Django"],
            "skill_confidence": 70
        },
        "experience_years": 3
    },
    {
        "credential": {
            "candidate_id": "anon_003",
            "verified_skills": ["Python", "FastAPI", "SQL", "Docker", "AWS"],
            "skill_confidence": 90
        },
        "experience_years": 6,
        "protocall_result": {"opted_in": True, "signal": 88}
    }
]

rankings = agent.rank_candidates(candidates, job_requirements)
for card in rankings:
    print(f"Rank {card['rank']}: {card['candidate_id']} - Score: {card['overall_score']} - {card['recommendation']}")
