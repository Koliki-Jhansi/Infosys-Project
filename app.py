"""
AeroAssist AI - Intelligent Airport & Airways Customer Support Platform
Main Flask Web Application
"""
import os
import json
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv

load_dotenv()

from database import (
    init_db, get_user_by_username_or_email, get_user_by_id, create_user,
    create_ticket, get_ticket_by_id, get_all_tickets, get_ticket_stats,
    update_ticket_ai_results, get_agent_runs_for_ticket, get_next_ticket_id
)
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


# ==========================================
# AUTHENTICATION ROUTES
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()

        # Handle quick demo login buttons
        demo_role = request.form.get("demo_login")
        if demo_role:
            if demo_role == "passenger":
                identifier, password = "passenger", "pass123"
            elif demo_role == "agent":
                identifier, password = "agent", "agent123"
            elif demo_role == "admin":
                identifier, password = "admin", "admin123"

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

        flash("Invalid username/email or password.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        full_name = request.form.get("full_name", "").strip()

        if not username or not email or not password or not full_name:
            flash("All fields are required.", "danger")
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
# DASHBOARD & TICKETS (MILESTONE 1)
# ==========================================
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    stats = get_ticket_stats(user_id=user_id, role=role)
    recent_tickets = get_all_tickets(user_id=user_id, role=role)[:6]

    return render_template("dashboard.html", stats=stats, tickets=recent_tickets)


@app.route("/tickets")
@login_required
def tickets_list():
    user = get_current_user()
    role = user["role"] if user else "passenger"
    user_id = user["id"] if user else None

    selected_category = request.args.get("category", "All")
    selected_status = request.args.get("status", "All")
    search_query = request.args.get("q", "").strip()

    ticket_items = get_all_tickets(
        category=selected_category,
        status=selected_status,
        search=search_query,
        user_id=user_id,
        role=role
    )

    return render_template(
        "tickets.html",
        tickets=ticket_items,
        selected_category=selected_category,
        selected_status=selected_status,
        search_query=search_query
    )


@app.route("/tickets/create", methods=["GET", "POST"])
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


@app.route("/tickets/<ticket_id>")
@login_required
def ticket_detail(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash(f"Ticket {ticket_id} not found.", "danger")
        return redirect(url_for("tickets_list"))

    agent_runs = get_agent_runs_for_ticket(ticket_id)

    # Compute Milestone 2 RAG preview for ticket details display
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
# MILESTONE 2: DEDICATED AI KNOWLEDGE RESOLUTION
# ==========================================
@app.route("/tickets/<ticket_id>/ai-resolution")
@login_required
def m2_ai_resolution_view(ticket_id):
    """Milestone 2 Dedicated Page: Airport Knowledge Resolution via TF-IDF + Cosine RAG."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash(f"Ticket {ticket_id} not found.", "danger")
        return redirect(url_for("tickets_list"))

    # Execute Milestone 2 RAG Pipeline
    rag_pipe = get_rag_pipeline()
    rag_result = rag_pipe.process_query(
        title=ticket["title"],
        description=ticket["description"],
        category=ticket["category"],
        metadata={"flight_number": ticket["flight_number"], "booking_ref": ticket["booking_ref"]}
    )

    return render_template(
        "m2_ai_resolution.html",
        ticket=ticket,
        rag_result=rag_result
    )


# ==========================================
# MILESTONE 3: DEDICATED MULTI-AGENT STUDIO
# ==========================================
@app.route("/tickets/<ticket_id>/multi-agent")
@app.route("/tickets/<ticket_id>/resolve")
@login_required
def multi_agent_studio_view(ticket_id):
    """Milestone 3 Dedicated Page: Five-Agent Sequential Aviation Resolution Studio."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash(f"Ticket {ticket_id} not found.", "danger")
        return redirect(url_for("tickets_list"))

    agent_runs = get_agent_runs_for_ticket(ticket_id)
    latest_run = agent_runs[0] if agent_runs else None

    return render_template(
        "multi_agent.html",
        ticket=ticket,
        latest_run=latest_run
    )


@app.route("/api/tickets/<ticket_id>/run-agents", methods=["POST"])
@login_required
def run_agents_api(ticket_id):
    """Executes the 5-agent sequential workflow and updates SQLite records."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"success": False, "error": "Ticket not found"}), 404

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
# KNOWLEDGE BASE BROWSER
# ==========================================
@app.route("/knowledge-base")
@login_required
def knowledge_base_view():
    articles = load_knowledge_base()
    selected_cluster = request.args.get("cluster", "All")
    search = request.args.get("q", "").strip().lower()

    filtered = articles
    if selected_cluster != "All":
        filtered = [a for a in filtered if a.get("cluster", "").upper() == selected_cluster.upper()]

    if search:
        filtered = [
            a for a in filtered
            if search in a["title"].lower() or search in a["content"].lower() or any(search in kw.lower() for kw in a.get("keywords", []))
        ]

    clusters = ["FLIGHTS", "CHECK-IN & BOARDING", "BAGGAGE", "AIRPORT FACILITIES", "SHOPPING & SERVICES", "BOOKING & PAYMENT", "PASSENGER ASSISTANCE"]
    return render_template("knowledge_base.html", articles=filtered, clusters=clusters, selected_cluster=selected_cluster, search=search)


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
