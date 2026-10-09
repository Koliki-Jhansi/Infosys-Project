"""
AeroAssist AI - Intelligent Airport & Airways Customer Support Platform
Main Flask Web Application
"""
import os
import json
import math
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv

load_dotenv()

from database import (
    init_db, get_user_by_username_or_email, get_user_by_id, create_user,
    create_ticket, get_ticket_by_id, get_all_tickets, get_ticket_stats,
    update_ticket_ai_results, get_agent_runs_for_ticket, get_next_ticket_id,
    is_user_authorized_for_ticket, get_dashboard_analytics,
    create_contact_message, get_contact_messages,
    update_ticket_jira_info, get_existing_jira_for_ticket,
    get_ai_performance_kpis, get_ai_performance_over_time,
    get_category_ai_performance, get_ai_confidence_distribution,
    get_agent_stage_performance, get_ai_performance_insights
)
from jira_service import create_jira_issue, get_jira_config
from classifier import get_classifier, CATEGORIES
from priority import calculate_priority
from severity import calculate_severity
from rag import get_retriever, get_rag_pipeline, load_knowledge_base
from agents import get_multi_agent_system, DECISION_THRESHOLD

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "aeroassist-flight-key-default-2026")

# Initialize database schema on start
init_db()

# ==========================================
# AUTHENTICATION HELPERS & DECORATORS
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access AeroAssist AI.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if "user_id" in session:
        return get_user_by_id(session["user_id"])
    return None

@app.context_processor
def inject_global_data():
    return {
        "current_user": get_current_user(),
        "categories": CATEGORIES,
        "now": datetime.now(),
        "decision_threshold": DECISION_THRESHOLD
    }


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ==========================================
# PUBLIC & WELCOME ROUTES
# ==========================================
@app.route("/")
def index():
    """Root route: Redirect to dashboard if logged in, else show welcome page."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    try:
        from rag import load_knowledge_base
        kb_count = len(load_knowledge_base())
    except Exception:
        kb_count = 566
    return render_template("welcome.html", kb_total_count=kb_count)


@app.route("/welcome")
def welcome():
    """Public Airport Welcome Page."""
    try:
        from rag import load_knowledge_base
        kb_count = len(load_knowledge_base())
    except Exception:
        kb_count = 566
    return render_template("welcome.html", kb_total_count=kb_count)


@app.route("/about")
def about():
    """Public About Section."""
    return redirect(url_for("welcome") + "#about")


@app.route("/services")
def services():
    """Public Services Section."""
    return redirect(url_for("welcome") + "#services")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Public Contact Us Page and Inbound Message Handler."""
    if request.method == "POST":
        # Anti-spam honeypot check: if website field is filled by bot, drop silently
        if request.form.get("website"):
            flash("Message submitted successfully.", "success")
            return redirect(url_for("contact"))

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        # Field validation
        if not full_name or not email or not subject or not message:
            flash("All fields are required. Please complete all fields before sending.", "danger")
            return render_template("contact.html")

        if "@" not in email or "." not in email:
            flash("Please provide a valid email address.", "danger")
            return render_template("contact.html")

        if len(message) < 5:
            flash("Please provide a detailed message (minimum 5 characters).", "danger")
            return render_template("contact.html")

        # Securely persist contact message in database for support review
        ip_addr = request.headers.get("X-Forwarded-For", request.remote_addr)
        msg_id = create_contact_message(
            full_name=full_name,
            email=email,
            subject=subject,
            message=message,
            ip_address=ip_addr
        )

        flash(
            f"Thank you, {full_name}! Your support inquiry (Ref #{msg_id}) has been recorded. "
            f"Our airline support operations team will review it and reply to {email} shortly.",
            "success"
        )
        return redirect(url_for("contact"))

    return render_template("contact.html")


# ==========================================
# AUTHENTICATION ROUTES
# ==========================================
@app.route("/login", methods=["GET", "POST"])
def login():
    register_mode = request.args.get("tab") == "register"

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()

        if not identifier or not password:
            flash("Invalid username or password.", "danger")
            return render_template("login.html", register_mode=False)

        user = get_user_by_username_or_email(identifier)
        if user:
            from werkzeug.security import check_password_hash
            if check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                session["full_name"] = user["full_name"]
                flash(f"Welcome back to AeroAssist, {user['full_name']}!", "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("dashboard"))

        flash("Invalid username or password.", "danger")
        return render_template("login.html", register_mode=False)

    return render_template("login.html", register_mode=register_mode)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        full_name = request.form.get("full_name", "").strip()

        if not username or not email or not password or not full_name:
            flash("All fields are required.", "danger")
            return render_template("login.html", register_mode=True)

        if confirm_password and password != confirm_password:
            flash("Passwords do not match. Please re-enter your password.", "danger")
            return render_template("login.html", register_mode=True)

        user_id = create_user(username, email, password, full_name, role="passenger")
        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            session["role"] = "passenger"
            session["full_name"] = full_name
            flash("Account registered successfully! Welcome to AeroAssist AI.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Username or email already exists.", "danger")

    return render_template("login.html", register_mode=True)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("login"))


# ==========================================
# PASSENGER DASHBOARD & TICKETS
# ==========================================
@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    resolution_status = request.args.get("resolution_status", "All")

    stats = get_ticket_stats(user_id=user_id, role=role)
    analytics = get_dashboard_analytics(user_id=user_id, role=role)
    ai_kpis = get_ai_performance_kpis(user_id=user_id, role=role, date_range="all")
    ai_time_series = get_ai_performance_over_time(user_id=user_id, role=role, date_range="all")
    category_ai = get_category_ai_performance(user_id=user_id, role=role)
    confidence_dist = get_ai_confidence_distribution(user_id=user_id, role=role)
    agent_stages = get_agent_stage_performance(user_id=user_id, role=role)
    ai_insights = get_ai_performance_insights(user_id=user_id, role=role)

    recent_tickets = get_all_tickets(
        user_id=user_id,
        role=role,
        resolution_status=resolution_status
    )[:8]
    
    # Real Knowledge Base count
    try:
        from rag import load_knowledge_base
        kb_articles = load_knowledge_base()
        kb_total_count = len(kb_articles)
    except Exception:
        kb_total_count = 566

    return render_template(
        "dashboard.html",
        stats=stats,
        analytics=analytics,
        ai_kpis=ai_kpis,
        ai_time_series=ai_time_series,
        category_ai=category_ai,
        confidence_dist=confidence_dist,
        agent_stages=agent_stages,
        ai_insights=ai_insights,
        kb_total_count=kb_total_count,
        tickets=recent_tickets,
        resolution_status=resolution_status
    )


@app.route("/tickets", endpoint="tickets_list")
@app.route("/tickets/list", endpoint="tickets")
@login_required
def tickets_list():
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    selected_category = request.args.get("category", "All")
    selected_status = request.args.get("status", "All")
    selected_resolution = request.args.get("resolution_status", "All")
    search_query = request.args.get("q", "").strip()

    ticket_items = get_all_tickets(
        category=selected_category,
        status=selected_status,
        search=search_query,
        user_id=user_id,
        role=role,
        resolution_status=selected_resolution
    )

    return render_template(
        "tickets.html",
        tickets=ticket_items,
        selected_category=selected_category,
        selected_status=selected_status,
        selected_resolution=selected_resolution,
        search_query=search_query
    )


@app.route("/tickets/create", methods=["GET", "POST"], endpoint="create_ticket_view")
@app.route("/tickets/new", methods=["GET", "POST"], endpoint="create_ticket")
@login_required
def create_ticket_view():
    user = get_current_user()
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        manual_category = request.form.get("category", "Auto-Classify")
        flight_number = request.form.get("flight_number", "").strip().upper()
        booking_ref = request.form.get("booking_ref", "").strip().upper()
        airport = request.form.get("airport", "").strip()
        travel_date = request.form.get("travel_date", "").strip()

        if not title or not description:
            flash("Ticket title and description are required.", "danger")
            return render_template("create_ticket.html")

        # Classification
        classifier = get_classifier()
        cls_result = classifier.classify(title, description)
        predicted_category = cls_result["predicted_category"]
        classification_confidence = cls_result["confidence"]

        final_category = predicted_category if manual_category == "Auto-Classify" else manual_category

        # Priority & Severity Calculation
        priority = calculate_priority(title, description, final_category, travel_date)
        severity = calculate_severity(final_category, priority, description)

        ticket_data = {
            "passenger_id": user["id"] if user else None,
            "passenger_name": user["full_name"] if user else request.form.get("passenger_name", "Anonymous Passenger"),
            "passenger_email": user["email"] if user else request.form.get("passenger_email", "passenger@aeroassist.ai"),
            "title": title,
            "description": description,
            "category": final_category,
            "predicted_category": predicted_category,
            "classification_confidence": classification_confidence,
            "priority": priority,
            "severity": severity,
            "status": "Open",
            "flight_number": flight_number or None,
            "booking_ref": booking_ref or None,
            "airport": airport or None,
            "travel_date": travel_date or None
        }

        ticket_id = create_ticket(ticket_data)
        flash(f"Support ticket {ticket_id} created successfully! Classified as '{final_category}'.", "success")
        return redirect(url_for("ticket_detail", ticket_id=ticket_id))

    return render_template("create_ticket.html")


@app.route("/tickets/<ticket_id>", endpoint="ticket_detail")
@app.route("/tickets/detail/<ticket_id>", endpoint="ticket_detail_view")
@login_required
def ticket_detail(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash(f"Ticket {ticket_id} not found.", "danger")
        return redirect(url_for("tickets_list"))

    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    # Ownership check
    if role == "passenger" and ticket["passenger_id"] and ticket["passenger_id"] != user_id:
        flash("Access denied. You are only authorized to view your own support tickets.", "danger")
        return redirect(url_for("tickets_list"))

    agent_runs = get_agent_runs_for_ticket(ticket_id)

    # Compute RAG preview for ticket details display
    rag_pipe = get_rag_pipeline()
    rag_preview = rag_pipe.process_query(
        title=ticket["title"],
        description=ticket["description"],
        category=ticket["category"],
        metadata={"flight_number": ticket["flight_number"], "booking_ref": ticket["booking_ref"]}
    )

    return render_template(
        "ticket_detail.html",
        ticket=ticket,
        agent_runs=agent_runs,
        rag_preview=rag_preview
    )


# ==========================================
# AI SOLUTIONS RESULT PAGE
# ==========================================
@app.route("/ai-solutions", endpoint="ai_solutions_view")
@app.route("/ai-solutions/view", endpoint="ai_solutions")
@app.route("/tickets/<ticket_id>/ai-resolution", endpoint="m2_ai_resolution_view")
@login_required
def ai_solutions_view(ticket_id=None):
    """AI Solutions Result Page: Displays tickets whose persisted final decision is AUTO_RESOLVE."""
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    if not ticket_id:
        ticket_id = request.args.get("ticket_id")

    # Fetch only tickets whose persisted decision is AUTO_RESOLVE
    auto_resolved_tickets = get_all_tickets(
        user_id=user_id,
        role=role,
        resolution_status="AUTO_RESOLVE"
    )

    selected_ticket = None
    latest_run = None
    agent_runs = []
    rag_preview = None

    if ticket_id:
        ticket = get_ticket_by_id(ticket_id)
        if ticket:
            if role == "passenger" and ticket["passenger_id"] and ticket["passenger_id"] != user_id:
                flash("Access denied. You are not authorized to view this ticket.", "danger")
                return redirect(url_for("ai_solutions_view"))
            selected_ticket = ticket
            agent_runs = get_agent_runs_for_ticket(ticket_id)
            latest_run = agent_runs[0] if agent_runs else None
        else:
            flash(f"Ticket {ticket_id} not found.", "danger")

    return render_template(
        "ai_resolution.html",
        tickets=auto_resolved_tickets,
        selected_ticket=selected_ticket,
        latest_run=latest_run,
        agent_runs=agent_runs
    )



# ==========================================
# MULTI-AGENT RESOLUTION WORKFLOW
# ==========================================
@app.route("/multi-agent", endpoint="multi_agent_studio_view")
@app.route("/multi-agent/view", endpoint="multi_agent")
@app.route("/tickets/<ticket_id>/multi-agent", endpoint="multi_agent_ticket")
@app.route("/tickets/<ticket_id>/resolve", endpoint="multi_agent_resolve")
@login_required
def multi_agent_studio_view(ticket_id=None):
    """Five-Agent Sequential Aviation Resolution Studio."""
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    if not ticket_id:
        ticket_id = request.args.get("ticket_id")

    user_tickets = get_all_tickets(user_id=user_id, role=role)
    selected_ticket = None
    latest_run = None
    agent_runs = []

    if ticket_id:
        selected_ticket = get_ticket_by_id(ticket_id)
        if selected_ticket:
            if role == "passenger" and selected_ticket["passenger_id"] and selected_ticket["passenger_id"] != user_id:
                flash("Access denied. You are not authorized to view this ticket.", "danger")
                return redirect(url_for("multi_agent_studio_view"))
            
            agent_runs = get_agent_runs_for_ticket(ticket_id)
            latest_run = agent_runs[0] if agent_runs else None
        else:
            flash(f"Ticket {ticket_id} not found.", "danger")

    elif user_tickets:
        selected_ticket = user_tickets[0]
        agent_runs = get_agent_runs_for_ticket(selected_ticket["ticket_id"])
        latest_run = agent_runs[0] if agent_runs else None

    return render_template(
        "multi_agent.html",
        ticket=selected_ticket,
        tickets=user_tickets,
        latest_run=latest_run,
        agent_runs=agent_runs
    )


@app.route("/api/tickets/<ticket_id>/run-agents", methods=["POST"])
@login_required
def run_agents_api(ticket_id):
    """Executes the 5-agent sequential workflow and updates SQLite records."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"success": False, "error": "Ticket not found"}), 404

    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    if role == "passenger" and ticket["passenger_id"] and ticket["passenger_id"] != user_id:
        return jsonify({"success": False, "error": "Unauthorized access to this ticket"}), 403

    ticket_dict = dict(ticket)
    mas = get_multi_agent_system()
    results = mas.process_ticket(ticket_dict)

    # Persist in database
    update_ticket_ai_results(ticket_id, results)

    return jsonify({
        "success": True,
        "results": results
    })


@app.route("/api/rag/preview", methods=["POST"])
@login_required
def rag_preview_api():
    """Standalone RAG preview API."""
    data = request.get_json() or {}
    title = data.get("title", "")
    description = data.get("description", "")
    category = data.get("category", "")

    rag_pipe = get_rag_pipeline()
    result = rag_pipe.process_query(title, description, category)
    return jsonify(result)


# ==========================================
# MILESTONE 4: ANALYTICS REST API ENDPOINTS
# ==========================================

@app.route("/api/analytics/ai-performance", methods=["GET"])
@login_required
def api_ai_performance():
    """
    Returns AI Performance KPIs and time-series history.
    Query param: ?range=7d | 30d | all (default: all)
    """
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    date_range = request.args.get("range", "all").lower()
    if date_range not in ["7d", "30d", "all"]:
        date_range = "all"

    kpis = get_ai_performance_kpis(user_id=user_id, role=role, date_range=date_range)
    time_series = get_ai_performance_over_time(user_id=user_id, role=role, date_range=date_range)

    return jsonify({
        "success": True,
        "kpis": kpis,
        "time_series": time_series
    })


@app.route("/api/analytics/category-performance", methods=["GET"])
@login_required
def api_category_performance():
    """
    Returns category-wise auto-resolution, escalation rates and ticket counts.
    """
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    categories = get_category_ai_performance(user_id=user_id, role=role)
    return jsonify({
        "success": True,
        "categories": categories
    })


@app.route("/api/analytics/agent-performance", methods=["GET"])
@login_required
def api_agent_performance():
    """
    Returns stage scores (Diagnosis, Retrieval, Completeness, Final) and bottleneck identification.
    """
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    stages = get_agent_stage_performance(user_id=user_id, role=role)
    return jsonify({
        "success": True,
        "agent_performance": stages
    })


@app.route("/api/analytics/decision-distribution", methods=["GET"])
@login_required
def api_decision_distribution():
    """
    Returns ticket decision distribution comparing auto-resolved, escalated, and unprocessed tickets.
    """
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    kpis = get_ai_performance_kpis(user_id=user_id, role=role, date_range="all")
    return jsonify({
        "success": True,
        "total_tickets": kpis["total_tickets"],
        "total_processed": kpis["total_processed"],
        "unprocessed_count": kpis["unprocessed_count"],
        "auto_resolve_count": kpis["auto_resolve_count"],
        "escalation_count": kpis["escalation_count"],
        "auto_resolve_rate": kpis["auto_resolve_rate"],
        "escalation_rate": kpis["escalation_rate"]
    })


@app.route("/api/analytics/confidence-distribution", methods=["GET"])
@login_required
def api_confidence_distribution():
    """
    Returns distribution of processed tickets across confidence score bands (<40%, 40-69.99%, 70-100%).
    """
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    dist = get_ai_confidence_distribution(user_id=user_id, role=role)
    return jsonify({
        "success": True,
        "confidence_distribution": dist
    })


@app.route("/api/analytics/insights", methods=["GET"])
@login_required
def api_ai_insights():
    """
    Returns factual, database-measured trend and bottleneck insights.
    """
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    insights_data = get_ai_performance_insights(user_id=user_id, role=role)
    return jsonify({
        "success": True,
        "insights": insights_data
    })


@app.route("/api/analytics/evaluation-report", methods=["GET"])
@login_required
def api_evaluation_report():
    """
    Runs or returns standardized evaluation benchmark report with accuracy, precision, recall, and F1 metrics.
    """
    try:
        from evaluate_ai import run_evaluation
        report = run_evaluation()
        return jsonify({
            "success": True,
            "report": report
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# ESCALATED TICKETS PAGE
# ==========================================
@app.route("/escalated-tickets", endpoint="escalated_tickets_view")
@app.route("/escalated-tickets/view", endpoint="escalated_tickets")
@login_required
def escalated_tickets_view():
    """Displays tickets where final AI decision is ESCALATE."""
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    ticket_id = request.args.get("ticket_id")
    search_query = request.args.get("q", "").strip()

    escalated_items = get_all_tickets(
        user_id=user_id,
        role=role,
        resolution_status="ESCALATE",
        search=search_query
    )

    selected_ticket = None
    latest_run = None
    agent_runs = []

    if ticket_id:
        ticket = get_ticket_by_id(ticket_id)
        if ticket:
            if role == "passenger" and ticket["passenger_id"] and ticket["passenger_id"] != user_id:
                flash("Access denied. You are not authorized to view this ticket.", "danger")
                return redirect(url_for("escalated_tickets_view"))
            selected_ticket = ticket
            agent_runs = get_agent_runs_for_ticket(ticket_id)
            latest_run = agent_runs[0] if agent_runs else None
        else:
            flash(f"Ticket {ticket_id} not found.", "danger")

    return render_template(
        "escalated_tickets.html",
        tickets=escalated_items,
        selected_ticket=selected_ticket,
        latest_run=latest_run,
        agent_runs=agent_runs,
        search_query=search_query
    )


@app.context_processor
def inject_jira_globals():
    cfg = get_jira_config()
    return {
        "jira_is_configured": cfg.get("is_configured", False),
        "jira_project_key": cfg.get("project_key", "SUP")
    }


@app.route("/tickets/<ticket_id>/create-jira", methods=["POST"], endpoint="create_jira_sync_route")
@app.route("/tickets/<ticket_id>/retry-jira", methods=["POST"], endpoint="retry_jira_sync")
@login_required
def retry_jira_sync(ticket_id):
    """Creates or retries Jira synchronization for an escalated passenger ticket."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash(f"Ticket {ticket_id} not found.", "danger")
        return redirect(url_for("escalated_tickets_view"))

    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    if role == "passenger" and ticket["passenger_id"] and ticket["passenger_id"] != user_id:
        flash("Access denied. You are not authorized to manage this ticket.", "danger")
        return redirect(url_for("escalated_tickets_view"))

    # If already created, avoid duplicate Jira issue creation
    if ticket["jira_issue_key"] and (ticket["jira_sync_status"] or "").lower() == "created":
        flash(f"Ticket {ticket_id} is already linked to Jira issue {ticket['jira_issue_key']}.", "info")
        referrer = request.referrer
        if referrer and ("escalated-tickets" in referrer or "tickets" in referrer):
            return redirect(referrer)
        return redirect(url_for("escalated_tickets_view", ticket_id=ticket_id))

    escalation_payload = {
        "escalation_reason": ticket["escalation_reason"] or "Manual support escalation sync.",
        "final_confidence": ticket["final_confidence"] or 0.495,
        "threshold": 0.70,
        "retrieved_kb_id": ticket["retrieved_kb_id"],
        "retrieval_similarity": ticket["retrieval_similarity"],
        "resolution_text": ticket["resolution_text"]
    }

    jira_res = create_jira_issue(
        ticket_data=dict(ticket),
        escalation_payload=escalation_payload,
        existing_issue_key=ticket["jira_issue_key"],
        existing_issue_url=ticket["jira_issue_url"]
    )

    update_ticket_jira_info(ticket_id, jira_res)

    if jira_res.get("jira_created"):
        flash(f"Jira sync successful! Created issue {jira_res.get('issue_key')}.", "success")
    elif (jira_res.get("status") or "").lower() in ["not configured", "not_configured"]:
        flash(f"Jira integration is not configured in server environment: {jira_res.get('message')}", "warning")
    else:
        flash(f"Jira sync failed: {jira_res.get('last_error') or jira_res.get('message')}", "danger")

    referrer = request.referrer
    if referrer and ("escalated-tickets" in referrer or "tickets" in referrer):
        return redirect(referrer)
    return redirect(url_for("escalated_tickets_view", ticket_id=ticket_id))


@app.route("/api/tickets/<ticket_id>/jira", methods=["POST"])
def api_create_or_sync_jira(ticket_id):
    """
    Protected JSON API endpoint to create/sync Jira issue for an escalated ticket.
    - Authenticates current user
    - Verifies ticket exists
    - Verifies ticket belongs to escalated workflow (confidence < 0.70 / ESCALATE)
    - Performs duplicate protection if Jira key already exists
    - Calls existing Jira service and persists result
    - Returns safe JSON fields without sensitive credentials
    """
    user = get_current_user()
    if not user:
        return jsonify({
            "success": False,
            "error": "Authentication required. Please log in."
        }), 401

    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({
            "success": False,
            "error": f"Ticket {ticket_id} not found."
        }), 404

    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None
    if role == "passenger" and ticket["passenger_id"] and ticket["passenger_id"] != user_id:
        return jsonify({
            "success": False,
            "error": "Access denied. You are not authorized to manage this ticket."
        }), 403

    # Decision threshold verification: confidence >= 0.70 is AUTO_RESOLVE, no Jira
    final_conf = ticket["final_confidence"]
    if ticket["ai_resolution_status"] == "AUTO_RESOLVE" or (final_conf is not None and final_conf >= 0.70):
        return jsonify({
            "success": False,
            "error": f"Ticket {ticket_id} has final confidence >= 0.70 (AUTO_RESOLVE). Jira tickets are only created for ESCALATED tickets."
        }), 400

    # Duplicate protection check
    if ticket["jira_issue_key"] and (ticket["jira_sync_status"] or "").lower() == "created":
        return jsonify({
            "success": True,
            "status": "CREATED",
            "jira_issue_key": ticket["jira_issue_key"],
            "jira_issue_url": ticket["jira_issue_url"],
            "message": f"Reused existing Jira escalation issue {ticket['jira_issue_key']}."
        }), 200

    escalation_payload = {
        "escalation_reason": ticket["escalation_reason"] or "Manual support escalation sync.",
        "final_confidence": ticket["final_confidence"] or 0.495,
        "threshold": 0.70,
        "retrieved_kb_id": ticket["retrieved_kb_id"],
        "retrieval_similarity": ticket["retrieval_similarity"],
        "resolution_text": ticket["resolution_text"]
    }

    jira_res = create_jira_issue(
        ticket_data=dict(ticket),
        escalation_payload=escalation_payload,
        existing_issue_key=ticket["jira_issue_key"],
        existing_issue_url=ticket["jira_issue_url"]
    )

    update_ticket_jira_info(ticket_id, jira_res)

    if jira_res.get("jira_created"):
        return jsonify({
            "success": True,
            "status": "CREATED",
            "jira_issue_key": jira_res.get("issue_key"),
            "jira_issue_url": jira_res.get("issue_url")
        }), 200
    elif (jira_res.get("status") or "").lower() in ["not configured", "not_configured"]:
        return jsonify({
            "success": False,
            "status": "NOT_CONFIGURED",
            "message": "Jira credentials are not configured in the server environment."
        }), 200
    else:
        return jsonify({
            "success": False,
            "status": "FAILED",
            "error": jira_res.get("last_error") or jira_res.get("message") or "Jira issue creation failed."
        }), 200




# ==========================================
# PASSENGER PROFILE
# ==========================================
@app.route("/profile", endpoint="profile_view")
@app.route("/profile/view", endpoint="profile")
@login_required
def profile_view():
    """Passenger Profile and statistics view."""
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    stats = get_ticket_stats(user_id=user_id, role=role)
    user_tickets = get_all_tickets(user_id=user_id, role=role)[:5]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        tickets=user_tickets
    )


# ==========================================
# KNOWLEDGE BASE BROWSER (PUBLIC & AUTHENTICATED)
# ==========================================
@app.route("/knowledge-base", endpoint="knowledge_base_view")
@app.route("/knowledge-base/view", endpoint="knowledge_base")
@app.route("/knowledge_base", endpoint="knowledge_base_alt")
def knowledge_base_view():
    articles = load_knowledge_base()
    total_articles_count = len(articles)

    selected_cluster = request.args.get("cluster", "All")
    search = request.args.get("q", "").strip().lower()
    page = int(request.args.get("page", 1))
    per_page = 15

    filtered = articles
    if selected_cluster != "All":
        filtered = [a for a in filtered if a.get("cluster", "").upper() == selected_cluster.upper()]

    if search:
        filtered = [
            a for a in filtered
            if search in a["title"].lower() or search in a["content"].lower() or any(search in kw.lower() for kw in a.get("keywords", []))
        ]

    total_filtered = len(filtered)
    total_pages = max(1, math.ceil(total_filtered / per_page))
    page = min(max(1, page), total_pages)
    start_idx = (page - 1) * per_page
    paginated_articles = filtered[start_idx:start_idx + per_page]

    clusters = [
        "FLIGHTS",
        "CHECK-IN & BOARDING",
        "BAGGAGE",
        "AIRPORT FACILITIES",
        "SHOPPING & SERVICES",
        "BOOKING & PAYMENT",
        "PASSENGER ASSISTANCE"
    ]

    return render_template(
        "knowledge_base.html",
        articles=paginated_articles,
        clusters=clusters,
        selected_cluster=selected_cluster,
        search=search,
        total_count=total_articles_count,
        filtered_count=total_filtered,
        page=page,
        total_pages=total_pages
    )


# ==========================================
# SEED TEST SAMPLES (8 DOMAIN TICKETS)
# ==========================================
@app.route("/seed-samples", methods=["POST"])
@login_required
def seed_samples():
    """Seeds realistic passenger test tickets across various airport domains."""
    user = get_current_user()
    p_id = user["id"] if user else None
    p_name = user["full_name"] if user else "Alex Morgan"
    p_email = user["email"] if user else "alex.morgan@aeroassist.ai"

    sample_tickets = [
        {
            "title": "My checked baggage has not arrived at baggage carousel",
            "description": "Landed from flight AA402 from London Heathrow. My black Samsonite suitcase is missing from carousel 4. Need to file a Property Irregularity Report.",
            "category": "Baggage",
            "flight_number": "AA402",
            "booking_ref": "LHR992",
            "airport": "JFK",
            "travel_date": date.today().isoformat()
        },
        {
            "title": "Unable to complete web check-in online getting system error",
            "description": "Attempting online check-in for flight BA189 departing tomorrow morning. Web portal says booking requires airport verification.",
            "category": "Check-in & Boarding",
            "flight_number": "BA189",
            "booking_ref": "BAK712",
            "airport": "LHR",
            "travel_date": date.today().isoformat()
        },
        {
            "title": "Need wheelchair assistance for elderly passenger from curb to gate",
            "description": "Traveling with my 78-year-old mother who cannot walk long distances. Requesting WCHR electric wheelchair buggy service from Entrance 2 to Gate B12.",
            "category": "Passenger Assistance",
            "flight_number": "EK203",
            "booking_ref": "DXB881",
            "airport": "DXB",
            "travel_date": date.today().isoformat()
        },
        {
            "title": "Flight was cancelled due to weather need rescheduling guidance",
            "description": "My flight DL901 was cancelled due to heavy fog. What are my options for free rebooking on the next flight or requesting an open voucher?",
            "category": "Delays & Cancellations",
            "flight_number": "DL901",
            "booking_ref": "DLX410",
            "airport": "ORD",
            "travel_date": date.today().isoformat()
        },
        {
            "title": "Payment succeeded but booking confirmation was not received",
            "description": "Credit card was charged $450 for booking reference but confirmation email and e-ticket number have not arrived in my inbox.",
            "category": "Booking & Confirmation",
            "flight_number": "LH450",
            "booking_ref": "LH7721",
            "airport": "FRA",
            "travel_date": date.today().isoformat()
        },
        {
            "title": "Where can I find information about airport parking options and fees?",
            "description": "Looking for long-term economy car parking rates for 5 days near Terminal 2 with shuttle bus service.",
            "category": "Airport Facilities",
            "flight_number": "UA210",
            "booking_ref": "UA9012",
            "airport": "SFO",
            "travel_date": date.today().isoformat()
        },
        {
            "title": "Suitcase handle and wheel cracked broken during baggage handling",
            "description": "Retrieved my hard-shell suitcase and found one wheel broken off and side cracked. Need damage inspection report DIR.",
            "category": "Baggage",
            "flight_number": "SQ321",
            "booking_ref": "SIN554",
            "airport": "SIN",
            "travel_date": date.today().isoformat()
        },
        {
            "title": "Complex international customs animal quarantine permit query",
            "description": "Transporting exotic pedigree falcon with customized international CITES treaty paperwork requiring rare veterinary border clearance.",
            "category": "General Support",
            "flight_number": "QR102",
            "booking_ref": "DOH302",
            "airport": "DOH",
            "travel_date": date.today().isoformat()
        }
    ]

    classifier = get_classifier()
    created_ids = []

    for t in sample_tickets:
        cls_res = classifier.classify(t["title"], t["description"])
        pred_cat = cls_res["predicted_category"]
        conf = cls_res["confidence"]
        prio = calculate_priority(t["title"], t["description"], t["category"], t["travel_date"])
        sev = calculate_severity(t["category"], prio, t["description"])

        t_data = {
            "passenger_id": p_id,
            "passenger_name": p_name,
            "passenger_email": p_email,
            "title": t["title"],
            "description": t["description"],
            "category": t["category"],
            "predicted_category": pred_cat,
            "classification_confidence": conf,
            "priority": prio,
            "severity": sev,
            "flight_number": t.get("flight_number"),
            "booking_ref": t.get("booking_ref"),
            "airport": t.get("airport"),
            "travel_date": t.get("travel_date")
        }
        tkt_id = create_ticket(t_data)
        created_ids.append(tkt_id)

    flash(f"Successfully generated {len(created_ids)} domain test tickets ({', '.join(created_ids[:3])}...)!", "success")
    return redirect(url_for("tickets_list"))


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    print(f"[*] AeroAssist AI starting on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
