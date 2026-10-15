import os
import shutil
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketStatus
from app.models.classification import TicketClassification
from app.models.setting import AppSetting
from app.models.ticket_note import TicketNote
from app.models.audit import AuditEvent
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketDetailResponse,
    TicketListResponse,
    TicketNoteCreate,
    TicketNoteResponse,
    TicketStatusHistoryResponse
)
from app.schemas.classification import ClassificationResponse
from app.api.deps import get_current_user, get_support_or_admin
from app.services.classification.engine import ClassificationEngine
from app.services.audit.audit_service import record_audit_event, record_status_change
from app.core.config import settings

router = APIRouter(prefix="/tickets", tags=["Tickets"])

def get_current_threshold(db: Session) -> float:
    threshold_setting = db.query(AppSetting).filter(AppSetting.key == "CONFIDENCE_THRESHOLD").first()
    if threshold_setting:
        try:
            return float(threshold_setting.value)
        except ValueError:
            pass
    return settings.CONFIDENCE_THRESHOLD

@router.post("", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket_title = ticket_in.title or ticket_in.subject or "Passenger Inquiry"
    pass_name = ticket_in.passenger_name or current_user.full_name
    pass_email = ticket_in.passenger_email or current_user.email
    aff_service = ticket_in.affected_service or "Flight Operations"
    urgency_val = ticket_in.urgency or ticket_in.priority or "Medium"
    impact_val = ticket_in.business_impact or "Single passenger"

    ticket = Ticket(
        title=ticket_title,
        description=ticket_in.description,
        affected_service=aff_service,
        category=ticket_in.category or "General",
        business_impact=impact_val,
        urgency=urgency_val,
        environment=ticket_in.environment or "production",
        affected_users=ticket_in.affected_users or 1,
        error_logs=ticket_in.error_logs,
        passenger_name=pass_name,
        passenger_email=pass_email,
        booking_reference=ticket_in.booking_reference,
        flight_number=ticket_in.flight_number,
        travel_date=ticket_in.travel_date,
        status=TicketStatus.SUBMITTED,
        reporter_id=current_user.id
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Set ticket number (e.g. TK-0001)
    ticket.ticket_number = f"TK-{ticket.id:04d}"
    db.commit()
    db.refresh(ticket)

    record_status_change(
        db=db,
        ticket_id=ticket.id,
        old_status=None,
        new_status=TicketStatus.SUBMITTED.value,
        changed_by_id=current_user.id,
        reason="Ticket submitted by passenger or support staff"
    )

    record_audit_event(
        db=db,
        entity_type="TICKET",
        entity_id=str(ticket.id),
        action="TICKET_CREATED",
        actor_id=current_user.id,
        details={
            "ticket_number": ticket.ticket_number,
            "title": ticket.title,
            "category": ticket.category,
            "pnr": ticket.booking_reference,
            "flight": ticket.flight_number
        }
    )

    # Automatically trigger classification
    threshold = get_current_threshold(db)
    engine = ClassificationEngine(threshold=threshold)
    classification_result = await engine.classify_ticket(
        ticket_id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        affected_service=ticket.affected_service,
        reported_category=ticket.category,
        urgency=ticket.urgency,
        business_impact=ticket.business_impact,
        environment=ticket.environment,
        affected_users=ticket.affected_users,
        error_logs=ticket.error_logs or ""
    )

    classification = TicketClassification(
        ticket_id=ticket.id,
        predicted_category=classification_result.predicted_category,
        priority=classification_result.priority,
        criticality=classification_result.criticality,
        confidence_score=classification_result.confidence_score,
        explanation=classification_result.explanation,
        detected_keywords=classification_result.detected_keywords,
        potential_business_impact=classification_result.potential_business_impact,
        recommended_next_action=classification_result.recommended_next_action,
        missing_information=classification_result.missing_information,
        requires_human_review=classification_result.requires_human_review,
        review_reason=classification_result.review_reason,
        model_name=classification_result.model_name,
        confidence_breakdown=classification_result.confidence_breakdown
    )
    db.add(classification)

    old_status = ticket.status.value
    ticket.status = TicketStatus(classification_result.status)
    ticket.ai_confidence = int(classification_result.confidence_score)
    db.commit()
    db.refresh(ticket)

    record_status_change(
        db=db,
        ticket_id=ticket.id,
        old_status=old_status,
        new_status=ticket.status.value,
        changed_by_id=None,
        reason=f"Classification completed: {classification_result.explanation}"
    )

    return ticket

@router.post("/with-attachment", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket_with_attachment(
    title: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    description: str = Form(...),
    category: str = Form("General"),
    urgency: Optional[str] = Form("Medium"),
    priority: Optional[str] = Form("Medium"),
    passenger_name: Optional[str] = Form(None),
    passenger_email: Optional[str] = Form(None),
    booking_reference: Optional[str] = Form(None),
    flight_number: Optional[str] = Form(None),
    travel_date: Optional[str] = Form(None),
    affected_service: Optional[str] = Form("Flight Operations"),
    business_impact: Optional[str] = Form("Single passenger"),
    environment: str = Form("production"),
    affected_users: int = Form(1),
    error_logs: Optional[str] = Form(None),
    attachment: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket_title = title or subject or "Passenger Inquiry"
    pass_name = passenger_name or current_user.full_name
    pass_email = passenger_email or current_user.email
    urgency_val = urgency or priority or "Medium"

    saved_path = None
    if attachment:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_ext = os.path.splitext(attachment.filename)[1].lower()
        allowed_extensions = [".txt", ".log", ".pdf", ".png", ".jpg", ".jpeg", ".json", ".csv", ".docx"]
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attachment file extension '{file_ext}' not permitted. Allowed: {allowed_extensions}"
            )
        
        saved_filename = f"{current_user.id}_{int(datetime.now().timestamp())}_{attachment.filename}"
        saved_path = os.path.join(settings.UPLOAD_DIR, saved_filename)
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(attachment.file, buffer)

    ticket = Ticket(
        title=ticket_title,
        description=description,
        affected_service=affected_service or "Flight Operations",
        category=category,
        business_impact=business_impact or "Single passenger",
        urgency=urgency_val,
        environment=environment,
        affected_users=affected_users,
        error_logs=error_logs,
        passenger_name=pass_name,
        passenger_email=pass_email,
        booking_reference=booking_reference,
        flight_number=flight_number,
        travel_date=travel_date,
        attachment_filename=attachment.filename if attachment else None,
        attachment_path=saved_path,
        status=TicketStatus.SUBMITTED,
        reporter_id=current_user.id
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    ticket.ticket_number = f"TK-{ticket.id:04d}"
    db.commit()
    db.refresh(ticket)

    # Classify ticket
    threshold = get_current_threshold(db)
    engine = ClassificationEngine(threshold=threshold)
    classification_result = await engine.classify_ticket(
        ticket_id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        affected_service=ticket.affected_service,
        reported_category=ticket.category,
        urgency=ticket.urgency,
        business_impact=ticket.business_impact,
        environment=ticket.environment,
        affected_users=ticket.affected_users,
        error_logs=ticket.error_logs or ""
    )

    classification = TicketClassification(
        ticket_id=ticket.id,
        predicted_category=classification_result.predicted_category,
        priority=classification_result.priority,
        criticality=classification_result.criticality,
        confidence_score=classification_result.confidence_score,
        explanation=classification_result.explanation,
        detected_keywords=classification_result.detected_keywords,
        potential_business_impact=classification_result.potential_business_impact,
        recommended_next_action=classification_result.recommended_next_action,
        missing_information=classification_result.missing_information,
        requires_human_review=classification_result.requires_human_review,
        review_reason=classification_result.review_reason,
        model_name=classification_result.model_name,
        confidence_breakdown=classification_result.confidence_breakdown
    )
    db.add(classification)
    ticket.status = TicketStatus(classification_result.status)
    ticket.ai_confidence = int(classification_result.confidence_score)
    db.commit()
    db.refresh(ticket)

    return ticket

@router.get("", response_model=TicketListResponse)
def list_tickets(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Ticket)

    # If passenger / requester, only view own tickets unless support/admin
    user_role_str = (
        current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    ).strip().upper()
    is_staff = user_role_str in ["ADMIN", "SUPPORT_AGENT", "SUPPORT_ENGINEER"]
    if not is_staff:
        query = query.filter(Ticket.reporter_id == current_user.id)


    if status_filter:
        norm_status = status_filter.strip()
        if norm_status == "Open":
            query = query.filter(Ticket.status.in_([TicketStatus.SUBMITTED, TicketStatus.CLASSIFIED]))
        elif norm_status == "In Progress":
            query = query.filter(Ticket.status == TicketStatus.IN_PROGRESS)
        elif norm_status == "AI Resolved":
            query = query.filter(Ticket.status == TicketStatus.RESOLVED)
        elif norm_status == "Escalated":
            query = query.filter(Ticket.status == TicketStatus.NEEDS_REVIEW)
        elif norm_status == "Closed":
            query = query.filter(Ticket.status == TicketStatus.CLOSED)
        else:
            query = query.filter(Ticket.status == norm_status)

    if category:
        query = query.filter(Ticket.category == category)
    if priority:
        query = query.join(TicketClassification).filter(TicketClassification.priority == priority)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Ticket.title.ilike(search_fmt),
                Ticket.description.ilike(search_fmt),
                Ticket.passenger_name.ilike(search_fmt),
                Ticket.booking_reference.ilike(search_fmt),
                Ticket.flight_number.ilike(search_fmt),
                Ticket.ticket_number.ilike(search_fmt)
            )
        )

    total = query.count()

    order_func = desc if order.lower() == "desc" else asc
    if sort_by == "created_at":
        query = query.order_by(order_func(Ticket.created_at))
    elif sort_by == "title":
        query = query.order_by(order_func(Ticket.title))
    elif sort_by == "status":
        query = query.order_by(order_func(Ticket.status))
    else:
        query = query.order_by(desc(Ticket.created_at))

    items = query.offset((page - 1) * size).limit(size).all()
    pages = (total + size - 1) // size if total > 0 else 1

    return TicketListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")
    
    is_staff = current_user.role in [UserRole.ADMIN, UserRole.SUPPORT_AGENT, UserRole.SUPPORT_ENGINEER]
    if not is_staff and ticket.reporter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this ticket")

    return ticket

@router.patch("/{ticket_id}", response_model=TicketDetailResponse)
def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    user_role_str = (
        current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    ).strip().upper()
    is_staff = user_role_str in ["ADMIN", "SUPPORT_AGENT", "SUPPORT_ENGINEER"]
    is_owner = (
        (ticket.reporter_id is not None and ticket.reporter_id == current_user.id)
        or (ticket.passenger_email and ticket.passenger_email.strip().lower() == current_user.email.strip().lower())
    )
    if not is_staff and not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this ticket")

    old_status = ticket.status.value

    if ticket_update.title:
        ticket.title = ticket_update.title
    if ticket_update.description:
        ticket.description = ticket_update.description
    if ticket_update.category:
        ticket.category = ticket_update.category
    if ticket_update.urgency:
        ticket.urgency = ticket_update.urgency
    if ticket_update.assigned_agent_id:
        ticket.assigned_agent_id = ticket_update.assigned_agent_id
    if ticket_update.final_response:
        ticket.final_response = ticket_update.final_response

    if ticket_update.status:
        st = ticket_update.status
        if st in ["Open", "SUBMITTED"]:
            ticket.status = TicketStatus.SUBMITTED
        elif st in ["In Progress", "IN_PROGRESS"]:
            ticket.status = TicketStatus.IN_PROGRESS
        elif st in ["AI Resolved", "RESOLVED"]:
            ticket.status = TicketStatus.RESOLVED
            ticket.resolved_at = datetime.now(timezone.utc)
        elif st in ["Escalated", "NEEDS_REVIEW"]:
            ticket.status = TicketStatus.NEEDS_REVIEW
        elif st in ["Closed", "CLOSED"]:
            ticket.status = TicketStatus.CLOSED
        else:
            try:
                ticket.status = TicketStatus(st)
            except ValueError:
                pass

        if ticket.status.value != old_status:
            record_status_change(
                db=db,
                ticket_id=ticket.id,
                old_status=old_status,
                new_status=ticket.status.value,
                changed_by_id=current_user.id,
                reason="Ticket status updated via PATCH"
            )

    db.commit()
    db.refresh(ticket)
    return ticket

@router.post("/{ticket_id}/notes", response_model=TicketNoteResponse, status_code=status.HTTP_201_CREATED)
def add_ticket_note(
    ticket_id: int,
    note_in: TicketNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    note = TicketNote(
        ticket_id=ticket.id,
        author_id=current_user.id,
        message_type=note_in.message_type or "INTERNAL_NOTE",
        content=note_in.content
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    record_audit_event(
        db=db,
        entity_type="TICKET_NOTE",
        entity_id=str(note.id),
        action="NOTE_ADDED",
        actor_id=current_user.id,
        details={"ticket_id": ticket.id, "type": note.message_type}
    )

    return note

@router.post("/{ticket_id}/resolve", response_model=TicketDetailResponse)
def resolve_ticket(
    ticket_id: int,
    payload: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    user_role_str = (
        current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    ).strip().upper()
    is_staff = user_role_str in ["ADMIN", "SUPPORT_ENGINEER", "SUPPORT_AGENT"]
    is_owner = (
        (ticket.reporter_id is not None and ticket.reporter_id == current_user.id)
        or (ticket.passenger_email and ticket.passenger_email.strip().lower() == current_user.email.strip().lower())
    )

    if not is_staff and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted. Requires one of roles: ['ADMIN', 'SUPPORT_ENGINEER', 'SUPPORT_AGENT'] or ticket owner."
        )

    old_status = ticket.status.value
    ticket.status = TicketStatus.RESOLVED
    ticket.resolved_at = datetime.now(timezone.utc)
    if payload and payload.get("response"):
        ticket.final_response = payload.get("response")

    resolver_desc = f"support staff ({user_role_str})" if is_staff else f"ticket owner ({current_user.full_name})"
    note = TicketNote(
        ticket_id=ticket.id,
        author_id=current_user.id,
        message_type="INTERNAL_NOTE",
        content=f"Ticket resolved by {current_user.full_name} ({resolver_desc})"
    )
    db.add(note)
    db.commit()
    db.refresh(ticket)

    record_status_change(
        db=db,
        ticket_id=ticket.id,
        old_status=old_status,
        new_status=ticket.status.value,
        changed_by_id=current_user.id,
        reason=f"Marked resolved by {resolver_desc}"
    )

    return ticket

@router.post("/{ticket_id}/escalate", response_model=TicketDetailResponse)
def escalate_ticket(
    ticket_id: int,
    payload: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    reason = (payload or {}).get("reason", "Escalated for human support review")
    old_status = ticket.status.value
    ticket.status = TicketStatus.NEEDS_REVIEW

    note = TicketNote(
        ticket_id=ticket.id,
        author_id=current_user.id,
        message_type="ESCALATION_REASON",
        content=f"Escalated: {reason}"
    )
    db.add(note)
    db.commit()
    db.refresh(ticket)

    record_status_change(
        db=db,
        ticket_id=ticket.id,
        old_status=old_status,
        new_status=ticket.status.value,
        changed_by_id=current_user.id,
        reason=reason
    )

    return ticket

@router.get("/{ticket_id}/history")
def get_ticket_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    status_hist = ticket.status_history
    audits = db.query(AuditEvent).filter(
        AuditEvent.details.contains(f'"ticket_id": {ticket.id}') |
        ((AuditEvent.entity_type == "TICKET") & (AuditEvent.entity_id == str(ticket.id)))
    ).order_by(desc(AuditEvent.created_at)).all()

    return {
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "status_history": [
            {
                "old_status": s.old_status,
                "new_status": s.new_status,
                "reason": s.reason,
                "created_at": s.created_at
            }
            for s in status_hist
        ],
        "audit_logs": [
            {
                "action": a.action,
                "details": a.details,
                "created_at": a.created_at
            }
            for a in audits
        ]
    }

@router.post("/{ticket_id}/classify", response_model=ClassificationResponse)
async def classify_ticket_endpoint(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    threshold = get_current_threshold(db)
    engine = ClassificationEngine(threshold=threshold)
    result = await engine.classify_ticket(
        ticket_id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        affected_service=ticket.affected_service or "Flight Operations",
        reported_category=ticket.category,
        urgency=ticket.urgency,
        business_impact=ticket.business_impact or "Single passenger",
        environment=ticket.environment or "production",
        affected_users=ticket.affected_users or 1,
        error_logs=ticket.error_logs or ""
    )

    classification = db.query(TicketClassification).filter(TicketClassification.ticket_id == ticket.id).first()
    if not classification:
        classification = TicketClassification(ticket_id=ticket.id)
        db.add(classification)

    classification.predicted_category = result.predicted_category
    classification.priority = result.priority
    classification.criticality = result.criticality
    classification.confidence_score = result.confidence_score
    classification.explanation = result.explanation
    classification.detected_keywords = result.detected_keywords
    classification.potential_business_impact = result.potential_business_impact
    classification.recommended_next_action = result.recommended_next_action
    classification.missing_information = result.missing_information
    classification.requires_human_review = result.requires_human_review
    classification.review_reason = result.review_reason
    classification.model_name = result.model_name
    classification.confidence_breakdown = result.confidence_breakdown

    old_status = ticket.status.value
    ticket.status = TicketStatus(result.status)
    ticket.ai_confidence = int(result.confidence_score)
    db.commit()
    db.refresh(classification)
    db.refresh(ticket)

    return classification

@router.get("/{ticket_id}/classification", response_model=ClassificationResponse)
def get_ticket_classification(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")
    
    is_staff = current_user.role in [UserRole.ADMIN, UserRole.SUPPORT_AGENT, UserRole.SUPPORT_ENGINEER]
    if not is_staff and ticket.reporter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    classification = db.query(TicketClassification).filter(TicketClassification.ticket_id == ticket_id).first()
    if not classification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No classification found for this ticket")
    return classification
