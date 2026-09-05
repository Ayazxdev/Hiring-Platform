"""
Configuration for Bias Detection Meta-Agent
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration (OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Selection - Claude for statistical analysis speed
BIAS_DETECTION_MODEL = os.getenv("LLM_MODEL", "anthropic/claude-3-haiku")
MODEL_TEMPERATURE = 0.1  # Low for deterministic analysis

# Bias Detection Thresholds (from AGENTS.md)
GENDER_GAP_THRESHOLD = 5      # Score gap > 5 points = gender bias
COLLEGE_BOOST_THRESHOLD = 10  # Tier-1 boost > 10 points = college bias
PROTOCALL_GAP_THRESHOLD = 8   # Accent discrimination > 8 points

# Alert Severity Levels
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

# Minimum sample size for statistical validity
MIN_SAMPLE_SIZE = 10

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
BIAS_ALERT_CHANNEL = "bias_alert"

# Audit Frequency
AUDIT_BATCH_SIZE = 50  # Audit every 50 candidates
