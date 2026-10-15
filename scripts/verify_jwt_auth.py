import json
import urllib.request
import urllib.error
import sys
import time
from datetime import datetime, timedelta, timezone
import jwt

BASE_URL = "http://127.0.0.1:8081/api"
SECRET_KEY = "aero-assistant-insecure-secret-key-change-in-production-min32chars"
ALGORITHM = "HS256"

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

def run_tests():
    print("=" * 70)
    print("      AERO ASSISTANT — COMPREHENSIVE JWT & AUTHENTICATION VERIFICATION")
    print("=" * 70)

    # 1. API Health
    print("\n1. Verifying API health...")
    status, body = request("GET", "/health")
    assert status == 200, f"Health check failed: {status}"
    print(f"   [PASS] API healthy: {body.get('app')}")

    # 2. Registration succeeds with valid data
    print("\n2. Testing Registration with valid data...")
    test_email = f"jwt_test_{int(time.time())}@aeroassistant.com"
    status, reg_body = request("POST", "/auth/register", {
        "email": test_email,
        "password": "SecurePassword123!",
        "full_name": "JWT Test Pilot",
        "role": "PASSENGER"
    })
    assert status == 201, f"Expected 201 for registration, got {status}: {reg_body}"
    assert "access_token" in reg_body, "access_token missing in register response"
    assert reg_body["user"]["email"] == test_email
    assert reg_body["user"]["role"] == "PASSENGER"
    print(f"   [PASS] User registered successfully: {test_email} (ID: {reg_body['user']['id']})")
    reg_token = reg_body["access_token"]

    # 3. Duplicate registration is handled correctly
    print("\n3. Testing Duplicate registration rejection...")
    status, dup_body = request("POST", "/auth/register", {
        "email": test_email,
        "password": "SecurePassword123!",
        "full_name": "Duplicate User",
        "role": "PASSENGER"
    })
    assert status == 400, f"Expected 400 for duplicate email, got {status}: {dup_body}"
    detail = dup_body.get("detail", "") if isinstance(dup_body, dict) else str(dup_body)
    assert "already exists" in detail.lower(), f"Unexpected error message: {detail}"
    print(f"   [PASS] Duplicate registration rejected: HTTP 400 ({detail})")

    # 4. Login returns a valid access token
    print("\n4. Testing Login with valid credentials...")
    status, login_body = request("POST", "/auth/login", {
        "email": test_email,
        "password": "SecurePassword123!"
    })
    assert status == 200, f"Expected 200 for login, got {status}: {login_body}"
    assert "access_token" in login_body, "access_token missing in login response"
    login_token = login_body["access_token"]
    assert login_body["user"]["email"] == test_email
    print(f"   [PASS] Login successful, token received.")

    # 5. Incorrect credentials are rejected
    print("\n5. Testing Incorrect credentials rejection...")
    status, wrong_body = request("POST", "/auth/login", {
        "email": test_email,
        "password": "WrongPassword999!"
    })
    assert status == 401, f"Expected 401 for bad password, got {status}: {wrong_body}"
    detail = wrong_body.get("detail", "") if isinstance(wrong_body, dict) else str(wrong_body)
    assert "incorrect" in detail.lower(), f"Unexpected error message: {detail}"
    print(f"   [PASS] Incorrect password rejected: HTTP 401 ({detail})")

    status, bad_email_body = request("POST", "/auth/login", {
        "email": "nonexistent_pilot_999@aeroassistant.com",
        "password": "Password123!"
    })
    assert status == 401, f"Expected 401 for nonexistent email, got {status}: {bad_email_body}"
    print(f"   [PASS] Nonexistent email rejected: HTTP 401")

    # 6. Valid token accesses protected endpoints
    print("\n6. Testing Protected endpoint access with valid token...")
    # Protected endpoint: /auth/me
    status, me_body = request("GET", "/auth/me", token=login_token)
    assert status == 200, f"Expected 200 for /auth/me, got {status}: {me_body}"
    assert me_body["email"] == test_email
    assert me_body["full_name"] == "JWT Test Pilot"
    print(f"   [PASS] GET /auth/me profile retrieved: {me_body['email']} (role: {me_body['role']})")

    # Protected endpoint: /tickets
    status, tickets_body = request("GET", "/tickets", token=login_token)
    assert status == 200, f"Expected 200 for /tickets, got {status}: {tickets_body}"
    print(f"   [PASS] GET /tickets accessed successfully: HTTP 200")

    # 7. Missing, invalid, and expired tokens are rejected
    print("\n7. Testing Missing, invalid, and expired token rejection...")
    # Missing token
    status, miss_body = request("GET", "/auth/me", token=None)
    assert status == 401, f"Expected 401 for missing token, got {status}: {miss_body}"
    print(f"   [PASS] Missing token rejected: HTTP 401 ({miss_body.get('detail')})")

    # Invalid token (tampered signature)
    status, inv_body = request("GET", "/auth/me", token=login_token + "tampered")
    assert status == 401, f"Expected 401 for tampered token, got {status}: {inv_body}"
    print(f"   [PASS] Invalid token rejected: HTTP 401 ({inv_body.get('detail')})")

    # Expired token (created with exp in past)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=60)
    expired_jwt = jwt.encode(
        {"sub": str(me_body["id"]), "email": test_email, "exp": past_time, "iat": past_time - timedelta(minutes=5)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    status, exp_body = request("GET", "/auth/me", token=expired_jwt)
    assert status == 401, f"Expected 401 for expired token, got {status}: {exp_body}"
    print(f"   [PASS] Expired token rejected: HTTP 401 ({exp_body.get('detail')})")

    # 8. Role-based restrictions remain enforced
    print("\n8. Testing Role-based permissions enforcement...")
    # Passenger cannot access review queue
    status, rev_pass = request("GET", "/reviews", token=login_token)
    assert status == 403, f"Expected 403 for passenger on /reviews, got {status}: {rev_pass}"
    print(f"   [PASS] Passenger denied access to /reviews: HTTP 403 ({rev_pass.get('detail')})")

    # Support Engineer can access review queue
    status, eng_login = request("POST", "/auth/login", {"email": "engineer@aeroassistant.com", "password": "EngineerPass123!"})
    assert status == 200, f"Failed engineer login: {status}"
    eng_token = eng_login["access_token"]
    status, rev_eng = request("GET", "/reviews", token=eng_token)
    assert status == 200, f"Expected 200 for engineer on /reviews, got {status}: {rev_eng}"
    print(f"   [PASS] Support Engineer permitted access to /reviews: HTTP 200 (queue items: {len(rev_eng)})")

    # 9. Logout behavior
    print("\n9. Testing Logout endpoint...")
    status, logout_body = request("POST", "/auth/logout", token=login_token)
    assert status == 200, f"Expected 200 for logout, got {status}: {logout_body}"
    print(f"   [PASS] Logout endpoint succeeded: {logout_body}")

    print("\n" + "=" * 70)
    print("      ALL JWT AUTHENTICATION & SECURITY VERIFICATION CHECKS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
