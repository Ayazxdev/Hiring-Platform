"""
LLM Extraction Prompts for Profile Parsing

These prompts are optimized for extracting structured data from unstructured
profile text scraped from various coding platforms.
"""

# LEETCODE EXTRACTION PROMPT
LEETCODE_PROMPT = """Extract LeetCode profile data.

--- INPUT TEXT ---
{raw_text}
-------------------

CRITICAL: OUTPUT ONLY JSON. NO TEXT BEFORE OR AFTER THE JSON OBJECT.

EXTRACTION RULES:
1. RANK: Look for 'Guardian', 'Knight', 'Master', or rank numbers. If 'Unrated', use that.
2. PROBLEMS SOLVED: Find pattern 'X / Y' (e.g., '450 / 3000'). Extract ONLY X. IGNORE percentages like '95%'.
3. TOP LANGUAGE: Language with most problems solved.
4. BADGES: Count of badges.
5. CONTEST RATING: Look for exact label 'Contest Rating' followed by number. If not found, return null.
6. TOP SKILLS: Extract skills labeled 'Advanced' or 'Intermediate'. IGNORE 'Fundamental'.

OUTPUT (COPY THIS STRUCTURE EXACTLY):
{{
  "rank": "String",
  "problems_solved": 0,
  "top_language": "String",
  "badges": 0,
  "contest_rating": null,
  "max_rating": null,
  "top_skills": [],
  "difficulty_breakdown": {{
    "easy": 0,
    "medium": 0,
    "hard": 0
  }}
}}

IMPORTANT:
- DO NOT write any text before {{
- DO NOT write any text after }}
- DO NOT use markdown fences
- ONLY output the JSON
"""


# CODECHEF EXTRACTION PROMPT
CODECHEF_PROMPT = """Extract CodeChef/Codeforces profile data.

--- INPUT TEXT ---
{raw_text}
-------------------

CRITICAL: OUTPUT ONLY JSON. NO TEXT BEFORE OR AFTER THE JSON OBJECT.

EXTRACTION RULES:
1. RANK: Look for 'Global Rank' or Division (e.g., 'Div 2'). Combine if found.
2. PROBLEMS SOLVED: Find 'Fully Solved (X)' or 'Total Problems'. Extract X. IGNORE 'Top X%'.
3. RATING: Look for rating number (0-3500 range). DO NOT confuse with Global Rank (usually 100k+).
4. TOP LANGUAGE: Language with most usage.
5. TOP SKILLS: Skills from 'Expertise' or verified paths.

OUTPUT (COPY THIS STRUCTURE EXACTLY):
{{
  "rank": "String",
  "problems_solved": 0,
  "top_language": "String",
  "badges": 0,
  "contest_rating": "String",
  "max_rating": null,
  "stars": 0,
  "top_skills": []
}}

IMPORTANT:
- DO NOT write any text before {{
- DO NOT write any text after }}
- DO NOT use markdown fences
- ONLY output the JSON
"""


# CODEFORCES EXTRACTION PROMPT
CODEFORCES_PROMPT = """You are a Codeforces Data Extractor.

--- INPUT TEXT ---
{raw_text}
------------------

Extract fields:
1. Rank: User Tier (e.g., 'Specialist', 'Expert', 'Master').
2. Rating: Current Contest Rating (Integer).
3. Max Rating: Highest Rating ever achieved (Integer).
4. Problems Solved: 'All time solved' count.
5. Top Language: Language with most submissions.

--- OUTPUT JSON ---
{{
  "rank": "String",
  "contest_rating": Integer,
  "max_rating": Integer,
  "problems_solved": Integer,
  "top_skills": ["List"],
  "top_language": "String",
  "badges": Integer
}}
"""


# GITHUB CONSISTENCY CHECK PROMPT
GITHUB_CONSISTENCY_PROMPT = """You are a Senior Engineering Recruiter and Technical Evaluator specializing in assessing developer consistency, reliability, and growth trends from GitHub activity data.
You will be given a JSON summary of a developer's GitHub commit history. Your task is to analyze this data and evaluate coding consistency, not raw volume.

--- CANDIDATE DATA ---
Observation Period: {period}
Total Commits (Year): {total_commits}
Max Gap: {max_gap} days
Recent Activity (Last 30 Days): {commits_last_30_days}
Days Since Last Commit: {days_since_last_commit}
Monthly Breakdown: {monthly_log}

--- CORE EVALUATION PRINCIPLE (CRITICAL) ---
Recent behavior is more important than historical behavior.
Weight the most recent 2–3 months more heavily than older activity. Do NOT penalize developers for past inactivity if recent consistency is strong.

--- SCORING LOGIC (0–10) ---
10: Flawless daily consistency.
8-9: Strong recent consistency (Recently active) OR predictable weekly patterns.
5-7: Generally consistent but with noticeable recent gaps.
1-4: Highly irregular, sporadic, or currently inactive.

--- REQUIRED PERSONAS (Choose exactly one) ---
 Veteran — Consistent contributions across most of the year.
 Recently active — Low/no activity earlier, but strong, sustained recent consistency.
 Burnout — Previously consistent, but little/no activity in last 1–2 months.
 Sporadic — Irregular activity with frequent gaps.
 Inactive — Minimal activity.

--- MANDATORY EDGE-CASE HANDLING ---
1. Rising Star: Long early inactivity followed by daily recent commits → HIGH score (8/10).
2. Burnout: Strong history but zero recent commits → LOW score.
3. Weekend Warrior: Commits only on weekends but never misses → Consistent (Veteran).

--- OUTPUT FORMAT (Strict JSON) ---
{{
  "consistency_score": Integer (0-10),
  "persona": "String",
  "reasoning": "String"
}}
"""


# LINKEDIN EXTRACTION PROMPT
LINKEDIN_PROMPT = """Extract structured profile data from this LinkedIn text.

--- INPUT TEXT ---
{raw_text}
------------------

Extract:
1. Current Title / Headline
2. Years of Experience (calculate from work history)
3. Current Company
4. Top Skills (listed skills section)
5. Education (highest degree)

--- OUTPUT JSON ---
{{
  "headline": "String",
  "years_experience": Integer,
  "current_company": "String",
  "top_skills": ["List"],
  "education": "String"
}}
"""


def get_prompt_for_platform(platform: str) -> str:
    """
    Get the appropriate extraction prompt for a platform.
    
    Args:
        platform: One of 'LeetCode', 'CodeChef', 'Codeforces', 'GitHub', 'LinkedIn'
        
    Returns:
        Prompt template string
    """
    prompts = {
        "LeetCode": LEETCODE_PROMPT,
        "CodeChef": CODECHEF_PROMPT,
        "Codeforces": CODEFORCES_PROMPT,
        "GitHub": GITHUB_CONSISTENCY_PROMPT,
        "LinkedIn": LINKEDIN_PROMPT
    }
    return prompts.get(platform, "Summarize this profile: {raw_text}")
