"""
Configuration for Transparent Matching Agent
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration (OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Selection - Gemini Pro for matching explanations
MATCHING_MODEL = "google/gemini-pro-1.5"
MODEL_TEMPERATURE = 0.2

# Matching Formula Weights (from AGENTS.md)
# score = (skill_confidence * 0.6) + (experience * 0.3) + (optional_protocall * 0.1)
MATCHING_WEIGHTS = {
    "skill_confidence": 0.60,   # 60% - skills from verification
    "experience": 0.30,         # 30% - years of experience
    "protocall": 0.10           # 10% - optional interview signal (MAX)
}

# Experience Scoring
EXPERIENCE_SCORE_MAP = {
    0: 20,    # Entry level
    1: 35,
    2: 50,
    3: 65,
    4: 75,
    5: 85,
    6: 90,
    7: 92,
    8: 95,
    9: 97,
    10: 100   # 10+ years
}

# EXCLUDED from scoring (CRITICAL - from AGENTS.md)
EXCLUDED_FIELDS = [
    "gender",
    "name",
    "college",
    "age",
    "location",
    "appearance",
    "accent"
]

# Minimum score for recommendation
RECOMMENDATION_THRESHOLD = 60

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
MATCH_CHANNEL = "match_completed"
