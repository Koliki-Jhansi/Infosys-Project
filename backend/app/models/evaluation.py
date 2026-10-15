from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base

class AIEvaluation(Base):
    __tablename__ = "ai_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_run_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="SET NULL"), nullable=True, index=True)
    model_name = Column(String(100), default="AeroAssist-Agentic-v1", nullable=False)
    confidence_score = Column(Float, nullable=False)
    validation_outcome = Column(String(50), default="PASS", nullable=False)  # PASS, NEEDS_REVISION, FAIL
    validation_details = Column(JSON, default=dict, nullable=False)
    final_outcome = Column(String(50), nullable=False)  # RESOLVED, ESCALATED, FAILED
    escalation_reason = Column(String(255), nullable=True)
    latency_ms = Column(Integer, default=0, nullable=False)
    retrieved_sources_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="SUCCESS", nullable=False)  # SUCCESS, ERROR
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    ticket = relationship("Ticket", foreign_keys=[ticket_id])
    workflow = relationship("WorkflowExecution", foreign_keys=[workflow_run_id])
    feedbacks = relationship("EvaluationFeedback", back_populates="evaluation", cascade="all, delete-orphan")


class EvaluationFeedback(Base):
    __tablename__ = "evaluation_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("ai_evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    accuracy_label = Column(String(50), nullable=False)  # CORRECT, PARTIALLY_CORRECT, INCORRECT, UNABLE_TO_ASSESS
    source_grounding_rating = Column(Integer, default=5, nullable=True)  # 1 to 5
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    evaluation = relationship("AIEvaluation", back_populates="feedbacks")
    ticket = relationship("Ticket", foreign_keys=[ticket_id])
    user = relationship("User", foreign_keys=[user_id])
