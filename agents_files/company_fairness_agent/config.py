"""
Configuration for Company Fairness Agent
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration (OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Selection - Claude Sonnet for nuanced bias detection
COMPANY_FAIRNESS_MODEL = "anthropic/claude-sonnet-4-20250514"
MODEL_TEMPERATURE = 0.2

# Fairness Thresholds
MINIMUM_FAIRNESS_SCORE = 60  # Below this = rejected from pipeline
SEVERE_PENALTY = 15  # Points deducted for severe bias
MODERATE_PENALTY = 10  # Points deducted for moderate bias
MINOR_PENALTY = 5  # Points deducted for minor bias

# Bias Keywords (common gendered/biased language)
GENDERED_KEYWORDS = [
    "rockstar", "ninja", "guru", "wizard", "hacker",
    "aggressive", "dominant", "assertive",
    "young", "energetic", "digital native",
    "chairman", "manpower", "mankind"
]

AGE_BIAS_KEYWORDS = [
    "young team", "fresh graduate", "recent graduate",
    "digital native", "young and dynamic",
    "maximum 5 years experience", "no more than"
]

COLLEGE_BIAS_KEYWORDS = [
    "tier-1 college", "iit", "nit", "bits",
    "top university", "premier institute",
    "ivy league", "oxbridge"
]

EXPERIENCE_INFLATION_PATTERNS = [
    r"\d{2,}\+ years",  # 10+ years for entry roles
    r"must have \d+ years",
    r"minimum \d{2,} years"
]

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_CHANNEL = "company_verified"
