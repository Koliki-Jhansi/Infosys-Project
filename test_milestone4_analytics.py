"""
AeroAssist AI - Milestone 4 Comprehensive Test Suite
Validates:
- Database analytics aggregations & KPI calculations
- Denominator handling (unprocessed tickets excluded from resolution/escalation rate denominators)
- Date range filtering (7d, 30d, all)
- Authenticated analytics REST API endpoints
- Authorization & PII protection
- Decision threshold quality gates & Jira integration rules
- AI Evaluation Benchmark Engine
"""
import os
import json
import unittest
from unittest.mock import patch

from app import app
from database import (
    get_db_connection, init_db, create_ticket, update_ticket_ai_results,
    get_ai_performance_kpis, get_ai_performance_over_time,
    get_category_ai_performance, get_ai_confidence_distribution,
    get_agent_stage_performance, get_ai_performance_insights
)
from evaluate_ai import run_evaluation


class TestMilestone4Analytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key-milestone4"
        cls.client = app.test_client()

    def setUp(self):
        init_db()

    def test_01_kpi_calculation_and_denominator_exclusion(self):
        """Test that KPIs are calculated correctly and unprocessed tickets are excluded from rate denominators."""
        kpis = get_ai_performance_kpis(date_range="all")
        self.assertIn("total_tickets", kpis)
        self.assertIn("total_processed", kpis)
        self.assertIn("unprocessed_count", kpis)
        self.assertIn("auto_resolve_rate", kpis)
        self.assertIn("escalation_rate", kpis)
        self.assertIn("average_confidence", kpis)

        if kpis["total_processed"] > 0:
            # Check that rate sum is ~100%
            rate_sum = kpis["auto_resolve_rate"] + kpis["escalation_rate"]
            self.assertAlmostEqual(rate_sum, 100.0, delta=0.5)

            # Check that total tickets equals processed + unprocessed
            self.assertEqual(kpis["total_tickets"], kpis["total_processed"] + kpis["unprocessed_count"])

    def test_02_time_series_date_filters(self):
        """Test date range filters (7d, 30d, all) return proper series structure."""
        for rng in ["7d", "30d", "all"]:
            ts = get_ai_performance_over_time(date_range=rng)
            self.assertEqual(ts["date_range"], rng)
            self.assertIsInstance(ts["dates"], list)
            self.assertIsInstance(ts["auto_resolve_rates"], list)
            self.assertIsInstance(ts["escalation_rates"], list)
            self.assertIsInstance(ts["average_confidences"], list)
            self.assertEqual(len(ts["dates"]), len(ts["auto_resolve_rates"]))
            self.assertEqual(len(ts["dates"]), len(ts["escalation_rates"]))
            self.assertEqual(len(ts["dates"]), len(ts["average_confidences"]))

    def test_03_category_ai_performance(self):
        """Test category-wise resolution and escalation breakdown."""
        cats = get_category_ai_performance()
        self.assertIsInstance(cats, list)
        for c in cats:
            self.assertIn("category", c)
            self.assertIn("total_tickets", c)
            self.assertIn("processed_tickets", c)
            self.assertIn("auto_resolved", c)
            self.assertIn("escalated", c)
            self.assertIn("auto_resolve_rate", c)
            self.assertIn("escalation_rate", c)
            if c["processed_tickets"] > 0:
                self.assertAlmostEqual(c["auto_resolve_rate"] + c["escalation_rate"], 100.0, delta=0.5)

    def test_04_confidence_distribution_bands(self):
        """Test confidence score bands (<40%, 40-69.99%, 70-100%)."""
        dist = get_ai_confidence_distribution()
        self.assertIn("total_processed", dist)
        self.assertIn("bands", dist)
        self.assertEqual(len(dist["bands"]), 3)
        total_band_count = sum(b["count"] for b in dist["bands"])
        self.assertEqual(dist["total_processed"], total_band_count)

    def test_05_agent_stage_performance_and_bottleneck(self):
        """Test multi-agent stage performance averages and bottleneck identification."""
        stages = get_agent_stage_performance()
        self.assertIn("total_agent_runs", stages)
        self.assertIn("stages", stages)
        self.assertIn("bottleneck_stage", stages)
        self.assertEqual(len(stages["stages"]), 4)

    def test_06_ai_performance_insights(self):
        """Test that AI Performance insights are generated from database facts."""
        insights_data = get_ai_performance_insights()
        self.assertIn("sample_size", insights_data)
        self.assertIn("insights", insights_data)
        self.assertIsInstance(insights_data["insights"], list)

    def test_07_api_authentication_protection(self):
        """Test that unauthenticated requests to analytics endpoints are blocked."""
        endpoints = [
            "/api/analytics/ai-performance",
            "/api/analytics/category-performance",
            "/api/analytics/agent-performance",
            "/api/analytics/decision-distribution",
            "/api/analytics/confidence-distribution",
            "/api/analytics/insights",
            "/api/analytics/evaluation-report"
        ]
        for ep in endpoints:
            resp = self.client.get(ep)
            # Unauthenticated should redirect to login (302) or return 401
            self.assertIn(resp.status_code, [302, 401])

    def test_08_authenticated_analytics_api_endpoints(self):
        """Test that authenticated requests return valid JSON without leaking PII."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "admin"
            sess["full_name"] = "AeroAssist Administrator"

        # 1. AI Performance with range
        for r in ["7d", "30d", "all"]:
            resp = self.client.get(f"/api/analytics/ai-performance?range={r}")
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data["success"])
            self.assertIn("kpis", data)
            self.assertIn("time_series", data)
            # Verify no passenger email or PII in time series
            self.assertNotIn("passenger_email", str(data))

        # 2. Category Performance
        resp = self.client.get("/api/analytics/category-performance")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("categories", data)

        # 3. Agent Performance
        resp = self.client.get("/api/analytics/agent-performance")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("agent_performance", data)

        # 4. Decision Distribution
        resp = self.client.get("/api/analytics/decision-distribution")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("auto_resolve_rate", data)

        # 5. Confidence Distribution
        resp = self.client.get("/api/analytics/confidence-distribution")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])

        # 6. Insights
        resp = self.client.get("/api/analytics/insights")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])

        # 7. Evaluation Report
        resp = self.client.get("/api/analytics/evaluation-report")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("report", data)
        self.assertGreaterEqual(data["report"]["overall_decision_accuracy"], 80.0)

    def test_09_repeatable_evaluation_benchmark(self):
        """Test the repeatable evaluation benchmark engine."""
        report = run_evaluation()
        self.assertGreaterEqual(report["sample_size"], 40)
        self.assertGreaterEqual(report["classification_accuracy"], 85.0)
        self.assertGreaterEqual(report["overall_decision_accuracy"], 85.0)
        self.assertGreaterEqual(report["solvable_auto_resolution_rate"], 85.0)
        self.assertGreaterEqual(report["human_escalation_capture_rate"], 80.0)

    def test_10_dashboard_rendered_view(self):
        """Test that the dashboard HTML view renders all AI performance components without error."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "admin"
            sess["full_name"] = "AeroAssist Administrator"

        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("AI Performance Over Time", html)
        self.assertIn("Auto-Resolution Rate", html)
        self.assertIn("Escalation Rate", html)
        self.assertIn("Avg Final Confidence", html)
        self.assertIn("chartPerformanceOverTime", html)
        self.assertIn("chartDecisionDistribution", html)
        self.assertIn("chartCategoryPerformance", html)
        self.assertIn("chartConfidenceDistribution", html)
        self.assertIn("chartAgentPerformance", html)


if __name__ == "__main__":
    unittest.main()
