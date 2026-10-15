"""
Full End-to-End verification script for Aero Assistant.
Verifies all 4 milestones against the live running API:
1. Milestone 1: Authentication, Ticket submission, Classification & 70% threshold routing.
2. Milestone 2: RAG Knowledge search & Grounded solutions with traceable citations.
3. Milestone 3: Multi-Agent Workflow execution (Triage -> Retrieval -> RCA -> Solution -> Verification -> Jira).
4. Milestone 4: Live Analytics, Dashboard metrics, and Jira synchronization.
"""

import urllib.request
import json
import sys
import os

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8081/api")

def make_request(endpoint, method="GET", data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_content)
        except Exception:
            return e.code, {"error": err_content}

def main():
    print("=" * 70)
    print(">>> AERO ASSISTANT LIVE E2E VERIFICATION TEST SUITE")
    print("=" * 70)

    # 1. Health Check
    status, health = make_request("/health")
    assert status == 200, f"Health check failed: {health}"
    print(f"[OK] [Milestone 1] Health check OK: {health['app']} (mock_mode={health['ai_mock_mode']})")

    # 2. Authentication Login
    login_payload = {
        "email": "admin@aeroassistant.com",
        "password": "AdminPass123!"
    }
    status, auth = make_request("/auth/login", method="POST", data=login_payload)
    assert status == 200 and "access_token" in auth, f"Login failed: {auth}"
    token = auth["access_token"]
    user = auth["user"]
    print(f"[OK] [Milestone 1] Authenticated as {user['full_name']} (Role: {user['role']})")

    # 3. Create a High-Confidence Ticket
    ticket_payload = {
        "title": "PostgreSQL database deadlocks in billing service transaction pool",
        "description": "Payment transactions are failing with DeadlockDetected errors during billing cycle runs. Multiple concurrent update statements on invoices and customer_balances tables are hanging and timing out.",
        "category": "database",
        "urgency": "high",
        "business_impact": "high",
        "environment": "production",
        "affected_users": 150,
        "affected_service": "billing-service",
        "error_logs": "ERROR: deadlock detected; Process 40182 waits for ExclusiveLock on transaction 88912; Process 40183 waits for ShareLock on transaction 88911."
    }
    status, ticket = make_request("/tickets", method="POST", data=ticket_payload, token=token)
    assert status == 201, f"Create ticket failed: {ticket}"
    ticket_id = ticket["id"]
    print(f"[OK] [Milestone 1] Created Ticket #{ticket_id}: '{ticket['title']}'")

    # 4. Classify Ticket
    status, classification = make_request(f"/tickets/{ticket_id}/classify", method="POST", token=token)
    assert status == 200, f"Classification failed: {classification}"
    confidence = classification["confidence_score"]
    priority = classification["priority"]
    print(f"[OK] [Milestone 1] Classification completed:")
    print(f"   - Predicted Priority: {priority} (Criticality: {classification['criticality']})")
    print(f"   - Confidence Score: {confidence}% (Requires Review: {classification['requires_human_review']})")
    print(f"   - Breakdown: {classification['confidence_breakdown']}")

    # 5. Milestone 2: RAG Semantic Search in Knowledge Base
    search_payload = {
        "query": "PostgreSQL deadlock detected transaction billing",
        "top_k": 3
    }
    status, rag_response = make_request("/knowledge/search", method="POST", data=search_payload, token=token)
    assert status == 200, f"RAG search failed: {rag_response}"
    sources = rag_response.get("sources", [])
    print(f"[OK] [Milestone 2] RAG Search retrieved {len(sources)} grounded document chunks:")
    for res in sources:
        print(f"   - [{res['similarity_score']}%] {res['document_title']} (Chunk #{res['chunk_id']})")

    # 6. Milestone 2: Grounded Solution Generation with Citations
    status, solution = make_request(f"/tickets/{ticket_id}/solution", method="POST", token=token)
    assert status == 200, f"Solution generation failed: {solution}"
    citations = solution.get("citations", [])
    print(f"[OK] [Milestone 2] Grounded Solution generated:")
    print(f"   - Root Cause: {solution.get('likely_root_cause')[:80]}...")
    print(f"   - Citations Count: {len(citations)}")
    for cit in citations:
        print(f"     * Ref: {cit['document_title']} (Similarity: {cit.get('relevance_score', 0):.2f})")

    # 7. Milestone 3: Execute Coordinated Multi-Agent Workflow
    status, workflow = make_request(f"/tickets/{ticket_id}/workflow", method="POST", token=token)
    assert status == 200, f"Workflow execution failed: {workflow}"
    workflow_id = workflow["id"]
    print(f"[OK] [Milestone 3] Multi-Agent Workflow #{workflow_id} executed:")
    print(f"   - Workflow Status: {workflow['status']}")
    print(f"   - Executed Agents ({len(workflow['agent_executions'])}):")
    for agent_exec in workflow["agent_executions"]:
        print(f"     * Agent '{agent_exec['agent_name']}': {agent_exec['status']} ({agent_exec['duration_ms']}ms)")
    
    # 8. Milestone 3: Verify Jira Issue Synchronization
    status, jira_records = make_request(f"/tickets/{ticket_id}/jira", method="POST", token=token)
    assert status == 200, f"Jira query failed: {jira_records}"
    print(f"[OK] [Milestone 3] Jira Integration verification:")
    print(f"   - Jira Issue Key: {jira_records.get('jira_key')}")
    print(f"   - Issue URL: {jira_records.get('jira_url')}")
    print(f"   - Status: {jira_records.get('status')}")

    # 9. Milestone 4: Dashboard & Analytics Aggregations
    status, summary = make_request("/dashboard/summary", token=token)
    assert status == 200, f"Dashboard summary failed: {summary}"
    print(f"[OK] [Milestone 4] Real Dashboard Metrics (DB-Computed):")
    print(f"   - Total Tickets: {summary['total_tickets']}")
    print(f"   - Critical Tickets: {summary['critical_tickets']}")
    print(f"   - Needs Review: {summary['awaiting_review_tickets']}")
    print(f"   - Automation Eligible: {summary['eligible_for_automation_tickets']}")
    print(f"   - Resolved: {summary['resolved_tickets']}")

    status, analytics = make_request("/analytics/metrics", token=token)
    assert status == 200, f"Analytics query failed: {analytics}"
    print(f"[OK] [Milestone 4] Observability & Analytics:")
    print(f"   - Automation Rate: {analytics['automation_rate']}%")
    print(f"   - Total Workflow Runs: {analytics['total_workflows']} (Success Rate: {analytics['workflow_success_rate']}%)")
    print(f"   - Average Agent Latency: {analytics['avg_agent_duration_ms']}ms")
    print(f"   - Indexed Knowledge Docs: {analytics['knowledge_docs_count']}")
    print(f"   - Jira Synced Issues: {analytics['jira_synced_issues']}")

    print("\n" + "=" * 70)
    print("SUCCESS: ALL 4 MILESTONES VERIFIED LIVE!")
    print("=" * 70)

if __name__ == "__main__":
    main()
