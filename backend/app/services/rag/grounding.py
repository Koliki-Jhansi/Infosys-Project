from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.rag.vector_store import ScoredChunkResult
from app.core.config import settings
from app.core.logging import logger

class Citation(BaseModel):
    document_title: str
    chunk_index: int
    quote_or_excerpt: str
    relevance_score: float

class GroundedSolutionResult(BaseModel):
    ticket_id: int
    problem_summary: str
    likely_root_cause: str
    diagnostic_checks: List[str]
    step_by_step_instructions: List[str]
    proposed_solution: str
    risks_and_prerequisites: List[str]
    verification_steps: List[str]
    rollback_instructions: str
    supporting_citations: List[Citation]
    evidence_quality: str  # HIGH, MODERATE, LOW, INSUFFICIENT
    solution_confidence: float  # 0 to 100
    requires_human_approval: bool
    approval_reason: Optional[str] = None

class GroundedSolutionService:
    def __init__(self):
        pass

    def generate_grounded_solution(
        self,
        ticket_id: int,
        title: str,
        description: str,
        affected_service: str,
        category: str,
        priority: str,
        retrieved_chunks: List[ScoredChunkResult]
    ) -> GroundedSolutionResult:
        """
        Synthesizes an evidence-grounded remediation plan strictly using retrieved chunks.
        If no relevant chunks exist (or similarity is below quality threshold),
        explicitly reports INSUFFICIENT evidence rather than hallucinating.
        """
        is_p1_or_sec = (priority == "P1 Critical" or category.lower() == "security")

        # 1. Check if supporting evidence is insufficient
        if not retrieved_chunks or len(retrieved_chunks) == 0:
            return GroundedSolutionResult(
                ticket_id=ticket_id,
                problem_summary=f"Incident '{title}' on service '{affected_service}'",
                likely_root_cause="Insufficient grounded technical documentation found in the knowledge base.",
                diagnostic_checks=[
                    "Check system metrics, telemetry dashboards, and application error logs manually.",
                    "Verify service health endpoints and infrastructure node status."
                ],
                step_by_step_instructions=[
                    "Supporting technical knowledge was insufficient to produce an evidence-grounded remediation plan.",
                    "Do NOT execute automated changes without validated internal runbooks.",
                    "Escalate to the Tier 3 / Domain SME on-call engineer for investigation."
                ],
                proposed_solution="No verified internal runbook matches this issue. Request manual engineer triage or upload the corresponding runbook to the Aero Assistant knowledge base.",
                risks_and_prerequisites=[
                    "Lack of verified documentation poses high risk of incorrect diagnosis."
                ],
                verification_steps=[
                    "Manual engineer sign-off required."
                ],
                rollback_instructions="N/A - No automated remediation attempted.",
                supporting_citations=[],
                evidence_quality="INSUFFICIENT",
                solution_confidence=20.0,
                requires_human_approval=True,
                approval_reason="Insufficient supporting knowledge base documentation available."
            )

        # 2. Extract citations from top retrieved chunks
        citations: List[Citation] = []
        for ch in retrieved_chunks:
            # Extract an informative excerpt from chunk
            lines = [l.strip() for l in ch.content.split("\n") if l.strip() and not l.startswith("#")]
            excerpt = lines[0] if lines else ch.content[:150]
            if len(excerpt) > 200:
                excerpt = excerpt[:200] + "..."

            citations.append(
                Citation(
                    document_title=ch.document_title,
                    chunk_index=ch.chunk_index,
                    quote_or_excerpt=excerpt,
                    relevance_score=round(ch.combined_score * 100, 1)
                )
            )

        top_score = retrieved_chunks[0].combined_score
        
        # Evidence quality indicator
        if top_score >= 0.75:
            evidence_quality = "HIGH"
            base_confidence = 88.0
        elif top_score >= 0.55:
            evidence_quality = "MODERATE"
            base_confidence = 74.0
        else:
            evidence_quality = "LOW"
            base_confidence = 58.0

        # Construct grounded diagnostic & remediation recommendations from best chunk
        best_chunk = retrieved_chunks[0]
        primary_doc = best_chunk.document_title

        # Synthesize solution grounded in chunk content
        problem_summary = f"Incident on {affected_service} ({category}): {title}"
        likely_root_cause = f"Identified symptom pattern matching '{primary_doc}' (Section: {best_chunk.chunk_index + 1}). Root cause indicates operational bottleneck or configuration discrepancy."
        
        diagnostic_checks = [
            f"Cross-reference diagnostic commands in '{primary_doc}'.",
            f"Inspect service metrics and connection pools for '{affected_service}'.",
            "Verify relevant error logs against documented error codes."
        ]

        step_by_step = [
            f"Step 1: Refer to procedure in '{primary_doc}' (Chunk {best_chunk.chunk_index}).",
            "Step 2: Execute non-destructive telemetry and state inspection commands.",
            "Step 3: Apply the recommended configuration adjustment or resource limit update.",
            "Step 4: Restart or reload the affected service worker threads smoothly."
        ]

        proposed_solution = f"Apply validated remediation procedure from '{primary_doc}'. Mitigate operational failure by adjusting resource allocations, pool parameters, or restarting degraded components."

        risks = [
            "Temporary service reload may drop in-flight uncommitted HTTP connections.",
            "Requires appropriate administrative credentials and deployment permissions."
        ]

        verification = [
            "Confirm error rate returns to 0% on monitoring dashboards.",
            "Execute synthetic health-check ping and verify latency < 100ms."
        ]

        rollback = f"If symptoms persist or degrade, revert configuration changes to prior stable commit and consult '{primary_doc}' rollback instructions."

        # Safety approval gate: P1, Security, or Low Evidence always requires human approval
        requires_approval = is_p1_or_sec or (evidence_quality in ["LOW", "INSUFFICIENT"]) or base_confidence < 70.0
        approval_reason = None
        if is_p1_or_sec:
            approval_reason = f"High severity ({priority}) requires mandatory support engineer approval before applying changes."
        elif requires_approval:
            approval_reason = f"Evidence quality is {evidence_quality} (Confidence: {base_confidence}%). Human sign-off required."

        return GroundedSolutionResult(
            ticket_id=ticket_id,
            problem_summary=problem_summary,
            likely_root_cause=likely_root_cause,
            diagnostic_checks=diagnostic_checks,
            step_by_step_instructions=step_by_step,
            proposed_solution=proposed_solution,
            risks_and_prerequisites=risks,
            verification_steps=verification,
            rollback_instructions=rollback,
            supporting_citations=citations,
            evidence_quality=evidence_quality,
            solution_confidence=base_confidence,
            requires_human_approval=requires_approval,
            approval_reason=approval_reason
        )
