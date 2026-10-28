from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_note import TicketNote
from app.models.workflow import WorkflowExecution, AgentExecution
from app.models.evaluation import AIEvaluation
from app.api.deps import get_current_user, get_support_or_admin
from app.services.workflows.airline_orchestrator import AirlineWorkflowOrchestrator
from app.services.agents.airline.retrieval_agent import AirlineRetrievalAgent
from app.services.agents.airline.validation_agent import ValidationAgent
from app.services.audit.audit_service import record_audit_event
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI Solution"])

class AiResolveRequest(BaseModel):
    custom_instructions: Optional[str] = None
    force_category: Optional[str] = None

class AiValidateRequest(BaseModel):
    response_text: str

@router.post("/resolve/{ticket_id}")
async def resolve_ticket_with_ai(
    ticket_id: int,
    payload: Optional[AiResolveRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    if payload and payload.force_category:
        ticket.category = payload.force_category
        db.commit()

    # Execute full airline multi-agent workflow
    orchestrator = AirlineWorkflowOrchestrator(db)
    workflow = await orchestrator.execute_or_resume_workflow(ticket_id=ticket.id)
    db.refresh(ticket)

    state = workflow.state_payload or {}
    diag_out = state.get("diagnosis", {})
    ret_out = state.get("retrieval", {})
    res_out = state.get("resolution", {})
    val_out = state.get("validation", {})
    priority_out = state.get("priority_criticality", {})
    esc_out = state.get("escalation", {})

    final_confidence = float(esc_out.get("final_confidence") or ticket.ai_confidence or 75.0)
    decision = esc_out.get("decision", "RESOLVED" if final_confidence >= settings.CONFIDENCE_THRESHOLD else "ESCALATED")

    agent_executions_list = [
        {
            "id": a.id,
            "agent_name": a.agent_name,
            "status": a.status,
            "duration_ms": a.duration_ms,
            "inputs": a.inputs,
            "outputs": a.outputs,
            "error_message": a.error_message,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in workflow.agent_executions
    ]

    record_audit_event(
        db=db,
        entity_type="AI_SOLUTION",
        entity_id=str(ticket.id),
        action="AI_SOLUTION_RESOLVE_TRIGGERED",
        actor_id=current_user.id,
        details={
            "workflow_id": workflow.id,
            "confidence": final_confidence,
            "decision": decision
        }
    )

    return {
        "workflow_id": workflow.id,
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number or f"TK-{ticket.id:04d}",
        "passenger_name": ticket.passenger_name or (ticket.reporter.full_name if ticket.reporter else "Passenger"),
        "passenger_email": ticket.passenger_email or (ticket.reporter.email if ticket.reporter else ""),
        "booking_reference": ticket.booking_reference,
        "flight_number": ticket.flight_number,
        "category": diag_out.get("category") or ticket.category,
        "priority": priority_out.get("priority") or (ticket.classification.priority if ticket.classification else ticket.urgency),
        "criticality": priority_out.get("criticality") or (ticket.classification.criticality if ticket.classification else ticket.business_impact),
        "ai_interpretation": diag_out.get("issue_summary"),
        "detected_keywords": diag_out.get("detected_keywords", []),
        "retrieved_sources": ret_out.get("sources", []),
        "generated_response": ticket.final_response or res_out.get("passenger_response"),
        "policy_summary": res_out.get("policy_summary"),
        "actionable_steps": res_out.get("actionable_steps", []),
        "citations": res_out.get("supporting_citations", []),
        "confidence_score": final_confidence,
        "threshold": settings.CONFIDENCE_THRESHOLD,
        "eligible_for_auto_resolve": (final_confidence >= settings.CONFIDENCE_THRESHOLD and val_out.get("verdict") == "PASS"),
        "status": ticket.status.value,
        "decision": decision,
        "decision_summary": esc_out.get("decision_summary"),
        "jira": esc_out.get("jira"),
        "jira_error": esc_out.get("jira_error"),
        "email_delivery": esc_out.get("email_delivery"),
        "validation": val_out,
        "agent_executions": agent_executions_list,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

@router.get("/results/{ticket_id}")
async def get_ai_results(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    workflow = (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.ticket_id == ticket.id)
        .order_by(WorkflowExecution.created_at.desc())
        .first()
    )

    if not workflow:
        return {
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number or f"TK-{ticket.id:04d}",
            "passenger_name": ticket.passenger_name or (ticket.reporter.full_name if ticket.reporter else "Passenger"),
            "passenger_email": ticket.passenger_email or (ticket.reporter.email if ticket.reporter else ""),
            "booking_reference": ticket.booking_reference,
            "flight_number": ticket.flight_number,
            "category": ticket.category,
            "priority": ticket.classification.priority if ticket.classification else ticket.urgency,
            "criticality": ticket.classification.criticality if ticket.classification else ticket.business_impact,
            "generated_response": ticket.final_response,
            "confidence_score": ticket.ai_confidence,
            "status": ticket.status.value,
            "decision": None,
            "retrieved_sources": [],
            "agent_executions": []
        }

    state = workflow.state_payload or {}
    diag_out = state.get("diagnosis", {})
    ret_out = state.get("retrieval", {})
    res_out = state.get("resolution", {})
    val_out = state.get("validation", {})
    priority_out = state.get("priority_criticality", {})
    esc_out = state.get("escalation", {})

    agent_executions_list = [
        {
            "id": a.id,
            "agent_name": a.agent_name,
            "status": a.status,
            "duration_ms": a.duration_ms,
            "inputs": a.inputs,
            "outputs": a.outputs,
            "error_message": a.error_message,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in workflow.agent_executions
    ]

    return {
        "workflow_id": workflow.id,
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number or f"TK-{ticket.id:04d}",
        "passenger_name": ticket.passenger_name or (ticket.reporter.full_name if ticket.reporter else "Passenger"),
        "passenger_email": ticket.passenger_email or (ticket.reporter.email if ticket.reporter else ""),
        "booking_reference": ticket.booking_reference,
        "flight_number": ticket.flight_number,
        "category": diag_out.get("category") or ticket.category,
        "priority": priority_out.get("priority") or (ticket.classification.priority if ticket.classification else ticket.urgency),
        "criticality": priority_out.get("criticality") or (ticket.classification.criticality if ticket.classification else ticket.business_impact),
        "ai_interpretation": diag_out.get("issue_summary"),
        "detected_keywords": diag_out.get("detected_keywords", []),
        "retrieved_sources": ret_out.get("sources", []),
        "generated_response": ticket.final_response or res_out.get("passenger_response"),
        "policy_summary": res_out.get("policy_summary"),
        "actionable_steps": res_out.get("actionable_steps", []),
        "citations": res_out.get("supporting_citations", []),
        "confidence_score": float(esc_out.get("final_confidence") or ticket.ai_confidence or 75.0),
        "threshold": settings.CONFIDENCE_THRESHOLD,
        "status": ticket.status.value,
        "decision": esc_out.get("decision"),
        "decision_summary": esc_out.get("decision_summary"),
        "jira": esc_out.get("jira"),
        "jira_error": esc_out.get("jira_error"),
        "email_delivery": esc_out.get("email_delivery"),
        "validation": val_out,
        "agent_executions": agent_executions_list,
        "workflow_status": workflow.status,
        "generated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
    }

@router.post("/validate/{ticket_id}")
async def validate_solution_text(
    ticket_id: int,
    payload: AiValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket #{ticket_id} not found")

    ret_agent = AirlineRetrievalAgent(db)
    state = {
        "ticket": {"title": ticket.title, "description": ticket.description, "category": ticket.category},
        "diagnosis": {"category": ticket.category, "missing_information": []},
        "resolution": {"passenger_response": payload.response_text}
    }
    _, ret_out, state = await ret_agent.run(state)
    val_agent = ValidationAgent()
    _, val_out, _ = await val_agent.run(state)

    return val_out
