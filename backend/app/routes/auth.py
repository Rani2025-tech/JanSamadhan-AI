import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
import jwt
from app.database import get_db
from app.models import User
from app.schemas import (
    SendOTPRequest,
    VerifyOTPRequest,
    AdminLoginRequest,
    TokenResponse,
    UserResponse,
    UserBase
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None

@router.post("/send-otp")
def send_otp(req: SendOTPRequest):
    clean_mobile = req.mobile.replace(" ", "").replace("-", "")
    if len(clean_mobile) != 10 or not clean_mobile.isdigit() or clean_mobile[0] not in "6789":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number must be a 10-digit number starting with 6, 7, 8, or 9."
        )
    return {
        "success": True,
        "message": f"6-digit OTP sent to +91 {clean_mobile}. (Demo Mock OTP: 123456)",
        "mock_otp": "123456"
    }

@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    clean_mobile = req.mobile.replace(" ", "").replace("-", "")
    if req.otp != "123456":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP. For demonstration, please use 123456."
        )

    # Find existing citizen user or create new clean user
    user = db.query(User).filter(User.phone == clean_mobile).first()
    if not user:
        user_id = f"USR-{clean_mobile[-4:]}{int(datetime.datetime.utcnow().timestamp()) % 1000}"
        user = User(
            id=user_id,
            name="",
            phone=clean_mobile,
            role="citizen",
            language="en",
            district=None,
            state=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.post("/admin-login", response_model=TokenResponse)
def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)):
    if not req.id_or_email.strip() or not req.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID / Email and password are required."
        )

    # Validate against env-driven admin password
    if req.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative password."
        )

    # Retrieve admin or demo officer
    admin = db.query(User).filter(
        (User.role == "admin") &
        ((User.employee_id == req.id_or_email) | (User.email == req.id_or_email))
    ).first()

    if not admin:
        admin = db.query(User).filter(User.role == "admin").first()

    if not admin:
        # Create default admin from env
        admin = User(
            id="EMP-4402",
            name="Dr. Alok Mohapatra, OAS",
            phone="9876500000",
            email=settings.ADMIN_EMAIL,
            employee_id=settings.ADMIN_EMPLOYEE_ID,
            role="admin",
            department="Grievance & Public Administration",
            language="en"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    token = create_access_token(admin.id, "admin")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.from_orm(admin)
    )

@router.post("/guest-login", response_model=TokenResponse)
def guest_login(db: Session = Depends(get_db)):
    guest = db.query(User).filter(User.role == "guest").first()
    if not guest:
        guest = User(
            id="GUEST-0001",
            name="Guest Citizen",
            role="guest",
            language="en"
        )
        db.add(guest)
        db.commit()
        db.refresh(guest)

    token = create_access_token(guest.id, "guest")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.from_orm(guest)
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return UserResponse.from_orm(current_user)

@router.put("/profile", response_model=UserResponse)
def update_profile(
    updates: UserBase,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if updates.name is not None:
        current_user.name = updates.name
    if updates.phone:
        current_user.phone = updates.phone
    if updates.email is not None:
        current_user.email = updates.email
    if updates.district is not None:
        current_user.district = updates.district
    if updates.state is not None:
        current_user.state = updates.state
    if updates.language:
        current_user.language = updates.language

    db.commit()
    db.refresh(current_user)
    return UserResponse.from_orm(current_user)
