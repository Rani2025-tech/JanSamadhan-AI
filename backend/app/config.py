import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend or root directory
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "JanSamadhan AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./jansamadhan.db")
    
    # JWT Auth (Must be set in environment; no static hardcoded default)
    JWT_SECRET: str = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Admin Credentials (Must be set in environment; no static hardcoded default)
    ADMIN_EMPLOYEE_ID: str = os.getenv("ADMIN_EMPLOYEE_ID", "OD-ADM-2024-88")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "alok.mohapatra@odisha.gov.in")
    
    # AI / Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    AI_CONFIDENCE_THRESHOLD: float = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.60"))
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ]

settings = Settings()

# Fail-fast security validation: Ensure critical secrets are configured
if not settings.JWT_SECRET:
    raise RuntimeError(
        "FATAL: JWT_SECRET (or SECRET_KEY) environment variable is required. "
        "Please configure it in your .env file or environment."
    )

if not settings.ADMIN_PASSWORD:
    raise RuntimeError(
        "FATAL: ADMIN_PASSWORD environment variable is required. "
        "Please configure it in your .env file or environment."
    )
