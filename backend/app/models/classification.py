import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base

class PriorityLevel(str, enum.Enum):
    P1 = "P1 Critical"
    P2 = "P2 High"
    P3 = "P3 Medium"
    P4 = "P4 Low"

class CriticalityLevel(str, enum.Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class TicketClassification(Base):
    __tablename__ = "ticket_classifications"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    predicted_category = Column(String(100), nullable=False)
    priority = Column(String(50), nullable=False)
    criticality = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0 to 100
    
    explanation = Column(Text, nullable=False)
    detected_keywords = Column(JSON, default=list, nullable=False)
    potential_business_impact = Column(Text, nullable=False)
    recommended_next_action = Column(Text, nullable=False)
    missing_information = Column(JSON, default=list, nullable=False)
    
    requires_human_review = Column(Boolean, default=False, nullable=False)
    review_reason = Column(String(255), nullable=True)
    is_reviewed = Column(Boolean, default=False, nullable=False)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    model_name = Column(String(100), default="deterministic-rule-engine", nullable=False)
    confidence_breakdown = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    ticket = relationship("Ticket", back_populates="classification")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
