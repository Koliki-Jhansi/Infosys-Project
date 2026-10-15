from typing import Dict, Any, Tuple
from app.services.agents.base import BaseAgent
from app.policies.priority_policy import detect_security_signals

class TicketTriageAgent(BaseAgent):
    def __init__(self):
        super().__init__("Ticket Triage Agent")

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket = state.get("ticket", {})
        classification = state.get("classification", {})
        
        title = ticket.get("title", "")
        description = ticket.get("description", "")
        error_logs = ticket.get("error_logs", "")
        category = ticket.get("category", "")
        urgency = ticket.get("urgency", "")
        impact = ticket.get("business_impact", "")
        affected_users = ticket.get("affected_users", 1)
        priority = classification.get("priority", "P3 Medium")
        confidence = classification.get("confidence_score", 0.0)

        # 1. Identify missing operational signals
        missing = []
        if len(description.split()) < 15:
            missing.append("Detailed steps to reproduce or observed error dialog")
        if not error_logs and ("error" in description.lower() or "exception" in description.lower()):
            missing.append("Applicable server logs or console traces")

        # 2. Security signals check
        sec_signals = detect_security_signals(f"{title} {description} {error_logs}")
        is_security_alert = (category.lower() == "security" or len(sec_signals) > 0)

        # 3. Determine if triage mandates human review gate
        is_p1 = (priority == "P1 Critical" or urgency == "Critical")
        low_confidence = (confidence < 70.0)

        requires_review = is_p1 or is_security_alert or low_confidence
        review_reasons = []
        if is_p1:
            review_reasons.append("P1 Critical triage safety policy")
        if is_security_alert:
            review_reasons.append(f"Security indicators detected ({', '.join(sec_signals) if sec_signals else 'Sec Category'})")
        if low_confidence:
            review_reasons.append(f"Confidence score {confidence}% is below 70% threshold")

        triage_status = "COMPLETED"
        if requires_review and not state.get("human_approved", False):
            triage_status = "WAITING_FOR_REVIEW"

        outputs = {
            "triage_summary": f"Incident triaged for service '{ticket.get('affected_service')}'. Priority: {priority}, Confidence: {confidence}%.",
            "is_security_alert": is_security_alert,
            "security_signals": sec_signals,
            "missing_information": missing,
            "requires_human_review": requires_review,
            "review_reasons": review_reasons,
            "cleared_for_automated_analysis": not requires_review or state.get("human_approved", False)
        }

        updated_state = {
            **state,
            "triage": outputs
        }

        return triage_status, outputs, updated_state
