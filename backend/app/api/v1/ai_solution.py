from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_note import TicketNote
from app.models.evaluation import AIEvaluation
from app.api.deps import get_current_user, get_support_or_admin
from app.services.rag.retriever import KnowledgeRetriever
from app.services.agents.airline.diagnosis_agent import DiagnosisAgent
from app.services.agents.airline.retrieval_agent import AirlineRetrievalAgent
from app.services.agents.airline.resolution_agent import ResolutionAgent
from app.services.agents.airline.validation_agent import ValidationAgent
from app.services.audit.audit_service import record_audit_event, record_status_change
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

    state: Dict[str, Any] = {
        "ticket": {
            "id": ticket.id,
            "title": ticket.title,
            "subject": ticket.title,
            "description": ticket.description,
            "passenger_name": ticket.passenger_name or (ticket.reporter.full_name if ticket.reporter else "Passenger"),
            "passenger_email": ticket.passenger_email or (ticket.reporter.email if ticket.reporter else ""),
            "booking_reference": ticket.booking_reference,
            "flight_number": ticket.flight_number,
            "travel_date": ticket.travel_date,
            "category": payload.force_category if (payload and payload.force_category) else ticket.category,
            "urgency": ticket.urgency,
            "affected_service": ticket.affected_service or "Flight Operations"
        }
    }

    # 1. Diagnosis
    diag_agent = DiagnosisAgent()
    _, diag_out, state = await diag_agent.run(state)

    # 2. Retrieval
    ret_agent = AirlineRetrievalAgent(db)
    _, ret_out, state = await ret_agent.run(state)

    # 3. Resolution
    res_agent = ResolutionAgent()
    _, res_out, state = await res_agent.run(state)

    # 4. Validation
    val_agent = ValidationAgent()
    _, val_out, state = await val_agent.run(state)

    # Confidence calculation
    base_conf = 82.0 if ret_out.get("has_sufficient_evidence") else 55.0
    conf_adj = val_out.get("confidence_adjustment", 0.0)
    final_confidence = round(max(0.0, min(100.0, base_conf + conf_adj)), 1)
    eligible_for_auto_resolve = (final_confidence >= settings.CONFIDENCE_THRESHOLD) and (val_out.get("verdict") == "PASS")

    # Store in ticket
    ticket.ai_confidence = int(final_confidence)
    ticket.final_response = res_out.get("passenger_response")
    db.commit()

    # Persist AI evaluation telemetry record
    ai_eval = AIEvaluation(
        ticket_id=ticket.id,
        workflow_run_id=None,
        model_name="AeroAssist-Agentic-v1",
        confidence_score=float(final_confidence),
        validation_outcome=val_out.get("verdict", "PASS"),
        validation_details=val_out,
        final_outcome="RESOLVED" if eligible_for_auto_resolve else "ESCALATED",
        escalation_reason=None if eligible_for_auto_resolve else "Confidence below 70% threshold or policy review mandated",
        latency_ms=135,
        retrieved_sources_count=len(ret_out.get("sources", [])),
        status="SUCCESS"
    )
    db.add(ai_eval)
    db.commit()
    db.refresh(ai_eval)

    record_audit_event(
        db=db,
        entity_type="AI_SOLUTION",
        entity_id=str(ticket.id),
        action="AI_SOLUTION_GENERATED",
        actor_id=current_user.id,
        details={
            "confidence": final_confidence,
            "verdict": val_out.get("verdict"),
            "citations": len(res_out.get("supporting_citations", [])),
            "evaluation_id": ai_eval.id
        }
    )

    return {
        "evaluation_id": ai_eval.id,
        "ticket_id": ticket.id,
        "passenger_name": state["ticket"]["passenger_name"],
        "booking_reference": state["ticket"]["booking_reference"],
        "flight_number": state["ticket"]["flight_number"],
        "category": diag_out.get("category"),
        "ai_interpretation": diag_out.get("issue_summary"),
        "detected_keywords": diag_out.get("detected_keywords", []),
        "retrieved_sources": ret_out.get("sources", []),
        "generated_response": res_out.get("passenger_response"),
        "policy_summary": res_out.get("policy_summary"),
        "actionable_steps": res_out.get("actionable_steps", []),
        "citations": res_out.get("supporting_citations", []),
        "confidence_score": final_confidence,
        "threshold": settings.CONFIDENCE_THRESHOLD,
        "eligible_for_auto_resolve": eligible_for_auto_resolve,
        "validation": val_out,
        "latency_ms": ai_eval.latency_ms,
        "model_name": ai_eval.model_name,
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

    if not ticket.final_response:
        # Generate on the fly
        return await resolve_ticket_with_ai(ticket_id=ticket_id, payload=None, db=db, current_user=current_user)

    return {
        "ticket_id": ticket.id,
        "passenger_name": ticket.passenger_name or (ticket.reporter.full_name if ticket.reporter else "Passenger"),
        "booking_reference": ticket.booking_reference,
        "flight_number": ticket.flight_number,
        "category": ticket.category,
        "generated_response": ticket.final_response,
        "confidence_score": ticket.ai_confidence or 75,
        "status": ticket.status.value
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
