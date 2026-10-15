import httpx
import sys

def run_jira_tests():
    print("=" * 60)
    print(" AeroAssist — Jira Cloud Integration Verification")
    print("=" * 60)

    client = httpx.Client(base_url="http://127.0.0.1:8081", timeout=15.0)

    # 1. Authenticate
    print("\n1. Authenticating as Support Engineer...")
    auth_resp = client.post("/api/auth/login", json={
        "email": "engineer@aeroassistant.com",
        "password": "EngineerPass123!"
    })
    assert auth_resp.status_code == 200, f"Login failed: {auth_resp.text}"
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   [PASS] Authenticated successfully.")

    # 2. Check Status
    print("\n2. Checking Jira Integration Status...")
    status_resp = client.get("/api/integrations/jira/status", headers=headers)
    assert status_resp.status_code == 200, f"Status check failed: {status_resp.text}"
    status_data = status_resp.json()
    print(f"   [PASS] Mode: {status_data['mode']} | Project: {status_data['project_key']} | Base URL: {status_data['base_url']}")

    # 3. Test Connectivity
    print("\n3. Testing Jira Cloud Connectivity...")
    test_resp = client.post("/api/integrations/jira/test", headers=headers)
    assert test_resp.status_code == 200, f"Connection test failed: {test_resp.text}"
    test_data = test_resp.json()
    print(f"   [PASS] Connectivity test: success={test_data['success']} | {test_data['message']}")

    # 4. Fetch Projects
    print("\n4. Retrieving Accessible Jira Projects...")
    proj_resp = client.get("/api/integrations/jira/projects", headers=headers)
    assert proj_resp.status_code == 200, f"Projects failed: {proj_resp.text}"
    projects = proj_resp.json()
    assert len(projects) > 0, "No projects returned"
    print(f"   [PASS] Retrieved {len(projects)} projects: {[p['key'] for p in projects]}")

    # 5. Search Issues with Filters & Pagination
    print("\n5. Searching Issues (Visual Filters)...")
    issues_resp = client.get("/api/integrations/jira/issues?page=1&size=5", headers=headers)
    assert issues_resp.status_code == 200, f"Issues search failed: {issues_resp.text}"
    issues_data = issues_resp.json()
    assert issues_data["total"] > 0, "No issues found"
    print(f"   [PASS] Total Issues: {issues_data['total']} | Page {issues_data['page']} of {issues_data['pages']}")

    # 6. Test JQL Query
    print("\n6. Testing JQL Search Mode...")
    jql_resp = client.get('/api/integrations/jira/issues?jql=project = AERO', headers=headers)
    assert jql_resp.status_code == 200, f"JQL search failed: {jql_resp.text}"
    jql_data = jql_resp.json()
    print(f"   [PASS] JQL 'project = AERO' matched {jql_data['total']} issues.")

    # 7. Create New Jira Issue
    print("\n7. Creating New Jira Issue...")
    create_payload = {
        "project_key": "AERO",
        "summary": "Avionics altimeter calibration variance on Boeing 787 testbed",
        "description": "Cabin crew reported primary altimeter offset of +35 feet during descent into ORD.",
        "priority": "High",
        "issue_type": "Bug",
        "assignee": "Sarah Connor"
    }
    create_resp = client.post("/api/integrations/jira/issues", json=create_payload, headers=headers)
    assert create_resp.status_code == 200, f"Issue creation failed: {create_resp.text}"
    new_issue = create_resp.json()
    created_key = new_issue["key"]
    print(f"   [PASS] Issue Created: {created_key} - '{new_issue['summary']}' [Status: {new_issue['status']}]")

    # 8. Get Issue Details
    print(f"\n8. Fetching Details for {created_key}...")
    detail_resp = client.get(f"/api/integrations/jira/issues/{created_key}", headers=headers)
    assert detail_resp.status_code == 200, f"Issue detail failed: {detail_resp.text}"
    detail = detail_resp.json()
    assert detail["key"] == created_key
    print(f"   [PASS] Retrieved details for {created_key} | Transitions available: {len(detail['transitions'])}")

    # 9. Update Issue Summary & Description
    print(f"\n9. Updating Issue {created_key}...")
    update_payload = {
        "summary": "Avionics altimeter calibration variance on Boeing 787 testbed (Updated)",
        "description": "Updated context: Checked wiring harness and pitot static tube inspection confirmed clear."
    }
    update_resp = client.put(f"/api/integrations/jira/issues/{created_key}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200, f"Issue update failed: {update_resp.text}"
    updated = update_resp.json()
    assert "Updated" in updated["summary"]
    print(f"   [PASS] Updated {created_key}: '{updated['summary']}'")

    # 10. Add Comment to Issue
    print(f"\n10. Adding Comment to {created_key}...")
    comm_resp = client.post(f"/api/integrations/jira/issues/{created_key}/comments", json={
        "comment": "Station avionics engineer verified barometric sensor readings match tower QNH."
    }, headers=headers)
    assert comm_resp.status_code == 200, f"Comment failed: {comm_resp.text}"
    comm = comm_resp.json()
    print(f"   [PASS] Comment added: ID {comm['id']} by {comm['author']}")

    # 11. Transition Issue Workflow
    print(f"\n11. Transitioning Issue Workflow for {created_key}...")
    trans_list_resp = client.get(f"/api/integrations/jira/issues/{created_key}/transitions", headers=headers)
    assert trans_list_resp.status_code == 200
    transitions = trans_list_resp.json()
    assert len(transitions) > 0, "No transitions available"
    target_transition = transitions[0]
    
    trans_resp = client.post(f"/api/integrations/jira/issues/{created_key}/transitions", json={
        "transition_id": target_transition["id"],
        "comment": "Transitioned to active diagnosis."
    }, headers=headers)
    assert trans_resp.status_code == 200, f"Transition failed: {trans_resp.text}"
    transitioned = trans_resp.json()
    print(f"   [PASS] Transitioned {created_key} via '{target_transition['name']}' to status: {transitioned['status']}")

    # 12. Link / Sync Ticket to Jira (Idempotent)
    print("\n12. Testing Ticket Synchronization & Idempotency...")
    # Fetch a ticket
    t_resp = client.get("/api/tickets?size=1", headers=headers)
    ticket_id = t_resp.json()["items"][0]["id"]
    
    sync_resp1 = client.post(f"/api/tickets/{ticket_id}/jira", headers=headers)
    assert sync_resp1.status_code == 200, f"Sync 1 failed: {sync_resp1.text}"
    sync1 = sync_resp1.json()
    print(f"   [PASS] Ticket #{ticket_id} synced to Jira: Key {sync1['jira_key']}")

    # Retry sync - must return existing record without duplicate
    sync_resp2 = client.post(f"/api/tickets/{ticket_id}/jira", headers=headers)
    assert sync_resp2.status_code == 200, f"Sync 2 failed: {sync_resp2.text}"
    sync2 = sync_resp2.json()
    assert sync1["id"] == sync2["id"] and sync1["jira_key"] == sync2["jira_key"], "Duplicate created!"
    print(f"   [PASS] Idempotency verified: duplicate creation prevented (returned existing #{sync2['id']})")

    # 13. Refresh Ticket Jira Status
    print(f"\n13. Refreshing Ticket #{ticket_id} Jira Status...")
    refresh_resp = client.post(f"/api/tickets/{ticket_id}/jira/refresh", headers=headers)
    assert refresh_resp.status_code == 200, f"Refresh failed: {refresh_resp.text}"
    refreshed = refresh_resp.json()
    print(f"   [PASS] Ticket #{ticket_id} Jira status refreshed: {refreshed['status']}")

    print("\n" + "=" * 60)
    print(" ALL 13 JIRA CLOUD INTEGRATION CHECKS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_jira_tests()
