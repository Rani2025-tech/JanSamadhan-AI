from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- User & Auth Schemas ---
class UserBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = "citizen"
    language: str = "or"
    state: Optional[str] = "Odisha"
    district: Optional[str] = None
    department: Optional[str] = None
    avatar: Optional[str] = None

class UserResponse(UserBase):
    id: str
    employee_id: Optional[str] = None

    class Config:
        from_attributes = True

class SendOTPRequest(BaseModel):
    mobile: str

class VerifyOTPRequest(BaseModel):
    mobile: str
    otp: str

class AdminLoginRequest(BaseModel):
    id_or_email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Status History Schemas ---
class StatusHistoryItemSchema(BaseModel):
    status: str
    date: str
    time: Optional[str] = None
    officer: Optional[str] = None
    note: str
    completed: bool = False
    current: bool = False

    class Config:
        from_attributes = True

# --- Complaint Schemas ---
class ComplaintCreate(BaseModel):
    title: str
    description: str
    category: str
    department: str
    urgency: str = "Medium"
    language: str = "English"
    state: Optional[str] = "Odisha"
    district: str
    area: str
    pincode: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    source: Optional[str] = "web_form"

class ComplaintStatusUpdate(BaseModel):
    status: str
    officer_note: str
    officer_name: Optional[str] = None

class ComplaintFeedback(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class AssignedOfficerSchema(BaseModel):
    name: str
    designation: str
    department: str
    phone: Optional[str] = None

class ComplaintResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    sub_category: Optional[str] = None
    department: str
    urgency: str
    language: str
    status: str
    state: Optional[str] = "Odisha"
    location: Dict[str, Any]
    submittedDate: str
    expectedDate: str
    daysRemaining: int
    assignedOfficer: Optional[AssignedOfficerSchema] = None
    statusHistory: List[StatusHistoryItemSchema] = []
    feedback: Optional[Dict[str, Any]] = None
    citizenPhone: Optional[str] = None
    
    # AI Enrichment
    ai_confidence: Optional[float] = None
    needs_human_review: Optional[bool] = False
    translated_text_en: Optional[str] = None
    sentiment: Optional[str] = None
    ai_summary: Optional[str] = None
    duplicate_of_id: Optional[str] = None

    class Config:
        from_attributes = True

class ComplaintAdminUpdate(BaseModel):
    category: Optional[str] = None
    department: Optional[str] = None
    urgency: Optional[str] = None
    status: Optional[str] = None

class DuplicateCheckRequest(BaseModel):
    text: str
    district: str
    category: str

class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    confidence: float
    matched_complaint_id: Optional[str] = None
    matched_title: Optional[str] = None
    message: str

# --- Notification Schemas ---
class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    timestamp: str
    type: str
    read: bool
    relatedGrvId: Optional[str] = None

    class Config:
        from_attributes = True

# --- AI Extraction & Slot Filling Schemas ---
class AIExtractionResult(BaseModel):
    language: str = Field(description="Detected language, e.g. Odia, Hindi, Bengali, English, Marathi, Tamil, Telugu")
    translated_text_en: str = Field(description="Accurate English translation of the grievance")
    category: str = Field(description="Civic category: Water Supply, Road Infrastructure, Electricity, Sanitation, Public Health, Ration / PDS")
    sub_category: Optional[str] = Field(default=None, description="Detailed sub-category, e.g. Pipeline Leakage, Potholes, Voltage Fluctuation")
    department: str = Field(description="State department: PHED, PWD, DISCOM, Municipal Corporation, Health & Family Welfare, Food Supplies & Consumer Welfare")
    urgency: str = Field(description="Low, Medium, High, or Critical")
    sentiment: str = Field(description="Citizen sentiment: Frustrated, Distressed, Urgent, Inconvenienced, Neutral")
    location: Dict[str, Any] = Field(default_factory=dict, description="Location details: {district, area, landmark, pincode}")
    summary: str = Field(description="One-sentence executive summary of the grievance")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")

class ChatInteractionRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    language: Optional[str] = "or"
    user_id: Optional[str] = None

class ChatInteractionResponse(BaseModel):
    session_id: str
    reply: str
    state: str  # greeting, collecting_info, confirming, filed
    slots: Dict[str, Any]
    ready_to_file: bool = False
    suggest_human_agent: bool = False
    confirmation_card: Optional[Dict[str, Any]] = None
    filed_complaint: Optional[ComplaintResponse] = None
    detected_faq: Optional[Dict[str, Any]] = None

# --- Admin Stats Schemas ---
class AdminStatsResponse(BaseModel):
    total_complaints: int
    open_complaints: int
    resolved_complaints: int
    avg_resolution_days: float
    satisfaction_rate: float
    sla_compliance_rate: float
    districts_count: int
    department_metrics: List[Dict[str, Any]]
    hotspot_clusters: List[Dict[str, Any]]
    admin_correction_rate: Optional[float] = 3.8
    total_corrections: Optional[int] = 0

