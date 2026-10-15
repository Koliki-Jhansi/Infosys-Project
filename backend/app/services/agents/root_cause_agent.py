from typing import Dict, Any, Tuple, List
from app.services.agents.base import BaseAgent

class RootCauseAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("Root Cause Analysis Agent")

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket = state.get("ticket", {})
        classification = state.get("classification", {})
        retrieval = state.get("retrieval", {})
        sources = retrieval.get("sources", [])

        title = ticket.get("title", "")
        description = ticket.get("description", "")
        error_logs = ticket.get("error_logs", "")
        service = ticket.get("affected_service", "")
        category = ticket.get("category", "")

        # 1. Confirmed facts extracted directly from telemetry/logs
        confirmed_facts = [
            f"Service affected: {service}",
            f"Environment: {ticket.get('environment', 'production').upper()}",
            f"Impact scale: {ticket.get('affected_users', 1)} user(s) impacted ({ticket.get('business_impact')})",
        ]
        if error_logs:
            first_log = error_logs.strip().split("\n")[0][:120]
            confirmed_facts.append(f"Recorded diagnostic signal: '{first_log}'")

        # 2. Ranked Hypotheses
        hypotheses = []
        if sources and len(sources) > 0:
            top_doc = sources[0]["document_title"]
            hypotheses.append({
                "rank": 1,
                "hypothesis": f"Primary operational failure matching documented pattern in '{top_doc}'",
                "confidence": "HIGH" if sources[0]["similarity_score"] >= 70 else "MODERATE",
                "grounded_source": top_doc
            })
            if len(sources) > 1:
                hypotheses.append({
                    "rank": 2,
                    "hypothesis": f"Secondary failure mode related to '{sources[1]['document_title']}'",
                    "confidence": "MODERATE",
                    "grounded_source": sources[1]["document_title"]
                })
        else:
            hypotheses.append({
                "rank": 1,
                "hypothesis": "Undocumented failure mode or environmental anomaly without internal runbook match",
                "confidence": "LOW",
                "grounded_source": "None"
            })

        # 3. Assumptions vs Facts
        assumptions = [
            "Assumes network infrastructure between upstream caller and service is functional.",
            "Assumes application configuration has not undergone unannounced manual mutations."
        ]

        # 4. Diagnostic recommendations
        diagnostic_checks = [
            f"Query active connections, CPU/Memory telemetry, and error rates for '{service}'.",
            "Inspect recent deployment commits or infrastructure config maps applied in the last 2 hours."
        ]
        if sources:
            diagnostic_checks.append(f"Follow diagnostic commands outlined in '{sources[0]['document_title']}'.")

        outputs = {
            "summary": f"RCA formulated {len(hypotheses)} ranked hypothesis(es) for {service}.",
            "confirmed_facts": confirmed_facts,
            "assumptions": assumptions,
            "ranked_hypotheses": hypotheses,
            "diagnostic_checks": diagnostic_checks
        }

        updated_state = {
            **state,
            "root_cause_analysis": outputs
        }

        return "COMPLETED", outputs, updated_state
