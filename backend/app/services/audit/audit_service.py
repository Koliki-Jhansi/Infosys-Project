from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent
from app.models.status_history import TicketStatusHistory
from app.core.logging import logger

def record_audit_event(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> AuditEvent:
    event = AuditEvent(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        actor_id=actor_id,
        details=details or {},
        correlation_id=correlation_id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info(f"Audit event [{entity_type}:{entity_id}] action={action} by actor={actor_id}")
    return event

def record_status_change(
    db: Session,
    ticket_id: int,
    old_status: Optional[str],
    new_status: str,
    changed_by_id: Optional[int] = None,
    reason: Optional[str] = None
) -> TicketStatusHistory:
    history = TicketStatusHistory(
        ticket_id=ticket_id,
        old_status=old_status,
        new_status=new_status,
        changed_by_id=changed_by_id,
        reason=reason
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
