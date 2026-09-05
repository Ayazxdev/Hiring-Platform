"""
Configuration for Skill Passport Agent
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration (OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Selection - Llama 8B for cost efficiency
PASSPORT_MODEL = "meta-llama/llama-3.1-8b-instruct"
MODEL_TEMPERATURE = 0.1

# Security Configuration (No Blockchain - from AGENTS.md)
# Using RSA-2048 + SHA-256 instead
RSA_KEY_SIZE = 2048
HASH_ALGORITHM = "SHA-256"

# Credential Expiry
CREDENTIAL_VALIDITY_DAYS = 365  # 1 year

# NFC Configuration
NFC_MAX_PAYLOAD_BYTES = 888  # NFC payload limit
NFC_ENABLED = True

# Database Configuration (PostgreSQL for registry)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "fair_hiring")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CREDENTIAL_CHANNEL = "credential_issued"

# Verification API
VERIFICATION_API_URL = os.getenv("VERIFICATION_API_URL", "http://localhost:8000/verify")
