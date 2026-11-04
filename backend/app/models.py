import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    phone = Column(String(20), index=True, nullable=True)
    email = Column(String(128), index=True, nullable=True)
    employee_id = Column(String(64), index=True, nullable=True)
    role = Column(String(20), default="citizen", nullable=False)  # citizen, admin, guest
    language = Column(String(10), default="or")
    state = Column(String(64), default="Odisha", nullable=True)
    district = Column(String(64), nullable=True)
    department = Column(String(128), nullable=True)
    password_hash = Column(String(256), nullable=True)
    avatar = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    complaints = relationship("Complaint", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(32), primary_key=True, index=True)  # e.g., GRV-1042
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, index=True)
    sub_category = Column(String(64), nullable=True)
    department = Column(String(64), nullable=False, index=True)
    urgency = Column(String(20), default="Medium", index=True)  # Low, Medium, High, Critical
    language = Column(String(32), default="English")
    status = Column(String(32), default="Submitted", index=True)  # Submitted, Assigned, In Progress, Resolved
    
    # Location
    state = Column(String(64), default="Odisha", nullable=False, index=True)
    district = Column(String(64), nullable=False, index=True)
    area = Column(String(256), nullable=False)
    pincode = Column(String(16), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    
    # Dates & Turnaround
    submitted_date = Column(String(32), nullable=False)
    expected_date = Column(String(32), nullable=False)
    days_remaining = Column(Integer, default=7)
    
    # Citizen reference
    user_id = Column(String(64), ForeignKey("users.id"), nullable=True)
    citizen_phone = Column(String(20), nullable=True)
    
    # Officer assignment
    assigned_officer_name = Column(String(128), nullable=True)
    assigned_officer_designation = Column(String(128), nullable=True)
    assigned_officer_dept = Column(String(128), nullable=True)
    assigned_officer_phone = Column(String(32), nullable=True)
    
    # Citizen Feedback
    feedback_rating = Column(Integer, nullable=True)
    feedback_comment = Column(Text, nullable=True)
    
    # AI Enrichment Fields
    ai_confidence = Column(Float, default=0.92)
    needs_human_review = Column(Boolean, default=False)
    translated_text_en = Column(Text, nullable=True)
    sentiment = Column(String(32), default="Neutral")
    ai_summary = Column(Text, nullable=True)
    duplicate_of_id = Column(String(32), nullable=True)
    source = Column(String(32), default="web_form")  # web_form, ai_assistant, voice
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="complaints")
    status_history = relationship(
        "StatusHistory",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="StatusHistory.id"
    )


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String(32), ForeignKey("complaints.id"), nullable=False, index=True)
    status = Column(String(32), nullable=False)
    date = Column(String(32), nullable=False)
    time = Column(String(32), nullable=True)
    officer = Column(String(128), nullable=True)
    note = Column(Text, nullable=False)
    completed = Column(Boolean, default=False)
    current = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    complaint = relationship("Complaint", back_populates="status_history")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(32), default="update")  # update, announcement
    read = Column(Boolean, default=False)
    related_grv_id = Column(String(32), nullable=True)
    timestamp_str = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=True)
    language = Column(String(10), default="or")
    state = Column(String(32), default="collecting")  # collecting, clarifying, confirming, filed
    slots_json = Column(Text, default="{}")  # JSON encoded slots
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.id"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    sender = Column(String(16), nullable=False)  # user, ai
    text = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


class AdminCorrection(Base):
    __tablename__ = "admin_corrections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String(32), ForeignKey("complaints.id"), nullable=False, index=True)
    admin_id = Column(String(64), nullable=True)
    field_name = Column(String(32), nullable=False)  # "category" or "department"
    original_value = Column(String(128), nullable=False)
    corrected_value = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


