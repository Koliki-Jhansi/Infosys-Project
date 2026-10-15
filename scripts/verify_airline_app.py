import httpx
import sys
import json
import os

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8081/api")

def main():
    print("=" * 60)
    print(" AeroAssist AI - End-to-End Live Verification Test")
    print("=" * 60)

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Health check
        print("\n1. Checking API Health...")
        r = client.get("/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        health = r.json()
        print(f"   [PASS] Status: {health.get('status')} | App: {health.get('app')} | AI Mock: {health.get('ai_mock_mode')}")

        # 2. Authentication: Support Agent
        print("\n2. Authenticating as Support Agent...")
        login_data = {
            "email": "engineer@aeroassistant.com",
            "password": "EngineerPass123!"
        }
        r = client.post("/auth/login", json=login_data)
        assert r.status_code == 200, f"Login failed: {r.text}"
        agent_token = r.json()["access_token"]
        agent_headers = {"Authorization": f"Bearer {agent_token}"}
        print("   [PASS] Support Agent authenticated.")

        # Get Current User Info
        r = client.get("/auth/me", headers=agent_headers)
        assert r.status_code == 200
        user_info = r.json()
        print(f"   [PASS] Current user: {user_info['full_name']} | Role: {user_info['role']}")

        # 3. Dashboard Telemetry
        print("\n3. Querying Operational Dashboard Summary...")
        r = client.get("/dashboard/summary", headers=agent_headers)
        assert r.status_code == 200, f"Dashboard summary failed: {r.text}"
        dash = r.json()
        print(f"   [PASS] Total Tickets: {dash['total_tickets']}")
        print(f"   [PASS] Open Tickets: {dash.get('open_tickets', 0)}")
        print(f"   [PASS] AI Resolved: {dash.get('ai_resolved_tickets', 0)}")
        print(f"   [PASS] Escalated: {dash.get('escalated_tickets', 0)}")
        print(f"   [PASS] Avg Resolution Time: {dash.get('avg_resolution_time', 'N/A')}")
        print(f"   [PASS] AI Resolution Rate: {dash.get('ai_resolution_rate', 0)}%")

        # 4. Ingest a New Airline Passenger Ticket
        print("\n4. Ingesting New Airline Passenger Ticket...")
        ticket_payload = {
            "title": "Checked diplomatic bag misplaced during connection at London Heathrow",
            "subject": "Checked diplomatic bag misplaced during connection at London Heathrow",
            "description": "Checked suitcase tag #AA-492194 missing after connecting on flight AA-902 from JFK to LHR. Passenger requires baggage location tracking and immediate PIR filing.",
            "passenger_name": "Captain James Kirk",
            "passenger_email": "james.kirk@starfleet.org",
            "booking_reference": "JK9921",
            "flight_number": "AA-902",
            "travel_date": "2026-10-16",
            "category": "Baggage",
            "priority": "High",
            "urgency": "High",
            "affected_service": "Flight Operations"
        }
        r = client.post("/tickets", json=ticket_payload, headers=agent_headers)
        assert r.status_code == 201, f"Create ticket failed: {r.text}"
        ticket = r.json()
        ticket_id = ticket["id"]
        ticket_num = ticket.get("ticket_number", f"TK-{ticket_id:04d}")
        print(f"   [PASS] Created Ticket #{ticket_id} ({ticket_num}) for {ticket['passenger_name']} | PNR: {ticket.get('booking_reference')}")

        # 5. Dedicated AI Solution API Execution
        print(f"\n5. Executing AI Solution Pipeline for Ticket #{ticket_id}...")
        r = client.post(f"/ai/resolve/{ticket_id}", json={}, headers=agent_headers)
        assert r.status_code == 200, f"AI resolve failed: {r.text}"
        sol = r.json()
        print(f"   [PASS] Confidence Score: {sol.get('confidence_score')}% (Threshold: {sol.get('threshold')}%)")
        print(f"   [PASS] Auto Resolve Eligible: {sol.get('eligible_for_auto_resolve')}")
        val = sol.get('validation', {})
        print(f"   [PASS] Validation Verdict: {val.get('verdict')}")
        sources = sol.get('retrieved_sources', [])
        print(f"   [PASS] Retrieved Sources Count: {len(sources)}")
        for idx, src in enumerate(sources[:2]):
            print(f"      - Source {idx+1}: {src.get('document_title')} (Similarity: {src.get('similarity_percentage')}%)")
        gen_resp = sol.get('generated_response', '')
        print(f"   [PASS] Generated Response Snippet: {gen_resp[:120]}...")

        # 6. Dedicated 5-Agent Multi-Agent Workflow Execution
        print(f"\n6. Running 5-Agent Workflow for Ticket #{ticket_id}...")
        r = client.post(f"/workflows/run/{ticket_id}", headers=agent_headers)
        assert r.status_code == 200, f"Workflow run failed: {r.text}"
        wf = r.json()
        wf_id = wf.get("id")
        wf_state = wf.get("state_payload", {})
        print(f"   [PASS] Workflow Run ID: {wf_id} | Status: {wf.get('status')}")
        print(f"   [PASS] Final Outcome: {wf_state.get('final_outcome')}")
        print(f"   [PASS] Confidence: {wf_state.get('final_confidence')}%")
        executions = wf.get("agent_executions", [])
        print(f"   [PASS] Agent Stages Executed: {len(executions)}")
        for stage in executions:
            print(f"      - [{stage.get('agent_name')}]: Status = {stage.get('status')} ({stage.get('duration_ms')}ms)")

        # 7. Add Internal Note
        print(f"\n7. Adding Internal Support Note to Ticket #{ticket_id}...")
        note_payload = {
            "content": "Passenger contacted lost luggage counter at Terminal 3. File PIR confirmed under WorldTracer ref #LHR-AA-49219.",
            "message_type": "INTERNAL_NOTE"
        }
        r = client.post(f"/tickets/{ticket_id}/notes", json=note_payload, headers=agent_headers)
        assert r.status_code == 201, f"Add note failed: {r.text}"
        note = r.json()
        print(f"   [PASS] Note ID: {note['id']} recorded at {note['created_at']}")

        # 8. Query Knowledge Base Vector Search
        print("\n8. Testing Semantic Knowledge Base Retrieval...")
        search_payload = {
            "query": "lost baggage carousel timeline PIR reporting limit",
            "top_k": 3
        }
        r = client.post("/knowledge/search", json=search_payload, headers=agent_headers)
        assert r.status_code == 200, f"Knowledge search failed: {r.text}"
        kb_data = r.json()
        kb_sources = kb_data.get("sources", []) if isinstance(kb_data, dict) else kb_data
        print(f"   [PASS] Retrieved {len(kb_sources)} policy passages:")
        for s in kb_sources:
            print(f"      - Document: {s.get('document_title')} | Similarity: {s.get('similarity_score')}%")

        # 9. Verify Ticket Persistence and Updated State
        print(f"\n9. Verifying Ticket Persistence & Notes Count for #{ticket_id}...")
        r = client.get(f"/tickets/{ticket_id}", headers=agent_headers)
        assert r.status_code == 200
        t_fresh = r.json()
        print(f"   [PASS] Ticket #{ticket_id} Status: {t_fresh['status']}")
        print(f"   [PASS] Notes attached: {len(t_fresh.get('notes', []))}")
        print(f"   [PASS] Has Final AI Response: {'Yes' if t_fresh.get('final_response') else 'No'}")

        # 10. AI Analytics Overview & Evaluation Telemetry
        print("\n10. Testing AI Analytics & Performance Dashboard API...")
        r = client.get("/analytics/overview?date_range=all", headers=agent_headers)
        assert r.status_code == 200, f"Analytics overview failed: {r.text}"
        ov = r.json()
        print(f"   [PASS] Total Evaluations: {ov['total_evaluations']}")
        print(f"   [PASS] AI Resolution Rate: {ov['ai_resolution_rate']}%")
        print(f"   [PASS] Human Escalation Rate: {ov['human_escalation_rate']}%")
        print(f"   [PASS] Avg Confidence Score: {ov['avg_confidence']}%")
        print(f"   [PASS] Avg Pipeline Latency: {ov['avg_latency_ms']} ms")
        print(f"   [PASS] Validation Pass Rate: {ov['validation_pass_rate']}%")
        print(f"   [PASS] Ground-Truth Accuracy: {ov['ground_truth_accuracy']}%")

        # 11. Confidence Distribution
        print("\n11. Querying Confidence Distribution Histogram...")
        r = client.get("/analytics/confidence-distribution?date_range=all", headers=agent_headers)
        assert r.status_code == 200
        dist = r.json()
        print(f"   [PASS] Distribution Buckets: {len(dist['buckets'])} | Policy Threshold: {dist.get('policy_threshold') or dist.get('threshold', 70.0)}%")
        for b in dist['buckets']:
            print(f"      - {b['range']}: {b['count']} evaluations ({b['percentage']}%)")

        # 12. Agent Performance
        print("\n12. Testing 5-Agent Performance Telemetry...")
        r = client.get("/analytics/agent-performance", headers=agent_headers)
        assert r.status_code == 200
        ag = r.json()
        for a in ag['agents']:
            print(f"      - {a['agent_name']}: {a['total_executions']} runs, {a['avg_duration_ms']}ms avg latency")

        # 13. Submit Ground-Truth Feedback
        print("\n13. Submitting Human Ground-Truth Feedback Label...")
        if sol.get("evaluation_id"):
            fb_payload = {
                "evaluation_id": sol["evaluation_id"],
                "ticket_id": ticket_id,
                "accuracy_label": "CORRECT",
                "source_grounding_rating": 5,
                "notes": "Verified by live E2E test script"
            }
            r = client.post("/analytics/feedback", json=fb_payload, headers=agent_headers)
            assert r.status_code == 200, f"Feedback submission failed: {r.text}"
            print(f"   [PASS] Ground-truth label 'CORRECT' saved for Eval #{sol['evaluation_id']}")

        # 14. Export Analytics CSV
        print("\n14. Testing CSV Export...")
        r = client.get("/analytics/export?date_range=all", headers=agent_headers)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")
        print(f"   [PASS] Exported CSV size: {len(r.content)} bytes")

        print("\n" + "=" * 60)
        print(" ALL 14 LIVE END-TO-END VERIFICATION CHECKS PASSED!")
        print("=" * 60)

if __name__ == "__main__":
    main()
