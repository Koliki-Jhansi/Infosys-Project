import pytest
from datetime import datetime, timezone
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketStatus
from app.models.jira import JiraIssueRecord
from app.models.classification import TicketClassification
from app.services.workflows.airline_orchestrator import AirlineWorkflowOrchestrator
from app.services.email.email_service import EmailDeliveryService
from app.services.jira.client import JiraClientService
from app.core.config import settings

@pytest.mark.asyncio
async def test_end_to_end_dashboard_and_workflow(db, client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()

    # 1. Test Viewing all tickets & dashboard summary matching database
    summary_res = client.get("/api/dashboard/summary", headers=headers)
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert "total_tickets" in summary_data
    assert "open_tickets" in summary_data
    assert "ai_resolved_tickets" in summary_data
    assert "escalated_tickets" in summary_data

    # Verify counts match DB directly
    db_total = db.query(Ticket).count()
    assert summary_data["total_tickets"] == db_total

    # List all tickets endpoint with pagination
    tickets_res = client.get("/api/tickets?page=1&size=10", headers=headers)
    assert tickets_res.status_code == 200
    tickets_data = tickets_res.json()
    assert "items" in tickets_data
    assert "total" in tickets_data
    assert "pages" in tickets_data
    assert tickets_data["total"] == db_total

    # 2 & 4. Test Handling confidence below 70% with Jira escalation
    ticket_low = Ticket(
        title="Antique fragile cello missing without luggage tag at ORD",
        description="Non-standard uncataloged antique equipment was placed on luggage carousel without barcoded tags or baggage manifest.",
        affected_service="Terminal Ground Handling",
        category="Baggage",
        urgency="Low",
        business_impact="Single passenger",
        passenger_name="Elena Rostova",
        passenger_email="elena@example.com",
        booking_reference="PNR-LOW77",
        flight_number="AA-101",
        reporter_id=admin_user.id
    )
    db.add(ticket_low)
    db.commit()
    db.refresh(ticket_low)
    ticket_low.ticket_number = f"TK-{ticket_low.id:04d}"
    db.commit()

    # Run AI solution
    orchestrator = AirlineWorkflowOrchestrator(db)
    wf_low = await orchestrator.execute_or_resume_workflow(ticket_id=ticket_low.id)
    assert wf_low.status == "COMPLETED"

    # Verify 6 stages executed
    stage_names = [a.agent_name for a in wf_low.agent_executions]
    assert "Diagnosis Agent" in stage_names
    assert "Retrieval Agent" in stage_names
    assert "Priority and Criticality Analysis" in stage_names
    assert "Resolution Agent" in stage_names
    assert "Validation Agent" in stage_names
    assert "Escalation Agent" in stage_names

    db.refresh(ticket_low)
    conf_low = ticket_low.ai_confidence
    assert conf_low is not None

    if conf_low < 70.0:
        # Jira issue must exist and ticket status must be NEEDS_REVIEW
        jira_rec = db.query(JiraIssueRecord).filter(JiraIssueRecord.ticket_id == ticket_low.id).first()
        assert jira_rec is not None
        assert jira_rec.jira_key is not None
        assert ticket_low.status == TicketStatus.NEEDS_REVIEW

    # 3 & 5. Test Handling confidence >= 70% with AI solution and email delivery
    ticket_high = Ticket(
        title="Check-in cutoff times for flight AA-304",
        description="Traveling from JFK to LHR on flight AA304, booking ref PNR9900. When does web check-in close?",
        affected_service="Flight Operations",
        category="Check-in and Boarding",
        urgency="Low",
        business_impact="Single passenger",
        passenger_name="Alice Smith",
        passenger_email="alice.smith@example.com",
        booking_reference="PNR9900",
        flight_number="AA-304",
        reporter_id=admin_user.id
    )
    db.add(ticket_high)
    db.commit()
    db.refresh(ticket_high)
    ticket_high.ticket_number = f"TK-{ticket_high.id:04d}"
    db.commit()

    wf_high = await orchestrator.execute_or_resume_workflow(ticket_id=ticket_high.id)
    assert wf_high.status == "COMPLETED"
    db.refresh(ticket_high)

    assert ticket_high.ai_confidence is not None
    assert ticket_high.final_response is not None
    assert len(ticket_high.final_response) > 10

    # Test Email Delivery Service with valid and invalid recipients
    email_service = EmailDeliveryService()
    # Invalid recipient
    res_invalid = email_service.send_solution_email(
        recipient_email="not-an-email",
        passenger_name="Test",
        ticket_number="TK-0001",
        ticket_title="Test",
        solution_text="Solution"
    )
    assert res_invalid["success"] is False
    assert res_invalid["status"] == "INVALID_RECIPIENT"

    # Missing recipient
    res_none = email_service.send_solution_email(
        recipient_email=None,
        passenger_name="Test",
        ticket_number="TK-0001",
        ticket_title="Test",
        solution_text="Solution"
    )
    assert res_none["success"] is False
    assert res_none["status"] == "INVALID_RECIPIENT"

    # 6. Test Escalated Tickets endpoint (Requirement 5)
    escalated_res = client.get("/api/tickets/escalated", headers=headers)
    assert escalated_res.status_code == 200
    escalated_data = escalated_res.json()
    assert "items" in escalated_data

    # Every item in escalated must have jira_records
    for item in escalated_data["items"]:
        assert "jira_records" in item
        assert len(item["jira_records"]) > 0
        assert item["jira_records"][0]["jira_key"] is not None

    # 7. Refreshing dashboard counts
    summary_after = client.get("/api/dashboard/summary", headers=headers).json()
    assert summary_after["total_tickets"] >= summary_data["total_tickets"] + 2
