import time
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import shutil, os, json, secrets, logging
from jose import jwt, JWTError
from datetime import datetime, timedelta
from backend.rag.rag_pipeline import ingest_pdf, get_answer_stream, get_answer
from backend.core.utils import get_all_pdfs, faiss_index_exists, ensure_folders
from backend.db import database as db

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or JWT_SECRET == "your-secret-key-change-in-production":
    logging.getLogger("uvicorn.error").warning("JWT_SECRET is missing or insecure default. Generating temporary key.")
    JWT_SECRET = secrets.token_hex(32)

JWT_ALGORITHM = "HS256"
try:
    JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
except ValueError:
    JWT_EXPIRE_HOURS = 24

security = HTTPBearer(auto_error=False)

def create_token(
    user_id: str,
    role: str,
    department: Optional[str] = None,
    expires_hours: Optional[int] = None,
    expires_minutes: Optional[int] = None,
    demo: bool = False,
    name: Optional[str] = None,
    email: Optional[str] = None
) -> str:
    if expires_minutes is not None:
        exp_delta = timedelta(minutes=expires_minutes)
    elif expires_hours is not None:
        exp_delta = timedelta(hours=expires_hours)
    else:
        exp_delta = timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "role": role,
        "department": department,
        "demo": demo,
        "exp": datetime.utcnow() + exp_delta
    }
    if name:
        payload["name"] = name
    if email:
        payload["email"] = email
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        department = payload.get("department")
        is_demo = bool(payload.get("demo", False))
        user_name = payload.get("name")
        user_email = payload.get("email")
        # Check active status in database if user exists
        try:
            user = db.get_user_by_id(user_id)
            if user:
                if user.get("active") != 1:
                    raise HTTPException(status_code=401, detail="User account is inactive or disabled")
                role = user.get("role") or role
                department = user.get("department") or department
                if user.get("name"):
                    user_name = user["name"]
                if user.get("email"):
                    user_email = user["email"]
                if user.get("is_demo") == 1:
                    is_demo = True
        except HTTPException:
            raise
        except Exception:
            pass

        return {
            "user_id": user_id,
            "role": (role or "").upper(),
            "department": department,
            "name": user_name or "Staff",
            "email": user_email or f"{user_id}@jansamadhan.local",
            "demo": is_demo
        }
    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def forbid_demo(current_user: dict = Depends(get_current_user)):
    if current_user.get("demo"):
        raise HTTPException(status_code=403, detail="Not available in demo mode")
    return current_user

def require_role(*allowed_roles: str):
    def role_dependency(current_user: dict = Depends(get_current_user)):
        user_role = (current_user.get("role") or "").upper()
        if user_role not in [r.upper() for r in allowed_roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_dependency

def get_admin_user(current_user: dict = Depends(get_current_user)):
    user_role = (current_user.get("role") or "").upper()
    if user_role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ── Models ────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str

class DemoLoginRequest(BaseModel):
    role: str

class SignupRequest(BaseModel):
    name: str = ""
    email: str = ""
    password: str = ""

class CreateStaffRequest(BaseModel):
    name: str
    email: str
    password: str
    department: str

class UpdateStaffRequest(BaseModel):
    active: Optional[int] = None
    department: Optional[str] = None
    new_password: Optional[str] = None

class QuestionRequest(BaseModel):
    question: str
    language: str = "auto"
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class AnswerResponse(BaseModel):
    answer: str
    source: str = "university documents"

class TicketRequest(BaseModel):
    user_id: str
    user_name: str
    session_id: str
    issue: str

class TicketStatusRequest(BaseModel):
    status: str

class FeedbackRequest(BaseModel):
    message_id: str
    session_id: str
    user_id: str
    rating: int  # 1 = thumbs up, 0 = thumbs down

# ── Auth ──────────────────────────────────────────────────────────
@router.post("/auth/signup", status_code=410)
def signup(req: Optional[dict] = None):
    raise HTTPException(
        status_code=410,
        detail="Public citizen registration is discontinued. Citizens can submit and track complaints directly without an account."
    )

@router.post("/auth/login")
def login(req: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_key = f"login:{req.email.strip().lower()}:{client_ip}"

    if db.too_many(rate_key, limit=5, window_seconds=600):
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Please try again after 10 minutes.",
            headers={"Retry-After": "600"}
        )

    user = db.login_user(req.email, req.password)
    if not user:
        db.record_event(rate_key)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    db.clear_events(rate_key)
    token = create_token(user["id"], user["role"], department=user.get("department"))
    return {
        "token": token,
        "role": user["role"],
        "name": user["name"],
        "department": user.get("department"),
        "expires_in": JWT_EXPIRE_HOURS * 3600
    }

@router.post("/auth/demo-login")
def demo_login(req: DemoLoginRequest, request: Request):
    demo_mode = os.getenv("DEMO_MODE", "0").strip()
    if demo_mode != "1":
        raise HTTPException(status_code=404, detail="Demo mode is disabled")

    role_norm = req.role.strip().lower()
    if role_norm not in ("official", "admin"):
        raise HTTPException(status_code=422, detail="Role must be 'official' or 'admin'")

    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_key = f"demo_login:{client_ip}"
    if db.too_many(rate_key, limit=20, window_seconds=3600):
        raise HTTPException(
            status_code=429,
            detail="Too many demo login requests. Please try again later.",
            headers={"Retry-After": "3600"}
        )
    db.record_event(rate_key)

    db.ensure_demo_accounts()

    if role_norm == "admin":
        user_email = "demo.admin@jansamadhan.demo"
    else:
        user_email = "demo.official@jansamadhan.demo"

    user = db.get_user_by_email(user_email)
    if not user:
        raise HTTPException(status_code=500, detail="Demo account could not be initialized")

    try:
        token_minutes = int(os.getenv("DEMO_TOKEN_MINUTES", "60"))
    except ValueError:
        token_minutes = 60
    expires_in_seconds = token_minutes * 60

    token = create_token(
        user_id=user["id"],
        role=user["role"],
        department=user.get("department"),
        expires_minutes=token_minutes,
        demo=True,
        name=user["name"],
        email=user["email"]
    )

    return {
        "token": token,
        "role": user["role"],
        "name": user["name"],
        "department": user.get("department"),
        "expires_in": expires_in_seconds,
        "demo": True
    }

# ── Staff Management (ADMIN only) ─────────────────────────────────
def _get_valid_departments() -> set:
    try:
        with open("data/departments.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item["department"] for item in data if "department" in item}
    except Exception:
        return set()

@router.post("/staff", dependencies=[Depends(forbid_demo)])
def create_staff(req: CreateStaffRequest, admin_user: dict = Depends(get_admin_user)):
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    valid_depts = _get_valid_departments()
    if req.department not in valid_depts:
        raise HTTPException(status_code=400, detail=f"Invalid department. Must be one of: {sorted(list(valid_depts))}")
    if db.get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = db.create_staff_user(req.name, req.email, req.password, req.department)
    return user

@router.get("/staff", dependencies=[Depends(forbid_demo)])
def list_staff(admin_user: dict = Depends(get_admin_user)):
    return db.list_staff_users()

@router.patch("/staff/{user_id}", dependencies=[Depends(forbid_demo)])
def update_staff(user_id: str, req: UpdateStaffRequest, admin_user: dict = Depends(get_admin_user)):
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Staff user not found")
    if req.department is not None:
        valid_depts = _get_valid_departments()
        if req.department not in valid_depts:
            raise HTTPException(status_code=400, detail=f"Invalid department: {req.department}")
    if req.new_password is not None:
        if len(req.new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    if req.active is not None and req.active not in (0, 1):
        raise HTTPException(status_code=400, detail="Active must be 0 or 1")
    updated = db.update_staff_user(user_id, active=req.active, department=req.department, password=req.new_password)
    return updated

# ── Chat Sessions ─────────────────────────────────────────────────
@router.post("/sessions")
def create_session(data: dict, current_user: dict = Depends(get_current_user)):
    session_id = db.create_session(current_user["user_id"], data.get("title", "New Chat"))
    return {"session_id": session_id}

@router.get("/sessions/{user_id}")
def get_sessions(user_id: str, current_user: dict = Depends(get_current_user)):
    return db.get_sessions(user_id)

@router.get("/messages/{session_id}")
def get_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    return db.get_messages(session_id)

class SaveMessageRequest(BaseModel):
    session_id: str
    user_id: str
    question: str
    answer: str

# ── Ask ───────────────────────────────────────────────────────────
@router.get("/health")
def health_check():
    return {"status": "ok", "message": "AI University Helpdesk is running"}

@router.post("/save-message")
def save_message(req: SaveMessageRequest, current_user: dict = Depends(get_current_user)):
    try:
        db.save_message(req.session_id, "user", req.question)
        db.save_message(req.session_id, "assistant", req.answer)
        sessions = db.get_sessions(req.user_id)
        for s in sessions:
            if s["id"] == req.session_id and s["title"] == "New Chat":
                db.update_session_title(req.session_id, req.question[:50])
    except Exception as e:
        print(f"Save message error: {e}")
    return {"status": "saved"}

@router.post("/ask-stream")
def ask_question_stream(request: QuestionRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials:
        try:
            jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not faiss_index_exists():
        raise HTTPException(status_code=400, detail="No documents uploaded yet.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        return StreamingResponse(get_answer_stream(request.question, request.language), media_type="text/plain")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.post("/ask-sync", response_model=AnswerResponse)
def ask_question_sync(request: QuestionRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials:
        try:
            jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not faiss_index_exists():
        raise HTTPException(status_code=400, detail="No documents uploaded yet. Please upload a university PDF first.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        start = time.time()
        answer = get_answer(request.question, request.language)
        response_time_ms = int((time.time() - start) * 1000)
        if request.session_id and request.user_id and request.user_id != "guest":
            try:
                db.save_message(request.session_id, "user", request.question)
                db.save_message(request.session_id, "assistant", answer)
                db.log_query(request.user_id, request.session_id, request.question, request.language, response_time_ms)
                sessions = db.get_sessions(request.user_id)
                for s in sessions:
                    if s["id"] == request.session_id and s["title"] == "New Chat":
                        db.update_session_title(request.session_id, request.question[:50])
            except Exception as db_err:
                print(f"DB save error (non-fatal): {db_err}")
        return AnswerResponse(answer=answer)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

# ── Tickets ───────────────────────────────────────────────────────
@router.post("/tickets")
def create_ticket(req: TicketRequest, current_user: dict = Depends(get_current_user)):
    ticket_id = db.create_ticket(req.user_id, req.user_name, req.session_id, req.issue)
    return {"ticket_id": ticket_id}

@router.get("/tickets")
def get_tickets(current_user: dict = Depends(get_admin_user)):
    return db.get_all_tickets()

@router.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, req: TicketStatusRequest, current_user: dict = Depends(get_admin_user)):
    db.update_ticket_status(ticket_id, req.status)
    return {"message": "Updated"}

# ── Upload & Documents ────────────────────────────────────────────
@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...), current_user: dict = Depends(get_admin_user)):
    ensure_folders()
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    save_path = os.path.join("data", file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        chunks = ingest_pdf(save_path)
        db.log_document_upload(file.filename, current_user["user_id"], chunks)
        return {"message": f"Uploaded '{file.filename}'", "chunks_created": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.get("/documents")
def list_documents(current_user: dict = Depends(get_current_user)):
    pdfs = get_all_pdfs()
    return {"total": len(pdfs), "documents": [os.path.basename(p) for p in pdfs]}

@router.get("/document-logs")
def get_document_logs(current_user: dict = Depends(get_admin_user)):
    return db.get_document_uploads()

@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    if req.rating not in (0, 1):
        raise HTTPException(status_code=400, detail="Rating must be 0 or 1")
    db.save_feedback(req.message_id, req.session_id, req.user_id, req.rating)
    return {"status": "saved"}

@router.get("/stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    return db.get_stats()
