from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketStatus
from app.models.classification import TicketClassification
from app.schemas.ticket import TicketResponse
from app.schemas.review import ReviewActionRequest, ReviewResponse, ReviewActionEnum
from app.api.deps import get_current_user, get_support_or_admin
from app.services.audit.audit_service import record_audit_event, record_status_change

router = APIRouter(tags=["Human Review Queue"])

@router.get("/reviews", response_model=List[TicketResponse])
def get_review_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    """
    Returns the queue of tickets needing human review:
    Tickets with status NEEDS_REVIEW or with requires_human_review=True and is_reviewed=False.
    """
    tickets = (
        db.query(Ticket)
        .outerjoin(TicketClassification)
        .filter(
            (Ticket.status == TicketStatus.NEEDS_REVIEW) |
            ((TicketClassification.requires_human_review == True) & (TicketClassification.is_reviewed == False))
        )
        .order_by(desc(Ticket.created_at))
        .all()
    )
    return tickets

@router.post("/tickets/{ticket_id}/review", response_model=ReviewResponse)
def review_ticket(
    ticket_id: int,
    action_in: ReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    classification = db.query(TicketClassification).filter(TicketClassification.ticket_id == ticket_id).first()
    if not classification:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket has not been classified yet")

    old_status = ticket.status.value
    new_status = old_status

    if action_in.action == ReviewActionEnum.APPROVE:
        new_status = TicketStatus.CLASSIFIED.value
        ticket.status = TicketStatus.CLASSIFIED
        classification.is_reviewed = True
        classification.reviewed_by_id = current_user.id
        classification.review_notes = action_in.notes or "Approved by support engineer for workflow progression."
        classification.reviewed_at = datetime.now(timezone.utc)
        message = f"Ticket #{ticket_id} approved and advanced to CLASSIFIED."

    elif action_in.action == ReviewActionEnum.REJECT:
        new_status = TicketStatus.CLOSED.value
        ticket.status = TicketStatus.CLOSED
        classification.is_reviewed = True
        classification.reviewed_by_id = current_user.id
        classification.review_notes = action_in.notes or "Ticket rejected during human review."
        classification.reviewed_at = datetime.now(timezone.utc)
        message = f"Ticket #{ticket_id} rejected and closed."

    elif action_in.action == ReviewActionEnum.OVERRIDE:
        if action_in.override_category:
            classification.predicted_category = action_in.override_category
            ticket.category = action_in.override_category
        if action_in.override_priority:
            classification.priority = action_in.override_priority
            
        new_status = TicketStatus.CLASSIFIED.value
        ticket.status = TicketStatus.CLASSIFIED
        classification.is_reviewed = True
        classification.reviewed_by_id = current_user.id
        classification.review_notes = (
            f"Overridden by {current_user.email}: "
            f"Category={action_in.override_category or 'Unchanged'}, "
            f"Priority={action_in.override_priority or 'Unchanged'}. Notes: {action_in.notes or 'None'}"
        )
        classification.reviewed_at = datetime.now(timezone.utc)
        message = f"Ticket #{ticket_id} classification overridden and advanced to CLASSIFIED."

    db.commit()
    db.refresh(ticket)
    db.refresh(classification)

    record_status_change(
        db=db,
        ticket_id=ticket.id,
        old_status=old_status,
        new_status=new_status,
        changed_by_id=current_user.id,
        reason=classification.review_notes
    )

    audit_event = record_audit_event(
        db=db,
        entity_type="REVIEW",
        entity_id=str(ticket.id),
        action=f"REVIEW_{action_in.action.value}",
        actor_id=current_user.id,
        details={
            "action": action_in.action.value,
            "old_status": old_status,
            "new_status": new_status,
            "notes": action_in.notes,
            "override_category": action_in.override_category,
            "override_priority": action_in.override_priority
        }
    )

    return ReviewResponse(
        success=True,
        ticket_id=ticket.id,
        new_status=new_status,
        message=message
    )
