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
    
    # JWT Auth (env-driven)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "jansamadhan_super_secure_jwt_secret_key_2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Admin Credentials (env-driven)
    ADMIN_EMPLOYEE_ID: str = os.getenv("ADMIN_EMPLOYEE_ID", "OD-ADM-2024-88")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin@2026")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "alok.mohapatra@odisha.gov.in")
    
    # AI / Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
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
