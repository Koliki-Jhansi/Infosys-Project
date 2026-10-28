from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.models.ticket import Ticket
from app.models.classification import TicketClassification

class PriorityCriticalityAgent(BaseAgent):
    def __init__(self, db: Session, name: str = "Priority and Criticality Analysis"):
        super().__init__(name=name)
        self.db = db

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket_data = state.get("ticket", {})
        ticket_id = ticket_data.get("id")
        diagnosis = state.get("diagnosis", {})
        
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first() if ticket_id else None

        # Check existing classification in DB or state
        existing_class = ticket.classification if ticket else None
        
        title_lower = (ticket_data.get("title") or "").lower()
        desc_lower = (ticket_data.get("description") or "").lower()
        category = diagnosis.get("category") or ticket_data.get("category") or "General"
        is_urgent = diagnosis.get("is_urgent", False)
        
        # Analyze priority & criticality
        if any(w in title_lower or w in desc_lower for w in ["medical", "emergency", "stranded", "safety", "wheelchair", "unaccompanied"]):
            priority = "P1 Critical"
            criticality = "Critical"
            reason = "Safety, special assistance, or emergency flight operational priority"
            conf = 92.0
        elif is_urgent or any(w in title_lower or w in desc_lower for w in ["cancelled", "missed connection", "diversion", "delay"]):
            priority = "P2 High"
            criticality = "High"
            reason = "Direct flight schedule disruption or missed connecting flight"
            conf = 88.0
        elif any(w in title_lower or w in desc_lower for w in ["lost baggage", "damaged bag", "refund", "rebooking"]):
            priority = "P3 Medium"
            criticality = "Medium"
            reason = "Standard baggage or rebooking passenger service request"
            conf = 84.0
        else:
            priority = existing_class.priority if existing_class else "P4 Low"
            criticality = existing_class.criticality if existing_class else "Low"
            reason = "General flight policy or procedural inquiry"
            conf = 80.0

        if existing_class:
            if not existing_class.priority:
                existing_class.priority = priority
            else:
                priority = existing_class.priority
            if not existing_class.criticality:
                existing_class.criticality = criticality
            else:
                criticality = existing_class.criticality
            self.db.commit()
        elif ticket:
            new_class = TicketClassification(
                ticket_id=ticket.id,
                predicted_category=category,
                priority=priority,
                criticality=criticality,
                confidence_score=conf,
                explanation=reason,
                detected_keywords=diagnosis.get("detected_keywords", []),
                potential_business_impact=criticality,
                recommended_next_action="AI Grounded Resolution",
                missing_information=diagnosis.get("missing_information", []),
                requires_human_review=(priority == "P1 Critical"),
                review_reason=reason if priority == "P1 Critical" else None,
                model_name="AeroAssist-Triage-v1"
            )
            self.db.add(new_class)
            self.db.commit()

        outputs = {
            "priority": priority,
            "criticality": criticality,
            "confidence_score": conf,
            "reasoning": reason,
            "category": category
        }

        updated_state = dict(state)
        updated_state["priority_criticality"] = outputs
        if "classification" not in updated_state or not updated_state["classification"]:
            updated_state["classification"] = outputs
        else:
            updated_state["classification"]["priority"] = priority
            updated_state["classification"]["criticality"] = criticality

        return "COMPLETED", outputs, updated_state
