import pytest
from app.services.agents.airline.diagnosis_agent import DiagnosisAgent
from app.services.agents.airline.retrieval_agent import AirlineRetrievalAgent
from app.services.agents.airline.resolution_agent import ResolutionAgent
from app.services.agents.airline.validation_agent import ValidationAgent
from app.services.agents.airline.escalation_agent import EscalationAgent
from app.services.workflows.airline_orchestrator import AirlineWorkflowOrchestrator
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole

@pytest.mark.asyncio
async def test_diagnosis_agent_entity_extraction():
    state = {
        "ticket": {
            "title": "Delayed luggage on flight FL-342 with booking ref AA-78942",
            "description": "Passenger arrived at JFK on flight FL342, checked bag was not found on carousel. PNR is AA78942.",
            "category": "Baggage",
            "passenger_name": "Marcus Vance",
            "passenger_email": "marcus@example.com"
        }
    }
    agent = DiagnosisAgent()
    status, outputs, updated_state = await agent.run(state)
    assert status == "COMPLETED"
    assert outputs["category"] == "Baggage"
    assert "booking_reference" in outputs["extracted_entities"]
    assert "flight_number" in outputs["extracted_entities"]
    assert outputs["is_urgent"] == True

@pytest.mark.asyncio
async def test_validation_agent_passes_clean_response():
    state = {
        "ticket": {"title": "Flight baggage inquiry", "description": "Need baggage policy", "category": "Baggage"},
        "diagnosis": {"category": "Baggage", "missing_information": []},
        "retrieval": {
            "has_sufficient_evidence": True,
            "sources": [{"document_title": "Baggage Policy", "chunk_id": 1, "relevance_score": 0.85, "excerpt": "Carry-on is 8kg"}]
        },
        "resolution": {
            "passenger_response": "Dear Passenger, in accordance with our airline baggage policy, you are permitted 1 carry-on bag up to 8kg. Thank you for flying with us."
        }
    }
    agent = ValidationAgent()
    status, outputs, updated_state = await agent.run(state)
    assert status == "COMPLETED"
    assert outputs["verdict"] == "PASS"
    assert outputs["is_valid"] == True

@pytest.mark.asyncio
async def test_validation_agent_flags_unauthorized_financial_commitment():
    state = {
        "ticket": {"title": "Refund claim", "description": "Want money back", "category": "Cancellation and Refund"},
        "diagnosis": {"category": "Cancellation and Refund", "missing_information": []},
        "retrieval": {
            "has_sufficient_evidence": True,
            "sources": [{"document_title": "Refund Procedure", "chunk_id": 2, "relevance_score": 0.75, "excerpt": "Refunds take 3-5 days"}]
        },
        "resolution": {
            "passenger_response": "Dear Passenger, guaranteed full refund of $1200 will be paid into your account tomorrow with zero questions asked."
        }
    }
    agent = ValidationAgent()
    status, outputs, updated_state = await agent.run(state)
    assert status == "COMPLETED"
    assert outputs["verdict"] == "FAIL"
    assert "Unauthorized financial commitment" in outputs["summary"]

@pytest.mark.asyncio
async def test_airline_orchestrator_full_run(db):
    user = User(email="test_passenger@aero.com", full_name="Alice Smith", hashed_password="pwd", role=UserRole.PASSENGER)
    db.add(user)
    db.commit()

    ticket = Ticket(
        title="Check-in cutoff times for international flight FL-204",
        description="Traveling from JFK to LHR on flight FL204, booking ref PNR9900. When does web check-in close?",
        affected_service="Airport Terminal Operations",
        category="Check-in and Boarding",
        urgency="Low",
        business_impact="Single passenger",
        environment="production",
        passenger_name="Alice Smith",
        passenger_email="alice@example.com",
        booking_reference="PNR9900",
        flight_number="FL204",
        reporter_id=user.id
    )
    db.add(ticket)
    db.commit()

    orchestrator = AirlineWorkflowOrchestrator(db)
    workflow = await orchestrator.execute_or_resume_workflow(ticket_id=ticket.id)

    assert workflow.status == "COMPLETED"
    assert len(workflow.agent_executions) >= 5
    agent_names = set(a.agent_name for a in workflow.agent_executions)
    assert "Diagnosis Agent" in agent_names
    assert "Retrieval Agent" in agent_names
    assert "Resolution Agent" in agent_names
    assert "Validation Agent" in agent_names
    assert "Escalation Agent" in agent_names
