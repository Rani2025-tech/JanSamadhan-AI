import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.database import get_db
from app.models import Complaint, StatusHistory, Notification, User, AdminCorrection
from app.config import settings
from app.schemas import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatusUpdate,
    ComplaintFeedback,
    ComplaintAdminUpdate,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    AssignedOfficerSchema,
    StatusHistoryItemSchema
)
from app.routes.auth import get_current_user, get_current_user_required, require_admin
from ai import extract, check_duplicate_complaint, translate

router = APIRouter(prefix="/complaints", tags=["Complaints"])

def format_complaint_response(c: Complaint) -> ComplaintResponse:
    # Build assigned officer object if present
    officer = None
    if c.assigned_officer_name:
        officer = AssignedOfficerSchema(
            name=c.assigned_officer_name,
            designation=c.assigned_officer_designation or "Nodal Officer",
            department=c.assigned_officer_dept or c.department,
            phone=c.assigned_officer_phone
        )

    # Build status history
    history = [
        StatusHistoryItemSchema(
            status=h.status,
            date=h.date,
            time=h.time,
            officer=h.officer,
            note=h.note,
            completed=h.completed,
            current=h.current
        )
        for h in c.status_history
    ]

    return ComplaintResponse(
        id=c.id,
        title=c.title,
        description=c.description,
        category=c.category,
        sub_category=c.sub_category,
        department=c.department,
        urgency=c.urgency,
        language=c.language,
        status=c.status,
        state=c.state or "Odisha",
        location={
            "district": c.district,
            "area": c.area,
            "pincode": c.pincode,
            "coordinates": [c.lat or 20.2961, c.lng or 85.8245]
        },
        submittedDate=c.submitted_date,
        expectedDate=c.expected_date,
        daysRemaining=c.days_remaining,
        assignedOfficer=officer,
        statusHistory=history,
        feedback={
            "rating": c.feedback_rating,
            "comment": c.feedback_comment
        } if c.feedback_rating else None,
        citizenPhone=c.citizen_phone,
        ai_confidence=c.ai_confidence,
        needs_human_review=bool(c.needs_human_review or (c.ai_confidence is not None and c.ai_confidence < settings.AI_CONFIDENCE_THRESHOLD)),
        translated_text_en=c.translated_text_en,
        sentiment=c.sentiment,
        ai_summary=c.ai_summary,
        duplicate_of_id=c.duplicate_of_id
    )

@router.get("", response_model=List[ComplaintResponse])
def get_complaints(
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)

    # 1. Enforce Role-Based Scoping
    if current_user.role == "admin":
        # Admin can view all or filter by user_id
        if user_id:
            query = query.filter(Complaint.user_id == user_id)
    else:
        # Citizen or Guest can ONLY view their own records (ignore user_id param)
        ownership_clauses = [Complaint.user_id == current_user.id]
        if current_user.phone:
            ownership_clauses.append(Complaint.citizen_phone == current_user.phone)
        query = query.filter(or_(*ownership_clauses))

    if status and status != "All":
        query = query.filter(Complaint.status.ilike(status))
    if department and department != "All":
        query = query.filter(Complaint.department.ilike(f"%{department}%"))
    if district and district != "All":
        query = query.filter(Complaint.district.ilike(f"%{district}%"))
    if state and state != "All":
        query = query.filter(Complaint.state.ilike(f"%{state}%"))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Complaint.id.ilike(search_pattern),
                Complaint.title.ilike(search_pattern),
                Complaint.description.ilike(search_pattern),
                Complaint.district.ilike(search_pattern),
                Complaint.area.ilike(search_pattern),
                Complaint.department.ilike(search_pattern)
            )
        )

    complaints = query.order_by(desc(Complaint.created_at)).offset(offset).limit(limit).all()
    return [format_complaint_response(c) for c in complaints]

@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    comp = db.query(Complaint).filter(Complaint.id.ilike(complaint_id)).first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")

    # Access control: admin has full access
    if current_user and current_user.role == "admin":
        return format_complaint_response(comp)

    # Citizen must be the owner
    is_owner = False
    if current_user:
        if comp.user_id and comp.user_id == current_user.id:
            is_owner = True
        elif current_user.phone and comp.citizen_phone == current_user.phone:
            is_owner = True

    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to view this grievance record."
        )

    return format_complaint_response(comp)

@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
def check_duplicate(req: DuplicateCheckRequest, db: Session = Depends(get_db)):
    result = check_duplicate_complaint(
        new_text=req.text,
        district=req.district,
        category=req.category,
        db=db
    )
    return DuplicateCheckResponse(**result)

@router.post("", response_model=ComplaintResponse)
def create_complaint(
    req: ComplaintCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Run AI extraction to enrich metadata
    ai_result = extract(f"{req.title}. {req.description}")

    # Generate sequential GRV-ID
    last_comp = db.query(Complaint).order_by(desc(Complaint.id)).first()
    if last_comp and last_comp.id.startswith("GRV-"):
        try:
            num = int(last_comp.id.split("-")[1])
            new_id = f"GRV-{num + 1:04d}"
        except Exception:
            new_id = f"GRV-{int(datetime.datetime.utcnow().timestamp()) % 10000:04d}"
    else:
        new_id = "GRV-1061"

    now = datetime.datetime.utcnow()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    sub_date = f"{now.day:02d} {months[now.month-1]} 2026"
    
    sla_days = 1 if req.urgency == "Critical" else 3 if req.urgency == "High" else 7
    exp_time = now + datetime.timedelta(days=sla_days)
    exp_date = f"{exp_time.day:02d} {months[exp_time.month-1]} 2026"

    # Duplicate detection check
    dup_check = check_duplicate_complaint(
        new_text=req.description,
        district=req.district,
        category=req.category,
        db=db,
        threshold=0.60
    )
    dup_id = dup_check.get("matched_complaint_id") if dup_check.get("is_duplicate") else None

    # Owner details strictly from current logged in user
    actual_user_id = current_user.id if current_user else req.user_id
    actual_phone = (current_user.phone if current_user and current_user.phone else req.citizen_phone)

    new_comp = Complaint(
        id=new_id,
        title=req.title,
        description=req.description,
        category=req.category or ai_result.category,
        sub_category=ai_result.sub_category,
        department=req.department or ai_result.department,
        urgency=req.urgency or ai_result.urgency,
        language=req.language or ai_result.language,
        status="Submitted",
        state=req.state or ai_result.location.get("state", "Odisha"),
        district=req.district or ai_result.location.get("district", "Khurda"),
        area=req.area or ai_result.location.get("area", "Central Area"),
        pincode=req.pincode,
        lat=req.lat or 20.2961,
        lng=req.lng or 85.8245,
        submitted_date=sub_date,
        expected_date=exp_date,
        days_remaining=sla_days,
        user_id=actual_user_id,
        citizen_phone=actual_phone,
        assigned_officer_name=f"Duty Desk ({req.department})",
        assigned_officer_designation="Intake Desk Officer",
        assigned_officer_dept=req.department,
        ai_confidence=ai_result.confidence,
        needs_human_review=bool(ai_result.confidence < settings.AI_CONFIDENCE_THRESHOLD),
        translated_text_en=ai_result.translated_text_en,
        sentiment=ai_result.sentiment,
        ai_summary=ai_result.summary,
        duplicate_of_id=dup_id,
        source=req.source or "web_form"
    )

    db.add(new_comp)

    # Initial Submitted Status History
    history_entry = StatusHistory(
        complaint_id=new_id,
        status="Submitted",
        date=sub_date,
        time=now.strftime("%I:%M %p"),
        officer="System Intake Desk",
        note=f"Grievance recorded and auto-classified to {req.department}.",
        completed=True,
        current=True
    )
    db.add(history_entry)

    # Notification for citizen (scoped to their user_id)
    if actual_user_id and not actual_user_id.startswith("guest_"):
        notif = Notification(
            id=f"NOTIF-{int(now.timestamp() * 1000)}",
            user_id=actual_user_id,
            title=f"Grievance Registered: {new_id}",
            message=f"Your complaint regarding '{req.title[:45]}...' has been registered with {req.department}.",
            type="update",
            read=False,
            related_grv_id=new_id,
            timestamp_str=f"{sub_date} • {now.strftime('%I:%M %p')}"
        )
        db.add(notif)

    db.commit()
    db.refresh(new_comp)
    return format_complaint_response(new_comp)

ALLOWED_TRANSITIONS = {
    "Submitted": ["Assigned"],
    "Assigned": ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved": ["In Progress"],  # Reopen with remark
}
VALID_STATUSES = {"Submitted", "Assigned", "In Progress", "Resolved"}

@router.put("/{complaint_id}/status", response_model=ComplaintResponse)
def update_complaint_status(
    complaint_id: str,
    update_data: ComplaintStatusUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    comp = db.query(Complaint).filter(Complaint.id.ilike(complaint_id)).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # State Machine Validation
    if update_data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{update_data.status}'. Must be one of: {sorted(list(VALID_STATUSES))}"
        )

    allowed = ALLOWED_TRANSITIONS.get(comp.status, [])
    if update_data.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{comp.status}' to '{update_data.status}'. Allowed transitions: {allowed}"
        )

    if comp.status == "Resolved" and update_data.status == "In Progress":
        if not update_data.officer_note or not update_data.officer_note.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reopening a resolved complaint requires an officer remark."
            )

    now = datetime.datetime.utcnow()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    date_str = f"{now.day:02d} {months[now.month-1]} 2026"
    time_str = now.strftime("%I:%M %p")

    # Mark existing status histories as not current
    for h in comp.status_history:
        h.current = False

    comp.status = update_data.status
    if update_data.status == "Resolved":
        comp.days_remaining = 0

    # Translate officer remark to citizen language
    citizen_lang = comp.language or "English"
    translated_note = update_data.officer_note
    if citizen_lang.lower() not in ["english", "en"]:
        try:
            translated_note = translate(update_data.officer_note, citizen_lang)
        except Exception:
            translated_note = update_data.officer_note

    # Add new status history entry
    new_hist = StatusHistory(
        complaint_id=comp.id,
        status=update_data.status,
        date=date_str,
        time=time_str,
        officer=update_data.officer_name or comp.assigned_officer_name or "Authorized Officer",
        note=translated_note,
        completed=True,
        current=True
    )
    db.add(new_hist)

    # Scoped Notification for the owner
    if comp.user_id and not comp.user_id.startswith("guest_"):
        notif = Notification(
            id=f"NOTIF-{int(now.timestamp() * 1000)}",
            user_id=comp.user_id,
            title=f"Status Update: {comp.id}",
            message=f"Status updated to '{update_data.status}'. Remark: {translated_note}",
            type="update",
            read=False,
            related_grv_id=comp.id,
            timestamp_str=f"{date_str} • {time_str}"
        )
        db.add(notif)

    db.commit()
    db.refresh(comp)
    return format_complaint_response(comp)

@router.patch("/{complaint_id}/admin-update", response_model=ComplaintResponse)
def admin_update_complaint(
    complaint_id: str,
    update_data: ComplaintAdminUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    comp = db.query(Complaint).filter(Complaint.id.ilike(complaint_id)).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    admin_id = admin_user.employee_id or admin_user.id or "ADMIN"
    # Track category correction
    if update_data.category and update_data.category != comp.category:
        db.add(AdminCorrection(
            complaint_id=comp.id,
            admin_id=admin_id,
            field_name="category",
            original_value=comp.category,
            corrected_value=update_data.category
        ))
        comp.category = update_data.category

    # Track department correction
    if update_data.department and update_data.department != comp.department:
        db.add(AdminCorrection(
            complaint_id=comp.id,
            admin_id=admin_id,
            field_name="department",
            original_value=comp.department,
            corrected_value=update_data.department
        ))
        comp.department = update_data.department

    if update_data.urgency:
        comp.urgency = update_data.urgency
    if update_data.status:
        comp.status = update_data.status

    comp.needs_human_review = False
    db.commit()
    db.refresh(comp)
    return format_complaint_response(comp)

@router.post("/{complaint_id}/feedback", response_model=ComplaintResponse)
def submit_complaint_feedback(
    complaint_id: str,
    fb: ComplaintFeedback,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    comp = db.query(Complaint).filter(Complaint.id.ilike(complaint_id)).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # 1. Rating must be 1 to 5
    if fb.rating < 1 or fb.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be an integer between 1 and 5."
        )

    # 2. Only owner can submit feedback
    is_owner = (comp.user_id == current_user.id) or (current_user.phone and comp.citizen_phone == current_user.phone)
    if not is_owner and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only submit feedback for your own complaint."
        )

    # 3. Only resolved complaints can accept feedback
    if comp.status != "Resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be submitted once the grievance is Resolved."
        )

    # 4. Only once (409 Conflict on repeat)
    if comp.feedback_rating is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback has already been submitted for this grievance."
        )

    comp.feedback_rating = fb.rating
    comp.feedback_comment = fb.comment

    db.commit()
    db.refresh(comp)
    return format_complaint_response(comp)
