import datetime
import hashlib
import hmac
import time
from collections import defaultdict
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func
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

# Password Hashing Utilities (PBKDF2-HMAC-SHA256 with constant-time verification)
PASSWORD_SALT = b"jansamadhan_sec_salt_2026"

def hash_password(password: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), PASSWORD_SALT, 100000).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    expected = hash_password(plain_password)
    return hmac.compare_digest(expected, hashed_password)

# In-Memory Rate Limiter (5 attempts per 10 minutes)
class RateLimiter:
    def __init__(self):
        self.otp_fails = defaultdict(list)
        self.admin_fails = defaultdict(list)

    def check_otp(self, phone: str):
        now = time.time()
        self.otp_fails[phone] = [t for t in self.otp_fails[phone] if now - t < 600]
        if len(self.otp_fails[phone]) >= 5:
            oldest = self.otp_fails[phone][0]
            rem = int(600 - (now - oldest))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed OTP attempts. Account locked for {rem} seconds."
            )

    def record_otp_failure(self, phone: str):
        now = time.time()
        self.otp_fails[phone] = [t for t in self.otp_fails[phone] if now - t < 600]
        self.otp_fails[phone].append(now)
        if len(self.otp_fails[phone]) >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed OTP attempts. Account temporarily locked for 10 minutes."
            )

    def reset_otp(self, phone: str):
        self.otp_fails.pop(phone, None)

    def check_admin(self, ip: str):
        now = time.time()
        self.admin_fails[ip] = [t for t in self.admin_fails[ip] if now - t < 600]
        if len(self.admin_fails[ip]) >= 5:
            oldest = self.admin_fails[ip][0]
            rem = int(600 - (now - oldest))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed admin login attempts from this IP. Blocked for {rem} seconds."
            )

    def record_admin_failure(self, ip: str):
        now = time.time()
        self.admin_fails[ip] = [t for t in self.admin_fails[ip] if now - t < 600]
        self.admin_fails[ip].append(now)
        if len(self.admin_fails[ip]) >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed admin login attempts. IP temporarily blocked for 10 minutes."
            )

    def reset_admin(self, ip: str):
        self.admin_fails.pop(ip, None)

auth_limiter = RateLimiter()

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
    """Soft auth check: returns None if missing or invalid token."""
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

def get_current_user_required(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Strict auth check: raises 401 if missing, invalid, or expired token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required."
        )
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload."
            )
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found."
            )
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )

def require_admin(current_user: User = Depends(get_current_user_required)) -> User:
    """Strict admin check: raises 403 if user is not an administrator."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required."
        )
    return current_user

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
    if len(clean_mobile) != 10 or not clean_mobile.isdigit() or clean_mobile[0] not in "6789":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number must be a 10-digit number starting with 6, 7, 8, or 9."
        )

    # 1. Check Rate Limit (5 attempts per 10 minutes)
    auth_limiter.check_otp(clean_mobile)

    if req.otp != "123456":
        auth_limiter.record_otp_failure(clean_mobile)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP. For demonstration, please use 123456."
        )

    # Reset OTP failure counter on successful verification
    auth_limiter.reset_otp(clean_mobile)

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
def admin_login(req: AdminLoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "127.0.0.1"

    if not req.id_or_email.strip() or not req.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID / Email and password are required."
        )

    # 1. Rate Limiting Check (5 attempts per IP per 10 minutes)
    auth_limiter.check_admin(client_ip)

    # 2. Strict Exact Admin Lookup (NO FALLBACK to first admin)
    clean_id = req.id_or_email.strip().lower()
    admin = db.query(User).filter(
        (User.role == "admin") &
        ((func.lower(User.employee_id) == clean_id) | (func.lower(User.email) == clean_id))
    ).first()

    if not admin:
        auth_limiter.record_admin_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative credentials."
        )

    # 3. Verify Password against Hash
    expected_hash = admin.password_hash or hash_password(settings.ADMIN_PASSWORD)
    if not verify_password(req.password, expected_hash):
        auth_limiter.record_admin_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative credentials."
        )

    # Reset admin failure counter on successful login
    auth_limiter.reset_admin(client_ip)

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
def get_me(current_user: User = Depends(get_current_user_required)):
    return UserResponse.from_orm(current_user)

@router.put("/profile", response_model=UserResponse)
def update_profile(
    updates: UserBase,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
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
