import os, logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.api.routes import router
from backend.api.grievance_routes import grievance_router
from backend.core.utils import ensure_folders
from backend.db.database import init_db, ensure_admin
from dotenv import load_dotenv

load_dotenv()

# ── Validate required secrets on startup ──────────────────────────
_REQUIRED = ["GROQ_API_KEY", "JWT_SECRET", "ADMIN_PASSWORD"]
_missing = [k for k in _REQUIRED if not os.getenv(k)]
if _missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(_missing)}\n"
        f"Copy .env.example to .env and fill in the values."
    )

app = FastAPI(
    title="JanSamadhan",
    description="Multilingual Citizen Grievance Chatbot",
    version="2.0.0"
)

# Generic exception handler to prevent stack trace leakage on unhandled 500s
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None)
        )
    logging.getLogger("uvicorn.error").error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

# Restricted CORS origins
_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
_origins = [_frontend_url, "http://localhost:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_folders()
init_db()
ensure_admin()

app.include_router(router, prefix="/api")
app.include_router(grievance_router, prefix="/api/grievances")

@app.get("/")
def root():
    return {"message": "Welcome to JanSamadhan - Multilingual Citizen Grievance Chatbot", "docs": "/docs"}
