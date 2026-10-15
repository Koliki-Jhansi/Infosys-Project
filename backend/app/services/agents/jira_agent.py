import hashlib
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.services.jira.client import JiraClientService
from app.models.jira import JiraIssueRecord

class WorkflowAndJiraAgent(BaseAgent):
    def __init__(self, db: Session):
        super().__init__("Workflow and Jira Agent")
        self.db = db
        self.jira_client = JiraClientService()

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket = state.get("ticket", {})
        classification = state.get("classification", {})
        solution = state.get("solution", {})
        verification = state.get("verification", {})
        workflow_id = state.get("workflow_id", 0)
        ticket_id = ticket.get("id", 0)

        # 1. Deterministic idempotency key: hash of ticket_id + workflow_id
        idempotency_raw = f"aero_ticket_{ticket_id}_wf_{workflow_id}"
        idempotency_key = hashlib.sha256(idempotency_raw.encode()).hexdigest()[:32]

        # 2. Check if already created in database
        existing_record = self.db.query(JiraIssueRecord).filter(JiraIssueRecord.idempotency_key == idempotency_key).first()
        if existing_record:
            outputs = {
                "jira_key": existing_record.jira_key,
                "jira_url": existing_record.jira_url,
                "project_key": existing_record.project_key,
                "priority": existing_record.priority,
                "status": existing_record.status,
                "created_new": False,
                "message": f"Idempotent match: Jira issue {existing_record.jira_key} already exists for this workflow."
            }
            return "COMPLETED", outputs, {**state, "jira": outputs}

        # 3. Format Jira Description with Grounded Recommendations & Citations
        title = ticket.get("title", "")
        service = ticket.get("affected_service", "")
        priority = classification.get("priority", "P3 Medium")
        root_cause = solution.get("likely_root_cause", "")
        proposed = solution.get("proposed_solution", "")
        citations = solution.get("supporting_citations", [])
        evidence_quality = solution.get("evidence_quality", "N/A")

        citations_text = ""
        for c in citations:
            citations_text += f"\n- {c.get('document_title')} (Chunk {c.get('chunk_index')}): \"{c.get('quote_or_excerpt')}\""

        jira_desc = (
            f"**[Aero Assistant AI Incident Workflow]**\n\n"
            f"*Affected Service:* {service}\n"
            f"*Severity:* {priority} (Confidence: {classification.get('confidence_score')}%, Quality: {evidence_quality})\n\n"
            f"**Likely Root Cause:**\n{root_cause}\n\n"
            f"**Proposed Solution & Remediation:**\n{proposed}\n\n"
            f"**Verified Supporting Citations:**{citations_text if citations_text else ' None'}\n\n"
            f"**Verification Status:** {verification.get('verdict', 'PASS')}\n"
        )

        jira_res = await self.jira_client.create_issue(
            summary=f"[{service}] {title}",
            description=jira_desc,
            priority=priority,
            idempotency_key=idempotency_key
        )

        # 4. Save JiraIssueRecord in database
        issue_record = JiraIssueRecord(
            ticket_id=ticket_id,
            workflow_id=workflow_id if workflow_id > 0 else None,
            jira_key=jira_res["key"],
            jira_url=jira_res["url"],
            project_key=jira_res["project_key"],
            issue_type=jira_res["issue_type"],
            summary=f"[{service}] {title}",
            priority=jira_res["priority"],
            status=jira_res["status"],
            idempotency_key=idempotency_key,
            metadata_payload=jira_res
        )
        self.db.add(issue_record)
        self.db.commit()
        self.db.refresh(issue_record)

        outputs = {
            "jira_key": issue_record.jira_key,
            "jira_url": issue_record.jira_url,
            "project_key": issue_record.project_key,
            "priority": issue_record.priority,
            "status": issue_record.status,
            "idempotency_hit": jira_res.get("idempotency_hit", False),
            "created_new": True,
            "message": f"Created Jira issue {issue_record.jira_key} for ticket #{ticket_id}."
        }

        updated_state = {
            **state,
            "jira": outputs
        }

        return "COMPLETED", outputs, updated_state
