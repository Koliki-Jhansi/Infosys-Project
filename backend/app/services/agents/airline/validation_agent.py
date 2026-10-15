from typing import Dict, Any, Tuple
from app.services.agents.base import BaseAgent

class ValidationAgent(BaseAgent):
    def __init__(self, name: str = "Validation Agent"):
        super().__init__(name=name)

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket = state.get("ticket", {})
        diagnosis = state.get("diagnosis", {})
        retrieval = state.get("retrieval", {})
        resolution = state.get("resolution", {})

        response_text = resolution.get("passenger_response", "")
        sources = retrieval.get("sources", [])
        has_evidence = retrieval.get("has_sufficient_evidence", False)
        missing_info = diagnosis.get("missing_information", [])

        validation_checks = []
        is_valid = True
        verdict = "PASS"
        rejection_reasons = []

        # Check 1: Evidence backing
        if not has_evidence or not sources:
            validation_checks.append({
                "check": "Knowledge Grounding Check",
                "status": "CAUTION",
                "detail": "No direct high-relevance airline policy chunks retrieved; requires human escalation."
            })
            verdict = "NEEDS_REVISION"
            rejection_reasons.append("Insufficient knowledge base grounding")
        else:
            validation_checks.append({
                "check": "Knowledge Grounding Check",
                "status": "PASS",
                "detail": f"Verified against {len(sources)} airline policy document chunks."
            })

        # Check 2: Unauthorized financial commitments
        unauthorized_phrases = ["guaranteed full refund of $", "refund approved immediately without documentation", "compensation guaranteed"]
        found_unauthorized = [p for p in unauthorized_phrases if p in response_text.lower()]
        if found_unauthorized:
            validation_checks.append({
                "check": "Financial Liability Guardrail",
                "status": "FAIL",
                "detail": f"Response contains unauthorized financial commitment: {found_unauthorized}"
            })
            is_valid = False
            verdict = "FAIL"
            rejection_reasons.append("Unauthorized financial commitment detected")
        else:
            validation_checks.append({
                "check": "Financial Liability Guardrail",
                "status": "PASS",
                "detail": "No unauthorized financial guarantees detected."
            })

        # Check 3: Missing essential identifier check
        if "Booking Reference (PNR)" in missing_info and "Flight Number" in missing_info:
            validation_checks.append({
                "check": "Flight Entity Specificity",
                "status": "CAUTION",
                "detail": "Both PNR and Flight Number missing from ticket input."
            })
        else:
            validation_checks.append({
                "check": "Flight Entity Specificity",
                "status": "PASS",
                "detail": "Passenger flight identifiers confirmed."
            })

        # Check 4: Tone and clarity check
        has_polite_salutation = "Dear" in response_text or "Hello" in response_text
        if has_polite_salutation and len(response_text) > 80:
            validation_checks.append({
                "check": "Tone and Passenger Courtesy",
                "status": "PASS",
                "detail": "Complies with AeroAssist passenger communication standards."
            })
        else:
            validation_checks.append({
                "check": "Tone and Passenger Courtesy",
                "status": "FAIL",
                "detail": "Response too terse or missing courteous salutation."
            })
            verdict = "FAIL"
            rejection_reasons.append("Inadequate response length or greeting structure")

        confidence_adjustment = 0.0
        if verdict == "PASS":
            confidence_adjustment = +5.0
        elif verdict == "NEEDS_REVISION":
            confidence_adjustment = -10.0
        else:
            confidence_adjustment = -25.0

        outputs = {
            "verdict": verdict,
            "is_valid": is_valid,
            "validation_checks": validation_checks,
            "rejection_reasons": rejection_reasons,
            "confidence_adjustment": confidence_adjustment,
            "summary": "Response passed all safety and grounding checks" if verdict == "PASS" else "; ".join(rejection_reasons)
        }

        updated_state = dict(state)
        updated_state["validation"] = outputs
        updated_state["is_valid"] = is_valid
        updated_state["verdict"] = verdict

        return "COMPLETED", outputs, updated_state
