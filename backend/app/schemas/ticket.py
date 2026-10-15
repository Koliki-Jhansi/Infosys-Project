from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.ticket import TicketStatus, TicketCategory, TicketUrgency, BusinessImpact, EnvironmentType
from app.schemas.auth import UserResponse
from app.schemas.classification import ClassificationResponse

class TicketCreate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    description: str = Field(..., min_length=5)
    affected_service: Optional[str] = "Flight Operations"
    category: str = "General"
    business_impact: Optional[str] = "Single passenger"
    urgency: Optional[str] = "Medium"
    priority: Optional[str] = "Medium"
    environment: Optional[str] = "production"
    affected_users: Optional[int] = 1
    error_logs: Optional[str] = None

    # Airline specific
    passenger_name: Optional[str] = None
    passenger_email: Optional[str] = None
    booking_reference: Optional[str] = None  # PNR (e.g. AA-78942)
    flight_number: Optional[str] = None      # e.g. FL-342
    travel_date: Optional[str] = None        # e.g. 2026-11-20

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    urgency: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    business_impact: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    final_response: Optional[str] = None

class TicketNoteCreate(BaseModel):
    content: str = Field(..., min_length=1)
    message_type: Optional[str] = "INTERNAL_NOTE"  # INTERNAL_NOTE, AI_RESPONSE, PASSENGER_UPDATE, ESCALATION_REASON

class TicketNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author_id: Optional[int] = None
    author: Optional[UserResponse] = None
    message_type: str
    content: str
    created_at: datetime

class TicketStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by_id: Optional[int] = None
    reason: Optional[str] = None
    created_at: datetime

class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_number: Optional[str] = None
    title: str
    description: str
    affected_service: Optional[str] = None
    category: str
    business_impact: Optional[str] = None
    urgency: str
    environment: Optional[str] = None
    affected_users: Optional[int] = 1
    error_logs: Optional[str] = None
    attachment_filename: Optional[str] = None
    attachment_path: Optional[str] = None
    
    # Airline passenger support fields
    passenger_name: Optional[str] = None
    passenger_email: Optional[str] = None
    booking_reference: Optional[str] = None
    flight_number: Optional[str] = None
    travel_date: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    assigned_agent: Optional[UserResponse] = None
    ai_confidence: Optional[int] = None
    final_response: Optional[str] = None
    resolved_at: Optional[datetime] = None

    status: TicketStatus
    reporter_id: int
    reporter: Optional[UserResponse] = None
    classification: Optional[ClassificationResponse] = None
    created_at: datetime
    updated_at: datetime

class TicketDetailResponse(TicketResponse):
    status_history: List[TicketStatusHistoryResponse] = []
    notes: List[TicketNoteResponse] = []

class TicketListResponse(BaseModel):
    items: List[TicketResponse]
    total: int
    page: int
    size: int
    pages: int
