from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.ticket import Ticket, TicketStatus
from app.models.jira import JiraIssueRecord
from app.api.deps import get_current_user, get_support_or_admin
from app.services.jira.client import JiraClientService
from app.services.audit.audit_service import record_audit_event, record_status_change
from app.core.config import settings
from app.schemas.jira import (
    JiraStatusResponse,
    JiraTestConnectionResponse,
    JiraProjectItem,
    JiraIssueItem,
    JiraIssueListResponse,
    JiraCreateIssueRequest,
    JiraUpdateIssueRequest,
    JiraTransitionItem,
    JiraTransitionRequest,
    JiraCommentItem,
    JiraAddCommentRequest,
    JiraIssueRecordResponse
)

router = APIRouter(tags=["Jira Integration"])

@router.get("/integrations/jira/status", response_model=JiraStatusResponse)
def get_jira_status(
    current_user: User = Depends(get_current_user)
):
    service = JiraClientService()
    is_real = service.is_real_cloud_configured()
    
    # Mask email for privacy (e.g. j***@example.com)
    email_parts = settings.JIRA_EMAIL.split("@")
    masked_email = f"{email_parts[0][:1]}***@{email_parts[1]}" if len(email_parts) == 2 else "Not configured"

    return JiraStatusResponse(
        connected=True,
        mode="REAL_CLOUD" if is_real else "SIMULATED",
        project_key=settings.JIRA_PROJECT_KEY,
        base_url=settings.JIRA_BASE_URL,
        default_issue_type=settings.JIRA_DEFAULT_ISSUE_TYPE,
        configured_email=masked_email,
        is_enabled=settings.JIRA_ENABLED
    )

@router.post("/integrations/jira/test", response_model=JiraTestConnectionResponse)
async def test_jira_connection(
    current_user: User = Depends(get_support_or_admin)
):
    service = JiraClientService()
    res = await service.test_connection()
    return JiraTestConnectionResponse(**res)

@router.get("/integrations/jira/projects", response_model=List[JiraProjectItem])
async def get_jira_projects(
    current_user: User = Depends(get_current_user)
):
    service = JiraClientService()
    projects = await service.get_projects()
    return [JiraProjectItem(**p) for p in projects]

@router.get("/integrations/jira/issues", response_model=JiraIssueListResponse)
async def list_jira_issues(
    project_key: Optional[str] = Query(None, description="Filter by Jira project key"),
    search: Optional[str] = Query(None, description="Keyword search in summary/key/description"),
    status: Optional[str] = Query(None, description="Filter by issue status"),
    priority: Optional[str] = Query(None, description="Filter by issue priority"),
    jql: Optional[str] = Query(None, description="Raw JQL query string"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    service = JiraClientService()
    result = await service.get_issues(
        project_key=project_key,
        search=search,
        status=status,
        priority=priority,
        jql=jql,
        page=page,
        size=size
    )
    return JiraIssueListResponse(**result)

@router.post("/integrations/jira/issues", response_model=JiraIssueItem)
async def create_jira_issue(
    payload: JiraCreateIssueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    if not payload.summary.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Issue summary is required.")

    service = JiraClientService()
    res = await service.create_issue(
        summary=payload.summary.strip(),
        description=payload.description.strip(),
        priority=payload.priority,
        issue_type=payload.issue_type,
        project_key=payload.project_key,
        assignee=payload.assignee or current_user.full_name,
        idempotency_key=payload.idempotency_key
    )

    record_audit_event(
        db=db,
        entity_type="JIRA",
        entity_id=res["key"],
        action="JIRA_MANUAL_ISSUE_CREATED",
        actor_id=current_user.id,
        details={"summary": payload.summary, "project_key": res.get("project_key")}
    )

    return JiraIssueItem(**res)

@router.get("/integrations/jira/issues/{issue_key}", response_model=JiraIssueItem)
async def get_jira_issue_detail(
    issue_key: str,
    current_user: User = Depends(get_current_user)
):
    service = JiraClientService()
    issue = await service.get_issue(issue_key)
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Jira issue {issue_key} not found.")
    return JiraIssueItem(**issue)

@router.put("/integrations/jira/issues/{issue_key}", response_model=JiraIssueItem)
async def update_jira_issue(
    issue_key: str,
    payload: JiraUpdateIssueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    service = JiraClientService()
    updated = await service.update_issue(
        key=issue_key,
        summary=payload.summary,
        description=payload.description
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Jira issue {issue_key} not found.")

    record_audit_event(
        db=db,
        entity_type="JIRA",
        entity_id=issue_key,
        action="JIRA_ISSUE_UPDATED",
        actor_id=current_user.id,
        details={"summary": payload.summary}
    )

    return JiraIssueItem(**updated)

@router.get("/integrations/jira/issues/{issue_key}/transitions", response_model=List[JiraTransitionItem])
async def get_jira_issue_transitions(
    issue_key: str,
    current_user: User = Depends(get_current_user)
):
    service = JiraClientService()
    transitions = await service.get_transitions(issue_key)
    return [JiraTransitionItem(**t) for t in transitions]

@router.post("/integrations/jira/issues/{issue_key}/transitions", response_model=JiraIssueItem)
async def transition_jira_issue(
    issue_key: str,
    payload: JiraTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    service = JiraClientService()
    updated = await service.transition_issue(
        key=issue_key,
        transition_id=payload.transition_id,
        comment_text=payload.comment
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Failed to transition Jira issue {issue_key}.")

    # Also update any linked JiraIssueRecord in our database
    linked_record = db.query(JiraIssueRecord).filter(JiraIssueRecord.jira_key == issue_key).first()
    if linked_record and updated.get("status"):
        linked_record.status = updated["status"]
        db.commit()

    record_audit_event(
        db=db,
        entity_type="JIRA",
        entity_id=issue_key,
        action="JIRA_ISSUE_TRANSITIONED",
        actor_id=current_user.id,
        details={"transition_id": payload.transition_id, "new_status": updated.get("status")}
    )

    return JiraIssueItem(**updated)

@router.get("/integrations/jira/issues/{issue_key}/comments", response_model=List[JiraCommentItem])
async def get_jira_issue_comments(
    issue_key: str,
    current_user: User = Depends(get_current_user)
):
    service = JiraClientService()
    comments = await service.get_comments(issue_key)
    return [JiraCommentItem(**c) for c in comments]

@router.post("/integrations/jira/issues/{issue_key}/comments", response_model=JiraCommentItem)
async def add_jira_issue_comment(
    issue_key: str,
    payload: JiraAddCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    if not payload.comment.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment text cannot be empty.")

    service = JiraClientService()
    comm = await service.add_comment(
        key=issue_key,
        author=current_user.full_name,
        comment_text=payload.comment.strip()
    )
    if not comm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Jira issue {issue_key} not found.")

    record_audit_event(
        db=db,
        entity_type="JIRA",
        entity_id=issue_key,
        action="JIRA_COMMENT_ADDED",
        actor_id=current_user.id,
        details={"comment_snippet": payload.comment[:100]}
    )

    return JiraCommentItem(**comm)

@router.post("/tickets/{ticket_id}/jira", response_model=JiraIssueRecordResponse)
async def create_jira_issue_for_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    # Check for existing JiraIssueRecord
    existing = db.query(JiraIssueRecord).filter(JiraIssueRecord.ticket_id == ticket_id).first()
    if existing:
        return existing

    service = JiraClientService()
    idempotency_key = f"manual_sync_ticket_{ticket_id}"
    priority = ticket.classification.priority if ticket.classification else "P3 Medium"

    desc = (
        f"**Flight Support Ticket #{ticket.id}: {ticket.title}**\n\n"
        f"Passenger: {ticket.passenger_name or 'N/A'}\n"
        f"PNR Reference: {ticket.booking_reference or 'N/A'}\n"
        f"Flight Number: {ticket.flight_number or 'N/A'}\n"
        f"Affected Service / Category: {ticket.category}\n"
        f"Urgency: {ticket.urgency}\n\n"
        f"Description:\n{ticket.description}\n"
    )

    jira_res = await service.create_issue(
        summary=f"[{ticket.category}] {ticket.title}",
        description=desc,
        priority=priority,
        project_key=settings.JIRA_PROJECT_KEY,
        assignee=current_user.full_name,
        idempotency_key=idempotency_key
    )

    issue_record = JiraIssueRecord(
        ticket_id=ticket.id,
        jira_key=jira_res["key"],
        jira_url=jira_res["url"],
        project_key=jira_res["project_key"],
        issue_type=jira_res["issue_type"],
        summary=f"[{ticket.category}] {ticket.title}",
        priority=jira_res["priority"],
        status=jira_res["status"],
        idempotency_key=idempotency_key,
        metadata_payload=jira_res
    )
    db.add(issue_record)
    db.commit()
    db.refresh(issue_record)

    record_audit_event(
        db=db,
        entity_type="JIRA",
        entity_id=issue_record.jira_key,
        action="JIRA_ISSUE_CREATED",
        actor_id=current_user.id,
        details={"ticket_id": ticket.id, "jira_key": issue_record.jira_key}
    )

    return issue_record

@router.post("/tickets/{ticket_id}/jira/refresh", response_model=JiraIssueRecordResponse)
async def refresh_ticket_jira_status(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    record = db.query(JiraIssueRecord).filter(JiraIssueRecord.ticket_id == ticket_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No linked Jira issue found for Ticket #{ticket_id}.")

    service = JiraClientService()
    issue = await service.get_issue(record.jira_key)
    if issue:
        if issue.get("status"):
            record.status = issue["status"]
        if issue.get("priority"):
            record.priority = issue["priority"]
        db.commit()
        db.refresh(record)

    return record

@router.post("/webhooks/jira")
async def jira_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.json()
    webhook_event = payload.get("webhookEvent", "jira:issue_updated")
    issue_data = payload.get("issue", {})
    key = issue_data.get("key")
    
    if key:
        record = db.query(JiraIssueRecord).filter(JiraIssueRecord.jira_key == key).first()
        if record:
            new_status = issue_data.get("fields", {}).get("status", {}).get("name")
            if new_status:
                record.status = new_status
                db.commit()
                record_audit_event(
                    db=db,
                    entity_type="JIRA_WEBHOOK",
                    entity_id=key,
                    action="JIRA_STATUS_SYNCED",
                    actor_id=None,
                    details={"new_status": new_status, "event": webhook_event}
                )

    return {"status": "received", "event": webhook_event}
