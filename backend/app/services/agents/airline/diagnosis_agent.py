import re
from typing import Dict, Any, Tuple
from app.services.agents.base import BaseAgent
from app.policies.confidence_policy import CATEGORY_FINGERPRINTS

class DiagnosisAgent(BaseAgent):
    def __init__(self, name: str = "Diagnosis Agent"):
        super().__init__(name=name)

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket = state.get("ticket", {})
        title = ticket.get("title", "") or ticket.get("subject", "")
        description = ticket.get("description", "")
        reported_category = ticket.get("category", "Other")
        
        combined = f"{title} {description}".lower()

        # Extract entities: PNR, Flight Number, Travel Date, Passenger Name
        extracted_entities = {}
        
        # PNR regex (e.g., AA-12345, PNR-89412, 6-char alphanumeric like QW78ZX)
        pnr_match = re.search(r'\b([A-Z]{2}-?\d{4,6}|[A-Z0-9]{6})\b', f"{title} {description}")
        if pnr_match:
            extracted_entities["booking_reference"] = pnr_match.group(1).upper()
        elif ticket.get("booking_reference"):
            extracted_entities["booking_reference"] = ticket.get("booking_reference")

        # Flight Number regex (e.g., FL-342, AA102, DL890)
        flight_match = re.search(r'\b([A-Z]{2}\s?-?\d{2,4})\b', f"{title} {description}")
        if flight_match:
            extracted_entities["flight_number"] = flight_match.group(1).upper().replace(" ", "")
        elif ticket.get("flight_number"):
            extracted_entities["flight_number"] = ticket.get("flight_number")

        # Passenger name & email
        if ticket.get("passenger_name"):
            extracted_entities["passenger_name"] = ticket.get("passenger_name")
        if ticket.get("passenger_email"):
            extracted_entities["passenger_email"] = ticket.get("passenger_email")

        # Detect category based on airline category fingerprints
        matched_category = reported_category
        highest_match = 0
        all_detected_kws = []

        for cat, kws in CATEGORY_FINGERPRINTS.items():
            matches = [kw for kw in kws if re.search(r'\b' + re.escape(kw) + r'\b', combined)]
            if matches:
                all_detected_kws.extend(matches)
            if len(matches) > highest_match:
                highest_match = len(matches)
                matched_category = cat

        missing_info = []
        if not extracted_entities.get("booking_reference"):
            missing_info.append("Booking Reference (PNR)")
        if not extracted_entities.get("flight_number"):
            missing_info.append("Flight Number")

        # Check urgency and disruption impact
        is_urgent = False
        urgency_reason = "Standard inquiry"
        if any(term in combined for term in ["delayed", "cancelled", "stranded", "emergency", "wheelchair", "missed connection"]):
            is_urgent = True
            urgency_reason = "Imminent travel disruption or passenger accessibility assistance"

        outputs = {
            "issue_summary": f"Passenger inquiry regarding {matched_category.lower()}: {title}",
            "category": matched_category,
            "extracted_entities": extracted_entities,
            "detected_keywords": list(dict.fromkeys(all_detected_kws))[:8],
            "missing_information": missing_info,
            "is_urgent": is_urgent,
            "urgency_reason": urgency_reason,
            "recommended_next_step": "Search airline knowledge base for applicable policy rules and entitlements"
        }

        updated_state = dict(state)
        updated_state["diagnosis"] = outputs
        updated_state["category"] = matched_category
        updated_state["entities"] = extracted_entities

        return "COMPLETED", outputs, updated_state
