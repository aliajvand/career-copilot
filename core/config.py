import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    PROJECT_NAME: str = "Job Career Co-Pilot Enterprise"
    
    # Core API Keys & Models (Never hardcode secrets!)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Platform Credentials (Strictly from .env)
    JOBINJA_USER: str = os.getenv("JOBINJA_USER", "")
    JOBINJA_PASS: str = os.getenv("JOBINJA_PASS", "")
    JOBVISION_USER: str = os.getenv("JOBVISION_USER", "")
    JOBVISION_PASS: str = os.getenv("JOBVISION_PASS", "")
    
    # Payment & Security Secrets
    ZARINPAL_MERCHANT_ID: str = os.getenv("ZARINPAL_MERCHANT_ID", "sandbox-test-merchant")
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "career_copilot_default_secure_key_32b")
    
    # Database Path (PostgreSQL ready or local SQLite)
    DATABASE_PATH: str = str(BASE_DIR / "data" / "career_copilot.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/career_copilot.db")
    
    # Operational Defaults
    DEFAULT_MATCH_THRESHOLD: int = 70
    DEFAULT_GOLDEN_HOUR: bool = True
    DAILY_APPLICATION_CAP: int = 15
    
    # Network Proxy
    PROXY_URL: str = os.getenv("PROXY_URL", os.getenv("HTTP_PROXY", ""))
    HTTP_PROXY: str = os.getenv("HTTP_PROXY", "")
    PUBLIC_URL: str = os.getenv("PUBLIC_URL", "http://localhost:8088")

settings = Settings()
