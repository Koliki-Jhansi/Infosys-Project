from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_note import TicketNote
from app.services.audit.audit_service import record_audit_event, record_status_change
from app.core.config import settings

class EscalationAgent(BaseAgent):
    def __init__(self, db: Session, name: str = "Escalation Agent"):
        super().__init__(name=name)
        self.db = db

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket_data = state.get("ticket", {})
        ticket_id = ticket_data.get("id")
        classification = state.get("classification", {})
        diagnosis = state.get("diagnosis", {})
        validation = state.get("validation", {})
        resolution = state.get("resolution", {})

        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first() if ticket_id else None

        # Determine confidence score
        raw_confidence = classification.get("confidence_score", 75.0)
        conf_adj = validation.get("confidence_adjustment", 0.0)
        final_confidence = round(max(0.0, min(100.0, raw_confidence + conf_adj)), 1)

        threshold = settings.CONFIDENCE_THRESHOLD  # default 70.0
        verdict = validation.get("verdict", "PASS")
        is_urgent = diagnosis.get("is_urgent", False)
        category = diagnosis.get("category", "")

        escalate_reasons = []
        should_escalate = False

        if final_confidence < threshold:
            should_escalate = True
            escalate_reasons.append(f"Confidence score ({final_confidence}%) is below 70% threshold")

        if verdict != "PASS":
            should_escalate = True
            escalate_reasons.append(f"Validation checks flagged: {validation.get('summary', 'Validation failed')}")

        if category in ["Special Assistance", "Security"]:
            should_escalate = True
            escalate_reasons.append(f"Category '{category}' mandates human agent authorization")

        if is_urgent and final_confidence < 85.0:
            should_escalate = True
            escalate_reasons.append("High urgency travel disruption requires station manager oversight")

        final_outcome = "ESCALATED" if should_escalate else "RESOLVED"
        decision_summary = (
            f"Escalated to human Support Agent: {'; '.join(escalate_reasons)}"
            if should_escalate
            else f"Automated AI Resolution Approved (Confidence: {final_confidence}% >= {threshold}%, Validation: PASS)"
        )

        # Update ticket in database if present
        if ticket:
            old_status = ticket.status.value
            ticket.ai_confidence = int(final_confidence)
            ticket.final_response = resolution.get("passenger_response", "")

            if should_escalate:
                ticket.status = TicketStatus.NEEDS_REVIEW
                new_status_str = "Escalated"
            else:
                ticket.status = TicketStatus.RESOLVED
                new_status_str = "AI Resolved"

            # Add internal note documenting escalation decision
            note = TicketNote(
                ticket_id=ticket.id,
                author_id=None,
                message_type="ESCALATION_REASON" if should_escalate else "AI_RESPONSE",
                content=f"Workflow Decision: {decision_summary}\n\nDraft Passenger Response:\n{ticket.final_response}"
            )
            self.db.add(note)
            self.db.commit()

            record_status_change(
                db=self.db,
                ticket_id=ticket.id,
                old_status=old_status,
                new_status=ticket.status.value,
                changed_by_id=None,
                reason=decision_summary
            )

            record_audit_event(
                db=self.db,
                entity_type="TICKET",
                entity_id=str(ticket.id),
                action="WORKFLOW_ESCALATION_DECISION",
                actor_id=None,
                details={
                    "final_outcome": final_outcome,
                    "confidence": final_confidence,
                    "reasons": escalate_reasons
                }
            )

        outputs = {
            "decision": final_outcome,
            "final_confidence": final_confidence,
            "threshold_used": threshold,
            "requires_human_agent": should_escalate,
            "escalation_reasons": escalate_reasons,
            "decision_summary": decision_summary,
            "assigned_queue": "Tier 2 Support Specialist" if should_escalate else "Resolved Queue"
        }

        updated_state = dict(state)
        updated_state["escalation"] = outputs
        updated_state["final_outcome"] = final_outcome
        updated_state["final_confidence"] = final_confidence

        return "COMPLETED", outputs, updated_state
