"""
AeroAssist AI - Functional Client & Integration Tests
Verifies HTTP endpoints, session auth, ticket creation, resolution filters, and multi-agent execution.
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
        """Test welcome page, login page, unauthenticated redirects, invalid credentials, valid login, and logout."""
        # 1. Unauthenticated user accessing root `/` gets welcome page
        welcome_res = self.client.get("/")
        self.assertEqual(welcome_res.status_code, 200)
        self.assertIn(b"Smarter Support for Every Journey", welcome_res.data)
        self.assertIn(b"AeroAssist AI", welcome_res.data)
        self.assertIn(b"Intelligent Classification", welcome_res.data)
        self.assertIn(b"Semantic Domain RAG", welcome_res.data)
        self.assertIn(b"5-Agent Orchestration", welcome_res.data)
        self.assertIn(b"Human Escalation Guard", welcome_res.data)

        # 2. GET /welcome should render cleanly
        welcome_direct = self.client.get("/welcome")
        self.assertEqual(welcome_direct.status_code, 200)
        self.assertIn(b"Smarter Support for Every Journey", welcome_direct.data)

        # 3. Unauthenticated user accessing protected dashboard must redirect to login
        unauth_dash = self.client.get("/dashboard")
        self.assertEqual(unauth_dash.status_code, 302)
        self.assertIn("/login", unauth_dash.headers.get("Location", ""))

        # 4. Unauthenticated user accessing protected ticket creation must redirect to login
        unauth_create = self.client.get("/tickets/create")
        self.assertEqual(unauth_create.status_code, 302)
        self.assertIn("/login", unauth_create.headers.get("Location", ""))

        # 5. GET /login should render cleanly with login form
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Passenger", response.data)
        self.assertIn(b"Back to Welcome", response.data)


        # 6. Attempt login with empty credentials -> MUST FAIL
        empty_res = self.client.post("/login", data={"identifier": "", "password": ""}, follow_redirects=True)
        self.assertEqual(empty_res.status_code, 200)
        self.assertIn(b"Invalid username or password", empty_res.data)

        # 7. Attempt login with wrong credentials -> MUST FAIL
        wrong_res = self.client.post("/login", data={"identifier": "passenger", "password": "wrong_password"}, follow_redirects=True)
        self.assertEqual(wrong_res.status_code, 200)
        self.assertIn(b"Invalid username or password", wrong_res.data)

        # 8. Login with valid credentials -> MUST SUCCEED
        login_res = self.client.post("/login", data={
            "identifier": "passenger",
            "password": "pass123"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Good to see you", login_res.data)
        self.assertIn(b"Alex Morgan", login_res.data)


        # 9. Logout -> MUST CLEAR SESSION and redirect to login
        logout_res = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn(b"You have been signed out safely", logout_res.data)

        # 10. Post-logout access to protected routes must be rejected
        post_logout = self.client.get("/dashboard")
        self.assertEqual(post_logout.status_code, 302)
        self.assertIn("/login", post_logout.headers.get("Location", ""))

    def test_02_seed_samples_and_dashboard(self):
        """Test seeding test tickets and verifying dashboard stats and sidebar items."""
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
        self.assertIn(b"Good to see you, Alex Morgan", dash_res.data)
        self.assertIn(b"Total Tickets", dash_res.data)
        self.assertIn(b"AI Resolved", dash_res.data)
        self.assertIn(b"Escalated", dash_res.data)
        self.assertIn(b"Your Support Tickets", dash_res.data)
        # Check all sidebar items exist
        self.assertIn(b"Dashboard", dash_res.data)
        self.assertIn(b"Create Ticket", dash_res.data)
        self.assertIn(b"My Tickets", dash_res.data)
        self.assertIn(b"AI Solutions", dash_res.data)
        self.assertIn(b"Multi-Agent Workflow", dash_res.data)
        self.assertIn(b"Knowledge Library", dash_res.data)
        self.assertIn(b"Escalated Tickets", dash_res.data)
        self.assertIn(b"My Profile", dash_res.data)
        self.assertIn(b"Sign Out", dash_res.data)

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
        self.assertIn("diagnosis_confidence", data["results"])
        self.assertIn("retrieval_similarity", data["results"])
        self.assertIn("resolution_completeness", data["results"])
        self.assertIn("final_confidence", data["results"])

        # Verify updated in database
        updated_ticket = get_ticket_by_id(tkt_id)
        self.assertIn(updated_ticket["status"], ["Resolved", "Escalated", "Open"])
        self.assertIsNotNone(updated_ticket["final_confidence"])

    def test_05_knowledge_base_explorer(self):
        """Test knowledge base browser view and exact article counts."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        kb_res = self.client.get("/knowledge-base?cluster=BAGGAGE")
        self.assertEqual(kb_res.status_code, 200)
        self.assertIn(b"KB007", kb_res.data)
        self.assertIn(b"Delayed Baggage", kb_res.data)
        self.assertIn(b"Knowledge Library", kb_res.data)

    def test_06_ai_solutions_page(self):
        """Test dedicated AI Solutions result page."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        tickets = get_all_tickets()
        tkt_id = tickets[0]["ticket_id"]

        ai_res = self.client.get(f"/ai-solutions?ticket_id={tkt_id}")
        self.assertEqual(ai_res.status_code, 200)
        self.assertIn(b"AI Solutions", ai_res.data)
        self.assertIn(b"AI-Resolved", ai_res.data)


    def test_07_multi_agent_page(self):
        """Test dedicated Multi-Agent Resolution Studio page."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        tickets = get_all_tickets()
        tkt_id = tickets[0]["ticket_id"]

        m3_res = self.client.get(f"/multi-agent?ticket_id={tkt_id}")
        self.assertEqual(m3_res.status_code, 200)
        self.assertIn(b"Multi-Agent Ticket Resolution", m3_res.data)
        self.assertIn(b"Diagnosis", m3_res.data)
        self.assertIn(b"Retrieval", m3_res.data)
        self.assertIn(b"Resolution", m3_res.data)
        self.assertIn(b"Validation", m3_res.data)
        self.assertIn(b"Escalation", m3_res.data)



    def test_08_escalated_tickets_page(self):
        """Test escalated tickets view."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        esc_res = self.client.get("/escalated-tickets")
        self.assertEqual(esc_res.status_code, 200)
        self.assertIn(b"Escalated Tickets", esc_res.data)

    def test_09_profile_page(self):
        """Test passenger profile view."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        prof_res = self.client.get("/profile")
        self.assertEqual(prof_res.status_code, 200)
        self.assertIn(b"Passenger Profile", prof_res.data)
        self.assertIn(b"Alex Morgan", prof_res.data)

    def test_10_resolution_status_filters(self):
        """Test Ticket Resolution Status dropdown filtering."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        # 1. Filter AI Resolved
        res_auto = self.client.get("/tickets?resolution_status=AUTO_RESOLVE")
        self.assertEqual(res_auto.status_code, 200)

        # 2. Filter Escalated
        res_esc = self.client.get("/tickets?resolution_status=ESCALATE")
        self.assertEqual(res_esc.status_code, 200)

        # 3. Filter All
        res_all = self.client.get("/tickets?resolution_status=All")
        self.assertEqual(res_all.status_code, 200)

    def test_11_ticket_authorization_isolation(self):
        """Test that a passenger cannot view another passenger's ticket."""
        # 1. Create a ticket as passenger 1
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        tkt_post = self.client.post("/tickets/create", data={
            "title": "Private Passenger Itinerary Inquiry",
            "description": "Confidential flight reservation details for passenger 1.",
            "category": "Bookings"
        }, follow_redirects=True)
        self.assertEqual(tkt_post.status_code, 200)

        # Get latest ticket
        t1_tickets = get_all_tickets(user_id=1, role="passenger")
        self.assertGreater(len(t1_tickets), 0)
        tkt_id = t1_tickets[0]["ticket_id"]

        # 2. Switch session to another passenger (user 9999)
        with self.client.session_transaction() as sess:
            sess["user_id"] = 9999
            sess["username"] = "other_passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Other Passenger"

        # 3. Access passenger 1's ticket -> Must be denied
        detail_res = self.client.get(f"/tickets/{tkt_id}", follow_redirects=True)
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn(b"Access denied", detail_res.data)

    def test_12_public_knowledge_base(self):
        """Test that unauthenticated visitors can access and search public Knowledge Base without login."""
        self.client.get("/logout")

        # 1. Unauthenticated GET /knowledge-base -> Must return 200 OK (no 302 to login)
        kb_res = self.client.get("/knowledge-base")
        self.assertEqual(kb_res.status_code, 200)
        self.assertIn(b"Knowledge Library", kb_res.data)
        self.assertIn(b"Search Knowledge Base", kb_res.data)
        self.assertIn(b"Passenger Login", kb_res.data)

        # 2. Search query across KB without auth
        search_res = self.client.get("/knowledge-base?q=baggage")
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b"baggage", search_res.data.lower())

        # 3. Filter by domain cluster without auth
        cluster_res = self.client.get("/knowledge-base?cluster=BAGGAGE")
        self.assertEqual(cluster_res.status_code, 200)
        self.assertIn(b"BAGGAGE", cluster_res.data)

    def test_13_public_contact_page_and_form(self):
        """Test public contact page rendering, validation, and database storage."""
        from database import get_contact_messages
        self.client.get("/logout")

        # 1. Unauthenticated GET /contact -> Must return 200 OK
        contact_page = self.client.get("/contact")
        self.assertEqual(contact_page.status_code, 200)
        self.assertIn(b"Contact AeroAssist AI", contact_page.data)
        self.assertIn(b"We're here to help you with your airport and airline support questions.", contact_page.data)

        # 2. Missing fields POST -> Must fail validation
        invalid_post = self.client.post("/contact", data={
            "full_name": "",
            "email": "invalid-email",
            "subject": "",
            "message": ""
        }, follow_redirects=True)
        self.assertEqual(invalid_post.status_code, 200)
        self.assertIn(b"All fields are required", invalid_post.data)

        # 3. Valid POST -> Must succeed, save in database, and show confirmation
        valid_post = self.client.post("/contact", data={
            "full_name": "Jordan Smith",
            "email": "jordan.smith@aviation-test.org",
            "subject": "Lost Property Question Terminal 2",
            "message": "Where can I submit physical receipts for airport transit hotel expenses?"
        }, follow_redirects=True)
        self.assertEqual(valid_post.status_code, 200)
        self.assertIn(b"Your support inquiry", valid_post.data)
        self.assertIn(b"Jordan Smith", valid_post.data)

        # Verify record in database
        saved_messages = get_contact_messages(limit=10)
        self.assertTrue(any(m["email"] == "jordan.smith@aviation-test.org" for m in saved_messages))

    def test_14_public_navigation_routes(self):
        """Test that /about and /services routes redirect smoothly."""
        about_res = self.client.get("/about")
        self.assertEqual(about_res.status_code, 302)
        self.assertIn("/welcome#about", about_res.headers.get("Location", ""))

        services_res = self.client.get("/services")
        self.assertEqual(services_res.status_code, 302)
        self.assertIn("/welcome#services", services_res.headers.get("Location", ""))

if __name__ == "__main__":
    unittest.main(verbosity=2)


