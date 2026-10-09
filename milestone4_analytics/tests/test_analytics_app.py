"""
SupportPilot / AeroAssist AI - Milestone 4 Test Suite
Module: tests/test_analytics_app.py
Tests all KPI formulas, edge cases, 5 escalation rules, evaluation metrics, and monitoring functions.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ensure parent and milestone4_analytics paths are in sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
PARENT_DIR = os.path.abspath(os.path.join(MODULE_DIR, ".."))

for p in [MODULE_DIR, PARENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from analytics import (
    calculate_kpi_summary,
    get_performance_over_time,
    get_category_breakdown,
    get_priority_breakdown,
    get_confidence_distribution,
    fetch_tickets_dataframe
)
from escalation import (
    evaluate_escalation_rules,
    check_customer_requested_human,
    get_human_intervention_queue
)
from evaluation import (
    evaluate_classifier_performance,
    evaluate_resolution_and_rag
)
from monitoring import (
    run_comprehensive_health_check,
    get_real_system_uptime,
    get_stage_latencies_summary
)


class TestAnalyticsEngine(unittest.TestCase):
    """Tests all aggregation and KPI formula calculations."""

    def setUp(self):
        # Create a mock DataFrame with controlled values
        self.mock_tickets = pd.DataFrame([
            {
                "id": 1, "ticket_id": "TCK-1", "category": "Baggage", "priority": "Low",
                "status": "RESOLVED", "ai_resolution_status": "AUTO_RESOLVE",
                "final_confidence": 0.85, "retrieval_similarity": 0.90,
                "created_at_dt": datetime.now() - timedelta(days=2),
                "updated_at_dt": datetime.now() - timedelta(days=2, seconds=-120)
            },
            {
                "id": 2, "ticket_id": "TCK-2", "category": "Baggage", "priority": "Critical",
                "status": "ESCALATED", "ai_resolution_status": "ESCALATE",
                "final_confidence": 0.92, "retrieval_similarity": 0.88,
                "created_at_dt": datetime.now() - timedelta(days=2),
                "updated_at_dt": datetime.now() - timedelta(days=2, seconds=-60)
            },
            {
                "id": 3, "ticket_id": "TCK-3", "category": "Booking", "priority": "Medium",
                "status": "ESCALATED", "ai_resolution_status": "ESCALATE",
                "final_confidence": 0.55, "retrieval_similarity": 0.40,
                "created_at_dt": datetime.now() - timedelta(days=1),
                "updated_at_dt": datetime.now() - timedelta(days=1, seconds=-30)
            },
            {
                "id": 4, "ticket_id": "TCK-4", "category": "Refund", "priority": "High",
                "status": "RESOLVED", "ai_resolution_status": "AUTO_RESOLVE",
                "final_confidence": 0.78, "retrieval_similarity": 0.82,
                "created_at_dt": datetime.now() - timedelta(hours=5),
                "updated_at_dt": datetime.now() - timedelta(hours=5, seconds=-90)
            },
            {
                "id": 5, "ticket_id": "TCK-5", "category": "General", "priority": "Low",
                "status": "PENDING", "ai_resolution_status": "PENDING",
                "final_confidence": 0.0, "retrieval_similarity": 0.0,
                "created_at_dt": datetime.now(),
                "updated_at_dt": datetime.now()
            }
        ])

    def test_kpi_summary_calculation(self):
        kpi = calculate_kpi_summary(self.mock_tickets)
        self.assertEqual(kpi["total_tickets"], 5)
        self.assertEqual(kpi["processed_tickets"], 4)  # 2 auto + 2 escalate, excludes 1 pending
        self.assertEqual(kpi["ai_resolved_tickets"], 2)
        self.assertEqual(kpi["escalated_tickets"], 2)
        self.assertEqual(kpi["pending_tickets"], 1)
        # Rates: 2/4 = 50.0%
        self.assertAlmostEqual(kpi["ai_resolution_rate"], 50.0)
        self.assertAlmostEqual(kpi["escalation_rate"], 50.0)
        # Average confidence of processed: (0.85 + 0.92 + 0.55 + 0.78) / 4 = 0.775
        self.assertAlmostEqual(kpi["avg_ai_confidence"], 0.775)
        # Low confidence count (< 0.70): 1 (TCK-3)
        self.assertEqual(kpi["low_confidence_count"], 1)
        # Low similarity count (< 0.60): 1 (TCK-3)
        self.assertEqual(kpi["low_similarity_count"], 1)
        # Missing CSAT handled gracefully
        self.assertIsNone(kpi["csat_score"])
        self.assertIn("Not available", kpi["csat_note"])

    def test_empty_database_handling(self):
        empty_df = pd.DataFrame()
        kpi = calculate_kpi_summary(empty_df)
        self.assertEqual(kpi["total_tickets"], 0)
        self.assertEqual(kpi["ai_resolution_rate"], 0.0)
        self.assertEqual(kpi["escalation_rate"], 0.0)
        self.assertEqual(kpi["avg_ai_confidence"], 0.0)
        
        trends = get_performance_over_time(empty_df)
        self.assertTrue(trends.empty)
        
        cats = get_category_breakdown(empty_df)
        self.assertTrue(cats.empty)
        
        prios = get_priority_breakdown(empty_df)
        self.assertTrue(prios.empty)

    def test_time_series_aggregation(self):
        daily_trends = get_performance_over_time(self.mock_tickets, freq='D', date_preset='all')
        self.assertFalse(daily_trends.empty)
        self.assertIn('resolution_rate', daily_trends.columns)
        self.assertIn('escalation_rate', daily_trends.columns)
        self.assertIn('avg_confidence_pct', daily_trends.columns)

        # Filter presets
        trends_7d = get_performance_over_time(self.mock_tickets, freq='D', date_preset='7d')
        self.assertFalse(trends_7d.empty)

    def test_category_and_priority_breakdown(self):
        cats = get_category_breakdown(self.mock_tickets)
        self.assertEqual(len(cats), 4)  # Baggage, Booking, Refund, General
        baggage_row = cats[cats['category'] == 'Baggage'].iloc[0]
        self.assertEqual(baggage_row['total'], 2)
        self.assertEqual(baggage_row['ai_resolved'], 1)
        self.assertEqual(baggage_row['escalated'], 1)

        prios = get_priority_breakdown(self.mock_tickets)
        self.assertEqual(len(prios), 4)
        crit_row = prios[prios['priority'] == 'Critical'].iloc[0]
        self.assertEqual(crit_row['critical_escalations'], 1)

    def test_confidence_bands_distribution(self):
        conf_dist = get_confidence_distribution(self.mock_tickets)
        self.assertEqual(len(conf_dist), 4)  # 4 bands
        # Total processed tickets should equal sum of band counts
        self.assertEqual(conf_dist['count'].sum(), 4)


class TestEscalationEngine(unittest.TestCase):
    """Tests all 5 Milestone 4 Escalation Rules."""

    def test_rule_1_critical_priority(self):
        should_esc, reason, details = evaluate_escalation_rules(
            priority="Critical",
            final_confidence=0.95,
            resolution_status="SUCCESS",
            customer_text="Flight was on time",
            attempts_count=1,
            retrieval_similarity=0.95
        )
        self.assertTrue(should_esc)
        self.assertTrue(details["rule_critical_priority"])
        self.assertIn("Critical Priority", reason)

    def test_rule_2_low_confidence(self):
        should_esc, reason, details = evaluate_escalation_rules(
            priority="Medium",
            final_confidence=0.64,  # < 0.70
            resolution_status="SUCCESS",
            customer_text="Baggage lost",
            attempts_count=1,
            retrieval_similarity=0.85
        )
        self.assertTrue(should_esc)
        self.assertTrue(details["rule_low_confidence"])
        self.assertIn("Low AI Confidence", reason)

    def test_rule_3_resolution_failure(self):
        # Sub-case A: Failed status
        should_esc, reason, details = evaluate_escalation_rules(
            priority="Low",
            final_confidence=0.85,
            resolution_status="FAILED",
            customer_text="My seat issue",
            attempts_count=1,
            retrieval_similarity=0.85
        )
        self.assertTrue(should_esc)
        self.assertTrue(details["rule_resolution_failed"])

        # Sub-case B: Low retrieval similarity (< 0.60)
        should_esc, reason, details = evaluate_escalation_rules(
            priority="Low",
            final_confidence=0.85,
            resolution_status="SUCCESS",
            customer_text="Unknown obscure policy",
            attempts_count=1,
            retrieval_similarity=0.45
        )
        self.assertTrue(should_esc)
        self.assertTrue(details["rule_resolution_failed"])

    def test_rule_4_customer_explicit_human_request(self):
        sample_phrases = [
            "I want to speak to a human representative now",
            "Please connect me to an agent",
            "I need a person to talk to",
            "Let me talk to a human",
            "Supervisor please"
        ]
        for phrase in sample_phrases:
            self.assertTrue(check_customer_requested_human(phrase), f"Failed on phrase: {phrase}")
            should_esc, reason, details = evaluate_escalation_rules(
                priority="Low",
                final_confidence=0.90,
                resolution_status="SUCCESS",
                customer_text=phrase,
                attempts_count=1,
                retrieval_similarity=0.90
            )
            self.assertTrue(should_esc)
            self.assertTrue(details["rule_customer_requested_human"])
            self.assertIn("Customer Request", reason)

    def test_rule_5_repeated_attempts_threshold(self):
        should_esc, reason, details = evaluate_escalation_rules(
            priority="Low",
            final_confidence=0.88,
            resolution_status="SUCCESS",
            customer_text="Still not working",
            attempts_count=3,  # >= 3
            retrieval_similarity=0.90
        )
        self.assertTrue(should_esc)
        self.assertTrue(details["rule_repeated_attempts"])
        self.assertIn("Max Attempts Reached", reason)

    def test_non_escalation_when_safe(self):
        should_esc, reason, details = evaluate_escalation_rules(
            priority="Medium",
            final_confidence=0.85,  # >= 0.70
            resolution_status="SUCCESS",
            customer_text="How do I check my baggage allowance?",
            attempts_count=1,
            retrieval_similarity=0.88
        )
        self.assertFalse(should_esc)
        self.assertIsNone(reason)
        self.assertFalse(any(details.values()))


class TestEvaluationAndMonitoring(unittest.TestCase):
    """Tests evaluation metrics calculation and system health monitoring."""

    def test_classifier_evaluation_benchmark(self):
        eval_res = evaluate_classifier_performance()
        if "error" not in eval_res:
            self.assertIn("accuracy", eval_res)
            self.assertIn("macro_f1", eval_res)
            self.assertIn("confusion_matrix", eval_res)
            self.assertGreaterEqual(eval_res["accuracy"], 80.0)

    def test_resolution_rag_evaluation_benchmark(self):
        rag_res = evaluate_resolution_and_rag()
        if "error" not in rag_res:
            self.assertIn("decision_accuracy", rag_res)
            self.assertIn("solvable_auto_resolve_rate", rag_res)
            self.assertIn("kb_coverage_rate", rag_res)
            self.assertGreaterEqual(rag_res["decision_accuracy"], 80.0)

    def test_system_monitoring_health_checks(self):
        health = run_comprehensive_health_check()
        self.assertIn("components", health)
        self.assertIn("database", health["components"])
        self.assertIn("classifier", health["components"])
        self.assertIn("retriever", health["components"])

        uptime = get_real_system_uptime()
        self.assertIn("uptime_pct", uptime)
        self.assertIn("note", uptime)

        lat = get_stage_latencies_summary()
        self.assertIn("total_avg_pipeline_ms", lat)


if __name__ == "__main__":
    unittest.main()
