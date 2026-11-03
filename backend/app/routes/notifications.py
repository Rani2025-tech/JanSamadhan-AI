from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Notification
from app.schemas import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])

def format_notif(n: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=n.id,
        title=n.title,
        message=n.message,
        timestamp=n.timestamp_str,
        type=n.type,
        read=n.read,
        relatedGrvId=n.related_grv_id
    )

@router.get("", response_model=List[NotificationResponse])
def get_notifications(db: Session = Depends(get_db)):
    items = db.query(Notification).order_by(desc(Notification.created_at)).all()
    return [format_notif(n) for n in items]

@router.put("/{notif_id}/read", response_model=NotificationResponse)
def mark_read(notif_id: str, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read = True
    db.commit()
    db.refresh(notif)
    return format_notif(notif)

@router.put("/read-all")
def mark_all_read(db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.read == False).update({"read": True})
    db.commit()
    return {"success": True, "message": "All notifications marked as read"}

