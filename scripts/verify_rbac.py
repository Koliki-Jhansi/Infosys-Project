import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8081/api"

def request(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(content)
            except Exception:
                return resp.status, content
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, content
    except Exception as e:
        return 0, str(e)

def login(email, password):
    status, body = request("POST", "/auth/login", {"email": email, "password": password})
    if status == 200:
        return body["access_token"], body["user"]
    raise Exception(f"Login failed for {email} ({status}): {body}")

def run_tests():
    print("=" * 70)
    print("       AERO ASSISTANT — ROLE-BASED ACCESS CONTROL (RBAC) TEST SUITE")
    print("=" * 70)

    # 1. Health check
    print("\n1. Verifying API health...")
    status, body = request("GET", "/health")
    assert status == 200, f"Health check failed: {status}"
    print(f"   [PASS] API is healthy: {body.get('app')}")

    # 2. Authenticate users of various roles
    print("\n2. Authenticating users...")
    admin_token, admin_user = login("admin@aeroassistant.com", "AdminPass123!")
    eng_token, eng_user = login("engineer@aeroassistant.com", "EngineerPass123!")
    agent_token, agent_user = login("agent@aeroassistant.com", "AgentPass123!")
    pass_token, pass_user = login("passenger@aeroassistant.com", "PassengerPass123!")
    req_token, req_user = login("requester@aeroassistant.com", "RequesterPass123!")

    print(f"   [PASS] Admin authenticated: {admin_user['email']} (role: {admin_user['role']})")
    print(f"   [PASS] Engineer authenticated: {eng_user['email']} (role: {eng_user['role']})")
    print(f"   [PASS] Agent authenticated: {agent_user['email']} (role: {agent_user['role']})")
    print(f"   [PASS] Passenger authenticated: {pass_user['email']} (role: {pass_user['role']})")
    print(f"   [PASS] Requester authenticated: {req_user['email']} (role: {req_user['role']})")

    # 3. Test Restricted Endpoint: GET /reviews
    print("\n3. Testing GET /reviews (Restricted to ADMIN, SUPPORT_ENGINEER, SUPPORT_AGENT)...")
    for name, token, should_allow in [
        ("ADMIN", admin_token, True),
        ("SUPPORT_ENGINEER", eng_token, True),
        ("SUPPORT_AGENT", agent_token, True),
        ("PASSENGER", pass_token, False),
        ("REQUESTER", req_token, False),
    ]:
        status, body = request("GET", "/reviews", token=token)
        if should_allow:
            assert status == 200, f"Expected 200 for {name}, got {status}: {body}"
            print(f"   [PASS] {name:16}: Allowed (HTTP 200, items: {len(body)})")
        else:
            assert status == 403, f"Expected 403 for {name}, got {status}: {body}"
            expected_msg = "Operation not permitted. Requires one of roles: ['ADMIN', 'SUPPORT_ENGINEER', 'SUPPORT_AGENT']"
            detail = body.get("detail", "") if isinstance(body, dict) else str(body)
            assert expected_msg in detail, f"Expected '{expected_msg}' in '{detail}'"
            print(f"   [PASS] {name:16}: Denied as intended (HTTP 403: {detail})")

    # 4. Test Restricted Endpoint: POST /integrations/jira/test
    print("\n4. Testing POST /integrations/jira/test (Restricted to ADMIN, SUPPORT_ENGINEER, SUPPORT_AGENT)...")
    for name, token, should_allow in [
        ("ADMIN", admin_token, True),
        ("SUPPORT_ENGINEER", eng_token, True),
        ("SUPPORT_AGENT", agent_token, True),
        ("PASSENGER", pass_token, False),
        ("REQUESTER", req_token, False),
    ]:
        status, body = request("POST", "/integrations/jira/test", token=token)
        if should_allow:
            assert status == 200, f"Expected 200 for {name}, got {status}: {body}"
            print(f"   [PASS] {name:16}: Allowed (HTTP 200, success={body.get('success')})")
        else:
            assert status == 403, f"Expected 403 for {name}, got {status}: {body}"
            expected_msg = "Operation not permitted. Requires one of roles: ['ADMIN', 'SUPPORT_ENGINEER', 'SUPPORT_AGENT']"
            detail = body.get("detail", "") if isinstance(body, dict) else str(body)
            assert expected_msg in detail, f"Expected '{expected_msg}' in '{detail}'"
            print(f"   [PASS] {name:16}: Denied as intended (HTTP 403: {detail})")

    # 5. Test Missing and Invalid Tokens
    print("\n5. Testing missing and invalid tokens...")
    status, body = request("GET", "/reviews", token=None)
    assert status == 401, f"Expected 401 for missing token, got {status}: {body}"
    print(f"   [PASS] Missing token on GET /reviews: HTTP 401 ({body})")

    status, body = request("GET", "/reviews", token="invalid.token.signature")
    assert status == 401, f"Expected 401 for invalid token, got {status}: {body}"
    print(f"   [PASS] Invalid token on GET /reviews: HTTP 401 ({body})")

    status, body = request("POST", "/integrations/jira/test", token=None)
    assert status == 401, f"Expected 401 for missing token, got {status}: {body}"
    print(f"   [PASS] Missing token on POST /integrations/jira/test: HTTP 401 ({body})")

    status, body = request("POST", "/integrations/jira/test", token="corrupted.jwt.here")
    assert status == 401, f"Expected 401 for invalid token, got {status}: {body}"
    print(f"   [PASS] Invalid token on POST /integrations/jira/test: HTTP 401 ({body})")

    # 6. Test Ticket Resolution: Staff vs Owner vs Unauthorized User
    print("\n6. Testing Ticket Resolution (Staff & Ticket Owner permitted; unauthorized denied)...")
    # Step A: Create ticket as passenger
    status, new_ticket = request("POST", "/tickets", {
        "title": "Passenger baggage inquiry",
        "description": "Where is my suitcase for flight AA982?",
        "category": "Baggage",
        "urgency": "Medium"
    }, token=pass_token)
    assert status == 201, f"Failed to create passenger ticket: {status}: {new_ticket}"
    ticket_id = new_ticket["id"]
    print(f"   [INFO] Created ticket #{ticket_id} reported by passenger (id={pass_user['id']})")

    # Step B: Another unauthorized user (requester) tries to resolve passenger's ticket -> DENIED 403
    status, body = request("POST", f"/tickets/{ticket_id}/resolve", {"response": "Trying to resolve someone else's ticket"}, token=req_token)
    assert status == 403, f"Expected 403 when non-owner/non-staff tries to resolve, got {status}: {body}"
    detail = body.get("detail", "") if isinstance(body, dict) else str(body)
    print(f"   [PASS] Unauthorized passenger resolving another ticket: Denied as intended (HTTP 403: {detail})")

    # Step C: The passenger ticket owner resolves their OWN ticket -> ALLOWED 200
    status, body = request("POST", f"/tickets/{ticket_id}/resolve", {"response": "I found my suitcase at carousel 4!"}, token=pass_token)
    assert status == 200, f"Expected 200 when ticket owner resolves own ticket, got {status}: {body}"
    assert body["status"] == "RESOLVED"
    print(f"   [PASS] Ticket owner resolving own ticket: Allowed (HTTP 200, status={body['status']})")

    # Step D: Support Staff (Agent/Admin) resolving any ticket -> ALLOWED 200
    status, body = request("POST", f"/tickets/{ticket_id}/resolve", {"response": "Support engineer closing ticket"}, token=eng_token)
    assert status == 200, f"Expected 200 when support engineer resolves ticket, got {status}: {body}"
    print(f"   [PASS] Support Engineer resolving ticket: Allowed (HTTP 200, status={body['status']})")

    # 7. Test Case-Insensitive Role Registration & Parsing
    print("\n7. Testing Case-Insensitive Role Normalization...")
    unique_suffix = abs(hash(str(ticket_id))) % 100000
    test_user_email = f"staff_test_{unique_suffix}@airline.com"
    status, reg_body = request("POST", "/auth/register", {
        "email": test_user_email,
        "password": "Password123!",
        "full_name": "Test Staff Engineer",
        "role": "support_engineer" # lowercase
    })
    assert status == 201, f"Expected 201 for lowercase role registration, got {status}: {reg_body}"
    assert reg_body["user"]["role"] == "SUPPORT_ENGINEER"
    new_staff_token = reg_body["access_token"]
    print(f"   [PASS] Registration parsed lowercase 'support_engineer' -> {reg_body['user']['role']}")

    # Check that this newly registered user can access restricted endpoint
    status, body = request("GET", "/reviews", token=new_staff_token)
    assert status == 200, f"Expected 200 for newly registered support engineer, got {status}: {body}"
    print(f"   [PASS] Newly registered support engineer allowed access to GET /reviews (HTTP 200)")

    print("\n" + "=" * 70)
    print("       ALL RBAC AUTHORIZATION AND ROLE VERIFICATION TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n[FAIL] Test assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
