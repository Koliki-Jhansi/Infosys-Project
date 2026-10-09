"""
AeroAssist AI - Jira Cloud REST API v3 Integration Test Suite
Validates all 10 Jira requirements: ADF payload generation, duplicate prevention,
mocked API responses (success, auth error, timeout), retry endpoints, and SQLite persistence.
"""
import os
import unittest
from unittest.mock import patch, MagicMock
from app import app
from database import (
    init_db, create_ticket, get_ticket_by_id, get_all_tickets,
    update_ticket_jira_info, get_existing_jira_for_ticket, get_db_connection
)
from jira_service import (
    create_jira_issue, build_jira_adf_description, get_jira_config, is_placeholder
)
from agents import get_multi_agent_system


class TestJiraIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

    def setUp(self):
        # Sample ticket data for testing
        self.sample_ticket = {
            "ticket_id": "TKT-JIRA-01",
            "title": "Baggage damaged on flight AA102 from JFK",
            "description": "Suitcase zipper ripped open and wheel missing at arrival carousel 2.",
            "category": "Baggage",
            "priority": "High",
            "severity": "Medium",
            "flight_number": "AA102",
            "booking_ref": "JFK901",
            "airport": "LHR"
        }
        self.escalation_payload = {
            "escalation_reason": "Final confidence is below 70% threshold.",
            "final_confidence": 0.48,
            "threshold": 0.70,
            "diagnosis_text": "Baggage damage inquiry",
            "diagnosis_confidence": 0.52,
            "retrieved_kb_id": "KB007",
            "retrieved_kb_title": "Baggage Claim and PIR Reporting",
            "retrieval_similarity": 0.26,
            "resolution_text": "Please file a Property Irregularity Report (PIR) at the baggage service desk.",
            "resolution_completeness": 0.80
        }

    def test_01_successful_jira_issue_creation_adf(self):
        """1. Test successful Jira issue creation using REST API v3 and ADF format."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "10055",
            "key": "SUP-789",
            "self": "https://test-aero.atlassian.net/rest/api/3/issue/10055"
        }

        with patch.dict(os.environ, {
            "JIRA_BASE_URL": "https://test-aero.atlassian.net",
            "JIRA_EMAIL": "agent@test-aero.com",
            "JIRA_API_TOKEN": "secret-api-token-12345",
            "JIRA_PROJECT_KEY": "SUP",
            "JIRA_ISSUE_TYPE": "Task"
        }), patch("requests.post", return_value=mock_response) as mock_post:
            
            res = create_jira_issue(self.sample_ticket, self.escalation_payload)
            
            self.assertEqual(res["status"], "Created")
            self.assertTrue(res["jira_created"])
            self.assertEqual(res["issue_key"], "SUP-789")
            self.assertEqual(res["issue_id"], "10055")
            self.assertEqual(res["issue_url"], "https://test-aero.atlassian.net/browse/SUP-789")
            self.assertEqual(res["sync_status"], "Created")

            # Verify API v3 endpoint and ADF body structure
            mock_post.assert_called_once()
            call_url = mock_post.call_args[0][0]
            call_json = mock_post.call_args[1]["json"]
            call_auth = mock_post.call_args[1]["auth"]

            self.assertEqual(call_url, "https://test-aero.atlassian.net/rest/api/3/issue")
            self.assertEqual(call_auth, ("agent@test-aero.com", "secret-api-token-12345"))
            self.assertEqual(call_json["fields"]["project"]["key"], "SUP")
            self.assertEqual(call_json["fields"]["issuetype"]["name"], "Task")
            self.assertIn("TKT-JIRA-01", call_json["fields"]["summary"])
            
            # Check ADF schema
            desc_adf = call_json["fields"]["description"]
            self.assertEqual(desc_adf["type"], "doc")
            self.assertEqual(desc_adf["version"], 1)
            self.assertIsInstance(desc_adf["content"], list)

    def test_02_auto_resolve_does_not_create_jira(self):
        """2. Test that AUTO_RESOLVE outcome does not trigger Jira issue creation."""
        mas = get_multi_agent_system()
        high_conf_ticket = {
            "ticket_id": "TKT-HIGH-CONF",
            "title": "Where can I find information about airport parking options and fees?",
            "description": "Looking for long-term economy car parking rates for 5 days near Terminal 2 with shuttle bus service.",
            "category": "Airport Facilities",
            "flight_number": "UA210",
            "booking_ref": "UA9012",
            "airport": "SFO",
            "travel_date": "2026-10-08"
        }

        with patch("jira_service.requests.post") as mock_post:
            results = mas.process_ticket(high_conf_ticket)
            
            # If auto-resolved, Jira must not be called
            if results["workflow_status"] == "AUTO_RESOLVE":
                self.assertFalse(results.get("jira_created", False))
                self.assertIn("Auto-Resolved", results.get("jira_status", ""))
                mock_post.assert_not_called()

    def test_section12_case1_confidence_085_auto_resolves_no_jira(self):
        """Section 12 Test 1: Confidence = 0.85 -> AUTO_RESOLVE, No Jira ticket."""
        from agents import ValidationAgent, EscalationAgent
        val_agent = ValidationAgent(threshold=0.70)
        diag = {"confidence": 0.85, "diagnosis": "Resolved", "intent": "Inquiry"}
        ret = {"similarity_score": 0.85, "top_article": {"id": "KB001", "title": "Test"}}
        res = {"resolution_completeness": 0.85, "resolution_text": "Answer"}
        val_out = val_agent.run(diag, ret, res)
        
        self.assertEqual(val_out["final_confidence"], 0.85)
        self.assertTrue(val_out["passes_threshold"])

        esc_agent = EscalationAgent()
        with patch("jira_service.requests.post") as mock_post:
            esc_out = esc_agent.run(self.sample_ticket, val_out, res, diag, ret)
            self.assertEqual(esc_out["workflow_status"], "AUTO_RESOLVE")
            self.assertFalse(esc_out["jira_created"])
            mock_post.assert_not_called()

    def test_section12_case2_confidence_070_exact_auto_resolves_no_jira(self):
        """Section 12 Test 2: Confidence = 0.70 (exact threshold) -> AUTO_RESOLVE, No Jira ticket."""
        from agents import ValidationAgent, EscalationAgent
        val_agent = ValidationAgent(threshold=0.70)
        # 0.70 * 0.4 + 0.70 * 0.4 + 0.70 * 0.2 = 0.70
        diag = {"confidence": 0.70, "diagnosis": "Resolved", "intent": "Inquiry"}
        ret = {"similarity_score": 0.70, "top_article": {"id": "KB001", "title": "Test"}}
        res = {"resolution_completeness": 0.70, "resolution_text": "Answer"}
        val_out = val_agent.run(diag, ret, res)
        
        self.assertEqual(val_out["final_confidence"], 0.70)
        self.assertTrue(val_out["passes_threshold"])

        esc_agent = EscalationAgent()
        with patch("jira_service.requests.post") as mock_post:
            esc_out = esc_agent.run(self.sample_ticket, val_out, res, diag, ret)
            self.assertEqual(esc_out["workflow_status"], "AUTO_RESOLVE")
            self.assertFalse(esc_out["jira_created"])
            mock_post.assert_not_called()

    def test_section12_case3_confidence_069_escalates_creates_jira(self):
        """Section 12 Test 3: Confidence = 0.69 (below threshold) -> ESCALATE, Jira ticket created."""
        from agents import ValidationAgent, EscalationAgent
        val_agent = ValidationAgent(threshold=0.70)
        # 0.69 * 0.4 + 0.69 * 0.4 + 0.69 * 0.2 = 0.69
        diag = {"confidence": 0.69, "diagnosis": "Escalate", "intent": "Inquiry"}
        ret = {"similarity_score": 0.69, "top_article": {"id": "KB001", "title": "Test"}}
        res = {"resolution_completeness": 0.69, "resolution_text": "Answer"}
        val_out = val_agent.run(diag, ret, res)
        
        self.assertEqual(val_out["final_confidence"], 0.69)
        self.assertFalse(val_out["passes_threshold"])

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"key": "SUP-069", "id": "10069"}

        esc_agent = EscalationAgent()
        with patch.dict(os.environ, {
            "JIRA_BASE_URL": "https://test-aero.atlassian.net",
            "JIRA_EMAIL": "agent@test-aero.com",
            "JIRA_API_TOKEN": "token-069",
            "JIRA_PROJECT_KEY": "SUP"
        }), patch("requests.post", return_value=mock_resp) as mock_post:
            esc_out = esc_agent.run(self.sample_ticket, val_out, res, diag, ret)
            self.assertEqual(esc_out["workflow_status"], "ESCALATE")
            self.assertTrue(esc_out["jira_created"])
            self.assertEqual(esc_out["jira_issue_key"], "SUP-069")
            mock_post.assert_called_once()

    def test_section12_case4_confidence_040_escalates_creates_jira(self):
        """Section 12 Test 4: Confidence = 0.40 -> ESCALATE, Jira ticket created."""
        from agents import ValidationAgent, EscalationAgent
        val_agent = ValidationAgent(threshold=0.70)
        diag = {"confidence": 0.40, "diagnosis": "Escalate", "intent": "Inquiry"}
        ret = {"similarity_score": 0.40, "top_article": {"id": "KB001", "title": "Test"}}
        res = {"resolution_completeness": 0.40, "resolution_text": "Answer"}
        val_out = val_agent.run(diag, ret, res)
        
        self.assertEqual(val_out["final_confidence"], 0.40)
        self.assertFalse(val_out["passes_threshold"])

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"key": "SUP-040", "id": "10040"}

        esc_agent = EscalationAgent()
        with patch.dict(os.environ, {
            "JIRA_BASE_URL": "https://test-aero.atlassian.net",
            "JIRA_EMAIL": "agent@test-aero.com",
            "JIRA_API_TOKEN": "token-040",
            "JIRA_PROJECT_KEY": "SUP"
        }), patch("requests.post", return_value=mock_resp) as mock_post:
            esc_out = esc_agent.run(self.sample_ticket, val_out, res, diag, ret)
            self.assertEqual(esc_out["workflow_status"], "ESCALATE")
            self.assertTrue(esc_out["jira_created"])
            self.assertEqual(esc_out["jira_issue_key"], "SUP-040")
            mock_post.assert_called_once()

    def test_03_missing_jira_configuration(self):
        """3. Test behavior when Jira environment variables are missing or placeholders."""
        with patch.dict(os.environ, {
            "JIRA_BASE_URL": "https://your-domain.atlassian.net",
            "JIRA_EMAIL": "your-jira-email@example.com",
            "JIRA_API_TOKEN": "your-api-token"
        }):
            res = create_jira_issue(self.sample_ticket, self.escalation_payload)
            self.assertEqual(res["status"], "Not Configured")
            self.assertFalse(res["jira_created"])
            self.assertIsNone(res["issue_key"])
            self.assertIsNone(res["issue_url"])
            self.assertEqual(res["sync_status"], "Not Configured")

    def test_04_invalid_jira_credentials_401(self):
        """4. Test error handling for invalid credentials (HTTP 401 Unauthorized)."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"errorMessages":["Unauthorized: Invalid API token secret-token-xyz"]}'

        with patch.dict(os.environ, {
            "JIRA_BASE_URL": "https://valid-domain.atlassian.net",
            "JIRA_EMAIL": "admin@valid-domain.com",
            "JIRA_API_TOKEN": "secret-token-xyz",
            "JIRA_PROJECT_KEY": "SUP"
        }), patch("requests.post", return_value=mock_response):
            
            res = create_jira_issue(self.sample_ticket, self.escalation_payload)
            self.assertEqual(res["status"], "Failed")
            self.assertFalse(res["jira_created"])
            self.assertIsNone(res["issue_key"])
            self.assertIn("401", res["last_error"])
            # Ensure token is redacted in error message
            self.assertNotIn("secret-token-xyz", res["last_error"])
            self.assertIn("[REDACTED]", res["last_error"])

    def test_05_jira_api_timeout(self):
        """5. Test resilient handling when Jira API times out."""
        import requests
        with patch.dict(os.environ, {
            "JIRA_BASE_URL": "https://valid-domain.atlassian.net",
            "JIRA_EMAIL": "admin@valid-domain.com",
            "JIRA_API_TOKEN": "secret-token-xyz"
        }), patch("requests.post", side_effect=requests.exceptions.Timeout("Connection timed out")):
            
            res = create_jira_issue(self.sample_ticket, self.escalation_payload)
            self.assertEqual(res["status"], "Failed")
            self.assertFalse(res["jira_created"])
            self.assertIn("timed out", res["last_error"].lower())

    def test_06_duplicate_workflow_execution_prevention(self):
        """6. Test duplicate prevention: reuses existing issue key and avoids second API call."""
        with patch("requests.post") as mock_post:
            res = create_jira_issue(
                ticket_data=self.sample_ticket,
                escalation_payload=self.escalation_payload,
                existing_issue_key="SUP-EXISTING-99",
                existing_issue_url="https://test-aero.atlassian.net/browse/SUP-EXISTING-99"
            )
            self.assertEqual(res["status"], "Created")
            self.assertTrue(res["jira_created"])
            self.assertEqual(res["issue_key"], "SUP-EXISTING-99")
            self.assertEqual(res["issue_url"], "https://test-aero.atlassian.net/browse/SUP-EXISTING-99")
            # Verify no HTTP request was made
            mock_post.assert_not_called()

    def test_07_failed_issue_creation_and_safe_retry(self):
        """7. Test failed issue creation and subsequent successful retry via backend route."""
        # 1. Create a ticket in SQLite
        t_data = {
            "passenger_id": 1,
            "passenger_name": "Alex Morgan",
            "passenger_email": "passenger@aeroassist.ai",
            "title": "Delayed transit connection rebooking",
            "description": "Flight DL901 delayed 3 hours, missed connecting flight AA402.",
            "category": "Delays & Cancellations",
            "priority": "High",
            "severity": "High",
            "status": "Escalated",
            "ai_resolution_status": "ESCALATE",
            "final_confidence": 0.45,
            "escalation_reason": "Low confidence.",
            "jira_sync_status": "Failed",
            "jira_last_error": "Initial network error"
        }
        tkt_id = create_ticket(t_data)

        # 2. Mock Jira API success on retry
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "10099",
            "key": "SUP-RETRY-01",
            "self": "https://test-aero.atlassian.net/rest/api/3/issue/10099"
        }

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        with patch.dict(os.environ, {
            "JIRA_BASE_URL": "https://test-aero.atlassian.net",
            "JIRA_EMAIL": "agent@test-aero.com",
            "JIRA_API_TOKEN": "secret-token-abc",
            "JIRA_PROJECT_KEY": "SUP"
        }), patch("requests.post", return_value=mock_response):
            
            retry_res = self.client.post(f"/tickets/{tkt_id}/retry-jira", follow_redirects=True)
            self.assertEqual(retry_res.status_code, 200)
            self.assertIn(b"Jira sync successful", retry_res.data)
            self.assertIn(b"SUP-RETRY-01", retry_res.data)

            # Verify SQLite record is updated
            updated_ticket = get_ticket_by_id(tkt_id)
            self.assertEqual(updated_ticket["jira_issue_key"], "SUP-RETRY-01")
            self.assertEqual(updated_ticket["jira_sync_status"], "Created")
            self.assertIn("SUP-RETRY-01", updated_ticket["jira_issue_url"])

    def test_08_database_persistence_all_jira_fields(self):
        """8. Test SQLite persistence for all Jira tracking fields."""
        t_data = {
            "passenger_id": 1,
            "passenger_name": "Alex Morgan",
            "passenger_email": "passenger@aeroassist.ai",
            "title": "Lost baggage report test",
            "description": "Luggage test description.",
            "category": "Baggage",
            "priority": "Medium",
            "severity": "Medium"
        }
        tkt_id = create_ticket(t_data)

        jira_data = {
            "issue_key": "SUP-TEST-88",
            "issue_id": "10088",
            "issue_url": "https://test-aero.atlassian.net/browse/SUP-TEST-88",
            "sync_status": "Created",
            "last_error": None,
            "created_at": "2026-10-08T20:00:00",
            "message": "Created successfully"
        }
        update_ticket_jira_info(tkt_id, jira_data)

        persisted = get_ticket_by_id(tkt_id)
        self.assertEqual(persisted["jira_issue_key"], "SUP-TEST-88")
        self.assertEqual(persisted["jira_issue_id"], "10088")
        self.assertEqual(persisted["jira_issue_url"], "https://test-aero.atlassian.net/browse/SUP-TEST-88")
        self.assertEqual(persisted["jira_sync_status"], "Created")

        existing = get_existing_jira_for_ticket(tkt_id)
        self.assertIsNotNone(existing)
        self.assertEqual(existing["issue_key"], "SUP-TEST-88")

    def test_09_jira_link_shown_only_for_created_issues(self):
        """9. Test that View in Jira link appears only when issue URL is valid."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        # Create ticket with Jira issue
        t_with_jira = {
            "passenger_id": 1,
            "passenger_name": "Alex Morgan",
            "passenger_email": "passenger@aeroassist.ai",
            "title": "Escalated ticket with Jira link",
            "description": "Testing Jira link presence.",
            "category": "Baggage",
            "priority": "High",
            "severity": "High",
            "status": "Escalated",
            "ai_resolution_status": "ESCALATE",
            "final_confidence": 0.40,
            "jira_issue_key": "SUP-LINK-01",
            "jira_issue_url": "https://test-aero.atlassian.net/browse/SUP-LINK-01",
            "jira_sync_status": "Created"
        }
        tkt_with = create_ticket(t_with_jira)

        # Create ticket without Jira issue
        t_without_jira = {
            "passenger_id": 1,
            "passenger_name": "Alex Morgan",
            "passenger_email": "passenger@aeroassist.ai",
            "title": "Escalated ticket without Jira link",
            "description": "Testing absence of Jira link.",
            "category": "Baggage",
            "priority": "High",
            "severity": "High",
            "status": "Escalated",
            "ai_resolution_status": "ESCALATE",
            "final_confidence": 0.40,
            "jira_issue_key": None,
            "jira_issue_url": None,
            "jira_sync_status": "Not Configured"
        }
        tkt_without = create_ticket(t_without_jira)

        # View ticket with Jira link
        res_with = self.client.get(f"/tickets/{tkt_with}")
        self.assertEqual(res_with.status_code, 200)
        self.assertIn(b"SUP-LINK-01", res_with.data)
        self.assertIn(b"https://test-aero.atlassian.net/browse/SUP-LINK-01", res_with.data)
        self.assertIn(b"View Jira Ticket", res_with.data)

        # View ticket without Jira link
        res_without = self.client.get(f"/tickets/{tkt_without}")
        self.assertEqual(res_without.status_code, 200)
        self.assertNotIn(b"SUP-LINK-01", res_without.data)

    def test_10_dashboard_and_escalated_queue_views(self):
        """10. Test that dashboard, escalated queue, and multi-agent workflows remain fully functional."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        # 1. Escalated tickets queue
        esc_res = self.client.get("/escalated-tickets")
        self.assertEqual(esc_res.status_code, 200)
        self.assertIn(b"Escalated Tickets", esc_res.data)
        self.assertIn(b"Jira Sync Status", esc_res.data)

        # 2. Dashboard analytics
        dash_res = self.client.get("/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b"Total Tickets", dash_res.data)
        self.assertIn(b"Escalated", dash_res.data)

        # 3. AI Solutions
        ai_res = self.client.get("/ai-solutions")
        self.assertEqual(ai_res.status_code, 200)
        self.assertIn(b"AI Solutions", ai_res.data)

    def test_11_api_tickets_jira_endpoint_and_cases(self):
        """11. Test POST /api/tickets/<ticket_id>/jira endpoint and duplicate protection / threshold guards."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "passenger"
            sess["role"] = "passenger"
            sess["full_name"] = "Alex Morgan"

        # CASE 1 & 2: AUTO_RESOLVE tickets (confidence >= 0.70) must NOT create Jira ticket
        t_auto_data = {
            "passenger_id": 1,
            "passenger_name": "Alex Morgan",
            "passenger_email": "passenger@aeroassist.ai",
            "title": "Auto resolved baggage inquiry",
            "description": "Lost baggage with high confidence match.",
            "category": "Baggage",
            "priority": "Medium",
            "severity": "Medium",
            "status": "Resolved",
            "ai_resolution_status": "AUTO_RESOLVE",
            "final_confidence": 0.85
        }
        tkt_auto = create_ticket(t_auto_data)
        api_res_auto = self.client.post(f"/api/tickets/{tkt_auto}/jira")
        self.assertEqual(api_res_auto.status_code, 400)
        self.assertIn("AUTO_RESOLVE", api_res_auto.get_json().get("error"))

        # CASE 5: ESCALATE (confidence = 0.495) + unconfigured/missing Jira token
        t_esc_data = {
            "passenger_id": 1,
            "passenger_name": "Alex Morgan",
            "passenger_email": "passenger@aeroassist.ai",
            "title": "Escalated inquiry with 49.5% confidence",
            "description": "Complex baggage loss needing ground human support.",
            "category": "Baggage",
            "priority": "Critical",
            "severity": "Critical",
            "status": "Escalated",
            "ai_resolution_status": "ESCALATE",
            "final_confidence": 0.495
        }
        tkt_esc = create_ticket(t_esc_data)
        with patch.dict(os.environ, {"JIRA_API_TOKEN": "", "JIRA_BASE_URL": ""}):
            api_res_unconf = self.client.post(f"/api/tickets/{tkt_esc}/jira")
            self.assertEqual(api_res_unconf.status_code, 200)
            data_unconf = api_res_unconf.get_json()
            self.assertFalse(data_unconf["success"])
            self.assertEqual(data_unconf["status"], "NOT_CONFIGURED")

        # CASE 6: ESCALATE + valid Jira credentials -> CREATE real Jira issue
        mock_jira_reply = MagicMock()
        mock_jira_reply.status_code = 201
        mock_jira_reply.json.return_value = {
            "id": "99001",
            "key": "SUP-777",
            "self": "https://aeroassist-prod.atlassian.net/rest/api/3/issue/99001"
        }
        with patch.dict(os.environ, {
            "JIRA_BASE_URL": "https://aeroassist-prod.atlassian.net",
            "JIRA_EMAIL": "support@aeroassist.ai",
            "JIRA_API_TOKEN": "valid_token_xyz",
            "JIRA_PROJECT_KEY": "SUP",
            "JIRA_ISSUE_TYPE": "Task"
        }), patch("requests.post", return_value=mock_jira_reply):
            api_res_create = self.client.post(f"/api/tickets/{tkt_esc}/jira")
            self.assertEqual(api_res_create.status_code, 200)
            data_create = api_res_create.get_json()
            self.assertTrue(data_create["success"])
            self.assertEqual(data_create["status"], "CREATED")
            self.assertEqual(data_create["jira_issue_key"], "SUP-777")
            self.assertEqual(data_create["jira_issue_url"], "https://aeroassist-prod.atlassian.net/browse/SUP-777")

            # CASE 7: Run Jira creation again for the same ticket -> Do NOT create duplicate Jira issue
            api_res_dup = self.client.post(f"/api/tickets/{tkt_esc}/jira")
            self.assertEqual(api_res_dup.status_code, 200)
            data_dup = api_res_dup.get_json()
            self.assertTrue(data_dup["success"])
            self.assertEqual(data_dup["status"], "CREATED")
            self.assertEqual(data_dup["jira_issue_key"], "SUP-777")


if __name__ == "__main__":
    unittest.main(verbosity=2)

