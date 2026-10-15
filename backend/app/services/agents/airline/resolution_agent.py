from typing import Dict, Any, Tuple
from app.services.agents.base import BaseAgent

class ResolutionAgent(BaseAgent):
    def __init__(self, name: str = "Resolution Agent"):
        super().__init__(name=name)

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket = state.get("ticket", {})
        diagnosis = state.get("diagnosis", {})
        retrieval = state.get("retrieval", {})
        
        passenger_name = ticket.get("passenger_name") or "Valued Passenger"
        booking_ref = ticket.get("booking_reference") or "your reservation"
        flight_num = ticket.get("flight_number") or "your flight"
        category = diagnosis.get("category", "General")
        sources = retrieval.get("sources", [])
        has_evidence = retrieval.get("has_sufficient_evidence", False)

        citations = []
        for s in sources[:3]:
            citations.append({
                "document_title": s["document_title"],
                "chunk_id": s["chunk_id"],
                "relevance_score": s["relevance_score"]
            })

        if not has_evidence or not sources:
            response_text = (
                f"Dear {passenger_name},\n\n"
                f"Thank you for reaching out to AeroAssist Passenger Support regarding {booking_ref}.\n\n"
                f"We have reviewed your request regarding your flight details. However, specific policy provisions "
                f"matching your exact circumstances could not be verified in our automated documentation library.\n\n"
                f"To ensure you receive accurate assistance, your case has been referred to an AeroAssist Customer Support Specialist "
                f"who will contact you directly within 2 business hours.\n\n"
                f"Warm regards,\nAeroAssist Customer Care Team"
            )
            policy_summary = "Insufficient automated evidence; referred to human support team."
            actionable_steps = [
                "Case logged in airline dispatch queue",
                "Assigned to airport station support specialist",
                "Direct passenger email/phone follow-up initiated"
            ]
        else:
            top_source = sources[0]
            doc_title = top_source["document_title"]
            excerpt = top_source["excerpt"]

            response_text = (
                f"Dear {passenger_name},\n\n"
                f"Thank you for contacting AeroAssist Customer Support regarding {flight_num} (Booking Reference: {booking_ref}).\n\n"
                f"In accordance with our airline policy '{doc_title}', we have verified the applicable guidelines for your inquiry:\n\n"
                f"• {excerpt[:280]}...\n\n"
                f"Next Steps & Entitlements:\n"
                f"1. Your request has been recorded under reference {ticket.get('id', 'NEW')}.\n"
                f"2. You can manage flight changes, check-in options, and baggage tracking directly through the AeroAssist mobile app or online portal.\n"
                f"3. If your inquiry involves an active airport delay or urgent baggage irregularity, please present your PIR / booking reference at the nearest AeroAssist Service Desk.\n\n"
                f"We appreciate your patience and look forward to welcoming you on board.\n\n"
                f"Warm regards,\nAeroAssist Passenger Solutions Team"
            )
            policy_summary = f"Grounded in '{doc_title}' ({category})"
            actionable_steps = [
                f"Consulted verified airline policy: {doc_title}",
                "Passenger notified of standard entitlements and timelines",
                "Reference number registered in airline servicing log"
            ]

        outputs = {
            "passenger_response": response_text,
            "policy_summary": policy_summary,
            "actionable_steps": actionable_steps,
            "supporting_citations": citations,
            "citations_count": len(citations),
            "generated_model": "aeroassist-resolution-synthesizer-v1"
        }

        updated_state = dict(state)
        updated_state["resolution"] = outputs
        updated_state["response_text"] = response_text
        updated_state["citations"] = citations

        return "COMPLETED", outputs, updated_state
