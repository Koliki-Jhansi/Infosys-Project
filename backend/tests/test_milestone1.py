import pytest
from app.policies.confidence_policy import evaluate_ticket_confidence_policy, calculate_explainable_confidence
from app.policies.priority_policy import calculate_priority_and_criticality, detect_security_signals

def test_confidence_boundary_69():
    """Confidence score of 69 (below 70) must route to NEEDS_REVIEW and require human review."""
    status, requires_review, reason = evaluate_ticket_confidence_policy(
        confidence_score=69.0,
        threshold=70.0,
        priority="P3 Medium",
        criticality="Medium",
        category="Application",
        detected_security_signals=[]
    )
    assert status == "NEEDS_REVIEW"
    assert requires_review is True
    assert "below automation threshold" in reason

def test_confidence_boundary_70():
    """Confidence score of 70 (at threshold) must route to CLASSIFIED without requiring human review."""
    status, requires_review, reason = evaluate_ticket_confidence_policy(
        confidence_score=70.0,
        threshold=70.0,
        priority="P3 Medium",
        criticality="Medium",
        category="Application",
        detected_security_signals=[]
    )
    assert status == "CLASSIFIED"
    assert requires_review is False
    assert "satisfies automation threshold" in reason

def test_confidence_boundary_71():
    """Confidence score of 71 (above threshold) must route to CLASSIFIED without requiring human review."""
    status, requires_review, reason = evaluate_ticket_confidence_policy(
        confidence_score=71.0,
        threshold=70.0,
        priority="P3 Medium",
        criticality="Medium",
        category="Application",
        detected_security_signals=[]
    )
    assert status == "CLASSIFIED"
    assert requires_review is False
    assert "satisfies automation threshold" in reason

def test_safety_override_critical_incident():
    """P1 Critical or Criticality Critical MUST require human review even with 99% confidence."""
    status, requires_review, reason = evaluate_ticket_confidence_policy(
        confidence_score=99.0,
        threshold=70.0,
        priority="P1 Critical",
        criticality="Critical",
        category="Infrastructure",
        detected_security_signals=[]
    )
    assert status == "NEEDS_REVIEW"
    assert requires_review is True
    assert "P1 Critical severity requires mandatory engineer oversight" in reason

def test_safety_override_security_incident():
    """Security incidents MUST require human review even with high confidence."""
    status, requires_review, reason = evaluate_ticket_confidence_policy(
        confidence_score=95.0,
        threshold=70.0,
        priority="P2 High",
        criticality="High",
        category="Security",
        detected_security_signals=["unauthorized", "exfiltration"]
    )
    assert status == "NEEDS_REVIEW"
    assert requires_review is True
    assert "Security incident requires security team authorization" in reason

def test_priority_matrix_deterministic_escalation():
    """Tests deterministic priority logic incorporating environment and user impact."""
    # Critical urgency + Extensive impact + Prod + 1000 users = P1 Critical
    priority, criticality, sec_flags, reason = calculate_priority_and_criticality(
        urgency="Critical",
        business_impact="Extensive / Organization-wide",
        environment="production",
        affected_users=1000,
        category="Database",
        title="Postgres primary replica deadlock",
        description="All write operations timing out",
        error_logs="FATAL: terminating connection due to administrator command"
    )
    assert priority == "P1 Critical"
    assert criticality == "Critical"

    # Low urgency + Minor impact + dev + 1 user = P4 Low
    priority_low, crit_low, _, _ = calculate_priority_and_criticality(
        urgency="Low",
        business_impact="Minor / Single user",
        environment="development",
        affected_users=1,
        category="Application",
        title="Typo in docs",
        description="Please update spelling on login button"
    )
    assert priority_low == "P4 Low"
    assert crit_low == "Low"

def test_security_signal_detection():
    flags = detect_security_signals("Possible CVE-2024-1234 exploit causing unauthorized admin access")
    assert "cve" in flags
    assert "exploit" in flags
    assert "unauthorized" in flags

def test_api_auth_and_ticket_flow(client, requester_token, engineer_token):
    headers = {"Authorization": f"Bearer {requester_token}"}
    
    # 1. Create ticket
    payload = {
        "title": "Production VPN gateway dropping packets for all remote employees",
        "description": "The Cisco AnyConnect VPN gateway has been dropping sessions every 3 minutes. Employees are experiencing severe latency and packet loss across multiple subnets. This began immediately after the 08:00 AM maintenance window.",
        "affected_service": "Corporate VPN Gateway",
        "category": "Network",
        "business_impact": "Extensive / Organization-wide",
        "urgency": "High",
        "environment": "production",
        "affected_users": 250,
        "error_logs": "ERROR: [vpn_gw_01] Packet loss 45% detected on interface eth0. Gateway session timeout."
    }
    create_resp = client.post("/api/tickets", json=payload, headers=headers)
    assert create_resp.status_code == 201
    ticket_data = create_resp.json()
    ticket_id = ticket_data["id"]
    assert ticket_data["title"] == payload["title"]
    assert ticket_data["classification"] is not None
    assert ticket_data["classification"]["predicted_category"] == "Network"
    assert ticket_data["classification"]["confidence_score"] > 0
    assert "confidence_breakdown" in ticket_data["classification"]

    # 2. Support engineer view in review queue or list
    eng_headers = {"Authorization": f"Bearer {engineer_token}"}
    list_resp = client.get("/api/tickets", headers=eng_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 3. Check dashboard summary
    dash_resp = client.get("/api/dashboard/summary", headers=eng_headers)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["total_tickets"] >= 1
    assert len(dash_data["priority_distribution"]) == 4

    # 4. Review ticket if in review queue
    review_resp = client.post(
        f"/api/tickets/{ticket_id}/review",
        json={"action": "APPROVE", "notes": "Approved by senior network engineer"},
        headers=eng_headers
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["success"] is True
    assert review_resp.json()["new_status"] == "CLASSIFIED"
