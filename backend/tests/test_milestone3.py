import pytest
from app.services.jira.simulator import SimulatedJiraService
from app.services.agents.triage_agent import TicketTriageAgent
from app.services.agents.verification_agent import SolutionVerificationAgent
from app.services.workflows.orchestrator import WorkflowOrchestrator

@pytest.mark.asyncio
async def test_triage_agent_flags_security():
    agent = TicketTriageAgent()
    state = {
        "ticket": {
            "title": "SQL Injection attempt detected on login",
            "description": "Attacker trying UNION SELECT password from admin_users. CVE vulnerability.",
            "affected_service": "Auth Gateway",
            "category": "Security",
            "urgency": "Critical",
            "business_impact": "Extensive / Organization-wide",
            "affected_users": 500,
            "error_logs": "ERROR: SQL injection regex matched payload"
        },
        "classification": {
            "priority": "P1 Critical",
            "confidence_score": 92.0
        }
    }
    status, outputs, updated_state = await agent.run(state)
    assert status == "WAITING_FOR_REVIEW"
    assert outputs["is_security_alert"] is True
    assert outputs["requires_human_review"] is True
    assert len(outputs["security_signals"]) > 0

@pytest.mark.asyncio
async def test_verification_agent_destructive_command_escalation():
    agent = SolutionVerificationAgent()
    state = {
        "ticket": {"category": "Application"},
        "classification": {"priority": "P2 High"},
        "solution": {
            "evidence_quality": "HIGH",
            "supporting_citations": [{"document_title": "Doc", "chunk_index": 0}],
            "step_by_step_instructions": [
                "Step 1: Backup files",
                "Step 2: Execute rm -rf /var/log/app/* to clear space"
            ],
            "rollback_instructions": "Restore from backup"
        },
        "revision_cycles": 0
    }
    status, outputs, _ = await agent.run(state)
    assert outputs["verdict"] == "ESCALATE"
    assert "destructive operations detected" in outputs["explanation"].lower()

def test_jira_simulator_idempotency():
    jira = SimulatedJiraService()
    key1 = jira.create_issue(
        summary="Test Pod Crash",
        description="Crash details",
        priority="P2 High",
        idempotency_key="unique_ticket_100_wf_1"
    )
    assert key1["idempotency_hit"] is False
    assert key1["key"].startswith("IT-")

    # Repeat with same idempotency key
    key2 = jira.create_issue(
        summary="Test Pod Crash",
        description="Crash details",
        priority="P2 High",
        idempotency_key="unique_ticket_100_wf_1"
    )
    assert key2["idempotency_hit"] is True
    assert key2["key"] == key1["key"]

@pytest.mark.asyncio
async def test_workflow_orchestrator_execution(db):
    from app.models.ticket import Ticket, TicketStatus
    from app.models.classification import TicketClassification
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    # Seed user and ticket
    user = User(
        email="wf_test@example.com",
        hashed_password=hash_password("pass"),
        full_name="Workflow Tester",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    ticket = Ticket(
        title="Payment Service JVM OOMKilled crash loop",
        description="Container memory exceeds 512Mi limit under high load. Exit code 137.",
        affected_service="payment-service",
        category="Infrastructure",
        business_impact="Significant / Department-wide",
        urgency="High",
        environment="production",
        affected_users=50,
        error_logs="K8s: Pod terminated reason OOMKilled",
        status=TicketStatus.CLASSIFIED,
        reporter_id=user.id
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    classification = TicketClassification(
        ticket_id=ticket.id,
        predicted_category="Infrastructure",
        priority="P2 High",
        criticality="High",
        confidence_score=85.0,
        explanation="Standard operational memory issue",
        detected_keywords=["oomkilled", "memory"],
        potential_business_impact="Significant",
        recommended_next_action="Increase memory limits",
        missing_information=[],
        requires_human_review=False
    )
    db.add(classification)
    db.commit()

    orchestrator = WorkflowOrchestrator(db)
    wf = await orchestrator.execute_or_resume_workflow(ticket_id=ticket.id)
    assert wf is not None
    assert wf.status in ["COMPLETED", "WAITING_FOR_REVIEW"]
    assert len(wf.agent_executions) >= 3
