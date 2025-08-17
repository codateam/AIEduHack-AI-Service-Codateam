from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from datetime import datetime, date, time
import uuid

# Enums for medical system
class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"

class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    PROCEDURE = "procedure"
    EMERGENCY = "emergency"
    TELEMEDICINE = "telemedicine"

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class PrescriptionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    READY = "ready"
    DISPENSED = "dispensed"
    CANCELLED = "cancelled"

class SubscriptionType(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    FAMILY = "family"
    CORPORATE = "corporate"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

# Base Models
class BaseUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    last_name: str
    email: str
    phone: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Patient(BaseUser):
    date_of_birth: date
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    insurance_info: Optional[Dict[str, Any]] = None
    medical_history: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    current_medications: Optional[List[str]] = []

class HealthcareProfessional(BaseUser):
    specialization: str
    license_number: str
    department: str
    availability: Optional[Dict[str, Any]] = None
    consultation_fee: Optional[float] = None

# Session and Interaction Models
class UserSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    room_name: str
    current_agent: Optional[str] = None
    context: Dict[str, Any] = {}
    conversation_history: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)

class TriageAssessment(BaseModel):
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    symptoms: List[str]
    urgency_level: UrgencyLevel
    recommended_action: str
    recommended_department: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

# Appointment Models
class AppointmentRequest(BaseModel):
    patient_id: str
    preferred_date: date
    preferred_time: Optional[time] = None
    appointment_type: AppointmentType
    department: Optional[str] = None
    doctor_id: Optional[str] = None
    reason: str
    urgency_level: UrgencyLevel = UrgencyLevel.LOW
    notes: Optional[str] = None

class Appointment(BaseModel):
    appointment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    appointment_date: datetime
    appointment_type: AppointmentType
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    department: str
    reason: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Prescription Models
class PrescriptionRefillRequest(BaseModel):
    patient_id: str
    medication_name: str
    current_prescription_id: Optional[str] = None
    pharmacy_preference: Optional[str] = None
    notes: Optional[str] = None

class Prescription(BaseModel):
    prescription_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    medication_name: str
    dosage: str
    quantity: int
    refills_remaining: int
    status: PrescriptionStatus = PrescriptionStatus.PENDING
    pharmacy: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

# Billing and Subscription Models
class Subscription(BaseModel):
    subscription_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subscription_type: SubscriptionType
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    start_date: date
    end_date: Optional[date] = None
    monthly_fee: float
    features: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)

class Payment(BaseModel):
    payment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subscription_id: Optional[str] = None
    amount: float
    payment_method: str
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_date: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = None

class BillingInquiry(BaseModel):
    inquiry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    inquiry_type: Literal["subscription", "payment", "refund", "general"]
    description: str
    status: Literal["open", "in_progress", "resolved"] = "open"
    created_at: datetime = Field(default_factory=datetime.now)

# Agent Response Models
class AgentResponse(BaseModel):
    agent_type: Literal["triage", "support", "billing"]
    message: str
    actions_taken: List[str] = []
    next_steps: Optional[str] = None
    requires_human_intervention: bool = False
    confidence_score: Optional[float] = None

class TriageResponse(AgentResponse):
    agent_type: Literal["triage"] = "triage"
    urgency_assessment: UrgencyLevel
    recommended_department: Optional[str] = None
    should_transfer: bool = False
    transfer_to: Optional[Literal["support", "billing", "emergency"]] = None

class SupportResponse(AgentResponse):
    agent_type: Literal["support"] = "support"
    appointment_scheduled: Optional[str] = None
    prescription_processed: Optional[str] = None
    professional_recommended: Optional[str] = None

class BillingResponse(AgentResponse):
    agent_type: Literal["billing"] = "billing"
    subscription_updated: Optional[str] = None
    payment_processed: Optional[str] = None
    billing_issue_resolved: Optional[str] = None

# Tool Function Models
class ToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    success: bool = False
    error_message: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.now)