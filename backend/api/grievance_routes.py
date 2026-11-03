import os
import time
import json
import secrets
import bcrypt
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from jose import jwt, JWTError

from backend.api.routes import require_role, get_admin_user, security, JWT_SECRET, JWT_ALGORITHM, forbid_demo
from backend.core.chatbot import handle_message
from backend.db import database as db
from backend.db.grievances import (
    get_grievance,
    list_grievances,
    update_status,
    add_feedback,
    list_clusters,
    get_stats,
    reset_pin,
    run_escalation,
    reroute_grievance,
    flag_misrouted,
    get_audit_log
)

grievance_router = APIRouter()

VALID_STATUSES = {"Submitted", "Assigned", "In Progress", "Resolved", "Reopened"}

ALLOWED_TRANSITIONS = {
    "Submitted": {"Assigned"},
    "Assigned": {"In Progress"},
    "In Progress": {"Resolved"},
    "Reopened": {"Assigned", "In Progress"},
    "Resolved": set()
}

_public_stats_cache = {"data": None, "timestamp": 0.0}

def get_client_ip(request: Request) -> str:
    """Extract client IP, taking first X-Forwarded-For value only if TRUST_PROXY=1."""
    if os.getenv("TRUST_PROXY") == "1":
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000, description="User grievance message or query")
    state: Optional[Dict[str, Any]] = None

class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Citizen rating from 1 to 5")
    comment: Optional[str] = Field(default="", max_length=2000)

class UpdateStatusRequest(BaseModel):
    status: str = Field(..., max_length=50)
    note: Optional[str] = Field(default="", max_length=2000)

class PrivateViewRequest(BaseModel):
    pin: str = Field(..., max_length=50, description="6-digit tracking PIN")

class RoutingRequest(BaseModel):
    department: str = Field(..., max_length=200)
    category: str = Field(..., max_length=200)
    note: str = Field(..., min_length=5, max_length=2000)

class FlagMisroutedRequest(BaseModel):
    note: str = Field(..., min_length=5, max_length=2000)

def get_optional_user(credentials=Depends(security)) -> Optional[dict]:
    """Helper to detect if caller has valid token without forcing auth."""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": payload.get("sub"),
            "role": payload.get("role"),
            "department": payload.get("department"),
            "demo": payload.get("demo", False),
            "name": payload.get("name")
        }
    except (JWTError, Exception):
        return None

# ── Public / Guest Endpoints ─────────────────────────────────────

@grievance_router.post("/chat")
def chat_endpoint(req: ChatRequest, request: Request):
    """Guest conversational grievance intake with IP rate limits."""
    client_ip = get_client_ip(request)
    chat_per_min = int(os.getenv("CHAT_RATE_PER_MIN", "15"))

    if db.too_many(f"chat_rate_min:{client_ip}", limit=chat_per_min, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Too many chat requests. Please wait a moment before trying again.",
            headers={"Retry-After": "60"}
        )
    if db.too_many(f"chat_rate_day:{client_ip}", limit=300, window_seconds=86400):
        raise HTTPException(
            status_code=429,
            detail="Daily chat limit reached. Please try again tomorrow.",
            headers={"Retry-After": "86400"}
        )

    db.record_event(f"chat_rate_min:{client_ip}")
    db.record_event(f"chat_rate_day:{client_ip}")

    reply_text, new_state, meta = handle_message(req.message, req.state)
    return {
        "reply": reply_text,
        "state": new_state,
        "meta": meta
    }

@grievance_router.get("/public-stats")
def get_public_stats_endpoint(request: Request):
    """Aggregated public metrics with 30s cache and 60 req/min rate limit."""
    client_ip = get_client_ip(request)
    if db.too_many(f"public_stats:{client_ip}", limit=60, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Too many public stats requests. Please wait a moment.",
            headers={"Retry-After": "60"}
        )
    db.record_event(f"public_stats:{client_ip}")

    now_ts = time.time()
    if _public_stats_cache["data"] is not None and (now_ts - _public_stats_cache["timestamp"]) < 30.0:
        return _public_stats_cache["data"]

    run_escalation()
    full_stats = get_stats()
    by_status = full_stats.get("by_status", {})
    total = sum(by_status.values())
    resolved = by_status.get("Resolved", 0)
    open_count = total - resolved

    avg_hours = full_stats.get("avg_resolution_hours")
    if avg_hours == 0.0 and resolved == 0:
        avg_hours = None

    overdue_count = full_stats.get("overdue_count", 0)
    demo_flag = os.getenv("DEMO_DATA_LABEL") == "1"

    data = {
        "total": total,
        "resolved": resolved,
        "open": open_count,
        "avg_resolution_hours": avg_hours,
        "overdue_count": overdue_count,
        "by_status": by_status,
        "demo": demo_flag
    }
    _public_stats_cache["data"] = data
    _public_stats_cache["timestamp"] = now_ts
    return data

# ── Staff / Admin Endpoints ──────────────────────────────────────

@grievance_router.get("/admin/stats")
def get_grievance_stats(staff_user: dict = Depends(require_role("ADMIN", "DEPARTMENT_OFFICIAL"))):
    """Summary metrics, top hotspots, cluster statistics, and resolution times with department scoping."""
    run_escalation()
    stats = get_stats()
    if staff_user.get("role") == "DEPARTMENT_OFFICIAL" and staff_user.get("department"):
        dept = staff_user["department"]
        stats["by_department"] = {dept: stats.get("by_department", {}).get(dept, 0)}
        if "avg_resolution_by_dept" in stats:
            stats["avg_resolution_by_dept"] = {dept: stats.get("avg_resolution_by_dept", {}).get(dept, 0.0)}
        if "overdue_by_dept" in stats:
            stats["overdue_by_dept"] = {dept: stats.get("overdue_by_dept", {}).get(dept, 0)}
    return stats

@grievance_router.get("/admin/clusters")
def get_clusters_list(staff_user: dict = Depends(require_role("ADMIN", "DEPARTMENT_OFFICIAL"))):
    """List of active duplicate complaint clusters with department scoping."""
    run_escalation()
    clusters = list_clusters()
    if staff_user.get("role") == "DEPARTMENT_OFFICIAL" and staff_user.get("department"):
        dept = staff_user["department"]
        filtered = []
        for cl in clusters:
            rep_id = cl.get("representative_ticket_id")
            if rep_id:
                grv = get_grievance(rep_id)
                if grv and grv.get("department") == dept:
                    filtered.append(cl)
            else:
                filtered.append(cl)
        return filtered
    return clusters

@grievance_router.get("/")
def list_all_grievances(
    status: Optional[str] = None,
    department: Optional[str] = None,
    priority: Optional[str] = None,
    language: Optional[str] = None,
    area: Optional[str] = None,
    overdue: Optional[bool] = None,
    needs_review: Optional[bool] = None,
    limit: int = Query(default=100, ge=1, le=500),
    staff_user: dict = Depends(require_role("ADMIN", "DEPARTMENT_OFFICIAL"))
):
    """Filtered listing of grievances scoped by department for officials."""
    run_escalation()
    effective_dept = department
    if staff_user.get("role") == "DEPARTMENT_OFFICIAL":
        effective_dept = staff_user.get("department")

    return list_grievances(
        status=status,
        department=effective_dept,
        priority=priority,
        language=language,
        area=area,
        overdue=overdue,
        needs_review=needs_review,
        limit=limit
    )

@grievance_router.patch("/{ticket_id}/status")
def patch_grievance_status(
    ticket_id: str,
    req: UpdateStatusRequest,
    staff_user: dict = Depends(require_role("ADMIN", "DEPARTMENT_OFFICIAL"))
):
    """Staff status update with timeline note, transition rules, and department scoping."""
    record = get_grievance(ticket_id)
    if not record:
        raise HTTPException(status_code=404, detail="Grievance ticket not found")

    if staff_user.get("role") == "DEPARTMENT_OFFICIAL":
        if staff_user.get("department") != record.get("department"):
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: You are assigned to '{staff_user.get('department')}' and cannot update tickets for '{record.get('department')}'"
            )

    status_clean = req.status.strip()
    matched_status = next((s for s in VALID_STATUSES if s.lower() == status_clean.lower()), None)
    if not matched_status:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {sorted(list(VALID_STATUSES))}")

    current_status = record.get("status", "Submitted")
    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if matched_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from '{current_status}' to '{matched_status}'. Allowed next transitions: {sorted(list(allowed))}"
        )

    if matched_status == "Resolved":
        if not req.note or len(req.note.strip()) < 5:
            raise HTTPException(
                status_code=400,
                detail="A resolution note of at least 5 characters is required when resolving a grievance."
            )

    if staff_user.get("demo"):
        actor_name = staff_user.get("name") or "Demo User (demo)"
    else:
        actor_name = f"{staff_user.get('name', 'Staff')} <{staff_user.get('email', staff_user.get('user_id', 'staff'))}>"
    updated = update_status(ticket_id, matched_status, note=req.note or "", actor=actor_name)
    if not updated:
        raise HTTPException(status_code=404, detail="Grievance ticket not found")

    return {
        "message": "Status updated successfully",
        "ticket_id": ticket_id,
        "status": matched_status
    }

@grievance_router.patch("/{ticket_id}/routing")
def patch_grievance_routing(
    ticket_id: str,
    req: RoutingRequest,
    admin_user: dict = Depends(get_admin_user)
):
    """Admin-only manual routing of grievance to correct category & department."""
    if not req.note or len(req.note.strip()) < 5:
        raise HTTPException(status_code=400, detail="Note must be at least 5 characters.")

    dept_clean = req.department.strip()
    cat_clean = req.category.strip()

    if cat_clean.lower() == "other / needs review" or dept_clean.lower() == "general administration / grievance cell":
        raise HTTPException(status_code=400, detail="'Other / Needs Review' is not allowed as a routing target.")

    dept_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "departments.json")
    valid_pairs = []
    if os.path.exists(dept_file):
        try:
            with open(dept_file, "r", encoding="utf-8") as f:
                depts_data = json.load(f)
                valid_pairs = [(item.get("category", "").lower(), item.get("department", "").lower(), item.get("category"), item.get("department")) for item in depts_data]
        except Exception:
            pass

    matched = next((p for p in valid_pairs if p[0] == cat_clean.lower() and p[1] == dept_clean.lower()), None)
    if not matched:
        raise HTTPException(status_code=400, detail="Department and category do not match data/departments.json.")

    target_cat = matched[2]
    target_dept = matched[3]

    record = get_grievance(ticket_id)
    if not record:
        raise HTTPException(status_code=404, detail="Grievance ticket not found")

    if admin_user.get("demo"):
        actor_name = admin_user.get("name") or "Demo Administrator (demo)"
    else:
        actor_name = f"{admin_user.get('name', 'Admin')} <{admin_user.get('email', admin_user.get('user_id', 'admin'))}>"
    success = reroute_grievance(ticket_id, target_dept, target_cat, req.note.strip(), actor=actor_name)
    if not success:
        raise HTTPException(status_code=404, detail="Grievance ticket not found")

    return {
        "ticket_id": ticket_id,
        "department": target_dept,
        "category": target_cat,
        "needs_review": 0,
        "routing_reason": "Manually routed by admin",
        "message": "Grievance re-routed successfully."
    }

@grievance_router.post("/{ticket_id}/flag-misrouted")
def flag_ticket_misrouted(
    ticket_id: str,
    req: FlagMisroutedRequest,
    staff_user: dict = Depends(require_role("ADMIN", "DEPARTMENT_OFFICIAL"))
):
    """Flags a grievance as misrouted for administrative re-routing."""
    if not req.note or len(req.note.strip()) < 5:
        raise HTTPException(status_code=400, detail="Note must be at least 5 characters.")

    record = get_grievance(ticket_id)
    if not record:
        raise HTTPException(status_code=404, detail="Grievance ticket not found")

    if staff_user.get("role") == "DEPARTMENT_OFFICIAL":
        if staff_user.get("department") != record.get("department"):
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: You are assigned to '{staff_user.get('department')}' and cannot flag tickets for '{record.get('department')}'"
            )

    if record.get("status") == "Resolved":
        raise HTTPException(status_code=400, detail="Cannot flag a resolved ticket as misrouted.")

    if staff_user.get("demo"):
        actor_name = staff_user.get("name") or "Demo User (demo)"
    else:
        actor_name = f"{staff_user.get('name', 'Staff')} <{staff_user.get('email', staff_user.get('user_id', 'staff'))}>"
    success = flag_misrouted(ticket_id, req.note.strip(), actor=actor_name)
    if not success:
        raise HTTPException(status_code=404, detail="Grievance ticket not found")

    return {
        "ticket_id": ticket_id,
        "needs_review": 1,
        "message": "Ticket flagged as misrouted successfully."
    }

@grievance_router.get("/admin/audit")
def get_audit_trail(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    admin_user: dict = Depends(get_admin_user)
):
    """Admin-only: chronological audit history entries joined with ticket and department."""
    return get_audit_log(limit=limit, offset=offset)

# ── Private View & Admin PIN Reset ───────────────────────────────

@grievance_router.post("/{ticket_id}/private")
def get_ticket_private_view(ticket_id: str, req: PrivateViewRequest, request: Request):
    """
    Private ticket details unlocked with citizen tracking PIN.
    Rate limited: 5 wrong attempts per ticket + client IP per 10 minutes -> 429.
    Wrong PIN or ticket without PIN returns generic 403.
    """
    client_ip = get_client_ip(request)
    rate_key = f"pin_attempt:{ticket_id}:{client_ip}"

    if db.too_many(rate_key, limit=5, window_seconds=600):
        raise HTTPException(
            status_code=429,
            detail="Too many invalid PIN attempts for this ticket. Please try again after 10 minutes.",
            headers={"Retry-After": "600"}
        )

    record = get_grievance(ticket_id)
    if not record:
        raise HTTPException(status_code=404, detail="Grievance ticket not found")

    pin_hash = record.get("pin_hash")
    if not pin_hash:
        db.record_event(rate_key)
        raise HTTPException(status_code=403, detail="Access denied. Invalid PIN or ticket cannot be viewed privately.")

    try:
        valid_pin = bcrypt.checkpw(req.pin.strip().encode("utf-8"), pin_hash.encode("utf-8"))
    except Exception:
        valid_pin = False

    if not valid_pin:
        db.record_event(rate_key)
        raise HTTPException(status_code=403, detail="Access denied. Invalid PIN or ticket cannot be viewed privately.")

    db.clear_events(rate_key)
    res = dict(record)
    res.pop("pin_hash", None)
    return res

@grievance_router.post("/{ticket_id}/reset-pin", dependencies=[Depends(forbid_demo)])
def reset_ticket_pin_endpoint(ticket_id: str, admin_user: dict = Depends(get_admin_user)):
    """Admin-only PIN reset. Generates new PIN, stores hash, logs timeline event."""
    record = get_grievance(ticket_id)
    if not record:
        raise HTTPException(status_code=404, detail="Grievance ticket not found")

    new_pin = f"{secrets.randbelow(900000) + 100000}"
    actor_name = f"{admin_user.get('name', 'Admin')} <{admin_user.get('email', admin_user.get('user_id', 'admin'))}>"
    reset_pin(ticket_id, new_pin, actor=actor_name)
    return {
        "ticket_id": ticket_id,
        "pin": new_pin,
        "message": "PIN reset successfully. Store this PIN safely as it cannot be retrieved again."
    }

# ── Ticket Details & Feedback ────────────────────────────────────

@grievance_router.get("/{ticket_id}")
def get_ticket_details(ticket_id: str, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    """
    Ticket details lookup.
    Staff (ADMIN or official assigned to this ticket's department) get full record with real actors.
    Public callers (unauthenticated or officials from another department) get masked view:
    ONLY ticket_id, status, department, category, priority, created_at, updated_at, sla_due_at,
    overdue, report_count, and history with masked actors.
    """
    client_ip = get_client_ip(request)
    if db.too_many(f"ticket_view:{client_ip}", limit=60, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Too many ticket view requests. Please wait a moment.",
            headers={"Retry-After": "60"}
        )
    db.record_event(f"ticket_view:{client_ip}")

    record = get_grievance(ticket_id)
    if not record:
        raise HTTPException(status_code=404, detail="Grievance ticket not found")

    is_staff = False
    if user:
        role = str(user.get("role", "")).upper()
        if role == "ADMIN":
            is_staff = True
        elif role == "DEPARTMENT_OFFICIAL" and user.get("department") == record.get("department"):
            is_staff = True

    if is_staff:
        res = dict(record)
        res.pop("pin_hash", None)
        return res

    # Public caller view: ONLY public fields, masked history, no private data
    masked_history = []
    for h in record.get("history", []):
        raw_actor = str(h.get("actor", "")).strip()
        masked_actor = "System" if raw_actor.lower() in ("system", "automated") else "Department staff"
        masked_history.append({
            "status": h.get("status"),
            "note": h.get("note"),
            "created_at": h.get("created_at"),
            "actor": masked_actor
        })

    return {
        "ticket_id": record.get("ticket_id"),
        "status": record.get("status"),
        "department": record.get("department"),
        "category": record.get("category"),
        "priority": record.get("priority"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
        "sla_due_at": record.get("sla_due_at"),
        "overdue": bool(record.get("overdue", False)),
        "report_count": record.get("report_count") or record.get("cluster_report_count", 1),
        "cluster_report_count": record.get("report_count") or record.get("cluster_report_count", 1),
        "history": masked_history
    }

@grievance_router.post("/{ticket_id}/feedback")
def submit_grievance_feedback(ticket_id: str, req: FeedbackRequest):
    """
    Citizen satisfaction feedback.
    If rating is <= 2 and grievance is Resolved, automatically reopens the ticket.
    """
    grv = get_grievance(ticket_id)
    if not grv:
        raise HTTPException(status_code=404, detail="Grievance ticket not found")

    add_feedback(ticket_id, req.rating, req.comment or "")

    reopened = False
    if grv.get("status") == "Resolved" and req.rating <= 2:
        note_text = f"Reopened automatically due to citizen low rating ({req.rating}/5)"
        if req.comment:
            note_text += f": {req.comment}"
        update_status(ticket_id, "Reopened", note=note_text, actor="Citizen")
        reopened = True

    return {
        "message": "Feedback submitted successfully",
        "ticket_id": ticket_id,
        "reopened": reopened
    }

