import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatus
from app.models.workflow import WorkflowExecution, AgentExecution
from app.models.evaluation import AIEvaluation
from app.services.agents.airline.diagnosis_agent import DiagnosisAgent
from app.services.agents.airline.retrieval_agent import AirlineRetrievalAgent
from app.services.agents.airline.resolution_agent import ResolutionAgent
from app.services.agents.airline.validation_agent import ValidationAgent
from app.services.agents.airline.escalation_agent import EscalationAgent
from app.services.audit.audit_service import record_audit_event
from app.core.logging import logger

class AirlineWorkflowOrchestrator:
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

        if not workflow or workflow.status in ["COMPLETED", "CANCELLED", "ESCALATED"]:
            workflow = WorkflowExecution(
                ticket_id=ticket.id,
                status="RUNNING",
                current_agent="Diagnosis Agent",
                revision_cycles=0,
                state_payload={}
            )
            self.db.add(workflow)
            self.db.commit()
            self.db.refresh(workflow)
        else:
            workflow.status = "RUNNING"
            self.db.commit()

        # Build initial state
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
            "ticket_number": ticket.ticket_number or f"TK-{ticket.id:04d}",
            "title": ticket.title,
            "subject": ticket.title,
            "description": ticket.description,
            "passenger_name": ticket.passenger_name or (ticket.reporter.full_name if ticket.reporter else "Passenger"),
            "passenger_email": ticket.passenger_email or (ticket.reporter.email if ticket.reporter else ""),
            "booking_reference": ticket.booking_reference,
            "flight_number": ticket.flight_number,
            "travel_date": ticket.travel_date,
            "category": ticket.category,
            "urgency": ticket.urgency,
            "affected_service": ticket.affected_service or "Flight Operations"
        }
        state["classification"] = classification_data
        if human_approval_notes:
            state["human_approved"] = True
            state["approval_notes"] = human_approval_notes

        try:
            # 1. Diagnosis Agent
            diag_agent = DiagnosisAgent()
            _, _, state = await self._run_agent(workflow, diag_agent, state)

            # 2. Retrieval Agent
            ret_agent = AirlineRetrievalAgent(self.db)
            _, _, state = await self._run_agent(workflow, ret_agent, state)

            # 3. Resolution Agent
            res_agent = ResolutionAgent()
            _, _, state = await self._run_agent(workflow, res_agent, state)

            # 4. Validation Agent
            val_agent = ValidationAgent()
            _, val_out, state = await self._run_agent(workflow, val_agent, state)

            # If validation requires revision and not exceeded cycles
            if val_out.get("verdict") == "NEEDS_REVISION" and workflow.revision_cycles < 2:
                workflow.revision_cycles += 1
                logger.info(f"Airline workflow revision cycle {workflow.revision_cycles} triggered for ticket #{ticket.id}")
                # Re-run resolution
                _, _, state = await self._run_agent(workflow, res_agent, state)
                # Re-run validation
                _, val_out, state = await self._run_agent(workflow, val_agent, state)

            # 5. Escalation Agent
            esc_agent = EscalationAgent(self.db)
            _, esc_out, state = await self._run_agent(workflow, esc_agent, state)

            final_decision = esc_out.get("decision", "RESOLVED")
            final_conf = float(esc_out.get("final_confidence", 85.0))
            val_verdict = state.get("validation", {}).get("verdict", "PASS")
            ret_sources = state.get("retrieval", {}).get("sources", [])
            total_duration = sum(a.duration_ms for a in workflow.agent_executions) or 150

            # Record AI evaluation for analytics
            ai_eval = AIEvaluation(
                ticket_id=ticket.id,
                workflow_run_id=workflow.id,
                model_name="AeroAssist-Agentic-v1",
                confidence_score=final_conf,
                validation_outcome=val_verdict,
                validation_details=state.get("validation", {}),
                final_outcome="RESOLVED" if final_decision == "RESOLVED" else "ESCALATED",
                escalation_reason=esc_out.get("escalation_reason") if final_decision != "RESOLVED" else None,
                latency_ms=total_duration,
                retrieved_sources_count=len(ret_sources),
                status="SUCCESS"
            )
            self.db.add(ai_eval)

            workflow.status = "COMPLETED"
            workflow.current_agent = "Completed"
            workflow.state_payload = state
            self.db.commit()

            record_audit_event(
                db=self.db,
                entity_type="WORKFLOW",
                entity_id=str(workflow.id),
                action="AIRLINE_WORKFLOW_COMPLETED",
                actor_id=None,
                details={
                    "ticket_id": ticket.id,
                    "final_decision": final_decision,
                    "final_confidence": esc_out.get("final_confidence"),
                    "evaluation_id": ai_eval.id
                }
            )

            return workflow

        except Exception as e:
            logger.error(f"Airline workflow #{workflow.id} execution failed: {str(e)}")
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
