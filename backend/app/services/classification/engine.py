import re
import json
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger
from app.policies.priority_policy import calculate_priority_and_criticality
from app.policies.confidence_policy import (
    calculate_explainable_confidence,
    evaluate_ticket_confidence_policy,
    CATEGORY_FINGERPRINTS
)

class ClassificationStructuredOutput(BaseModel):
    ticket_id: int
    predicted_category: str
    priority: str
    criticality: str
    confidence_score: float = Field(ge=0, le=100)
    explanation: str
    detected_keywords: List[str]
    potential_business_impact: str
    recommended_next_action: str
    missing_information: List[str]
    requires_human_review: bool
    review_reason: Optional[str] = None
    status: str
    model_name: str
    confidence_breakdown: Dict[str, Any]
    classification_timestamp: str

class ClassificationEngine:
    def __init__(self, threshold: Optional[float] = None):
        self.threshold = threshold if threshold is not None else settings.CONFIDENCE_THRESHOLD

    async def classify_ticket(
        self,
        ticket_id: int,
        title: str,
        description: str,
        affected_service: str,
        reported_category: str,
        urgency: str,
        business_impact: str,
        environment: str,
        affected_users: int,
        error_logs: str = ""
    ) -> ClassificationStructuredOutput:
        """
        Executes AI or deterministic classification with priority policy and explainable confidence scoring.
        """
        if settings.AI_MOCK_MODE or not settings.LLM_API_KEY or settings.LLM_API_KEY.startswith("mock"):
            return self._deterministic_classify(
                ticket_id=ticket_id,
                title=title,
                description=description,
                affected_service=affected_service,
                reported_category=reported_category,
                urgency=urgency,
                business_impact=business_impact,
                environment=environment,
                affected_users=affected_users,
                error_logs=error_logs
            )
        else:
            try:
                return await self._llm_classify(
                    ticket_id=ticket_id,
                    title=title,
                    description=description,
                    affected_service=affected_service,
                    reported_category=reported_category,
                    urgency=urgency,
                    business_impact=business_impact,
                    environment=environment,
                    affected_users=affected_users,
                    error_logs=error_logs
                )
            except Exception as e:
                logger.error(f"LLM classification failed: {str(e)}. Falling back to deterministic policy engine.")
                fallback = self._deterministic_classify(
                    ticket_id=ticket_id,
                    title=title,
                    description=description,
                    affected_service=affected_service,
                    reported_category=reported_category,
                    urgency=urgency,
                    business_impact=business_impact,
                    environment=environment,
                    affected_users=affected_users,
                    error_logs=error_logs
                )
                # On fallback failure, enforce human review
                fallback.requires_human_review = True
                fallback.status = "NEEDS_REVIEW"
                fallback.review_reason = f"LLM error fallback ({str(e)[:100]}); human review mandated."
                fallback.model_name = f"{fallback.model_name}-fallback"
                return fallback

    def _predict_category(self, title: str, description: str, error_logs: str, reported_category: str) -> Tuple[str, List[str]]:
        combined = f"{title} {description} {error_logs}".lower()
        best_category = reported_category
        highest_matches = 0
        all_detected_kws = []

        for category, keywords in CATEGORY_FINGERPRINTS.items():
            matches = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', combined)]
            if matches:
                all_detected_kws.extend(matches)
            if len(matches) > highest_matches:
                highest_matches = len(matches)
                best_category = category

        # Clean duplicates while preserving order
        unique_kws = list(dict.fromkeys(all_detected_kws))
        return best_category, unique_kws

    def _deterministic_classify(
        self,
        ticket_id: int,
        title: str,
        description: str,
        affected_service: str,
        reported_category: str,
        urgency: str,
        business_impact: str,
        environment: str,
        affected_users: int,
        error_logs: str = ""
    ) -> ClassificationStructuredOutput:
        predicted_cat, detected_kws = self._predict_category(title, description, error_logs, reported_category)
        
        # Priority and criticality from policy matrix
        priority, criticality, sec_flags, escalation_reason = calculate_priority_and_criticality(
            urgency=urgency,
            business_impact=business_impact,
            environment=environment,
            affected_users=affected_users,
            category=predicted_cat,
            title=title,
            description=description,
            error_logs=error_logs
        )

        # Confidence calculation
        confidence, breakdown, missing_info = calculate_explainable_confidence(
            reported_category=reported_category,
            predicted_category=predicted_cat,
            title=title,
            description=description,
            error_logs=error_logs,
            affected_users=affected_users,
            affected_service=affected_service,
            has_valid_structured_output=True
        )

        # Safety & confidence policy routing
        status, requires_review, review_reason = evaluate_ticket_confidence_policy(
            confidence_score=confidence,
            threshold=self.threshold,
            priority=priority,
            criticality=criticality,
            category=predicted_cat,
            detected_security_signals=sec_flags
        )

        explanation = (
            f"Classified as '{predicted_cat}' ({priority}) based on symptom matching and deterministic impact matrix. "
            f"{escalation_reason}. Estimated confidence is {confidence}% based on input evidence completeness and keyword agreement."
        )

        potential_impact = (
            f"Impacting {affected_users} user(s) on service '{affected_service}' in {environment}. "
            f"Reported organizational impact: {business_impact}."
        )

        if priority == "P1 Critical":
            recommended_action = "Page Incident Commander and Tier 3 on-call immediately; isolate affected service segment."
        elif predicted_cat == "Security":
            recommended_action = "Initiate SecOps incident response protocol and revoke suspicious session tokens."
        elif status == "NEEDS_REVIEW":
            recommended_action = "Request additional diagnostic logs or user clarification before automated remediation."
        else:
            recommended_action = "Execute automated RAG diagnostic search and initiate remediation runbook."

        return ClassificationStructuredOutput(
            ticket_id=ticket_id,
            predicted_category=predicted_cat,
            priority=priority,
            criticality=criticality,
            confidence_score=confidence,
            explanation=explanation,
            detected_keywords=detected_kws,
            potential_business_impact=potential_impact,
            recommended_next_action=recommended_action,
            missing_information=missing_info,
            requires_human_review=requires_review,
            review_reason=review_reason,
            status=status,
            model_name="deterministic-explainable-classifier-v1",
            confidence_breakdown=breakdown,
            classification_timestamp=datetime.now(timezone.utc).isoformat()
        )

    async def _llm_classify(
        self,
        ticket_id: int,
        title: str,
        description: str,
        affected_service: str,
        reported_category: str,
        urgency: str,
        business_impact: str,
        environment: str,
        affected_users: int,
        error_logs: str = ""
    ) -> ClassificationStructuredOutput:
        # Prompt for OpenAI or compatible endpoint
        prompt = f"""You are the classification engine for Aero Assistant IT Service Desk.
Analyze the following IT support ticket and provide a structured JSON assessment:

Title: {title}
Description: {description}
Reported Category: {reported_category}
Affected Service: {affected_service}
Urgency: {urgency}
Reported Impact: {business_impact}
Environment: {environment}
Affected Users: {affected_users}
Error Logs: {error_logs}

Return ONLY valid JSON matching this schema:
{{
  "predicted_category": "Network | Application | Database | Authentication and access | Infrastructure | Hardware | Deployment | Security | Other",
  "explanation": "Detailed explanation for category and operational urgency",
  "detected_keywords": ["list", "of", "detected", "symptom", "keywords"],
  "recommended_next_action": "Actionable troubleshooting or escalation step"
}}
"""
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": "You are a senior IT operations triage AI that outputs strict JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{settings.LLM_BASE_URL}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_content)

        predicted_cat = parsed.get("predicted_category", reported_category)
        detected_kws = parsed.get("detected_keywords", [])
        raw_explanation = parsed.get("explanation", "")
        recommended_action = parsed.get("recommended_next_action", "")

        # Always enforce deterministic priority policy regardless of LLM text
        priority, criticality, sec_flags, escalation_reason = calculate_priority_and_criticality(
            urgency=urgency,
            business_impact=business_impact,
            environment=environment,
            affected_users=affected_users,
            category=predicted_cat,
            title=title,
            description=description,
            error_logs=error_logs
        )

        confidence, breakdown, missing_info = calculate_explainable_confidence(
            reported_category=reported_category,
            predicted_category=predicted_cat,
            title=title,
            description=description,
            error_logs=error_logs,
            affected_users=affected_users,
            affected_service=affected_service,
            has_valid_structured_output=True
        )

        status, requires_review, review_reason = evaluate_ticket_confidence_policy(
            confidence_score=confidence,
            threshold=self.threshold,
            priority=priority,
            criticality=criticality,
            category=predicted_cat,
            detected_security_signals=sec_flags
        )

        return ClassificationStructuredOutput(
            ticket_id=ticket_id,
            predicted_category=predicted_cat,
            priority=priority,
            criticality=criticality,
            confidence_score=confidence,
            explanation=f"{raw_explanation} [Policy: {escalation_reason}]",
            detected_keywords=detected_kws,
            potential_business_impact=f"Impacting {affected_users} user(s) on service '{affected_service}' ({business_impact})",
            recommended_next_action=recommended_action,
            missing_information=missing_info,
            requires_human_review=requires_review,
            review_reason=review_reason,
            status=status,
            model_name=settings.LLM_MODEL,
            confidence_breakdown=breakdown,
            classification_timestamp=datetime.now(timezone.utc).isoformat()
        )
