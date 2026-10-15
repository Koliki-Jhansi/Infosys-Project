from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.ticket import Ticket
from app.models.workflow import WorkflowExecution, AgentExecution
from app.api.deps import get_current_user, get_support_or_admin
from app.services.workflows.airline_orchestrator import AirlineWorkflowOrchestrator
from app.services.workflows.orchestrator import WorkflowOrchestrator
from app.services.audit.audit_service import record_audit_event

router = APIRouter(tags=["Multi-Agent Workflows"])

class AgentExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_name: str
    status: str
    inputs: dict
    outputs: dict
    duration_ms: int
    error_message: Optional[str] = None
    created_at: datetime

class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    status: str
    current_agent: Optional[str] = None
    revision_cycles: int
    state_payload: dict
    error_details: Optional[str] = None
    agent_executions: List[AgentExecutionResponse] = []
    created_at: datetime
    updated_at: datetime

class WorkflowApprovalRequest(BaseModel):
    notes: Optional[str] = None

@router.post("/workflows/run/{ticket_id}", response_model=WorkflowResponse)
async def run_workflow_for_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orchestrator = AirlineWorkflowOrchestrator(db)
    workflow = await orchestrator.execute_or_resume_workflow(ticket_id=ticket_id)
    return workflow

@router.post("/tickets/{ticket_id}/workflow", response_model=WorkflowResponse)
async def trigger_ticket_workflow(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orchestrator = AirlineWorkflowOrchestrator(db)
    workflow = await orchestrator.execute_or_resume_workflow(ticket_id=ticket_id)
    return workflow

@router.get("/tickets/{ticket_id}/workflow", response_model=Optional[WorkflowResponse])
def get_ticket_latest_workflow(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wf = (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.ticket_id == ticket_id)
        .order_by(WorkflowExecution.created_at.desc())
        .first()
    )
    return wf

@router.get("/tickets/{ticket_id}/workflows", response_model=List[WorkflowResponse])
def get_all_ticket_workflows(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.ticket_id == ticket_id)
        .order_by(WorkflowExecution.created_at.desc())
        .all()
    )

@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
def get_workflow_details(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wf = db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow #{workflow_id} not found")
    return wf

@router.post("/workflows/{workflow_id}/resume", response_model=WorkflowResponse)
@router.post("/workflows/{workflow_id}/retry", response_model=WorkflowResponse)
async def resume_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wf = db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow #{workflow_id} not found")

    ticket = db.query(Ticket).filter(Ticket.id == wf.ticket_id).first()
    user_role_str = (
        current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    ).strip().upper()
    is_staff = user_role_str in ["ADMIN", "SUPPORT_ENGINEER", "SUPPORT_AGENT"]
    is_owner = ticket and (
        (ticket.reporter_id is not None and ticket.reporter_id == current_user.id)
        or (ticket.passenger_email and ticket.passenger_email.strip().lower() == current_user.email.strip().lower())
    )

    if not is_staff and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted. Requires one of roles: ['ADMIN', 'SUPPORT_ENGINEER', 'SUPPORT_AGENT'] or ticket owner."
        )
    
    orchestrator = AirlineWorkflowOrchestrator(db)
    return await orchestrator.execute_or_resume_workflow(ticket_id=wf.ticket_id, workflow_id=wf.id)

@router.post("/workflows/{workflow_id}/cancel", response_model=WorkflowResponse)
def cancel_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wf = db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow #{workflow_id} not found")

    ticket = db.query(Ticket).filter(Ticket.id == wf.ticket_id).first()
    user_role_str = (
        current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    ).strip().upper()
    is_staff = user_role_str in ["ADMIN", "SUPPORT_ENGINEER", "SUPPORT_AGENT"]
    is_owner = ticket and (
        (ticket.reporter_id is not None and ticket.reporter_id == current_user.id)
        or (ticket.passenger_email and ticket.passenger_email.strip().lower() == current_user.email.strip().lower())
    )

    if not is_staff and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted. Requires one of roles: ['ADMIN', 'SUPPORT_ENGINEER', 'SUPPORT_AGENT'] or ticket owner."
        )
    
    wf.status = "CANCELLED"
    wf.error_details = f"Cancelled by user {current_user.email}"
    db.commit()
    db.refresh(wf)

    record_audit_event(
        db=db,
        entity_type="WORKFLOW",
        entity_id=str(wf.id),
        action="WORKFLOW_CANCELLED",
        actor_id=current_user.id,
        details={"ticket_id": wf.ticket_id}
    )
    return wf


@router.post("/workflows/{workflow_id}/approve", response_model=WorkflowResponse)
async def approve_workflow_gate(
    workflow_id: int,
    payload: WorkflowApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    wf = db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow #{workflow_id} not found")
    
    orchestrator = AirlineWorkflowOrchestrator(db)
    record_audit_event(
        db=db,
        entity_type="WORKFLOW",
        entity_id=str(wf.id),
        action="WORKFLOW_APPROVED",
        actor_id=current_user.id,
        details={"notes": payload.notes}
    )
    return await orchestrator.execute_or_resume_workflow(
        ticket_id=wf.ticket_id,
        workflow_id=wf.id,
        human_approval_notes=payload.notes or f"Approved by {current_user.email}"
    )

@router.post("/workflows/{workflow_id}/reject", response_model=WorkflowResponse)
def reject_workflow_gate(
    workflow_id: int,
    payload: WorkflowApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support_or_admin)
):
    wf = db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow #{workflow_id} not found")
    
    wf.status = "FAILED"
    wf.error_details = f"Rejected at approval gate by {current_user.email}: {payload.notes or 'No reason provided'}"
    db.commit()
    db.refresh(wf)

    record_audit_event(
        db=db,
        entity_type="WORKFLOW",
        entity_id=str(wf.id),
        action="WORKFLOW_REJECTED",
        actor_id=current_user.id,
        details={"notes": payload.notes}
    )
    return wf

@router.get("/workflows/{workflow_id}/agents", response_model=List[AgentExecutionResponse])
def get_workflow_agent_executions(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wf = db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow #{workflow_id} not found")
    return wf.agent_executions
