"""
SupportPilot / AeroAssist AI - Milestone 4 Escalation Engine
Module: escalation.py
Implements automatic escalation evaluation rules, decision tree, and human-intervention queue queries.
"""

import re
import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

HUMAN_REQUEST_KEYWORDS = [
    r"\bhuman\b",
    r"\bagent\b",
    r"\bperson\b",
    r"\brepresentative\b",
    r"\boperator\b",
    r"\bspeak (to|with) (a |an )?(human|agent|person|rep)\b",
    r"\btalk to (a |an )?(human|agent|person|rep)\b",
    r"\bconnect (me )?(to|with) (a |an )?(human|agent|person)\b",
    r"\bhuman support\b",
    r"\bmanager\b",
    r"\bsupervisor\b"
]


def check_customer_requested_human(text: Optional[str]) -> bool:
    """Checks if the customer text contains an explicit request for human intervention."""
    if not text:
        return False
    text_lower = str(text).lower()
    for pattern in HUMAN_REQUEST_KEYWORDS:
        if re.search(pattern, text_lower):
            return True
    return False


def evaluate_escalation_rules(
    priority: Optional[str],
    final_confidence: float,
    resolution_status: Optional[str],
    customer_text: Optional[str] = None,
    attempts_count: int = 1,
    retrieval_similarity: float = 1.0,
    resolution_text: Optional[str] = None
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Evaluates a ticket against the 5 Milestone 4 Escalation Rules:
    
    1. Priority is Critical.
    2. AI confidence is below 0.70.
    3. Resolution has failed (status in ['FAILED', 'ERROR'], retrieval < 0.60, or empty resolution).
    4. The customer has explicitly requested human support.
    5. Repeated resolution attempts have reached three or more (attempts >= 3).
    
    Returns:
        (should_escalate: bool, primary_reason: Optional[str], rule_evaluations: Dict[str, bool])
    """
    prio_str = str(priority).strip().upper() if priority else "MEDIUM"
    
    # Rule 1: Critical Priority
    rule_critical = (prio_str == "CRITICAL")
    
    # Rule 2: Low Confidence (< 0.70)
    rule_low_confidence = (final_confidence < 0.70)
    
    # Rule 3: Resolution Failure
    stat_upper = str(resolution_status).strip().upper() if resolution_status else ""
    rule_resolution_failed = (
        stat_upper in ["FAILED", "ERROR", "UNRESOLVED"] or
        retrieval_similarity < 0.60 or
        (resolution_text is not None and len(str(resolution_text).strip()) == 0 and stat_upper != "PENDING")
    )
    
    # Rule 4: Explicit Customer Request for Human
    rule_human_request = check_customer_requested_human(customer_text)
    
    # Rule 5: Repeated Resolution Attempts (>= 3)
    rule_max_attempts = (attempts_count >= 3)
    
    evaluations = {
        "rule_critical_priority": rule_critical,
        "rule_low_confidence": rule_low_confidence,
        "rule_resolution_failed": rule_resolution_failed,
        "rule_customer_requested_human": rule_human_request,
        "rule_repeated_attempts": rule_max_attempts
    }
    
    # Determine Primary Escalation Reason (Hierarchy of triggers)
    primary_reason = None
    if rule_critical:
        primary_reason = "Critical Priority: Safety/Operation-critical ticket requires immediate human handling."
    elif rule_human_request:
        primary_reason = "Customer Request: Customer explicitly requested human representative support."
    elif rule_max_attempts:
        primary_reason = f"Max Attempts Reached: Repeated resolution attempts ({attempts_count}) exceeded threshold."
    elif rule_resolution_failed:
        if retrieval_similarity < 0.60:
            primary_reason = f"KB Retrieval Below Safety Threshold ({retrieval_similarity:.2f} < 0.60)."
        else:
            primary_reason = "Resolution Failed: AI could not generate a valid verified resolution."
    elif rule_low_confidence:
        primary_reason = f"Low AI Confidence ({final_confidence:.2f} < 0.70 threshold)."
        
    should_escalate = any(evaluations.values())
    
    return should_escalate, primary_reason, evaluations


def get_human_intervention_queue(
    db_path: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    escalation_reason_substr: Optional[str] = None,
    status: Optional[str] = None
) -> pd.DataFrame:
    """
    Queries escalated and unresolved tickets requiring human intervention.
    Includes Ticket ID, Category, Priority, AI Confidence, Resolution Status, Escalation Reason, Attempts, and Jira Key.
    """
    from .analytics import get_db_connection
    
    try:
        conn = get_db_connection(db_path)
        query = """
            SELECT 
                t.id,
                t.ticket_id,
                t.customer_id,
                t.category,
                t.priority,
                t.severity,
                t.status,
                t.ai_resolution_status,
                t.final_confidence,
                t.retrieval_similarity,
                t.resolution_text,
                t.escalation_reason,
                t.jira_issue_key,
                t.created_at,
                t.updated_at,
                (SELECT COUNT(*) FROM agent_runs ar WHERE ar.ticket_id = t.ticket_id) AS attempts_count
            FROM tickets t
            WHERE t.ai_resolution_status = 'ESCALATE' 
               OR t.status IN ('OPEN', 'IN_PROGRESS', 'PENDING', 'ESCALATED')
            ORDER BY 
                CASE 
                    WHEN UPPER(t.priority) = 'CRITICAL' THEN 1
                    WHEN UPPER(t.priority) = 'HIGH' THEN 2
                    WHEN UPPER(t.priority) = 'MEDIUM' THEN 3
                    ELSE 4
                END,
                t.created_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
    except Exception:
        cols = [
            "id", "ticket_id", "customer_id", "category", "priority", "severity",
            "status", "ai_resolution_status", "final_confidence", "retrieval_similarity",
            "resolution_text", "escalation_reason", "jira_issue_key", "created_at", "updated_at",
            "attempts_count"
        ]
        df = pd.DataFrame(columns=cols)

    if df.empty:
        return df

    # Normalization
    df['final_confidence'] = pd.to_numeric(df['final_confidence'], errors='coerce').fillna(0.0)
    df['retrieval_similarity'] = pd.to_numeric(df['retrieval_similarity'], errors='coerce').fillna(0.0)
    df['attempts_count'] = pd.to_numeric(df['attempts_count'], errors='coerce').fillna(1).astype(int)

    # Filtering
    if category and category != "All":
        df = df[df['category'] == category]
    if priority and priority != "All":
        df = df[df['priority'].str.upper() == priority.upper()]
    if status and status != "All":
        df = df[df['status'].str.upper() == status.upper()]
    if escalation_reason_substr:
        df = df[df['escalation_reason'].fillna("").str.contains(escalation_reason_substr, case=False)]

    return df
