"""
AeroAssist AI - Multi-Agent System (Milestone 3)
Implements the mandatory FIVE-AGENT sequential workflow:
1. Diagnosis Agent
2. Retrieval Agent
3. Resolution Agent
4. Validation Agent
5. Escalation Agent
"""
import os
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from classifier import get_classifier
from rag.retriever import get_retriever
from rag.pipeline import get_rag_pipeline
from jira_service import create_jira_issue
from email_service import send_escalation_email

DECISION_THRESHOLD = float(os.getenv("DECISION_THRESHOLD", "0.70"))

# ==============================================================================
# AGENT 1: DIAGNOSIS AGENT
# ==============================================================================
class DiagnosisAgent:
    """
    Agent 1: Understands passenger issue, extracts intent and entities,
    and produces structured diagnosis with statistical classification confidence score.
    """
    def __init__(self):
        self.classifier = get_classifier()

    def run(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        title = ticket_data.get("title", "")
        description = ticket_data.get("description", "")
        
        # Run classification
        cls_result = self.classifier.classify(title, description)
        category = cls_result["predicted_category"]
        raw_conf = cls_result["confidence"]

        # Semantic intent extraction distinguishing procedures vs errors vs requests
        intent = self._extract_intent(title, description, category)
        
        # Entity extraction (flight number, PNR, terminal/airport)
        entities = self._extract_entities(title, description, ticket_data)

        # Genuine statistical diagnosis confidence from classification engine
        diag_conf = round(float(raw_conf), 4)

        return {
            "agent_name": "Diagnosis Agent",
            "category": category,
            "intent": intent,
            "diagnosis": f"Passenger inquiry regarding {category.lower()} categorized under '{intent}'.",
            "extracted_entities": entities,
            "confidence": diag_conf,
            "status": "COMPLETED"
        }

    def _extract_intent(self, title: str, description: str, category: str) -> str:
        text = f"{title} {description}".lower()

        # 1. Check-in & Boarding
        if category == "Check-in & Boarding" or any(k in text for k in ["check-in", "check in", "boarding", "kiosk", "security"]):
            if any(err in text for err in ["error", "fail", "failed", "crash", "unable", "not working", "stuck", "cannot", "can't", "issue", "problem"]):
                if "boarding pass" in text:
                    return "Boarding pass generation and download error"
                return "Online check-in failure and error troubleshooting"
            elif any(proc in text for proc in ["how to check in", "online check-in", "web check-in", "mobile check-in", "check in online", "check-in process", "check-in procedure", "steps to check in", "complete online check-in"]):
                return "General online check-in procedure and steps"
            elif any(bp in text for bp in ["lost printed boarding pass", "misplaced", "lost boarding pass", "reprint boarding pass"]):
                return "Boarding gate departure and boarding pass reprint assistance"
            elif any(bp in text for bp in ["boarding pass", "digital boarding pass", "wallet", "bar code", "qr code", "print pass"]):
                if any(proc in text for proc in ["how", "obtain", "get", "download", "save", "retrieve"]):
                    return "Digital boarding pass issuance and retrieval"
                return "Boarding pass generation and wallet storage"
            elif any(k in text for k in ["kiosk", "self-service", "bag drop", "tag"]):
                return "Airport self-service kiosk and automated bag drop"
            elif any(k in text for k in ["gate", "zone", "final call", "departure time"]):
                return "Boarding gate departure and zone sequencing"
            elif any(k in text for k in ["security", "screening", "liquid", "100ml", "lag", "prohibited", "laptop", "scanner", "fireworks", "flares", "hazardous"]):
                return "Airport security screening guidelines and prohibited items"
            return "General online check-in procedure and steps"

        # 2. Baggage
        elif category == "Baggage" or any(k in text for k in ["baggage", "luggage", "suitcase", "carry-on", "cabin bag", "checked bag"]):
            if any(k in text for k in ["cabin", "carry-on", "carry on", "hand luggage", "overhead bin", "size allowed", "cabin baggage"]):
                return "Cabin baggage allowance and dimension guidelines"
            elif any(k in text for k in ["checked", "check in bag", "how many bags", "weight allowed", "per bag", "checked baggage"]):
                return "Checked baggage allowance and weight limits"
            elif any(k in text for k in ["delay", "delayed", "not arrive", "missing luggage", "carousel", "pir", "property irregularity"]):
                return "Delayed baggage reporting and PIR file creation"
            elif any(k in text for k in ["lost", "unclaimed", "21 days", "declare lost", "lost baggage claim", "compensation"]):
                return "Lost baggage claim process and compensation"
            elif any(k in text for k in ["damaged", "broken", "cracked", "torn", "wheel", "handle broken"]):
                return "Damaged baggage inspection and repair claims"
            elif any(k in text for k in ["excess", "extra weight", "overweight", "pre-book baggage"]):
                return "Excess baggage purchase and overweight charges"
            elif any(k in text for k in ["instrument", "sport", "pet", "special luggage"]):
                return "Special baggage, sporting equipment, and pet transport"
            return "Baggage allowance and luggage policy inquiry"

        # 3. Delays & Cancellations
        elif category == "Delays & Cancellations" or any(k in text for k in ["delay", "cancel", "reschedule", "late"]):
            if any(k in text for k in ["cancel", "cancelled", "canceled", "rebook"]):
                return "Flight cancellation procedures and rebooking options"
            elif any(k in text for k in ["delay", "delayed", "voucher", "refreshment", "meal", "hotel", "late"]):
                return "Flight delay policy, compensation, and refreshment care"
            return "Flight disruption and schedule change assistance"

        # 4. Booking & Confirmation
        elif category == "Booking & Confirmation" or any(k in text for k in ["booking", "e-ticket", "pnr", "itinerary", "name"]):
            if any(k in text for k in ["name", "correction", "passport update", "spelling"]):
                return "Passenger name correction and travel document update"
            elif any(k in text for k in ["confirm", "e-ticket", "receipt", "pnr", "itinerary"]):
                return "Booking confirmation, PNR lookup, and e-ticket issuance"
            return "Booking management and reservation inquiry"

        # 5. Refunds & Payments
        elif category == "Refunds & Payments" or any(k in text for k in ["refund", "payment", "charge", "fare", "voucher"]):
            if any(k in text for k in ["double", "duplicate", "failed", "card error"]):
                return "Payment failure and duplicate charge resolution"
            elif any(k in text for k in ["ancillary", "seat selection", "meal refund", "priority boarding"]):
                return "Paid ancillary and add-on service fee refund"
            elif any(k in text for k in ["refund", "reimburse", "claim cash"]):
                return "Ticket refund eligibility, processing times, and vouchers"
            return "Fare payment and refund inquiry"

        # 6. Airport Facilities
        elif category == "Airport Facilities" or any(k in text for k in ["lounge", "parking", "terminal", "wifi"]):
            if any(k in text for k in ["lounge", "vip", "club"]):
                return "Airport lounge access, locations, and amenities"
            elif any(k in text for k in ["parking", "park", "tariff", "car"]):
                return "Airport parking options, tariffs, and pre-booking"
            elif any(k in text for k in ["transport", "shuttle", "bus", "train", "transfer", "inter-transfer", "terminal transfer"]):
                return "Airport ground transportation and terminal transfers"
            return "Airport facilities, navigation, and amenities"

        # 7. Shopping & Services
        elif category == "Shopping & Services" or any(k in text for k in ["duty free", "tax", "vat", "dining", "restaurant", "food"]):
            if any(k in text for k in ["duty free", "duty-free", "customs allowance", "liquor", "tobacco"]):
                return "Airport duty free shopping and customs allowances"
            elif any(k in text for k in ["tax", "vat", "tourist refund"]):
                return "Airport VAT / Tax refund desk procedures"
            elif any(k in text for k in ["food", "dining", "restaurant", "dietary", "halal", "kosher"]):
                return "Dining, food courts, and special dietary options"
            return "Airport commercial retail and dining services"

        # 8. Passenger Assistance
        elif category == "Passenger Assistance" or any(k in text for k in ["wheelchair", "special assistance", "senior", "elderly", "minor", "child", "guide dog", "service animal"]):
            if any(k in text for k in ["wheelchair", "prm", "mobility", "disabled"]):
                return "Wheelchair and special mobility assistance requests"
            elif any(k in text for k in ["senior", "elderly", "unaccompanied minor", "child alone"]):
                return "Senior citizen and unaccompanied minor passenger care"
            elif any(k in text for k in ["lost and found", "left behind", "property recovery"]):
                return "Airport lost and found office and property recovery"
            elif any(k in text for k in ["guide dog", "service animal"]):
                return "Special passenger assistance and accredited guide dog travel"
            return "Special passenger assistance and accessibility support"

        return f"Passenger inquiry regarding {category}"

    def _extract_entities(self, title: str, description: str, ticket_data: Dict) -> Dict[str, Optional[str]]:
        combined = f"{title} {description}"
        
        flight = ticket_data.get("flight_number")
        if not flight:
            flight_match = re.search(r"\b([A-Z]{2}\s?\d{3,4})\b", combined)
            flight = flight_match.group(1) if flight_match else None

        pnr = ticket_data.get("booking_ref")
        if not pnr:
            pnr_match = re.search(r"\b([A-Z0-9]{6})\b", combined)
            pnr = pnr_match.group(1) if pnr_match else None

        return {
            "flight_number": flight,
            "booking_ref": pnr,
            "airport": ticket_data.get("airport")
        }


# ==============================================================================
# AGENT 2: RETRIEVAL AGENT
# ==============================================================================
class RetrievalAgent:
    """
    Agent 2: Searches the AeroAssist Knowledge Base using Milestone 2 RAG retriever
    (TF-IDF + Cosine Similarity).
    """
    def __init__(self):
        self.retriever = get_retriever()

    def run(self, ticket_data: Dict[str, Any], diagnosis_output: Dict[str, Any]) -> Dict[str, Any]:
        query = f"{ticket_data.get('title', '')} {ticket_data.get('description', '')} {diagnosis_output.get('intent', '')}"
        
        retrieval_res = self.retriever.retrieve(query, top_k=3)
        top_art = retrieval_res["top_article"]
        sim_score = retrieval_res["similarity_score"]
        found = retrieval_res["knowledge_found"]

        return {
            "agent_name": "Retrieval Agent",
            "knowledge_found": found,
            "top_article": top_art,
            "similarity_score": round(float(sim_score), 4),
            "ranked_articles": retrieval_res["ranked_articles"],
            "top_5_articles": retrieval_res.get("top_5_articles", retrieval_res["ranked_articles"][:5]),
            "relevance_threshold": retrieval_res["relevance_threshold"],
            "status": "COMPLETED"
        }


# ==============================================================================
# AGENT 3: RESOLUTION AGENT
# ==============================================================================
class ResolutionAgent:
    """
    Agent 3: Generates passenger-facing resolution grounded in retrieved knowledge.
    Calculates resolution completeness score.
    """
    def __init__(self):
        self.pipeline = get_rag_pipeline()

    def run(self, ticket_data: Dict[str, Any], diagnosis_output: Dict[str, Any], retrieval_output: Dict[str, Any]) -> Dict[str, Any]:
        # Formulate grounded resolution
        top_art = retrieval_output.get("top_article")
        found = retrieval_output.get("knowledge_found", False)
        sim_score = retrieval_output.get("similarity_score", 0.0)

        metadata = {
            "flight_number": ticket_data.get("flight_number"),
            "booking_ref": ticket_data.get("booking_ref"),
            "airport": ticket_data.get("airport"),
            "travel_date": ticket_data.get("travel_date")
        }

        if not found or not top_art:
            res_text = (
                f"We received your request regarding '{ticket_data.get('title')}'.\n"
                "Human support required. Because your inquiry requires non-standard airline verification or specific operational review, "
                "an automated resolution cannot be safely provided at this stage. Your request is being transferred to a "
                "human passenger support specialist."
            )
            steps = [
                "Ticket escalated to Airport Ground Customer Care.",
                "A human agent will review and contact you with operational guidance."
            ]
            completeness = 0.25
        else:
            steps = self.pipeline._extract_actionable_steps(top_art["content"], metadata)
            res_text = (
                f"Dear {ticket_data.get('passenger_name', 'Passenger')},\n\n"
                f"Thank you for contacting AeroAssist Support. Regarding your inquiry on '{ticket_data.get('title')}':\n\n"
                f"Procedural Guidance ({top_art['id']} - {top_art['title']}):\n{top_art['content']}\n\n"
                f"Recommended Next Steps:\n" + "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)]) +
                "\n\nIf you require further on-ground assistance, please present this ticket ID at our customer service counter."
            )
            # Completeness is high (0.95) when actionable guidance steps are present
            completeness = 0.95 if len(steps) >= 3 else (0.85 if len(steps) >= 1 else 0.70)

        return {
            "agent_name": "Resolution Agent",
            "resolution_text": res_text,
            "resolution_steps": steps,
            "resolution_completeness": round(float(completeness), 4),
            "status": "COMPLETED"
        }


# ==============================================================================
# AGENT 4: VALIDATION AGENT (QUALITY GATE)
# ==============================================================================
class ValidationAgent:
    """
    Agent 4: Quality Gate.
    Weighted Confidence Formula:
    Final Confidence = Diagnosis Confidence * 0.40 + Retrieval Similarity * 0.40 + Resolution Completeness * 0.20
    Evaluates against decision threshold (70%).
    """
    def __init__(self, threshold: float = DECISION_THRESHOLD):
        self.threshold = threshold

    def run(self, diag_output: Dict[str, Any], ret_output: Dict[str, Any], res_output: Dict[str, Any]) -> Dict[str, Any]:
        diag_conf = diag_output.get("confidence", 0.0)
        ret_sim = ret_output.get("similarity_score", 0.0)
        res_comp = res_output.get("resolution_completeness", 0.0)

        # Weighted calculation
        final_conf = (diag_conf * 0.40) + (ret_sim * 0.40) + (res_comp * 0.20)
        final_conf = round(float(final_conf), 4)

        passes = bool(final_conf >= self.threshold)

        return {
            "agent_name": "Validation Agent",
            "diagnosis_confidence": diag_conf,
            "retrieval_similarity": ret_sim,
            "resolution_completeness": res_comp,
            "weights": {"diagnosis": 0.40, "retrieval": 0.40, "completeness": 0.20},
            "final_confidence": final_conf,
            "threshold": self.threshold,
            "passes_threshold": passes,
            "status": "COMPLETED"
        }


# ==============================================================================
# AGENT 5: ESCALATION AGENT
# ==============================================================================
class EscalationAgent:
    """
    Agent 5: Executes final outcome decision.
    If Final AI Confidence >= Threshold (70%): AUTO_RESOLVE
    If Final AI Confidence < Threshold: ESCALATE (triggers human handoff, Jira & Email if configured).
    """
    def run(self, ticket_data: Dict[str, Any], validation_output: Dict[str, Any], res_output: Dict[str, Any], diag_output: Dict[str, Any], ret_output: Dict[str, Any]) -> Dict[str, Any]:
        passes = validation_output.get("passes_threshold", False)
        final_conf = validation_output.get("final_confidence", 0.0)

        if passes:
            # AUTO_RESOLVE PATH
            return {
                "agent_name": "Escalation Agent",
                "workflow_status": "AUTO_RESOLVE",
                "decision": "AUTO_RESOLVE",
                "escalation_required": False,
                "escalation_reason": "Confidence exceeds decision threshold. Ticket auto-resolved.",
                "jira_status": "Not Required (Auto-Resolved)",
                "jira_created": False,
                "jira_issue_key": None,
                "jira_issue_url": None,
                "jira_message": None,
                "email_status": "Not Required (Auto-Resolved)",
                "status": "COMPLETED"
            }
        else:
            # ESCALATION PATH (Human support required)
            reason = (
                f"Final confidence ({final_conf * 100:.1f}%) is below the required {validation_output.get('threshold') * 100:.0f}% threshold. "
                f"Knowledge similarity ({ret_output.get('similarity_score', 0.0) * 100:.1f}%) insufficient for automated guarantee."
            )

            top_art = ret_output.get("top_article") or {}

            escalation_payload = {
                "escalation_reason": reason,
                "final_confidence": final_conf,
                "threshold": validation_output.get("threshold", self.threshold if hasattr(self, 'threshold') else 0.70),
                "diagnosis_text": diag_output.get("diagnosis"),
                "diagnosis_intent": diag_output.get("intent"),
                "diagnosis_confidence": diag_output.get("confidence"),
                "retrieved_kb_id": top_art.get("id"),
                "retrieved_kb_title": top_art.get("title"),
                "retrieval_similarity": ret_output.get("similarity_score"),
                "resolution_text": res_output.get("resolution_text"),
                "resolution_completeness": res_output.get("resolution_completeness")
            }

            # Duplicate protection: check if ticket already has an active Jira issue
            existing_jira_key = ticket_data.get("jira_issue_key")
            existing_jira_url = ticket_data.get("jira_issue_url")
            ticket_id = ticket_data.get("ticket_id")

            if not existing_jira_key and ticket_id:
                try:
                    from database import get_existing_jira_for_ticket
                    existing_jira = get_existing_jira_for_ticket(ticket_id)
                    if existing_jira:
                        existing_jira_key = existing_jira.get("issue_key")
                        existing_jira_url = existing_jira.get("issue_url")
                except Exception:
                    pass

            # Dispatch to external integrations (Jira & Email)
            jira_res = create_jira_issue(
                ticket_data=ticket_data,
                escalation_payload=escalation_payload,
                existing_issue_key=existing_jira_key,
                existing_issue_url=existing_jira_url
            )
            email_res = send_escalation_email(ticket_data, escalation_payload)

            return {
                "agent_name": "Escalation Agent",
                "workflow_status": "ESCALATE",
                "decision": "ESCALATE",
                "escalation_required": True,
                "escalation_reason": reason,
                "jira_status": jira_res.get("status", "Not Configured"),
                "jira_created": jira_res.get("jira_created", False),
                "jira_issue_key": jira_res.get("issue_key"),
                "jira_issue_id": jira_res.get("issue_id"),
                "jira_issue_url": jira_res.get("issue_url"),
                "jira_sync_status": jira_res.get("sync_status", "Not Configured"),
                "jira_last_error": jira_res.get("last_error"),
                "jira_created_at": jira_res.get("created_at"),
                "jira_message": jira_res.get("message"),
                "email_status": email_res.get("status", "Not Configured"),
                "email_message": email_res.get("message"),
                "status": "COMPLETED"
            }


# ==============================================================================
# MULTI-AGENT ORCHESTRATOR
# ==============================================================================
class MultiAgentSystem:
    """
    Coordinates the 5 agents sequentially:
    Diagnosis -> Retrieval -> Resolution -> Validation -> Escalation
    """
    def __init__(self, threshold: float = DECISION_THRESHOLD):
        self.threshold = threshold
        self.agent_diagnosis = DiagnosisAgent()
        self.agent_retrieval = RetrievalAgent()
        self.agent_resolution = ResolutionAgent()
        self.agent_validation = ValidationAgent(threshold=threshold)
        self.agent_escalation = EscalationAgent()

    def process_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Diagnosis Agent
        diagnosis = self.agent_diagnosis.run(ticket_data)

        # 2. Retrieval Agent
        retrieval = self.agent_retrieval.run(ticket_data, diagnosis)

        # 3. Resolution Agent
        resolution = self.agent_resolution.run(ticket_data, diagnosis, retrieval)

        # 4. Validation Agent
        validation = self.agent_validation.run(diagnosis, retrieval, resolution)

        # 5. Escalation Agent
        escalation = self.agent_escalation.run(ticket_data, validation, resolution, diagnosis, retrieval)

        # Integrated multi-agent payload
        top_art = retrieval.get("top_article")
        return {
            "ticket_id": ticket_data.get("ticket_id"),
            "workflow_status": escalation["workflow_status"],
            "decision": escalation["decision"],
            "diagnosis_category": diagnosis["category"],
            "diagnosis_intent": diagnosis["intent"],
            "diagnosis_confidence": diagnosis["confidence"],
            "extracted_entities": diagnosis["extracted_entities"],
            "retrieval_found": retrieval["knowledge_found"],
            "retrieved_kb_id": top_art["id"] if top_art else None,
            "retrieved_kb_title": top_art["title"] if top_art else None,
            "retrieval_similarity": retrieval["similarity_score"],
            "ranked_articles": retrieval["ranked_articles"],
            "resolution_text": resolution["resolution_text"],
            "resolution_steps": resolution["resolution_steps"],
            "resolution_completeness": resolution["resolution_completeness"],
            "final_confidence": validation["final_confidence"],
            "threshold": validation["threshold"],
            "escalation_required": escalation["escalation_required"],
            "escalation_reason": escalation["escalation_reason"],
            "jira_status": escalation["jira_status"],
            "jira_created": escalation.get("jira_created", False),
            "jira_issue_key": escalation.get("jira_issue_key"),
            "jira_issue_url": escalation.get("jira_issue_url"),
            "jira_message": escalation.get("jira_message"),
            "email_status": escalation["email_status"],
            "email_message": escalation.get("email_message"),
            "agent_trace": [
                diagnosis,
                retrieval,
                resolution,
                validation,
                escalation
            ]
        }


# Global singleton instance
_mas_instance = None

def get_multi_agent_system(threshold: float = DECISION_THRESHOLD) -> MultiAgentSystem:
    global _mas_instance
    if _mas_instance is None:
        _mas_instance = MultiAgentSystem(threshold=threshold)
    return _mas_instance
