import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# API Configurations
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")  # Fast and free on Groq

# Database Configuration
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "sessions.db"))

# Memory Configurations
# 5 turns means 5 user messages + 5 assistant responses (10 messages total)
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "5"))

# Log configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
