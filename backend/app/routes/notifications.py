from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.database import get_db
from app.models import Notification, User
from app.schemas import NotificationResponse
from app.routes.auth import get_current_user, get_current_user_required

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
def get_notifications(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user and current_user.role == "admin":
        items = db.query(Notification).order_by(desc(Notification.created_at)).all()
    elif current_user:
        # Return user's own updates + general platform announcements
        items = db.query(Notification).filter(
            or_(
                Notification.user_id == current_user.id,
                (Notification.type == "announcement") & (Notification.user_id == None)
            )
        ).order_by(desc(Notification.created_at)).all()
    else:
        # Guests and unauthenticated: only general platform announcements
        items = db.query(Notification).filter(
            (Notification.type == "announcement") & (Notification.user_id == None)
        ).order_by(desc(Notification.created_at)).all()

    return [format_notif(n) for n in items]

@router.put("/{notif_id}/read", response_model=NotificationResponse)
def mark_read(
    notif_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Access control: citizen can only mark their own notifications as read
    if current_user.role != "admin":
        if notif.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot modify another user's notifications."
            )

    notif.read = True
    db.commit()
    db.refresh(notif)
    return format_notif(notif)

@router.put("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    if current_user and current_user.role == "admin":
        db.query(Notification).filter(Notification.read == False).update({"read": True})
    elif current_user:
        db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.read == False
        ).update({"read": True})

    db.commit()
    return {"success": True, "message": "All notifications marked as read"}
