import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()

# App
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:3000")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# NVIDIA Nemotron (nvidia/nvidia-nemotron-nano-9b-v2)
# Use NIM or OpenAI-compatible inference endpoint
NVIDIA_NEMOTRON_ENDPOINT = os.getenv("NVIDIA_NEMOTRON_ENDPOINT", "")
NVIDIA_NEMOTRON_API_KEY = os.getenv("NVIDIA_NEMOTRON_API_KEY", "")

# GitHub OAuth
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_CALLBACK_PATH = "/auth/github/callback"

# LinkedIn (OAuth or paste; API access restricted)
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_CALLBACK_PATH = "/auth/linkedin/callback"

# DB (default: backend/resumes.db)
DATABASE_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parent / "resumes.db"))
