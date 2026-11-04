import os
import sys
from pathlib import Path

# Add backend directory to sys.path so app and ai packages resolve smoothly
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routes import (
    auth_router,
    complaints_router,
    notifications_router,
    admin_router,
    chat_router,
)

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager
import logging
from app.database import SessionLocal
from app.models import Complaint, User

logger = logging.getLogger("jansamadhan")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup check: auto-seed if database is empty on ephemeral disks
    db = SessionLocal()
    try:
        complaint_count = db.query(Complaint).count()
        user_count = db.query(User).count()
        if complaint_count == 0 or user_count == 0:
            logger.info("Database is empty (users=%d, complaints=%d). Triggering auto-seed...", user_count, complaint_count)
            from seed import seed_database
            seed_database(force=False)
            logger.info("Startup auto-seeding completed successfully.")
        else:
            logger.info("Database verified online with %d complaints and %d users.", complaint_count, user_count)
    except Exception as e:
        logger.error("Error during startup database auto-seed check: %s", e)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Official API for JanSamadhan Multilingual Citizen Grievance Redressal Portal",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(complaints_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "JanSamadhan AI Backend",
        "version": settings.VERSION,
        "gemini_active": bool(settings.GEMINI_API_KEY)
    }

# Mount static assets and SPA fallback if dist directory is present
dist_dir = Path(__file__).resolve().parent.parent / "dist"
if (dist_dir / "index.html").exists():
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = dist_dir / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(dist_dir / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
