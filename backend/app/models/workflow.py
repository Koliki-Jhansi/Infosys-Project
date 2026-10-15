from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, RUNNING, COMPLETED, FAILED, WAITING_FOR_REVIEW, CANCELLED
    current_agent = Column(String(100), nullable=True)
    revision_cycles = Column(Integer, default=0, nullable=False)
    state_payload = Column(JSON, default=dict, nullable=False)
    error_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    ticket = relationship("Ticket", back_populates="workflows")
    agent_executions = relationship("AgentExecution", back_populates="workflow", cascade="all, delete-orphan", order_by="AgentExecution.created_at.asc()")
    jira_records = relationship("JiraIssueRecord", back_populates="workflow", cascade="all, delete-orphan")

class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED, WAITING_FOR_REVIEW, SKIPPED
    inputs = Column(JSON, default=dict, nullable=False)
    outputs = Column(JSON, default=dict, nullable=False)
    duration_ms = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    workflow = relationship("WorkflowExecution", back_populates="agent_executions")
