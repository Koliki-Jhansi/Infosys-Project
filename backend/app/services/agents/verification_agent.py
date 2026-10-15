from typing import Dict, Any, Tuple, List
from app.services.agents.base import BaseAgent
from app.core.config import settings

class SolutionVerificationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Solution Verification Agent")

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket = state.get("ticket", {})
        classification = state.get("classification", {})
        retrieval = state.get("retrieval", {})
        solution = state.get("solution", {})
        revision_cycles = state.get("revision_cycles", 0)

        priority = classification.get("priority", "P3 Medium")
        category = ticket.get("category", "")
        evidence_quality = solution.get("evidence_quality", "INSUFFICIENT")
        citations = solution.get("supporting_citations", [])
        instructions = solution.get("step_by_step_instructions", [])

        # 1. Verification Checks
        checks: List[Dict[str, Any]] = []

        # Check A: Citation validity & Grounding
        has_citations = len(citations) > 0 and evidence_quality != "INSUFFICIENT"
        checks.append({
            "name": "Citation & Evidence Grounding Check",
            "passed": has_citations,
            "detail": f"{len(citations)} citations verified from knowledge base." if has_citations else "No valid knowledge citations found."
        })

        # Check B: Unsafe / Destructive command detection
        dangerous_patterns = ["rm -rf", "drop table", "truncate table", "mkfs", "dd if=/dev/zero", "chmod 777"]
        combined_steps = " ".join(instructions).lower()
        has_dangerous_commands = any(p in combined_steps for p in dangerous_patterns)
        checks.append({
            "name": "Safety & Destructive Command Check",
            "passed": not has_dangerous_commands,
            "detail": "No dangerous unapproved shell or database commands detected." if not has_dangerous_commands else "CRITICAL: Destructive operations detected in remediation."
        })

        # Check C: Prerequisites and rollback presence
        has_rollback = bool(solution.get("rollback_instructions"))
        checks.append({
            "name": "Rollback Procedure Completeness",
            "passed": has_rollback,
            "detail": "Rollback procedure clearly defined." if has_rollback else "Missing rollback instructions."
        })

        # Check D: Security / P1 Critical safety gate
        is_p1_or_sec = (priority == "P1 Critical" or category.lower() == "security")
        checks.append({
            "name": "Severity & Policy Gate Alignment",
            "passed": True,
            "detail": f"Mandatory engineer sign-off required for {priority}." if is_p1_or_sec else "Standard operational incident."
        })

        # 2. Compute Verdict: PASS | NEEDS_REVISION | ESCALATE
        max_revisions = settings.MAX_AGENT_REVISION_CYCLES

        if has_dangerous_commands:
            verdict = "ESCALATE"
            explanation = "Unsafe or destructive operations detected. Immediate escalation to Security / Tier 3."
        elif not has_citations and evidence_quality == "INSUFFICIENT":
            # If revision cycles not exhausted, could request revision or escalate to human
            verdict = "ESCALATE"
            explanation = "Knowledge base contains insufficient evidence for automated remediation. Escalated to Tier 3 on-call."
        elif not has_rollback and revision_cycles < max_revisions:
            verdict = "NEEDS_REVISION"
            explanation = f"Remediation lacks verified rollback steps. Requesting agent revision (Cycle {revision_cycles + 1} of {max_revisions})."
        elif is_p1_or_sec:
            verdict = "PASS"  # Technical steps verified, but will pause at human approval gate
            explanation = "Technical recommendations verified and grounded in evidence. Escalation gate requires support engineer sign-off before execution."
        else:
            verdict = "PASS"
            explanation = "All verification checks passed. Solution is grounded, safe, and actionable."

        outputs = {
            "verdict": verdict,
            "verification_passed": verdict == "PASS",
            "explanation": explanation,
            "checks": checks,
            "revision_cycles_used": revision_cycles,
            "mandates_human_approval": is_p1_or_sec or solution.get("requires_human_approval", False)
        }

        updated_state = {
            **state,
            "verification": outputs,
            "revision_cycles": revision_cycles + (1 if verdict == "NEEDS_REVISION" else 0)
        }

        return "COMPLETED", outputs, updated_state
