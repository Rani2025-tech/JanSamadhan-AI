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
    
    # JWT Auth (env-driven with demo fallback)
    JWT_SECRET: str = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "jansamadhan_jwt_secret_token_2026_hackathon"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Admin Credentials (env-driven with demo fallback)
    ADMIN_EMPLOYEE_ID: str = os.getenv("ADMIN_EMPLOYEE_ID", "OD-ADM-2024-88")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD") or "Admin@2026"
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

# Validation & Security Warnings: Inform when running with fallback secrets
if not (os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")):
    import warnings
    warnings.warn(
        "JWT_SECRET (or SECRET_KEY) environment variable is not configured. "
        "Using fallback demo token. Configure JWT_SECRET in production.",
        RuntimeWarning,
        stacklevel=2
    )

if not os.getenv("ADMIN_PASSWORD"):
    import warnings
    warnings.warn(
        "ADMIN_PASSWORD environment variable is not configured. "
        "Using demo admin credentials. Configure ADMIN_PASSWORD in production.",
        RuntimeWarning,
        stacklevel=2
    )
