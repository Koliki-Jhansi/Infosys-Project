"""
AeroAssist AI - Database Layer
SQLite persistence for Tickets, Users, and Multi-Agent Audit Records.
"""
import sqlite3
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "aeroassist.db")


def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initializes the database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'passenger',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tickets Table (designed for Milestones 1, 2, and 3)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            passenger_id INTEGER,
            passenger_name TEXT NOT NULL,
            passenger_email TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            predicted_category TEXT,
            classification_confidence REAL,
            priority TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            flight_number TEXT,
            booking_ref TEXT,
            airport TEXT,
            travel_date TEXT,
            ai_resolution_status TEXT DEFAULT 'PENDING',
            final_confidence REAL,
            resolution_text TEXT,
            retrieved_kb_id TEXT,
            retrieval_similarity REAL,
            escalation_reason TEXT,
            jira_issue_key TEXT,
            jira_issue_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (passenger_id) REFERENCES users(id)
        )
    """)

    # Multi-Agent Run Audit Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            workflow_status TEXT NOT NULL,
            diagnosis_category TEXT,
            diagnosis_intent TEXT,
            diagnosis_confidence REAL,
            retrieval_found INTEGER,
            retrieval_kb_id TEXT,
            retrieval_similarity REAL,
            resolution_completeness REAL,
            final_confidence REAL,
            threshold REAL DEFAULT 0.70,
            outcome TEXT NOT NULL,
            jira_status TEXT,
            jira_issue_key TEXT,
            jira_issue_url TEXT,
            jira_message TEXT,
            email_status TEXT,
            raw_payload TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
        )
    """)

    # Dynamic migrations for existing databases
    cursor.execute("PRAGMA table_info(tickets)")
    ticket_cols = [row["name"] for row in cursor.fetchall()]
    if "jira_issue_key" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN jira_issue_key TEXT")
    if "jira_issue_url" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN jira_issue_url TEXT")

    cursor.execute("PRAGMA table_info(agent_runs)")
    run_cols = [row["name"] for row in cursor.fetchall()]
    if "jira_issue_key" not in run_cols:
        cursor.execute("ALTER TABLE agent_runs ADD COLUMN jira_issue_key TEXT")
    if "jira_issue_url" not in run_cols:
        cursor.execute("ALTER TABLE agent_runs ADD COLUMN jira_issue_url TEXT")
    if "jira_message" not in run_cols:
        cursor.execute("ALTER TABLE agent_runs ADD COLUMN jira_message TEXT")
    if "email_message" not in run_cols:
        cursor.execute("ALTER TABLE agent_runs ADD COLUMN email_message TEXT")

    conn.commit()

    # Create default demo users if they don't exist
    seed_default_users(conn)
    conn.close()


def seed_default_users(conn):
    """Seeds default demo passenger and agent accounts."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_users = [
            ("passenger", "passenger@aeroassist.ai", generate_password_hash("pass123"), "Alex Morgan", "passenger"),
            ("agent", "agent@aeroassist.ai", generate_password_hash("agent123"), "Sarah Chen (Airport Support Lead)", "agent"),
            ("admin", "admin@aeroassist.ai", generate_password_hash("admin123"), "AeroAssist Administrator", "admin")
        ]
        cursor.executemany(
            "INSERT INTO users (username, email, password_hash, full_name, role) VALUES (?, ?, ?, ?, ?)",
            demo_users
        )
        conn.commit()


# ==========================================
# USER OPERATIONS
# ==========================================

def get_user_by_username_or_email(identifier):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (identifier, identifier)
    )
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def create_user(username, email, password, full_name, role="passenger"):
    conn = get_db_connection()
    cursor = conn.cursor()
    pwd_hash = generate_password_hash(password)
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, full_name, role) VALUES (?, ?, ?, ?, ?)",
            (username, email, pwd_hash, full_name, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


# ==========================================
# TICKET OPERATIONS
# ==========================================

def get_next_ticket_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tickets ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    next_num = (row["id"] + 1) if row else 1
    return f"TKT-{next_num:03d}"


def create_ticket(ticket_data):
    """Inserts a new support ticket and returns the generated ticket_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    ticket_id = ticket_data.get("ticket_id") or get_next_ticket_id()
    
    cursor.execute("""
        INSERT INTO tickets (
            ticket_id, passenger_id, passenger_name, passenger_email,
            title, description, category, predicted_category, classification_confidence,
            priority, severity, status, flight_number, booking_ref, airport, travel_date,
            ai_resolution_status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (
        ticket_id,
        ticket_data.get("passenger_id"),
        ticket_data.get("passenger_name", "Anonymous Passenger"),
        ticket_data.get("passenger_email", "passenger@aeroassist.ai"),
        ticket_data.get("title"),
        ticket_data.get("description"),
        ticket_data.get("category"),
        ticket_data.get("predicted_category"),
        ticket_data.get("classification_confidence"),
        ticket_data.get("priority", "Medium"),
        ticket_data.get("severity", "Moderate"),
        ticket_data.get("status", "Open"),
        ticket_data.get("flight_number"),
        ticket_data.get("booking_ref"),
        ticket_data.get("airport"),
        ticket_data.get("travel_date")
    ))
    conn.commit()
    conn.close()
    return ticket_id


def get_ticket_by_id(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE ticket_id = ? OR id = ?", (ticket_id, ticket_id))
    ticket = cursor.fetchone()
    conn.close()
    return ticket


def get_all_tickets(category=None, status=None, search=None, user_id=None, role="admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if role == "passenger" and user_id:
        query += " AND passenger_id = ?"
        params.append(user_id)

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR ticket_id LIKE ? OR flight_number LIKE ? OR booking_ref LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard, wildcard])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    tickets = cursor.fetchall()
    conn.close()
    return tickets


def get_ticket_stats(user_id=None, role="admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    where_clause = ""
    params = []
    if role == "passenger" and user_id:
        where_clause = " WHERE passenger_id = ?"
        params.append(user_id)

    cursor.execute(f"SELECT COUNT(*) as total FROM tickets{where_clause}", params)
    total = cursor.fetchone()["total"]

    cursor.execute(f"SELECT COUNT(*) as cnt FROM tickets{where_clause} {'AND' if where_clause else 'WHERE'} status = 'Open'", params)
    open_cnt = cursor.fetchone()["cnt"]

    cursor.execute(f"SELECT COUNT(*) as cnt FROM tickets{where_clause} {'AND' if where_clause else 'WHERE'} status = 'In Progress'", params)
    in_progress_cnt = cursor.fetchone()["cnt"]

    cursor.execute(f"SELECT COUNT(*) as cnt FROM tickets{where_clause} {'AND' if where_clause else 'WHERE'} status = 'Resolved'", params)
    resolved_cnt = cursor.fetchone()["cnt"]

    cursor.execute(f"SELECT COUNT(*) as cnt FROM tickets{where_clause} {'AND' if where_clause else 'WHERE'} status = 'Escalated'", params)
    escalated_cnt = cursor.fetchone()["cnt"]

    conn.close()
    return {
        "total": total,
        "open": open_cnt,
        "in_progress": in_progress_cnt,
        "resolved": resolved_cnt,
        "escalated": escalated_cnt
    }


def get_existing_jira_for_ticket(ticket_id):
    """Retrieves existing Jira issue key and URL for a ticket to prevent duplicate creation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT jira_issue_key, jira_issue_url FROM tickets WHERE ticket_id = ?", (ticket_id,))
    row = cursor.fetchone()
    if row and row["jira_issue_key"]:
        conn.close()
        return {"issue_key": row["jira_issue_key"], "issue_url": row["jira_issue_url"]}
    
    # Fallback: check agent_runs
    cursor.execute("SELECT jira_issue_key, jira_issue_url FROM agent_runs WHERE ticket_id = ? AND jira_issue_key IS NOT NULL ORDER BY id DESC LIMIT 1", (ticket_id,))
    run_row = cursor.fetchone()
    conn.close()
    if run_row and run_row["jira_issue_key"]:
        return {"issue_key": run_row["jira_issue_key"], "issue_url": run_row["jira_issue_url"]}
    return None


def update_ticket_ai_results(ticket_id, ai_results):
    """Updates ticket record with multi-agent resolution or escalation outcome."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    status = "Resolved" if ai_results.get("workflow_status") == "AUTO_RESOLVE" else "Escalated"
    ai_status = ai_results.get("workflow_status", "AUTO_RESOLVE")
    
    jira_key = ai_results.get("jira_issue_key")
    jira_url = ai_results.get("jira_issue_url")
    jira_msg = ai_results.get("jira_message")
    
    cursor.execute("""
        UPDATE tickets SET
            status = ?,
            ai_resolution_status = ?,
            final_confidence = ?,
            resolution_text = ?,
            retrieved_kb_id = ?,
            retrieval_similarity = ?,
            escalation_reason = ?,
            jira_issue_key = COALESCE(?, jira_issue_key),
            jira_issue_url = COALESCE(?, jira_issue_url),
            updated_at = CURRENT_TIMESTAMP
        WHERE ticket_id = ?
    """, (
        status,
        ai_status,
        ai_results.get("final_confidence"),
        ai_results.get("resolution_text"),
        ai_results.get("retrieved_kb_id"),
        ai_results.get("retrieval_similarity"),
        ai_results.get("escalation_reason"),
        jira_key,
        jira_url,
        ticket_id
    ))
    
    email_status = ai_results.get("email_status", "Not Configured")
    email_msg = ai_results.get("email_message")
    
    # Insert audit record
    cursor.execute("""
        INSERT INTO agent_runs (
            ticket_id, workflow_status, diagnosis_category, diagnosis_intent,
            diagnosis_confidence, retrieval_found, retrieval_kb_id, retrieval_similarity,
            resolution_completeness, final_confidence, threshold, outcome,
            jira_status, jira_issue_key, jira_issue_url, jira_message, email_status, email_message, raw_payload, executed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        ticket_id,
        ai_status,
        ai_results.get("diagnosis_category"),
        ai_results.get("diagnosis_intent"),
        ai_results.get("diagnosis_confidence"),
        1 if ai_results.get("retrieval_found") else 0,
        ai_results.get("retrieved_kb_id"),
        ai_results.get("retrieval_similarity"),
        ai_results.get("resolution_completeness"),
        ai_results.get("final_confidence"),
        ai_results.get("threshold", 0.70),
        ai_status,
        ai_results.get("jira_status", "Not Configured"),
        jira_key,
        jira_url,
        jira_msg,
        email_status,
        email_msg,
        json.dumps(ai_results)
    ))

    conn.commit()
    conn.close()


def get_agent_runs_for_ticket(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agent_runs WHERE ticket_id = ? ORDER BY executed_at DESC", (ticket_id,))
    runs = cursor.fetchall()
    conn.close()
    return runs
