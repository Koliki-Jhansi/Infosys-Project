import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatus
from app.models.classification import TicketClassification
from app.models.workflow import WorkflowExecution, AgentExecution
from app.services.agents.triage_agent import TicketTriageAgent
from app.services.agents.retrieval_agent import KnowledgeRetrievalAgent
from app.services.agents.root_cause_agent import RootCauseAnalysisAgent
from app.services.agents.solution_agent import SolutionGenerationAgent
from app.services.agents.verification_agent import SolutionVerificationAgent
from app.services.agents.jira_agent import WorkflowAndJiraAgent
from app.services.audit.audit_service import record_audit_event, record_status_change
from app.core.config import settings
from app.core.logging import logger

class WorkflowOrchestrator:
    def __init__(self, db: Session):
        self.db = db

    async def execute_or_resume_workflow(
        self,
        ticket_id: int,
        workflow_id: Optional[int] = None,
        human_approval_notes: Optional[str] = None
    ) -> WorkflowExecution:
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise ValueError(f"Ticket #{ticket_id} not found")

        # Load or create WorkflowExecution
        if workflow_id:
            workflow = self.db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_id).first()
        else:
            workflow = (
                self.db.query(WorkflowExecution)
                .filter(WorkflowExecution.ticket_id == ticket_id)
                .order_by(WorkflowExecution.created_at.desc())
                .first()
            )

        if not workflow or workflow.status in ["COMPLETED", "CANCELLED"]:
            workflow = WorkflowExecution(
                ticket_id=ticket.id,
                status="RUNNING",
                current_agent="Ticket Triage Agent",
                revision_cycles=0,
                state_payload={}
            )
            self.db.add(workflow)
            self.db.commit()
            self.db.refresh(workflow)
        else:
            workflow.status = "RUNNING"
            self.db.commit()

        # Build initial state dictionary
        classification_data = {}
        if ticket.classification:
            c = ticket.classification
            classification_data = {
                "predicted_category": c.predicted_category,
                "priority": c.priority,
                "criticality": c.criticality,
                "confidence_score": c.confidence_score,
                "requires_human_review": c.requires_human_review
            }

        state: Dict[str, Any] = workflow.state_payload or {}
        state["workflow_id"] = workflow.id
        state["ticket"] = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "affected_service": ticket.affected_service,
            "category": ticket.category,
            "business_impact": ticket.business_impact,
            "urgency": ticket.urgency,
            "environment": ticket.environment,
            "affected_users": ticket.affected_users,
            "error_logs": ticket.error_logs
        }
        state["classification"] = classification_data
        if human_approval_notes:
            state["human_approved"] = True
            state["approval_notes"] = human_approval_notes

        # Execute agents sequentially
        try:
            # 1. Triage Agent
            if not state.get("triage"):
                triage_agent = TicketTriageAgent()
                status_res, out, state = await self._run_agent(workflow, triage_agent, state)
                if status_res == "WAITING_FOR_REVIEW":
                    workflow.status = "WAITING_FOR_REVIEW"
                    workflow.current_agent = "Ticket Triage Agent"
                    workflow.state_payload = state
                    self.db.commit()
                    return workflow

            # 2. Knowledge Retrieval Agent
            if not state.get("retrieval"):
                retrieval_agent = KnowledgeRetrievalAgent(self.db)
                _, out, state = await self._run_agent(workflow, retrieval_agent, state)

            # 3. Root Cause Analysis Agent
            if not state.get("root_cause_analysis"):
                rca_agent = RootCauseAnalysisAgent()
                _, out, state = await self._run_agent(workflow, rca_agent, state)

            # 4. Solution Generation Agent
            if not state.get("solution"):
                sol_agent = SolutionGenerationAgent()
                _, out, state = await self._run_agent(workflow, sol_agent, state)

            # 5. Solution Verification Agent (with revision loop)
            ver_agent = SolutionVerificationAgent()
            _, ver_out, state = await self._run_agent(workflow, ver_agent, state)
            
            # Check for Revision Loop
            if ver_out.get("verdict") == "NEEDS_REVISION":
                cycle = state.get("revision_cycles", 1)
                if cycle <= settings.MAX_AGENT_REVISION_CYCLES:
                    logger.info(f"Triggering Agent Revision Loop cycle {cycle} for ticket #{ticket.id}")
                    # Re-run solution agent with revised constraints
                    sol_agent = SolutionGenerationAgent()
                    _, out, state = await self._run_agent(workflow, sol_agent, state)
                    # Re-verify
                    _, ver_out, state = await self._run_agent(workflow, ver_agent, state)

            # Check if Verification mandates Human Approval Gate
            if ver_out.get("mandates_human_approval") and not state.get("human_approved", False):
                workflow.status = "WAITING_FOR_REVIEW"
                workflow.current_agent = "Human Approval Gate"
                workflow.state_payload = state
                self.db.commit()
                return workflow

            # 6. Workflow & Jira Agent
            jira_agent = WorkflowAndJiraAgent(self.db)
            _, jira_out, state = await self._run_agent(workflow, jira_agent, state)

            # Workflow complete
            workflow.status = "COMPLETED"
            workflow.current_agent = "Completed"
            workflow.state_payload = state
            
            # Update ticket status to IN_PROGRESS or RESOLVED
            old_status = ticket.status.value
            ticket.status = TicketStatus.IN_PROGRESS
            self.db.commit()

            record_status_change(
                db=self.db,
                ticket_id=ticket.id,
                old_status=old_status,
                new_status=ticket.status.value,
                changed_by_id=None,
                reason=f"Multi-agent workflow completed. Jira issue {jira_out.get('jira_key')} synchronized."
            )

            record_audit_event(
                db=self.db,
                entity_type="WORKFLOW",
                entity_id=str(workflow.id),
                action="WORKFLOW_COMPLETED",
                actor_id=None,
                details={"jira_key": jira_out.get("jira_key"), "ticket_id": ticket.id}
            )

            return workflow

        except Exception as e:
            logger.error(f"Workflow #{workflow.id} execution failed: {str(e)}")
            workflow.status = "FAILED"
            workflow.error_details = str(e)
            self.db.commit()
            return workflow

    async def _run_agent(
        self,
        workflow: WorkflowExecution,
        agent,
        state: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        workflow.current_agent = agent.name
        self.db.commit()

        start_time = time.time()
        try:
            status_res, outputs, updated_state = await agent.run(state)
            duration_ms = int((time.time() - start_time) * 1000)

            # Persist AgentExecution record
            agent_rec = AgentExecution(
                workflow_id=workflow.id,
                agent_name=agent.name,
                status=status_res,
                inputs=state.get("ticket", {}),
                outputs=outputs,
                duration_ms=duration_ms
            )
            self.db.add(agent_rec)
            workflow.state_payload = updated_state
            self.db.commit()

            return status_res, outputs, updated_state
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            agent_rec = AgentExecution(
                workflow_id=workflow.id,
                agent_name=agent.name,
                status="FAILED",
                inputs=state.get("ticket", {}),
                outputs={},
                duration_ms=duration_ms,
                error_message=str(e)
            )
            self.db.add(agent_rec)
            self.db.commit()
            raise
