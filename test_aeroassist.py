"""
AeroAssist AI - Comprehensive Verification Test Suite
Tests Milestone 1, Milestone 2, and Milestone 3 functionality.
"""
import os
import sys
import unittest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

from database import (
    init_db, create_user, get_user_by_username_or_email,
    create_ticket, get_ticket_by_id, get_all_tickets, get_ticket_stats,
    update_ticket_ai_results, get_agent_runs_for_ticket
)
from classifier import get_classifier, CATEGORIES
from priority import calculate_priority
from severity import calculate_severity
from rag import load_knowledge_base, get_retriever, get_rag_pipeline
from agents import get_multi_agent_system, MultiAgentSystem


class TestMilestone1(unittest.TestCase):
    """Milestone 1: Passenger Support & Ticket Management Tests"""

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_database_and_users(self):
        user = get_user_by_username_or_email("passenger")
        self.assertIsNotNone(user, "Default passenger demo user should exist")
        self.assertEqual(user["role"], "passenger")

    def test_ticket_classifier(self):
        clf = get_classifier()
        
        # Test Baggage classification
        res1 = clf.classify("My checked baggage has not arrived on the carousel", "Luggage missing after flight")
        self.assertEqual(res1["predicted_category"], "Baggage")
        self.assertGreaterEqual(res1["confidence"], 0.20)

        # Test Check-in classification
        res2 = clf.classify("Unable to complete web check-in online", "System error generating boarding pass")
        self.assertEqual(res2["predicted_category"], "Check-in & Boarding")

        # Test Wheelchair / Assistance
        res3 = clf.classify("Need wheelchair assistance for elderly passenger", "Mobility support from check-in to gate")
        self.assertEqual(res3["predicted_category"], "Passenger Assistance")

    def test_priority_and_severity(self):
        # Critical urgency
        prio_crit = calculate_priority("Medical emergency at boarding gate", "Passenger immobile", "Passenger Assistance")
        self.assertEqual(prio_crit, "Critical")
        sev_crit = calculate_severity("Passenger Assistance", prio_crit)
        self.assertEqual(sev_crit, "Critical")

        # High urgency
        prio_high = calculate_priority("Lost baggage assistance", "Delayed baggage PIR", "Baggage")
        self.assertEqual(prio_high, "High")

        # Low urgency
        prio_low = calculate_priority("Airport car parking tariffs", "Inquiry about long term parking rates", "Airport Facilities")
        self.assertEqual(prio_low, "Low")

    def test_ticket_creation_and_persistence(self):
        ticket_data = {
            "passenger_name": "Test Passenger",
            "passenger_email": "test@aeroassist.ai",
            "title": "Unit Test Delayed Baggage",
            "description": "My bag was delayed on flight AA100",
            "category": "Baggage",
            "priority": "High",
            "severity": "Major",
            "flight_number": "AA100",
            "booking_ref": "TST001",
            "airport": "JFK"
        }
        tkt_id = create_ticket(ticket_data)
        self.assertTrue(tkt_id.startswith("TKT-"))

        saved = get_ticket_by_id(tkt_id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["title"], "Unit Test Delayed Baggage")
        self.assertEqual(saved["flight_number"], "AA100")


class TestMilestone2(unittest.TestCase):
    """Milestone 2: Airport Knowledge Base Resolution / RAG Tests"""

    def test_knowledge_base_loading(self):
        articles = load_knowledge_base()
        self.assertGreaterEqual(len(articles), 20, "Knowledge base should have at least 20 comprehensive articles")
        clusters = {a["cluster"] for a in articles}
        expected_clusters = {"FLIGHTS", "CHECK-IN & BOARDING", "BAGGAGE", "AIRPORT FACILITIES", "SHOPPING & SERVICES", "BOOKING & PAYMENT", "PASSENGER ASSISTANCE"}
        self.assertTrue(expected_clusters.issubset(clusters), f"All 7 clusters should be present. Found: {clusters}")

    def test_tfidf_retriever(self):
        retriever = get_retriever()
        
        # Test relevant retrieval for delayed baggage
        res = retriever.retrieve("Delayed baggage reporting Property Irregularity Report PIR", top_k=3)
        self.assertTrue(res["knowledge_found"])
        self.assertIsNotNone(res["top_article"])
        self.assertIn("Baggage", res["top_article"]["category"])
        self.assertGreaterEqual(res["similarity_score"], 0.30)

        # Test relevant retrieval for airport parking
        res_park = retriever.retrieve("long term economy parking tariffs shuttle bus", top_k=3)
        self.assertTrue(res_park["knowledge_found"])
        self.assertEqual(res_park["top_article"]["id"], "KB012")

    def test_rag_pipeline_and_grounded_resolution(self):
        pipeline = get_rag_pipeline()
        res = pipeline.process_query(
            title="Wheelchair mobility assistance request",
            description="Need wheelchair from curb to gate B12",
            category="Passenger Assistance"
        )
        self.assertTrue(res["knowledge_found"])
        self.assertTrue(res["top_article"]["category"] == "Passenger Assistance" or "KB020" in res["context"])
        self.assertIn("Official Support Guidance", res["resolution_text"])
        self.assertGreaterEqual(res["resolution_completeness"], 0.70)


class TestMilestone3(unittest.TestCase):
    """Milestone 3: Multi-Agent Airport Support & Decision Gate Tests"""

    def setUp(self):
        self.mas = get_multi_agent_system()

    def test_auto_resolve_path(self):
        """Ticket with strong domain match should satisfy >= 70% threshold and AUTO_RESOLVE."""
        ticket_data = {
            "ticket_id": "TKT-AUTO-TEST",
            "passenger_name": "John Flyer",
            "passenger_email": "john@flyer.com",
            "title": "Delayed checked baggage PIR report",
            "description": "My checked baggage has not arrived on carousel. Need to file Property Irregularity Report PIR at airport baggage claim.",
            "category": "Baggage",
            "flight_number": "AA501",
            "booking_ref": "PNR771"
        }
        res = self.mas.process_ticket(ticket_data)
        
        self.assertEqual(len(res["agent_trace"]), 5, "Must execute all 5 agents sequentially")
        self.assertEqual(res["agent_trace"][0]["agent_name"], "Diagnosis Agent")
        self.assertEqual(res["agent_trace"][1]["agent_name"], "Retrieval Agent")
        self.assertEqual(res["agent_trace"][2]["agent_name"], "Resolution Agent")
        self.assertEqual(res["agent_trace"][3]["agent_name"], "Validation Agent")
        self.assertEqual(res["agent_trace"][4]["agent_name"], "Escalation Agent")

        # Validate exact formula: 0.40 * Diag + 0.40 * Ret + 0.20 * Comp
        diag_c = res["diagnosis_confidence"]
        ret_s = res["retrieval_similarity"]
        comp_c = res["resolution_completeness"]
        expected_final = round((diag_c * 0.40) + (ret_s * 0.40) + (comp_c * 0.20), 4)
        self.assertAlmostEqual(res["final_confidence"], expected_final, places=3)

        self.assertGreaterEqual(res["final_confidence"], 0.70, "High match should exceed 70% threshold")
        self.assertEqual(res["workflow_status"], "AUTO_RESOLVE")
        self.assertFalse(res["escalation_required"])

    def test_escalation_path(self):
        """Out-of-scope or vague inquiry should yield low similarity, < 70% confidence, and ESCALATE."""
        ticket_data = {
            "ticket_id": "TKT-ESC-TEST",
            "passenger_name": "Elena Smith",
            "passenger_email": "elena@example.com",
            "title": "Quantum teleportation luggage inquiry",
            "description": "Can I transmit my parcel using experimental teleportation physics over airport airspace?",
            "category": "General Support"
        }
        res = self.mas.process_ticket(ticket_data)

        self.assertLess(res["final_confidence"], 0.70, "Out-of-scope ticket should not pass 70% gate")
        self.assertEqual(res["workflow_status"], "ESCALATE")
        self.assertTrue(res["escalation_required"])
        self.assertIn("Human support required", res["resolution_text"])

    def test_jira_unconfigured_and_duplicate_protection(self):
        """Test Jira service behavior when unconfigured and duplicate prevention."""
        from jira_service import create_jira_issue, build_jira_description
        
        ticket_data = {
            "ticket_id": "TKT-067",
            "title": "Checked baggage not received after arrival",
            "category": "Baggage",
            "priority": "High",
            "flight_number": "AA402",
            "description": "Bag not arrived on carousel"
        }
        escalation_payload = {
            "diagnosis_text": "Delayed baggage assistance required",
            "diagnosis_confidence": 0.85,
            "retrieved_kb_id": "KB007",
            "retrieved_kb_title": "Delayed Baggage Reporting & PIR File Creation",
            "retrieval_similarity": 0.55,
            "resolution_text": "Follow PIR steps at airport counter.",
            "resolution_completeness": 0.80,
            "final_confidence": 0.662,
            "escalation_reason": "Final confidence (66.2%) below 70% threshold."
        }

        # 1. Test Description Formatting
        desc = build_jira_description(ticket_data, escalation_payload)
        self.assertIn("AeroAssist Human Support Escalation", desc)
        self.assertIn("Ticket ID: TKT-067", desc)
        self.assertIn("Category: Baggage", desc)
        self.assertIn("Priority: High", desc)
        self.assertIn("Final AI Confidence", desc)
        self.assertIn("66.2%", desc)
        self.assertIn("KB007 - Delayed Baggage Reporting & PIR File Creation", desc)

        # 2. Test Duplicate Protection (Reusing existing Jira issue)
        reuse_res = create_jira_issue(
            ticket_data=ticket_data,
            escalation_payload=escalation_payload,
            existing_issue_key="AERO-104",
            existing_issue_url="https://aeroassist.atlassian.net/browse/AERO-104"
        )
        self.assertEqual(reuse_res["status"], "Created")
        self.assertTrue(reuse_res["jira_created"])
        self.assertEqual(reuse_res["issue_key"], "AERO-104")
        self.assertEqual(reuse_res["issue_url"], "https://aeroassist.atlassian.net/browse/AERO-104")
        self.assertIn("Reused existing", reuse_res["message"])

        # 3. Test Unconfigured Jira (when no env vars set)
        orig_url = os.environ.pop("JIRA_URL", None)
        unconf_res = create_jira_issue(ticket_data, escalation_payload)
        self.assertEqual(unconf_res["status"], "Not Configured")
        self.assertFalse(unconf_res["jira_created"])
        self.assertIsNone(unconf_res["issue_key"])
        if orig_url:
            os.environ["JIRA_URL"] = orig_url

        # 4. Test Email Service Unconfigured & Body Builder
        from email_service import send_escalation_email, build_email_body
        email_body = build_email_body(ticket_data, escalation_payload)
        self.assertIn("Human Support Escalation Notice", email_body)
        self.assertIn("TKT-067", email_body)
        self.assertIn("Final AI Confidence", email_body)
        
        orig_smtp = os.environ.pop("SMTP_HOST", None)
        unconf_email = send_escalation_email(ticket_data, escalation_payload)
        self.assertEqual(unconf_email["status"], "Not Configured")
        if orig_smtp:
            os.environ["SMTP_HOST"] = orig_smtp


if __name__ == "__main__":
    unittest.main(verbosity=2)
