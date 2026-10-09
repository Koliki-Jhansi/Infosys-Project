"""
SupportPilot — AI Performance & Analytics
Milestone 4 Separate Analytics Application (Streamlit + Pandas + Plotly)
Runs independently on port 8501 without modifying or breaking existing dashboard.
"""

import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta

# Ensure parent directory and milestone4_analytics are accessible
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from analytics import (
    DEFAULT_DB_PATH,
    fetch_tickets_dataframe,
    fetch_agent_runs_dataframe,
    calculate_kpi_summary,
    get_performance_over_time,
    get_category_breakdown,
    get_priority_breakdown,
    get_confidence_distribution
)
from escalation import (
    get_human_intervention_queue,
    evaluate_escalation_rules
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

# Set page configuration
st.set_page_config(
    page_title="SupportPilot — AI Performance & Analytics",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0284c7 0%, #3b82f6 50%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        text-align: center;
    }
    .kpi-title {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 0.35rem;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #94a3b8;
        margin-top: 0.3rem;
    }
    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-healthy {
        background-color: #dcfce7;
        color: #15803d;
    }
    .status-standby {
        background-color: #fef9c3;
        color: #a16207;
    }
    .status-critical {
        background-color: #fee2e2;
        color: #b91c1c;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/airplane-mode-on.png", width=64)
    st.title("SupportPilot Analytics")
    st.caption("Milestone 4 AI Analytics & Evaluation Suite")
    st.markdown("---")
    
    st.subheader("⚙️ Data & Date Filters")
    date_filter = st.selectbox(
        "Date Range Preset",
        ["All Available History", "Last 30 Days", "Last 7 Days"],
        index=0
    )
    date_preset_map = {
        "All Available History": "all",
        "Last 30 Days": "30d",
        "Last 7 Days": "7d"
    }
    
    aggregation_freq = st.radio(
        "Time Series Aggregation",
        ["Daily", "Weekly"],
        horizontal=True
    )
    freq_code = "D" if aggregation_freq == "Daily" else "W"
    
    st.markdown("---")
    st.subheader("📁 Database Status")
    db_exists = os.path.exists(DEFAULT_DB_PATH)
    if db_exists:
        st.success(f"Connected: `aeroassist.db`")
        st.caption(f"Path: `{os.path.basename(DEFAULT_DB_PATH)}`")
    else:
        st.error("Database file missing!")
        
    st.markdown("---")
    if st.button("🔄 Refresh Data & Cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ----------------- DATA LOADING -----------------
@st.cache_data(ttl=60)
def load_app_data(date_preset: str):
    df_tickets = fetch_tickets_dataframe()
    df_runs = fetch_agent_runs_dataframe()
    kpis = calculate_kpi_summary(df_tickets, df_runs)
    df_trends = get_performance_over_time(df_tickets, freq=freq_code, date_preset=date_preset)
    df_cat = get_category_breakdown(df_tickets)
    df_prio = get_priority_breakdown(df_tickets)
    df_conf = get_confidence_distribution(df_tickets)
    return df_tickets, df_runs, kpis, df_trends, df_cat, df_prio, df_conf

df_tickets, df_runs, kpis, df_trends, df_cat, df_prio, df_conf = load_app_data(date_preset_map[date_filter])

# ----------------- MAIN HEADER -----------------
col_title, col_stat = st.columns([4, 1])
with col_title:
    st.markdown('<div class="main-header">SupportPilot — AI Performance & Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Live Telemetry, Escalation Rule Engine, RAG Quality, and AI Evaluation</div>', unsafe_allow_html=True)

with col_stat:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="text-align: right;"><span class="status-pill status-healthy">● System Operational</span><br><small style="color:#64748b;">Port 8501 (Independent)</small></div>',
        unsafe_allow_html=True
    )

# ----------------- TOP-LEVEL TABS -----------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Executive KPIs & Trends",
    "🔍 Category & Priority Analysis",
    "🎯 Confidence Distribution",
    "🚨 Human Intervention Monitor",
    "🧪 Classifier & RAG Benchmark",
    "🩺 System Health & Logs"
])

# -------------------------------------------------------------
# TAB 1: EXECUTIVE KPIS & TRENDS
# -------------------------------------------------------------
with tab1:
    st.markdown("### 📈 Core Performance Indicators")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.metric(
            label="Total Tickets",
            value=f"{kpis['total_tickets']:,}",
            help="Total tickets stored in production database."
        )
    with kpi_col2:
        st.metric(
            label="AI Resolution Rate",
            value=f"{kpis['ai_resolution_rate']}%",
            delta=f"{kpis['ai_resolved_tickets']} resolved",
            help="Auto-resolved tickets ÷ processed tickets × 100"
        )
    with kpi_col3:
        st.metric(
            label="Escalation Rate",
            value=f"{kpis['escalation_rate']}%",
            delta=f"-{kpis['escalated_tickets']} escalated",
            delta_color="inverse",
            help="Escalated tickets ÷ processed tickets × 100"
        )
    with kpi_col4:
        st.metric(
            label="Average AI Confidence",
            value=f"{kpis['avg_ai_confidence'] * 100:.1f}%",
            help="Mean final confidence across all processed tickets."
        )

    kpi_col5, kpi_col6, kpi_col7, kpi_col8 = st.columns(4)
    with kpi_col5:
        st.metric(
            label="KB Coverage Rate",
            value=f"{kpis['kb_coverage_rate']}%",
            help="Tickets matched with similarity >= 0.60 ÷ eligible tickets × 100"
        )
    with kpi_col6:
        st.metric(
            label="Resolution Success Rate",
            value=f"{kpis['resolution_success_rate']}%",
            help="Auto-resolved tickets with confidence >= 0.70 ÷ eligible tickets × 100"
        )
    with kpi_col7:
        res_time_val = f"{kpis['avg_resolution_time_sec']}s" if kpis['avg_resolution_time_sec'] else "Not available"
        st.metric(
            label="Avg Resolution Time",
            value=res_time_val,
            help="Calculated duration for successfully resolved tickets."
        )
    with kpi_col8:
        st.metric(
            label="Customer Satisfaction (CSAT)",
            value="Not available",
            help="No customer rating survey data is collected in the current ticket schema."
        )

    st.markdown("---")
    st.markdown("### 📉 AI Performance Over Time")
    st.caption("Tracking daily/weekly AI Resolution Rate (%), Human Escalation Rate (%), and Average AI Confidence (%)")
    
    if df_trends.empty:
        st.info("No time-series data available for the selected date range.")
    else:
        fig_trend = go.Figure()
        
        # 1. AI Resolution Rate Line
        fig_trend.add_trace(go.Scatter(
            x=df_trends['period'],
            y=df_trends['resolution_rate'],
            name='AI Resolution Rate (%)',
            mode='lines+markers',
            line=dict(color='#10b981', width=3),
            marker=dict(size=7),
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>AI Resolution Rate:</b> %{y:.1f}%<extra></extra>"
        ))
        
        # 2. Escalation Rate Line
        fig_trend.add_trace(go.Scatter(
            x=df_trends['period'],
            y=df_trends['escalation_rate'],
            name='Escalation Rate (%)',
            mode='lines+markers',
            line=dict(color='#ef4444', width=3, dash='dot'),
            marker=dict(size=7),
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Escalation Rate:</b> %{y:.1f}%<extra></extra>"
        ))
        
        # 3. Average AI Confidence Line
        fig_trend.add_trace(go.Scatter(
            x=df_trends['period'],
            y=df_trends['avg_confidence_pct'],
            name='Average AI Confidence (%)',
            mode='lines+markers',
            line=dict(color='#3b82f6', width=2),
            marker=dict(size=6),
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Avg Confidence:</b> %{y:.1f}%<extra></extra>"
        ))
        
        fig_trend.update_layout(
            height=420,
            margin=dict(l=20, r=20, t=30, b=20),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                title="Date",
                showgrid=True,
                gridcolor="#f1f5f9"
            ),
            yaxis=dict(
                title="Percentage (%)",
                range=[0, 105],
                showgrid=True,
                gridcolor="#f1f5f9"
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

# -------------------------------------------------------------
# TAB 2: CATEGORY & PRIORITY ANALYSIS
# -------------------------------------------------------------
with tab2:
    st.markdown("### 📊 Ticket Category & Priority Distribution")
    
    col_c1, col_c2 = st.columns([3, 2])
    
    with col_c1:
        st.subheader("Category Breakdown & Escalations")
        if df_cat.empty:
            st.info("No category data found.")
        else:
            fig_cat = go.Figure()
            fig_cat.add_trace(go.Bar(
                x=df_cat['category'],
                y=df_cat['ai_resolved'],
                name='AI Resolved',
                marker_color='#10b981'
            ))
            fig_cat.add_trace(go.Bar(
                x=df_cat['category'],
                y=df_cat['escalated'],
                name='Escalated to Human',
                marker_color='#ef4444'
            ))
            fig_cat.update_layout(
                barmode='stack',
                height=380,
                xaxis_title="Category",
                yaxis_title="Ticket Count",
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
    with col_c2:
        st.subheader("Resolution vs Escalation Ratio")
        if kpis['processed_tickets'] == 0:
            st.info("No processed tickets to display.")
        else:
            labels = ['AI Resolved', 'Escalated to Human']
            values = [kpis['ai_resolved_tickets'], kpis['escalated_tickets']]
            colors = ['#10b981', '#ef4444']
            
            fig_donut = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=.6,
                marker=dict(colors=colors),
                textinfo='label+percent'
            )])
            fig_donut.update_layout(
                height=380,
                margin=dict(l=20, r=20, t=30, b=20),
                showlegend=False
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            
    st.markdown("---")
    st.subheader("Priority Distribution & Critical Attention")
    
    col_p1, col_p2 = st.columns([3, 2])
    with col_p1:
        if df_prio.empty:
            st.info("No priority data found.")
        else:
            fig_prio = px.bar(
                df_prio,
                x='priority',
                y='total',
                color='priority',
                color_discrete_map={
                    'Critical': '#ef4444',
                    'High': '#f97316',
                    'Medium': '#3b82f6',
                    'Low': '#10b981'
                },
                labels={'priority': 'Priority Level', 'total': 'Total Tickets'},
                text='total'
            )
            fig_prio.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
            st.plotly_chart(fig_prio, use_container_width=True)
            
    with col_p2:
        st.markdown("#### 🚨 Safety Rule Note")
        st.info("""
        **Priority Escalation Protocol:**
        - All **Critical** priority tickets (e.g. In-flight Emergencies, Severe Safety Incidents) bypass automated resolution and are immediately routed to senior human dispatchers.
        - **High** priority tickets require both confidence $\ge 0.70$ and KB similarity $\ge 0.60$.
        """)

# -------------------------------------------------------------
# TAB 3: CONFIDENCE DISTRIBUTION
# -------------------------------------------------------------
with tab3:
    st.markdown("### 🎯 AI Confidence Score Analysis")
    st.caption("Distribution of AI confidence across all processed decisions against safe threshold boundaries (0.70).")
    
    col_d1, col_d2 = st.columns([3, 2])
    with col_d1:
        if df_conf.empty:
            st.info("No confidence records available.")
        else:
            fig_conf = px.bar(
                df_conf,
                x='band',
                y='count',
                color='band',
                color_discrete_sequence=['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
                labels={'band': 'Confidence Band', 'count': 'Ticket Count'},
                text='percentage'
            )
            fig_conf.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_conf.update_layout(height=360, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
            st.plotly_chart(fig_conf, use_container_width=True)
            
    with col_d2:
        st.subheader("Confidence Threshold Breakdown")
        st.dataframe(
            df_conf[['band', 'count', 'percentage', 'resolved_count', 'escalated_count']],
            column_config={
                "band": "Band",
                "count": "Total",
                "percentage": "Share (%)",
                "resolved_count": "AI Resolved",
                "escalated_count": "Escalated"
            },
            hide_index=True,
            use_container_width=True
        )
        st.caption("⚠️ Tickets with confidence < 0.70 are automatically escalated to prevent hallucinations.")

# -------------------------------------------------------------
# TAB 4: HUMAN INTERVENTION MONITOR
# -------------------------------------------------------------
with tab4:
    st.markdown("### 🚨 Human Intervention Monitor")
    st.caption("Real-time monitoring queue of tickets requiring human agent intervention, inspection, and assignment.")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_cat = st.selectbox(
            "Filter Category",
            ["All"] + sorted([str(c) for c in df_tickets['category'].dropna().unique() if str(c)]),
            key="queue_filter_cat"
        )
    with col_f2:
        filter_prio = st.selectbox(
            "Filter Priority",
            ["All", "Critical", "High", "Medium", "Low"],
            key="queue_filter_prio"
        )
    with col_f3:
        search_reason = st.text_input("Search Escalation Reason / Keyword", placeholder="e.g. Critical, Low Confidence, Human")

    df_queue = get_human_intervention_queue(
        category=filter_cat if filter_cat != "All" else None,
        priority=filter_prio if filter_prio != "All" else None,
        escalation_reason_substr=search_reason if search_reason else None
    )
    
    st.markdown(f"**Found {len(df_queue)} tickets requiring human intervention:**")
    
    if df_queue.empty:
        st.success("🎉 No tickets currently pending human intervention for the selected filters.")
    else:
        st.dataframe(
            df_queue[[
                'ticket_id', 'category', 'priority', 'final_confidence', 
                'status', 'escalation_reason', 'attempts_count', 'jira_issue_key', 'created_at'
            ]],
            column_config={
                "ticket_id": "Ticket ID",
                "category": "Category",
                "priority": "Priority",
                "final_confidence": st.column_config.NumberColumn("AI Confidence", format="%.2f"),
                "status": "Ticket Status",
                "escalation_reason": "Escalation Reason",
                "attempts_count": "Attempts",
                "jira_issue_key": "Jira Key",
                "created_at": "Created At"
            },
            hide_index=True,
            use_container_width=True
        )

    st.markdown("---")
    st.subheader("🧪 Live Escalation Rule Tester")
    st.caption("Test individual ticket parameters against the 5 Milestone 4 Escalation Rules.")
    
    with st.expander("Test Custom Ticket Escalation Conditions", expanded=False):
        t_c1, t_c2, t_c3 = st.columns(3)
        with t_c1:
            t_prio = st.selectbox("Ticket Priority", ["Critical", "High", "Medium", "Low"])
            t_conf = st.slider("AI Confidence", 0.0, 1.0, 0.75, 0.01)
        with t_c2:
            t_sim = st.slider("KB Retrieval Similarity", 0.0, 1.0, 0.85, 0.01)
            t_attempts = st.number_input("Attempts Count", min_value=1, max_value=10, value=1)
        with t_c3:
            t_status = st.selectbox("Resolution Status", ["SUCCESS", "FAILED", "PENDING"])
            t_text = st.text_input("Customer Input Text", value="I need to speak to a human representative")

        should_esc, reason, details = evaluate_escalation_rules(
            priority=t_prio,
            final_confidence=t_conf,
            resolution_status=t_status,
            customer_text=t_text,
            attempts_count=t_attempts,
            retrieval_similarity=t_sim
        )
        
        if should_esc:
            st.error(f"🚨 **ESCALATE TO HUMAN**: {reason}")
        else:
            st.success("✅ **AUTO-RESOLVE APPROVED**: All safety and confidence criteria satisfied.")
        st.json(details)

# -------------------------------------------------------------
# TAB 5: CLASSIFIER & RAG BENCHMARK
# -------------------------------------------------------------
with tab5:
    st.markdown("### 🧪 Classifier & Resolution Benchmark Evaluation")
    st.caption("Rigorous offline evaluation against 40 ground-truth labelled test scenarios (data/evaluation_dataset.json).")
    
    if st.button("🚀 Run Full Model & RAG Evaluation Benchmark", type="primary"):
        with st.spinner("Evaluating classifier and RAG pipeline against ground truth dataset..."):
            cls_res = evaluate_classifier_performance()
            rag_res = evaluate_resolution_and_rag()
            st.session_state['cls_eval_results'] = cls_res
            st.session_state['rag_eval_results'] = rag_res
            st.success("Evaluation complete!")

    if 'cls_eval_results' in st.session_state and 'rag_eval_results' in st.session_state:
        cls_res = st.session_state['cls_eval_results']
        rag_res = st.session_state['rag_eval_results']
        
        st.markdown("#### 1. Classifier Evaluation Metrics")
        b_c1, b_c2, b_c3, b_c4 = st.columns(4)
        with b_c1:
            st.metric("Classification Accuracy", f"{cls_res.get('accuracy', 0)}%")
        with b_c2:
            st.metric("Macro Precision", f"{cls_res.get('macro_precision', 0)}%")
        with b_c3:
            st.metric("Macro Recall", f"{cls_res.get('macro_recall', 0)}%")
        with b_c4:
            st.metric("Macro F1-Score", f"{cls_res.get('macro_f1', 0)}%")

        st.markdown("##### Per-Category Classification Performance")
        st.dataframe(cls_res.get('per_class_df'), hide_index=True, use_container_width=True)

        st.markdown("##### Confusion Matrix")
        labels = cls_res.get('labels', [])
        cm_data = cls_res.get('confusion_matrix', [])
        if labels and cm_data:
            fig_cm = px.imshow(
                cm_data,
                x=labels,
                y=labels,
                color_continuous_scale='Blues',
                labels=dict(x="Predicted Category", y="True Ground-Truth Category", color="Count"),
                text_auto=True
            )
            fig_cm.update_layout(height=480, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_cm, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 2. Resolution & RAG Quality Metrics")
        r_c1, r_c2, r_c3, r_c4 = st.columns(4)
        with r_c1:
            st.metric("Decision Accuracy", f"{rag_res.get('decision_accuracy', 0)}%")
        with r_c2:
            st.metric("Solvable Auto-Resolution", f"{rag_res.get('solvable_auto_resolve_rate', 0)}%")
        with r_c3:
            st.metric("Escalation Safety Rate", f"{rag_res.get('escalation_safety_rate', 0)}%")
        with r_c4:
            st.metric("KB Coverage Rate", f"{rag_res.get('kb_coverage_rate', 0)}%")
            
        st.caption("Results computed using ground-truth dataset. Unlabelled production samples are excluded from ground-truth scores.")
    else:
        st.info("Click the button above to run the live model and RAG evaluation benchmark.")

# -------------------------------------------------------------
# TAB 6: SYSTEM HEALTH & LOGS
# -------------------------------------------------------------
with tab6:
    st.markdown("### 🩺 System Diagnostics & Availability")
    st.caption("Real-time component health checks, latency tracking, and true uptime measurement.")
    
    col_h1, col_h2 = st.columns([3, 2])
    with col_h1:
        st.subheader("Live Component Probes")
        health = run_comprehensive_health_check()
        for comp, info in health.get("components", {}).items():
            status = info.get("status")
            badge_class = "status-healthy" if "HEALTHY" in status else ("status-standby" if "STANDBY" in status else "status-critical")
            st.markdown(f"""
            <div style="padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{comp.replace('_', ' ').title()}</strong><br>
                    <small style="color: #64748b;">{info.get('details', '')}</small>
                </div>
                <div style="text-align: right;">
                    <span class="status-pill {badge_class}">{status}</span><br>
                    <small style="color: #94a3b8;">{info.get('latency_ms', 0):.1f} ms</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_h2:
        st.subheader("Uptime & Availability")
        uptime_info = get_real_system_uptime()
        st.metric(
            label="Calculated System Uptime",
            value=f"{uptime_info['uptime_pct']}%",
            help="Computed dynamically from recorded health probe history."
        )
        st.caption(f"ℹ️ {uptime_info['note']}")
        
        st.markdown("#### Average Stage Latencies")
        lat = get_stage_latencies_summary()
        st.write(f"- **Classifier:** {lat['classifier_avg_ms']} ms")
        st.write(f"- **Diagnosis Agent:** {lat['diagnosis_avg_ms']} ms")
        st.write(f"- **KB Retriever:** {lat['retriever_avg_ms']} ms")
        st.write(f"- **Resolution Agent:** {lat['resolution_avg_ms']} ms")
        st.write(f"- **Safety Guardrail:** {lat['safety_guardrail_avg_ms']} ms")
        st.write(f"**Total Pipeline Average:** **{lat['total_avg_pipeline_ms']} ms**")
