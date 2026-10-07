"""
AeroAssist AI - Functional Client & Integration Tests
Verifies HTTP endpoints, session auth, ticket creation, and multi-agent execution.
"""
import os
import json
import unittest
from app import app
from database import init_db, get_ticket_by_id, get_all_tickets

class TestAeroAssistFunctional(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

    def test_01_landing_and_login(self):
        """Test login page, unauthenticated redirects, invalid credentials, valid login, and logout."""
        # 1. Unauthenticated user accessing protected dashboard must redirect to login
        unauth_dash = self.client.get("/dashboard")
        self.assertEqual(unauth_dash.status_code, 302)
        self.assertIn("/login", unauth_dash.headers.get("Location", ""))

        # 2. Unauthenticated user accessing protected ticket creation must redirect to login
        unauth_create = self.client.get("/tickets/create")
        self.assertEqual(unauth_create.status_code, 302)
        self.assertIn("/login", unauth_create.headers.get("Location", ""))

        # 3. GET /login should render cleanly
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AeroAssist AI", response.data)
        self.assertIn(b"Passenger & Staff Portal", response.data)

        # 4. Attempt login with empty credentials -> MUST FAIL
        empty_res = self.client.post("/login", data={"identifier": "", "password": ""}, follow_redirects=True)
        self.assertEqual(empty_res.status_code, 200)
        self.assertIn(b"Invalid username or password", empty_res.data)

        # 5. Attempt login with wrong credentials -> MUST FAIL
        wrong_res = self.client.post("/login", data={"identifier": "passenger", "password": "wrong_password"}, follow_redirects=True)
        self.assertEqual(wrong_res.status_code, 200)
        self.assertIn(b"Invalid username or password", wrong_res.data)

        # 6. Login with valid credentials -> MUST SUCCEED
        login_res = self.client.post("/login", data={
            "identifier": "passenger",
            "password": "pass123"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Alex Morgan", login_res.data)
        self.assertIn(b"Airport & Airways Support Dashboard", login_res.data)

        # 7. Logout -> MUST CLEAR SESSION and redirect to login
        logout_res = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn(b"You have been signed out safely", logout_res.data)

        # 8. Post-logout access to protected routes must be rejected
        post_logout = self.client.get("/dashboard")
        self.assertEqual(post_logout.status_code, 302)
        self.assertIn("/login", post_logout.headers.get("Location", ""))

    def test_02_seed_samples_and_dashboard(self):
        """Test seeding 8 test tickets and verifying dashboard stats."""
        # Authenticate
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        seed_res = self.client.post("/seed-samples", follow_redirects=True)
        self.assertEqual(seed_res.status_code, 200)

        # Dashboard check
        dash_res = self.client.get("/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b"Airport & Airways Support Dashboard", dash_res.data)
        self.assertIn(b"Active Airport Support Tickets", dash_res.data)

    def test_03_create_ticket_with_classification(self):
        """Test raising a new ticket and verify scikit-learn classification."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        post_data = {
            "title": "Need wheelchair assistance from curb to departure gate",
            "description": "Passenger has limited mobility and requires WCHR wheelchair assistance from Terminal Entrance 2 to Gate B12.",
            "category": "Auto-Classify",
            "flight_number": "EK203",
            "booking_ref": "DXB881",
            "airport": "DXB",
            "travel_date": "2026-10-10"
        }
        res = self.client.post("/tickets/create", data=post_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Passenger Assistance", res.data)
        self.assertIn(b"EK203", res.data)

    def test_04_run_multi_agent_api(self):
        """Test executing 5-agent sequential API on a ticket."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        tickets = get_all_tickets()
        self.assertGreater(len(tickets), 0)
        test_ticket = tickets[0]
        tkt_id = test_ticket["ticket_id"]

        api_res = self.client.post(f"/api/tickets/{tkt_id}/run-agents")
        self.assertEqual(api_res.status_code, 200)
        data = api_res.get_json()
        self.assertTrue(data["success"])
        self.assertIn(data["results"]["workflow_status"], ["AUTO_RESOLVE", "ESCALATE"])
        self.assertEqual(len(data["results"]["agent_trace"]), 5)

        # Verify updated in database
        updated_ticket = get_ticket_by_id(tkt_id)
        self.assertIn(updated_ticket["status"], ["Resolved", "Escalated"])
        self.assertIsNotNone(updated_ticket["final_confidence"])

    def test_05_knowledge_base_explorer(self):
        """Test knowledge base browser view."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        kb_res = self.client.get("/knowledge-base?cluster=BAGGAGE")
        self.assertEqual(kb_res.status_code, 200)
        self.assertIn(b"KB007", kb_res.data)
        self.assertIn(b"Delayed Baggage Reporting", kb_res.data)

    def test_06_separated_m2_page(self):
        """Test dedicated Milestone 2 AI Knowledge Resolution page."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        tickets = get_all_tickets()
        tkt_id = tickets[0]["ticket_id"]

        m2_res = self.client.get(f"/tickets/{tkt_id}/ai-resolution")
        self.assertEqual(m2_res.status_code, 200)
        self.assertIn(b"AI Knowledge Resolution", m2_res.data)
        self.assertIn(b"Milestone 2", m2_res.data)
        self.assertIn(b"Pre-Execution RAG Vector Retrieval", m2_res.data)
        self.assertIn(b"Generated Knowledge-Grounded Resolution", m2_res.data)
        self.assertIn(b"Continue to Multi-Agent Workflow", m2_res.data)

    def test_07_separated_m3_page(self):
        """Test dedicated Milestone 3 Multi-Agent Studio page."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        tickets = get_all_tickets()
        tkt_id = tickets[0]["ticket_id"]

        m3_res = self.client.get(f"/tickets/{tkt_id}/multi-agent")
        self.assertEqual(m3_res.status_code, 200)
        self.assertIn(b"Multi-Agent Ticket Resolution Studio", m3_res.data)
        self.assertIn(b"Milestone 3", m3_res.data)
        self.assertIn(b"1. Diagnosis Agent", m3_res.data)
        self.assertIn(b"2. Retrieval Agent", m3_res.data)
        self.assertIn(b"3. Resolution Agent", m3_res.data)
        self.assertIn(b"4. Validation Gate", m3_res.data)
        self.assertIn(b"5. Escalation Agent", m3_res.data)

if __name__ == "__main__":
    unittest.main(verbosity=2)
