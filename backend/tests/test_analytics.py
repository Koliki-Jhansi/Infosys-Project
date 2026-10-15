import pytest
from fastapi.testclient import TestClient
from app.models.evaluation import AIEvaluation, EvaluationFeedback
from app.models.ticket import Ticket, TicketStatus

@pytest.fixture
def auth_header(admin_token: str):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def seeded_evaluation(db, client: TestClient):
    ticket = Ticket(
        title="24-Hour Cancellation Refund",
        description="I cancelled within 24 hours of purchase, requesting refund.",
        category="Cancellation and Refund",
        affected_service="Flight Operations",
        business_impact="Single passenger",
        urgency="Medium",
        passenger_name="Sarah Miller",
        passenger_email="sarah@example.com",
        booking_reference="AA-TEST1",
        flight_number="AA-100",
        status=TicketStatus.RESOLVED,
        reporter_id=1,
        ticket_number="TK-0001"
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    eval_rec = AIEvaluation(
        ticket_id=ticket.id,
        model_name="AeroAssist-Agentic-v1",
        confidence_score=92.5,
        validation_outcome="PASS",
        validation_details={"verdict": "PASS", "checks": []},
        final_outcome="RESOLVED",
        latency_ms=125,
        retrieved_sources_count=3,
        status="SUCCESS"
    )
    db.add(eval_rec)
    db.commit()
    db.refresh(eval_rec)
    return eval_rec

def test_analytics_overview(client: TestClient, auth_header: dict, seeded_evaluation):
    response = client.get("/api/analytics/overview?date_range=all", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["total_evaluations"] >= 1
    assert "ai_resolution_rate" in data
    assert "human_escalation_rate" in data
    assert "avg_confidence" in data
    assert "avg_latency_ms" in data
    assert "validation_pass_rate" in data
    assert "ai_error_rate" in data

def test_confidence_distribution_buckets(client: TestClient, auth_header: dict, seeded_evaluation):
    response = client.get("/api/analytics/confidence-distribution?date_range=all", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert "buckets" in data
    ranges = [b["range"] for b in data["buckets"]]
    assert "0-29%" in ranges
    assert "30-49%" in ranges
    assert "50-69%" in ranges
    assert "70-84%" in ranges
    assert "85-100%" in ranges
    assert data["policy_threshold"] == 70.0

def test_agent_performance_five_agents(client: TestClient, auth_header: dict):
    response = client.get("/api/analytics/agent-performance", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    agent_names = [a["agent_name"] for a in data["agents"]]
    assert "Diagnosis Agent" in agent_names
    assert "Retrieval Agent" in agent_names
    assert "Resolution Agent" in agent_names
    assert "Validation Agent" in agent_names
    assert "Escalation Agent" in agent_names

def test_evaluations_list(client: TestClient, auth_header: dict, seeded_evaluation):
    response = client.get("/api/analytics/evaluations?page=1&size=10", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    item = data["items"][0]
    assert "id" in item
    assert "ticket_id" in item
    assert "confidence_score" in item
    assert "final_outcome" in item

def test_submit_ground_truth_feedback(client: TestClient, auth_header: dict, seeded_evaluation):
    feedback_payload = {
        "evaluation_id": seeded_evaluation.id,
        "ticket_id": seeded_evaluation.ticket_id,
        "accuracy_label": "CORRECT",
        "source_grounding_rating": 5,
        "notes": "Verified by airline QA test"
    }
    res = client.post("/api/analytics/feedback", json=feedback_payload, headers=auth_header)
    assert res.status_code == 200
    assert res.json()["success"] is True

def test_export_analytics_csv(client: TestClient, auth_header: dict, seeded_evaluation):
    response = client.get("/api/analytics/export?date_range=all", headers=auth_header)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    csv_text = response.text
    assert "Evaluation ID" in csv_text
    assert "Confidence Score" in csv_text
    assert "Final Outcome" in csv_text
