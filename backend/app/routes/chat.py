import json
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChatSession, ChatMessage, Complaint, StatusHistory, Notification
from app.schemas import ChatInteractionRequest, ChatInteractionResponse, ComplaintResponse
from app.routes.complaints import format_complaint_response
from ai import slot_filling_assistant

router = APIRouter(prefix="/chat", tags=["AI Chat"])

@router.post("/message", response_model=ChatInteractionResponse)
def handle_chat_message(req: ChatInteractionRequest, db: Session = Depends(get_db)):
    # 1. Retrieve or initialize chat session
    session_id = req.session_id or f"CHAT-{uuid.uuid4().hex[:12]}"
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not chat_session:
        chat_session = ChatSession(
            id=session_id,
            user_id=req.user_id or "USR-8921",
            language=req.language or "or",
            state="collecting",
            slots_json="{}"
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)

    existing_slots = {}
    try:
        existing_slots = json.loads(chat_session.slots_json)
    except Exception:
        existing_slots = {}

    # 2. Record user message in DB
    user_msg_record = ChatMessage(
        session_id=session_id,
        sender="user",
        text=req.message,
        metadata_json="{}"
    )
    db.add(user_msg_record)
    db.commit()

    # 3. Process turn through SlotFillingAssistant
    (
        reply_text,
        next_state,
        updated_slots,
        ready_to_file,
        confirmation_card,
        detected_faq,
        suggest_human_agent
    ) = slot_filling_assistant.process_turn(
        user_message=req.message,
        current_state=chat_session.state,
        existing_slots=existing_slots,
        language=req.language or chat_session.language or "or"
    )

    # 4. Update session state
    chat_session.state = next_state
    chat_session.slots_json = json.dumps(updated_slots)

    filed_complaint_obj = None

    # 5. If confirmed and ready to file, auto-create Complaint in DB!
    if ready_to_file:
        now = datetime.datetime.utcnow()
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        sub_date = f"{now.day:02d} {months[now.month-1]} 2026"
        
        urgency = updated_slots.get("urgency", "Medium")
        sla_days = 1 if urgency == "Critical" else 3 if urgency == "High" else 7
        exp_time = now + datetime.timedelta(days=sla_days)
        exp_date = f"{exp_time.day:02d} {months[exp_time.month-1]} 2026"

        last_comp = db.query(Complaint).order_by(Complaint.id.desc()).first()
        try:
            num = int(last_comp.id.split("-")[1])
            new_id = f"GRV-{num + 1:04d}"
        except Exception:
            new_id = f"GRV-{int(now.timestamp()) % 10000:04d}"

        new_comp = Complaint(
            id=new_id,
            title=updated_slots.get("issue", "Civic grievance")[:60],
            description=updated_slots.get("issue", "Reported via AI Assistant"),
            category=updated_slots.get("category", "Water Supply"),
            sub_category=f"{updated_slots.get('category')} Issue",
            department=updated_slots.get("department", "PHED"),
            urgency=urgency,
            language=req.language or "Odia",
            status="Submitted",
            state=updated_slots.get("state", "Odisha"),
            district=updated_slots.get("district", "Ganjam"),
            area=updated_slots.get("area", "Central Area"),
            lat=20.2961,
            lng=85.8245,
            submitted_date=sub_date,
            expected_date=exp_date,
            days_remaining=sla_days,
            user_id=chat_session.user_id or "USR-8921",
            citizen_phone="9876543210",
            assigned_officer_name=f"Duty Desk ({updated_slots.get('department')})",
            assigned_officer_designation="Intake Desk Officer",
            assigned_officer_dept=updated_slots.get("department"),
            ai_confidence=0.96,
            translated_text_en=updated_slots.get("translated_text_en"),
            sentiment=updated_slots.get("sentiment", "Frustrated"),
            ai_summary=updated_slots.get("summary"),
            source="ai_assistant"
        )
        db.add(new_comp)

        # Status History
        hist = StatusHistory(
            complaint_id=new_id,
            status="Submitted",
            date=sub_date,
            time=now.strftime("%I:%M %p"),
            officer="AI Intake Assistant",
            note=f"Grievance recorded via conversational slot filling in {req.language}.",
            completed=True,
            current=True
        )
        db.add(hist)

        # Notification
        notif = Notification(
            id=f"NOTIF-{int(now.timestamp() * 1000)}",
            user_id=chat_session.user_id or "USR-8921",
            title=f"Grievance Filed: {new_id}",
            message=f"Your ticket {new_id} ({new_comp.category}) has been submitted to {new_comp.department}.",
            type="update",
            read=False,
            related_grv_id=new_id,
            timestamp_str=f"{sub_date} • {now.strftime('%I:%M %p')}"
        )
        db.add(notif)
        db.commit()
        db.refresh(new_comp)

        filed_complaint_obj = format_complaint_response(new_comp)
        reply_text += f"\n\nTracking Ticket ID: **{new_id}**\nDepartment: **{new_comp.department}**\nTarget SLA: **{exp_date}**"

    # 6. Record AI message in DB
    ai_msg_record = ChatMessage(
        session_id=session_id,
        sender="ai",
        text=reply_text,
        metadata_json=json.dumps({"state": next_state, "ready_to_file": ready_to_file})
    )
    db.add(ai_msg_record)
    db.commit()

    return ChatInteractionResponse(
        session_id=session_id,
        reply=reply_text,
        state=next_state,
        slots=updated_slots,
        ready_to_file=ready_to_file,
        suggest_human_agent=suggest_human_agent,
        confirmation_card=confirmation_card,
        filed_complaint=filed_complaint_obj,
        detected_faq=detected_faq
    )

@router.get("/session/{session_id}")
def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = [
        {"sender": m.sender, "text": m.text, "created_at": m.created_at.isoformat()}
        for m in chat_session.messages
    ]
    return {
        "session_id": chat_session.id,
        "language": chat_session.language,
        "state": chat_session.state,
        "slots": json.loads(chat_session.slots_json),
        "messages": messages
    }

