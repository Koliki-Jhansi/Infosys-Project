import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base

class TicketStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CLASSIFIED = "CLASSIFIED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class TicketCategory(str, enum.Enum):
    NETWORK = "Network"
    APPLICATION = "Application"
    DATABASE = "Database"
    AUTHENTICATION_ACCESS = "Authentication and access"
    INFRASTRUCTURE = "Infrastructure"
    HARDWARE = "Hardware"
    DEPLOYMENT = "Deployment"
    SECURITY = "Security"
    OTHER = "Other"

class TicketUrgency(str, enum.Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class BusinessImpact(str, enum.Enum):
    EXTENSIVE = "Extensive / Organization-wide"
    SIGNIFICANT = "Significant / Department-wide"
    MODERATE = "Moderate / Team or Group"
    MINOR = "Minor / Single user"

class EnvironmentType(str, enum.Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    affected_service = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    business_impact = Column(String(100), nullable=False)
    urgency = Column(String(50), nullable=False)
    environment = Column(String(50), default="production", nullable=False)
    affected_users = Column(Integer, default=1, nullable=False)
    error_logs = Column(Text, nullable=True)
    attachment_filename = Column(String(255), nullable=True)
    attachment_path = Column(String(512), nullable=True)
    
    # Airline specific passenger support fields
    ticket_number = Column(String(64), unique=True, index=True, nullable=True)
    passenger_name = Column(String(255), nullable=True, index=True)
    passenger_email = Column(String(255), nullable=True, index=True)
    booking_reference = Column(String(64), nullable=True, index=True)  # PNR (e.g. AA-78942)
    flight_number = Column(String(64), nullable=True, index=True)      # e.g. FL-342
    travel_date = Column(String(64), nullable=True)                    # e.g. 2026-11-20
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ai_confidence = Column(Integer, nullable=True)                     # Percentage 0-100
    final_response = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    status = Column(Enum(TicketStatus), default=TicketStatus.SUBMITTED, nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    reporter = relationship("User", back_populates="tickets", foreign_keys=[reporter_id])
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id])
    classification = relationship("TicketClassification", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    status_history = relationship("TicketStatusHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketStatusHistory.created_at.desc()")
    workflows = relationship("WorkflowExecution", back_populates="ticket", cascade="all, delete-orphan", order_by="WorkflowExecution.created_at.desc()")
    jira_records = relationship("JiraIssueRecord", back_populates="ticket", cascade="all, delete-orphan")
    notes = relationship("TicketNote", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketNote.created_at.asc()")
