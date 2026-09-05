"""
Configuration for LangGraph Orchestration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Redis Configuration (Pub/Sub)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Redis Event Channels (from AGENTS.md)
CHANNELS = {
    "company_verified": "company_verified",
    "skill_verified": "skill_verified", 
    "bias_alert": "bias_alert",
    "match_completed": "match_completed",
    "credential_issued": "credential_issued"
}

# Workflow Thresholds
COMPANY_FAIRNESS_THRESHOLD = 60  # Minimum score to proceed
PORTFOLIO_STRONG_THRESHOLD = 70  # Skip test if above
BIAS_BATCH_SIZE = 50  # Run bias detection every N candidates

# LLM Cache Configuration
ENABLE_LLM_CACHE = True
CACHE_TTL_SECONDS = 3600  # 1 hour
