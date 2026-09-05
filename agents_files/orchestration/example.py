"""
Example usage of the complete Fair Hiring workflow
"""
import json
from state import create_initial_state
from workflow import workflow

# SAMPLE DATA

# Job Description (will be checked for fairness)
job_description = """
Senior Python Developer

We're looking for an experienced Python developer to join our engineering team.

Requirements:
- 5+ years of Python experience
- Experience with FastAPI or Django
- PostgreSQL knowledge
- Docker experience preferred

We offer:
- Competitive salary
- Remote work options
- Health benefits
"""

# Job Requirements (structured)
job_requirements = {
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "preferred_skills": ["Docker", "AWS", "Kubernetes"],
    "experience_years_min": 3
}

# Candidate Application
application = {
    "name": "Jane Smith",  # Will be anonymized
    "email": "jane.smith@example.com",
    "resume": "Experienced Python developer with 5 years building web APIs and microservices.",
    "experience_years": 5,
    "github_url": "https://github.com/janesmith",
    "leetcode_id": "janesmith",
    "gender": "F",  # For bias detection ONLY
    "college": "State University",
    "college_tier": 2,
    
    # Pre-scraped platform data
    "github_data": {
        "source": "github",
        "data": {
            "total_commits_last_year": 180,
            "consistency_score": 75,
            "projects": [
                {"name": "api-gateway", "project_score": 82, "code_quality": "clean"},
                {"name": "data-pipeline", "project_score": 78, "code_quality": "clean"}
            ],
            "top_languages": ["Python", "JavaScript", "Go"]
        }
    },
    
    "leetcode_data": {
        "source": "leetcode",
        "data": {
            "rank": "~100,000",
            "problems_solved": 85,
            "difficulty_breakdown": {"easy": 30, "medium": 45, "hard": 10},
            "top_language": "Python",
            "contest_rating": "1650",
            "max_rating": 1720
        }
    },
    
    # Optional Protocall result
    "protocall_result": {
        "opted_in": True,
        "signal": 82,
        "explanation_clarity": 85,
        "concept_understanding": 80
    }
}

# RUN WORKFLOW
print("=" * 70)
print("FAIR HIRING NETWORK - COMPLETE WORKFLOW")
print("=" * 70)

# Create initial state
initial_state = create_initial_state(
    application=application,
    job_description=job_description,
    job_requirements=job_requirements
)

# Run workflow
print("\nStarting workflow execution...\n")

try:
    # Execute the workflow
    final_state = workflow.invoke(initial_state)
    
    # Print results
    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETED")
    print("=" * 70)
    
    print(f"\n📋 Workflow Status: {final_state['workflow_status']}")
    print(f"📍 Final Stage: {final_state['current_stage']}")
    
    print(f"\n🏢 Company Fairness:")
    print(f"   Score: {final_state['company_fairness_score']}")
    print(f"   Status: {final_state['company_status']}")
    
    print(f"\n👤 Candidate:")
    print(f"   Anonymous ID: {final_state['candidate_id']}")
    print(f"   Verified Skills: {', '.join(final_state['verified_skills'])}")
    print(f"   Skill Confidence: {final_state['skill_confidence']}")
    print(f"   Signal Strength: {final_state['signal_strength']}")
    
    print(f"\n⚖️ Bias Check:")
    print(f"   Detected: {final_state['bias_detected']}")
    if final_state['bias_severity']:
        print(f"   Severity: {final_state['bias_severity']}")
    
    print(f"\n🎯 Match Result:")
    print(f"   Overall Score: {final_state['overall_score']}")
    print(f"   Matched Skills: {', '.join(final_state['matched_skills'])}")
    print(f"   Missing Skills: {', '.join(final_state['missing_skills'])}")
    print(f"   Recommendation: {final_state['recommendation']}")
    
    print(f"\n🎫 Credential:")
    print(f"   Credential ID: {final_state['credential_id']}")
    print(f"   Issued: {final_state['credential_issued']}")
    
    print(f"\n📡 Events Published:")
    for event in final_state['events_published']:
        print(f"   - {event['channel']}")
    
    print(f"\n⏱️ Timestamps:")
    for key, value in final_state['timestamps'].items():
        print(f"   {key}: {value}")
    
    # Export full state
    print("\n" + "=" * 70)
    print("FULL STATE (JSON)")
    print("=" * 70)
    
    # Remove large nested objects for cleaner output
    export_state = {k: v for k, v in final_state.items() 
                    if k not in ['raw_application', 'skill_credential', 'match_scorecard']}
    print(json.dumps(export_state, indent=2, default=str))
    
except Exception as e:
    print(f"\n❌ Workflow failed: {e}")
    raise
