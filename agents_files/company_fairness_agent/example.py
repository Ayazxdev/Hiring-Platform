"""
Example usage of Company Fairness Agent
"""
import json
from agents.company_fairness_agent import CompanyFairnessAgent

# Initialize agent
agent = CompanyFairnessAgent()

# Sample job description with biases
biased_jd = """
Senior Software Engineer - Rockstar Developer Wanted!

We're looking for a coding ninja to join our young and dynamic team. 
You should be a self-starter with aggressive problem-solving skills.

Requirements:
- Must be from a Tier-1 college (IIT/NIT preferred)
- 10+ years of experience in Python
- Recent graduate energy with senior-level skills
- Digital native who lives and breathes code

We offer:
- Competitive salary
- Stock options
- Free snacks and games room
"""

# Sample fair job description
fair_jd = """
Senior Software Engineer

We're looking for an experienced engineer to join our collaborative team.

Requirements:
- Strong Python programming skills
- 5+ years of software development experience
- Experience with distributed systems
- Excellent problem-solving abilities

We offer:
- Competitive salary based on experience
- Comprehensive health benefits
- Flexible work arrangements
- Professional development budget
"""

# Test biased JD
print("=" * 60)
print("TESTING BIASED JOB DESCRIPTION")
print("=" * 60)
result1 = agent.verify_company(biased_jd, company_id="test_biased_001")
print(json.dumps(result1, indent=2))

print("\n" + "=" * 60)
print("TESTING FAIR JOB DESCRIPTION")
print("=" * 60)
result2 = agent.verify_company(fair_jd, company_id="test_fair_001")
print(json.dumps(result2, indent=2))

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Biased JD Score: {result1['fairness_score']} - {result1['status']}")
print(f"Fair JD Score: {result2['fairness_score']} - {result2['status']}")
