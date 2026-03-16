from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseModel):
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    github_client_id: str = os.getenv("GITHUB_CLIENT_ID", "")
    github_client_secret: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    linkedin_client_id: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    linkedin_client_secret: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    nvidia_api_base_url: str = os.getenv("NVIDIA_API_BASE_URL", "").rstrip("/")
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    nemotron_model: str = os.getenv("NEMOTRON_MODEL", "nvidia/nvidia-nemotron-nano-9b-v2")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
