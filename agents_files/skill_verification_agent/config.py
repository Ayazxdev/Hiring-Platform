"""
Configuration for Skill Verification Agent
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration (OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Selection
SKILL_VERIFICATION_MODEL = os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
MODEL_TEMPERATURE = 0.3

# Scoring Weights
SCORING_WEIGHTS = {
    "github": 0.60,        # 60% weight for GitHub
    "coding_platforms": 0.40  # 40% weight for LeetCode/CodeChef
}

# GitHub Scoring Sub-weights
GITHUB_WEIGHTS = {
    "commits_score": 0.30,
    "consistency_score": 0.30,
    "project_quality": 0.40
}

# Thresholds
PORTFOLIO_STRONG_THRESHOLD = 70  # Above this = skip test
KEYWORD_DENSITY_THRESHOLD = 0.30  # Above this = manipulation

# Redis Configuration (Optional)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# LinkedIn Strategy
ENABLE_LINKEDIN = False  # Set to True if you implement user upload

# Options: "ollama" (local, free) or "openrouter" (cloud, paid)
LLM_BACKEND = os.getenv("LLM_BACKEND", "openrouter")

# Ollama model (used when LLM_BACKEND = "ollama")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# OpenRouter model (used when LLM_BACKEND = "openrouter")
OPENROUTER_SCRAPER_MODEL = os.getenv("OPENROUTER_SCRAPER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

# Chrome settings for Selenium
CHROME_HEADLESS = os.getenv("CHROME_HEADLESS", "true").lower() == "true"

# Scraping timeouts (seconds)
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", 10))
SCROLL_WAIT_TIME = int(os.getenv("SCROLL_WAIT_TIME", 2))

# GITHUB API CONFIGURATION
# GitHub Personal Access Token (for API access)
GITHUB_PAT = os.getenv("GITHUB_PAT")

# GitHub API settings
GITHUB_USE_API = os.getenv("GITHUB_USE_API", "true").lower() == "true"  # Use API instead of scraping
GITHUB_MAX_REPOS = int(os.getenv("GITHUB_MAX_REPOS", 30))  # Max repos to analyze
GITHUB_MAX_COMMITS_PER_REPO = int(os.getenv("GITHUB_MAX_COMMITS_PER_REPO", 100))

# GitHub Signal Weights (used for final scoring)
GITHUB_SIGNAL_WEIGHTS = {
    "credibility": 0.25,    # Account age, profile completeness
    "skill": 0.35,          # Languages, code depth
    "consistency": 0.40     # Commit patterns, activity
}
