from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base

class JiraIssueRecord(Base):
    __tablename__ = "jira_issue_records"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=True, index=True)
    
    jira_key = Column(String(50), nullable=False, index=True)  # e.g. IT-101
    jira_url = Column(String(512), nullable=False)
    project_key = Column(String(50), nullable=False)
    issue_type = Column(String(50), default="Task", nullable=False)
    summary = Column(String(255), nullable=False)
    priority = Column(String(50), nullable=False)
    status = Column(String(50), default="To Do", nullable=False)
    
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    metadata_payload = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    ticket = relationship("Ticket", back_populates="jira_records")
    workflow = relationship("WorkflowExecution", back_populates="jira_records")
