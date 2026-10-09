"""
SupportPilot / AeroAssist AI - Milestone 4 Analytics Engine
Module: analytics.py
Calculates live aggregation metrics, KPI indicators, time-series data, and distributions
from the production SQLite database (aeroassist.db) in read-only mode.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Default database path resolution
DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "aeroassist.db")
)


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns a read-only SQLite connection to the ticket database."""
    target_path = db_path or DEFAULT_DB_PATH
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Database file not found at: {target_path}")
    conn = sqlite3.connect(f"file:{target_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_tickets_dataframe(
    db_path: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> pd.DataFrame:
    """Fetches all tickets into a Pandas DataFrame with typed columns and date filtering."""
    try:
        conn = get_db_connection(db_path)
        query = """
            SELECT 
                id, 
                ticket_id, 
                customer_id, 
                category, 
                priority, 
                severity, 
                status, 
                ai_resolution_status, 
                final_confidence, 
                retrieval_similarity, 
                resolution_text, 
                escalation_reason, 
                jira_issue_key, 
                created_at, 
                updated_at
            FROM tickets
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
    except Exception as e:
        # Return empty DataFrame with expected columns on error
        cols = [
            "id", "ticket_id", "customer_id", "category", "priority", "severity",
            "status", "ai_resolution_status", "final_confidence", "retrieval_similarity",
            "resolution_text", "escalation_reason", "jira_issue_key", "created_at", "updated_at"
        ]
        df = pd.DataFrame(columns=cols)

    if df.empty:
        return df

    # Normalize dates
    df['created_at_dt'] = pd.to_datetime(df['created_at'], errors='coerce')
    df['updated_at_dt'] = pd.to_datetime(df['updated_at'], errors='coerce')
    
    # Fill numeric nulls
    df['final_confidence'] = pd.to_numeric(df['final_confidence'], errors='coerce').fillna(0.0)
    df['retrieval_similarity'] = pd.to_numeric(df['retrieval_similarity'], errors='coerce').fillna(0.0)

    # Date filtering
    if start_date:
        df = df[df['created_at_dt'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['created_at_dt'] <= pd.to_datetime(end_date)]

    return df


def fetch_agent_runs_dataframe(db_path: Optional[str] = None) -> pd.DataFrame:
    """Fetches agent execution telemetry records."""
    try:
        conn = get_db_connection(db_path)
        query = """
            SELECT 
                id,
                ticket_id,
                category_predicted,
                priority_calculated,
                diagnosis_confidence,
                retrieval_similarity,
                resolution_completeness,
                safety_passed,
                final_confidence,
                outcome,
                executed_at
            FROM agent_runs
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
    except Exception:
        cols = [
            "id", "ticket_id", "category_predicted", "priority_calculated",
            "diagnosis_confidence", "retrieval_similarity", "resolution_completeness",
            "safety_passed", "final_confidence", "outcome", "executed_at"
        ]
        df = pd.DataFrame(columns=cols)

    if not df.empty:
        df['executed_at_dt'] = pd.to_datetime(df['executed_at'], errors='coerce')
        for col in ['diagnosis_confidence', 'retrieval_similarity', 'resolution_completeness', 'final_confidence']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    return df


def calculate_kpi_summary(df_tickets: pd.DataFrame, df_runs: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Computes core KPI metrics according to project specifications.
    
    Definitions:
    - Total tickets: Total rows in the tickets table.
    - Processed tickets: Tickets with ai_resolution_status in ['AUTO_RESOLVE', 'ESCALATE'].
    - AI resolution rate: AI-resolved tickets ÷ processed tickets × 100.
    - Escalation rate: Escalated tickets ÷ processed tickets × 100.
    - Average AI confidence: Mean of final_confidence for processed tickets.
    - Knowledge-base coverage: Tickets with retrieval_similarity >= 0.60 ÷ eligible tickets × 100.
    - Resolution success rate: Successfully resolved tickets ÷ eligible tickets × 100.
    """
    if df_tickets.empty:
        return {
            "total_tickets": 0,
            "processed_tickets": 0,
            "pending_tickets": 0,
            "ai_resolved_tickets": 0,
            "escalated_tickets": 0,
            "ai_resolution_rate": 0.0,
            "escalation_rate": 0.0,
            "avg_ai_confidence": 0.0,
            "avg_retrieval_similarity": 0.0,
            "kb_coverage_rate": 0.0,
            "resolution_success_rate": 0.0,
            "avg_resolution_time_sec": None,
            "csat_score": None,
            "csat_note": "Not available: No customer satisfaction survey records stored in ticket schema.",
            "uptime_pct": None,
            "uptime_note": "Calculated dynamically via health-check monitoring logs.",
            "low_confidence_count": 0,
            "low_similarity_count": 0
        }

    total_tickets = len(df_tickets)
    
    # Status categorizations
    auto_resolved = df_tickets[df_tickets['ai_resolution_status'] == 'AUTO_RESOLVE']
    escalated = df_tickets[df_tickets['ai_resolution_status'] == 'ESCALATE']
    pending = df_tickets[df_tickets['ai_resolution_status'] == 'PENDING']
    
    processed_count = len(auto_resolved) + len(escalated)
    pending_count = len(pending)
    auto_resolved_count = len(auto_resolved)
    escalated_count = len(escalated)

    # Rates with non-zero denominator check
    ai_resolution_rate = (auto_resolved_count / processed_count * 100.0) if processed_count > 0 else 0.0
    escalation_rate = (escalated_count / processed_count * 100.0) if processed_count > 0 else 0.0

    # Confidences for processed tickets
    if processed_count > 0:
        processed_mask = df_tickets['ai_resolution_status'].isin(['AUTO_RESOLVE', 'ESCALATE'])
        processed_df = df_tickets[processed_mask]
        avg_confidence = float(processed_df['final_confidence'].mean())
        avg_similarity = float(processed_df['retrieval_similarity'].mean())
        
        # Knowledge-base coverage: similarity >= 0.60 threshold
        kb_covered = (processed_df['retrieval_similarity'] >= 0.60).sum()
        kb_coverage_rate = (kb_covered / processed_count * 100.0)
        
        # Resolution success: Auto resolved with confidence >= 0.70 & similarity >= 0.60
        valid_auto_resolved = (
            (processed_df['ai_resolution_status'] == 'AUTO_RESOLVE') &
            (processed_df['final_confidence'] >= 0.70)
        ).sum()
        resolution_success_rate = (valid_auto_resolved / processed_count * 100.0)
        
        low_confidence_count = int((processed_df['final_confidence'] < 0.70).sum())
        low_similarity_count = int((processed_df['retrieval_similarity'] < 0.60).sum())
    else:
        avg_confidence = 0.0
        avg_similarity = 0.0
        kb_coverage_rate = 0.0
        resolution_success_rate = 0.0
        low_confidence_count = 0
        low_similarity_count = 0

    # Average resolution time estimate
    # Uses time difference between created_at and updated_at for resolved tickets if valid
    durations = []
    for _, row in auto_resolved.iterrows():
        if pd.notna(row['created_at_dt']) and pd.notna(row['updated_at_dt']):
            diff = (row['updated_at_dt'] - row['created_at_dt']).total_seconds()
            if 0 < diff < 86400:  # Reasonable range < 24 hours
                durations.append(diff)
    
    avg_resolution_time_sec = float(np.mean(durations)) if durations else None

    return {
        "total_tickets": total_tickets,
        "processed_tickets": processed_count,
        "pending_tickets": pending_count,
        "ai_resolved_tickets": auto_resolved_count,
        "escalated_tickets": escalated_count,
        "ai_resolution_rate": round(ai_resolution_rate, 2),
        "escalation_rate": round(escalation_rate, 2),
        "avg_ai_confidence": round(avg_confidence, 4),
        "avg_retrieval_similarity": round(avg_similarity, 4),
        "kb_coverage_rate": round(kb_coverage_rate, 2),
        "resolution_success_rate": round(resolution_success_rate, 2),
        "avg_resolution_time_sec": round(avg_resolution_time_sec, 2) if avg_resolution_time_sec is not None else None,
        "csat_score": None,
        "csat_note": "Not available: Customer rating / CSAT collection is not implemented in the current production ticket schema.",
        "uptime_pct": None,
        "uptime_note": "Measured via live health-check monitoring probe in System Monitoring tab.",
        "low_confidence_count": low_confidence_count,
        "low_similarity_count": low_similarity_count
    }


def get_performance_over_time(
    df_tickets: pd.DataFrame,
    freq: str = 'D',
    date_preset: str = 'all'
) -> pd.DataFrame:
    """
    Aggregates performance trends over time.
    Calculates:
    - AI Resolution Rate (%)
    - Escalation Rate (%)
    - Average AI Confidence (%)
    Grouped by Day ('D') or Week ('W').
    """
    if df_tickets.empty:
        return pd.DataFrame(columns=['period', 'total', 'processed', 'ai_resolved', 'escalated', 'resolution_rate', 'escalation_rate', 'avg_confidence_pct'])

    df = df_tickets.copy()
    df = df[df['created_at_dt'].notna()]
    if df.empty:
        return pd.DataFrame(columns=['period', 'total', 'processed', 'ai_resolved', 'escalated', 'resolution_rate', 'escalation_rate', 'avg_confidence_pct'])

    # Apply date filter preset
    max_dt = df['created_at_dt'].max()
    if date_preset == '7d':
        df = df[df['created_at_dt'] >= (max_dt - timedelta(days=7))]
    elif date_preset == '30d':
        df = df[df['created_at_dt'] >= (max_dt - timedelta(days=30))]

    if df.empty:
        return pd.DataFrame(columns=['period', 'total', 'processed', 'ai_resolved', 'escalated', 'resolution_rate', 'escalation_rate', 'avg_confidence_pct'])

    df['period'] = df['created_at_dt'].dt.to_period(freq).dt.to_timestamp()
    
    grouped = []
    for period, group in df.groupby('period'):
        processed = group[group['ai_resolution_status'].isin(['AUTO_RESOLVE', 'ESCALATE'])]
        proc_cnt = len(processed)
        auto_cnt = len(group[group['ai_resolution_status'] == 'AUTO_RESOLVE'])
        esc_cnt = len(group[group['ai_resolution_status'] == 'ESCALATE'])
        
        res_rate = (auto_cnt / proc_cnt * 100.0) if proc_cnt > 0 else 0.0
        esc_rate = (esc_cnt / proc_cnt * 100.0) if proc_cnt > 0 else 0.0
        avg_conf = (processed['final_confidence'].mean() * 100.0) if proc_cnt > 0 else 0.0
        
        grouped.append({
            'period': period,
            'total': len(group),
            'processed': proc_cnt,
            'ai_resolved': auto_cnt,
            'escalated': esc_cnt,
            'resolution_rate': round(res_rate, 2),
            'escalation_rate': round(esc_rate, 2),
            'avg_confidence_pct': round(avg_conf, 2)
        })

    result_df = pd.DataFrame(grouped).sort_values('period').reset_index(drop=True)
    return result_df


def get_category_breakdown(df_tickets: pd.DataFrame) -> pd.DataFrame:
    """Calculates ticket volume, resolution, and escalation breakdown per category."""
    if df_tickets.empty:
        return pd.DataFrame(columns=['category', 'total', 'ai_resolved', 'escalated', 'pending', 'escalation_rate', 'avg_confidence'])

    records = []
    for cat, group in df_tickets.groupby('category'):
        total = len(group)
        auto_cnt = len(group[group['ai_resolution_status'] == 'AUTO_RESOLVE'])
        esc_cnt = len(group[group['ai_resolution_status'] == 'ESCALATE'])
        pend_cnt = len(group[group['ai_resolution_status'] == 'PENDING'])
        proc_cnt = auto_cnt + esc_cnt
        
        esc_rate = (esc_cnt / proc_cnt * 100.0) if proc_cnt > 0 else 0.0
        avg_conf = float(group['final_confidence'].mean()) if total > 0 else 0.0
        
        records.append({
            'category': str(cat) if cat else "Unassigned",
            'total': total,
            'ai_resolved': auto_cnt,
            'escalated': esc_cnt,
            'pending': pend_cnt,
            'escalation_rate': round(esc_rate, 2),
            'avg_confidence': round(avg_conf, 4)
        })

    result_df = pd.DataFrame(records).sort_values('total', ascending=False).reset_index(drop=True)
    return result_df


def get_priority_breakdown(df_tickets: pd.DataFrame) -> pd.DataFrame:
    """Calculates ticket distribution across priority levels and critical escalations."""
    if df_tickets.empty:
        return pd.DataFrame(columns=['priority', 'total', 'ai_resolved', 'escalated', 'critical_escalations'])

    records = []
    order = ['Critical', 'High', 'Medium', 'Low']
    
    for prio, group in df_tickets.groupby('priority'):
        prio_str = str(prio).capitalize() if prio else "Medium"
        total = len(group)
        auto_cnt = len(group[group['ai_resolution_status'] == 'AUTO_RESOLVE'])
        esc_cnt = len(group[group['ai_resolution_status'] == 'ESCALATE'])
        crit_esc = esc_cnt if prio_str == 'Critical' else 0
        
        records.append({
            'priority': prio_str,
            'total': total,
            'ai_resolved': auto_cnt,
            'escalated': esc_cnt,
            'critical_escalations': crit_esc
        })

    result_df = pd.DataFrame(records)
    # Sort by standard priority order
    result_df['order_idx'] = result_df['priority'].apply(lambda x: order.index(x) if x in order else 99)
    result_df = result_df.sort_values('order_idx').drop(columns=['order_idx']).reset_index(drop=True)
    return result_df


def get_confidence_distribution(df_tickets: pd.DataFrame) -> pd.DataFrame:
    """Groups processed tickets into clear confidence bands."""
    if df_tickets.empty:
        return pd.DataFrame(columns=['band', 'count', 'percentage', 'resolved_count', 'escalated_count'])

    processed = df_tickets[df_tickets['ai_resolution_status'].isin(['AUTO_RESOLVE', 'ESCALATE'])].copy()
    if processed.empty:
        return pd.DataFrame(columns=['band', 'count', 'percentage', 'resolved_count', 'escalated_count'])

    bins = [-0.01, 0.50, 0.70, 0.85, 1.01]
    labels = [
        "Low (< 0.50)",
        "Moderate (0.50 - 0.69)",
        "Good (0.70 - 0.84)",
        "High (0.85 - 1.00)"
    ]
    
    processed['band'] = pd.cut(processed['final_confidence'], bins=bins, labels=labels)
    
    summary = []
    total_proc = len(processed)
    for label in labels:
        subset = processed[processed['band'] == label]
        cnt = len(subset)
        pct = (cnt / total_proc * 100.0) if total_proc > 0 else 0.0
        res_cnt = len(subset[subset['ai_resolution_status'] == 'AUTO_RESOLVE'])
        esc_cnt = len(subset[subset['ai_resolution_status'] == 'ESCALATE'])
        summary.append({
            'band': label,
            'count': cnt,
            'percentage': round(pct, 1),
            'resolved_count': res_cnt,
            'escalated_count': esc_cnt
        })

    return pd.DataFrame(summary)
