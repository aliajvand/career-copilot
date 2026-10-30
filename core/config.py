import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Job Career Co-Pilot & Automation"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Database
    DATABASE_PATH: str = str(BASE_DIR / "data" / "career_copilot.db")
    
    # Defaults
    DEFAULT_MATCH_THRESHOLD: int = 70  # minimum % to apply
    DEFAULT_GOLDEN_HOUR: bool = True   # 8:30 - 10:30 AM queue
    DAILY_APPLICATION_CAP: int = 15    # prevent spam
    
    # Proxy if needed for Gemini
    PROXY_URL: str = os.getenv("HTTP_PROXY", "")

    class Config:
        env_file = ".env"

settings = Settings()
