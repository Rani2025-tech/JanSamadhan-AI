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
    search: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)

    if user_id:
        query = query.filter(Complaint.user_id == user_id)
    if status and status != "All":
        query = query.filter(Complaint.status.ilike(status))
    if department and department != "All":
        query = query.filter(Complaint.department.ilike(f"%{department}%"))
    if district and district != "All":
        query = query.filter(Complaint.district.ilike(f"%{district}%"))
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

    # Order by ID / creation descending
    complaints = query.order_by(desc(Complaint.created_at)).offset(offset).limit(limit).all()
    return [format_complaint_response(c) for c in complaints]

@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id.ilike(complaint_id)).first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")
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
def create_complaint(req: ComplaintCreate, db: Session = Depends(get_db)):
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
        district=req.district or ai_result.location.get("district", "Ganjam"),
        area=req.area or ai_result.location.get("area", "Central Area"),
        pincode=req.pincode,
        lat=req.lat or 20.2961,
        lng=req.lng or 85.8245,
        submitted_date=sub_date,
        expected_date=exp_date,
        days_remaining=sla_days,
        user_id="USR-8921",
        citizen_phone="9876543210",
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

    # Notification for citizen
    notif = Notification(
        id=f"NOTIF-{int(now.timestamp() * 1000)}",
        user_id="USR-8921",
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

@router.put("/{complaint_id}/status", response_model=ComplaintResponse)
def update_complaint_status(
    complaint_id: str,
    update_data: ComplaintStatusUpdate,
    db: Session = Depends(get_db)
):
    comp = db.query(Complaint).filter(Complaint.id.ilike(complaint_id)).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

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

    # Notification
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
    db: Session = Depends(get_db)
):
    comp = db.query(Complaint).filter(Complaint.id.ilike(complaint_id)).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    admin_id = "ADM-EMP-001"
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
    db: Session = Depends(get_db)
):
    comp = db.query(Complaint).filter(Complaint.id.ilike(complaint_id)).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    comp.feedback_rating = fb.rating
    comp.feedback_comment = fb.comment

    db.commit()
    db.refresh(comp)
    return format_complaint_response(comp)

