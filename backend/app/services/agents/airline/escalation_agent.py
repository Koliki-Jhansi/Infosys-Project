from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.services.agents.base import BaseAgent
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_note import TicketNote
from app.models.jira import JiraIssueRecord
from app.services.jira.client import JiraClientService
from app.services.email.email_service import EmailDeliveryService
from app.services.audit.audit_service import record_audit_event, record_status_change
from app.core.config import settings
from app.core.logging import logger

class EscalationAgent(BaseAgent):
    def __init__(self, db: Session, name: str = "Escalation Agent"):
        super().__init__(name=name)
        self.db = db

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket_data = state.get("ticket", {})
        ticket_id = ticket_data.get("id")
        classification = state.get("classification", {})
        diagnosis = state.get("diagnosis", {})
        retrieval = state.get("retrieval", {})
        validation = state.get("validation", {})
        resolution = state.get("resolution", {})

        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first() if ticket_id else None

        # Determine actual grounded confidence score
        has_evidence = retrieval.get("has_sufficient_evidence", True)
        if "confidence_score" in classification and classification["confidence_score"]:
            base_conf = float(classification["confidence_score"])
        elif has_evidence:
            base_conf = 84.0
        else:
            base_conf = 56.0

        conf_adj = validation.get("confidence_adjustment", 0.0)
        final_confidence = round(max(0.0, min(100.0, base_conf + conf_adj)), 1)

        threshold = settings.CONFIDENCE_THRESHOLD  # default 70.0
        verdict = validation.get("verdict", "PASS")
        is_urgent = diagnosis.get("is_urgent", False)
        category = diagnosis.get("category", "") or (ticket.category if ticket else "General")

        escalate_reasons = []
        should_escalate = False

        if final_confidence < threshold:
            should_escalate = True
            escalate_reasons.append(f"Confidence score ({final_confidence}%) is below {threshold}% threshold")

        if verdict != "PASS":
            should_escalate = True
            escalate_reasons.append(f"Validation checks flagged: {validation.get('summary', 'Validation checks failed')}")

        if category in ["Special Assistance", "Security"]:
            should_escalate = True
            escalate_reasons.append(f"Category '{category}' mandates human specialist authorization")

        if is_urgent and final_confidence < 85.0:
            should_escalate = True
            escalate_reasons.append("High urgency travel disruption requires station manager oversight")

        jira_record_dict: Optional[Dict[str, Any]] = None
        email_record_dict: Optional[Dict[str, Any]] = None
        jira_error_msg: Optional[str] = None
        final_outcome = "ESCALATED" if should_escalate else "RESOLVED"

        if should_escalate:
            # 1. Low Confidence / Escalation: Create Jira Ticket
            try:
                jira_client = JiraClientService()
                idempotency_key = f"manual_sync_ticket_{ticket.id}" if ticket else f"wf_escalate_{state.get('workflow_id', 0)}"

                # Check for existing record to prevent duplicate Jira tickets
                existing_jira = (
                    self.db.query(JiraIssueRecord)
                    .filter(
                        (JiraIssueRecord.ticket_id == ticket.id) |
                        (JiraIssueRecord.idempotency_key == idempotency_key)
                    )
                    .first()
                ) if ticket else None

                if existing_jira:
                    jira_record = existing_jira
                    jira_record_dict = {
                        "jira_key": jira_record.jira_key,
                        "jira_url": jira_record.jira_url,
                        "status": jira_record.status,
                        "priority": jira_record.priority,
                        "is_existing": True
                    }
                else:
                    priority_str = (
                        classification.get("priority")
                        or (ticket.classification.priority if ticket and ticket.classification else None)
                        or (ticket.urgency if ticket else "P3 Medium")
                    )
                    criticality_str = (
                        classification.get("criticality")
                        or (ticket.classification.criticality if ticket and ticket.classification else None)
                        or (ticket.business_impact if ticket else "Medium")
                    )

                    jira_desc = (
                        f"**AeroAssist Flight Operations Escalation — Ticket #{ticket.id if ticket else 'N/A'}: {ticket.title if ticket else 'N/A'}**\n\n"
                        f"*Priority:* {priority_str} | *Criticality:* {criticality_str}\n"
                        f"*Passenger:* {ticket.passenger_name if ticket else 'N/A'} "
                        f"(PNR: {ticket.booking_reference if ticket else 'N/A'}, Flight: {ticket.flight_number if ticket else 'N/A'})\n"
                        f"*Category:* {category}\n\n"
                        f"**Issue Description:**\n{ticket.description if ticket else 'N/A'}\n\n"
                        f"**Escalation Analysis:**\n"
                        f"- AI Confidence Score: {final_confidence}% (< {threshold}%)\n"
                        f"- Escalation Reasons: {'; '.join(escalate_reasons)}\n"
                        f"- Missing Information: {diagnosis.get('missing_information', [])}\n\n"
                        f"**Draft AI Resolution (Pending Human Review):**\n"
                        f"{resolution.get('passenger_response', 'N/A')}\n"
                    )

                    jira_res = await jira_client.create_issue(
                        summary=f"[{category}] {ticket.title if ticket else 'Passenger Incident'}",
                        description=jira_desc,
                        priority=priority_str,
                        project_key=settings.JIRA_PROJECT_KEY,
                        assignee="Support Specialist",
                        idempotency_key=idempotency_key
                    )

                    jira_record = JiraIssueRecord(
                        ticket_id=ticket.id if ticket else 0,
                        workflow_id=state.get("workflow_id"),
                        jira_key=jira_res["key"],
                        jira_url=jira_res["url"],
                        project_key=jira_res.get("project_key", settings.JIRA_PROJECT_KEY),
                        issue_type=jira_res.get("issue_type", "Task"),
                        summary=f"[{category}] {ticket.title if ticket else 'Passenger Incident'}",
                        priority=jira_res.get("priority", priority_str),
                        status=jira_res.get("status", "To Do"),
                        idempotency_key=idempotency_key,
                        metadata_payload=jira_res
                    )
                    self.db.add(jira_record)
                    self.db.commit()
                    self.db.refresh(jira_record)

                    jira_record_dict = {
                        "jira_key": jira_record.jira_key,
                        "jira_url": jira_record.jira_url,
                        "status": jira_record.status,
                        "priority": jira_record.priority,
                        "is_existing": False
                    }

                # Mark ticket as escalated ONLY after Jira confirms successful creation
                if ticket:
                    old_status = ticket.status.value
                    ticket.status = TicketStatus.NEEDS_REVIEW
                    ticket.ai_confidence = int(final_confidence)
                    ticket.final_response = resolution.get("passenger_response", "")

                    note = TicketNote(
                        ticket_id=ticket.id,
                        author_id=None,
                        message_type="ESCALATION_REASON",
                        content=(
                            f"Workflow Decision: Escalated to Jira ({jira_record_dict['jira_key']}).\n"
                            f"Reasons: {'; '.join(escalate_reasons)}\n"
                            f"Jira URL: {jira_record_dict['jira_url']}"
                        )
                    )
                    self.db.add(note)
                    self.db.commit()

                    record_status_change(
                        db=self.db,
                        ticket_id=ticket.id,
                        old_status=old_status,
                        new_status=ticket.status.value,
                        changed_by_id=None,
                        reason=f"Jira issue {jira_record_dict['jira_key']} created. Confidence {final_confidence}%."
                    )

                    record_audit_event(
                        db=self.db,
                        entity_type="TICKET",
                        entity_id=str(ticket.id),
                        action="WORKFLOW_JIRA_ESCALATED",
                        actor_id=None,
                        details={
                            "jira_key": jira_record_dict["jira_key"],
                            "confidence": final_confidence,
                            "reasons": escalate_reasons
                        }
                    )

            except Exception as e:
                jira_error_msg = str(e)
                final_outcome = "ESCALATION_FAILED"
                logger.error(f"Jira escalation creation failed: {jira_error_msg}")
                # Do NOT mark ticket escalated if Jira creation failed

        else:
            # 2. High Confidence (>= 70%): AI Solution approved & send email
            if ticket:
                old_status = ticket.status.value
                ticket.status = TicketStatus.RESOLVED
                ticket.resolved_at = datetime.now(timezone.utc)
                ticket.ai_confidence = int(final_confidence)
                ticket.final_response = resolution.get("passenger_response", "")

                # Send email using configured email service
                email_service = EmailDeliveryService()
                recipient_email = ticket.passenger_email or (ticket.reporter.email if ticket.reporter else None)
                email_res = email_service.send_solution_email(
                    recipient_email=recipient_email,
                    passenger_name=ticket.passenger_name or (ticket.reporter.full_name if ticket.reporter else "Passenger"),
                    ticket_number=ticket.ticket_number or f"TK-{ticket.id:04d}",
                    ticket_title=ticket.title,
                    solution_text=ticket.final_response
                )
                email_record_dict = email_res

                note = TicketNote(
                    ticket_id=ticket.id,
                    author_id=None,
                    message_type="AI_RESPONSE",
                    content=(
                        f"Workflow Decision: Automated Resolution Approved (Confidence: {final_confidence}%).\n\n"
                        f"Email Status: {email_res.get('status')} - {email_res.get('message')}\n\n"
                        f"Passenger Response:\n{ticket.final_response}"
                    )
                )
                self.db.add(note)
                self.db.commit()

                record_status_change(
                    db=self.db,
                    ticket_id=ticket.id,
                    old_status=old_status,
                    new_status=ticket.status.value,
                    changed_by_id=None,
                    reason=f"AI Resolution approved with {final_confidence}% confidence. Email status: {email_res.get('status')}."
                )

                record_audit_event(
                    db=self.db,
                    entity_type="TICKET",
                    entity_id=str(ticket.id),
                    action="WORKFLOW_AI_RESOLVED",
                    actor_id=None,
                    details={
                        "confidence": final_confidence,
                        "email_delivery": email_res
                    }
                )

        decision_summary = (
            f"Escalated to Jira ({jira_record_dict.get('jira_key') if jira_record_dict else 'Pending'}): {'; '.join(escalate_reasons)}"
            if should_escalate and not jira_error_msg
            else f"Jira Escalation Failed: {jira_error_msg}"
            if jira_error_msg
            else f"AI Resolution Approved (Confidence: {final_confidence}% >= {threshold}%, Validation: PASS)"
        )

        outputs = {
            "decision": final_outcome,
            "final_confidence": final_confidence,
            "threshold_used": threshold,
            "requires_human_agent": should_escalate,
            "escalation_reasons": escalate_reasons,
            "decision_summary": decision_summary,
            "jira": jira_record_dict,
            "jira_error": jira_error_msg,
            "email_delivery": email_record_dict,
            "assigned_queue": "Tier 2 Support Specialist" if should_escalate else "Resolved Queue"
        }

        updated_state = dict(state)
        updated_state["escalation"] = outputs
        updated_state["final_outcome"] = final_outcome
        updated_state["final_confidence"] = final_confidence
        if jira_record_dict:
            updated_state["jira"] = jira_record_dict
        if email_record_dict:
            updated_state["email_delivery"] = email_record_dict

        return "COMPLETED" if not jira_error_msg else "FAILED", outputs, updated_state
