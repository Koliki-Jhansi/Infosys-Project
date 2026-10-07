"""
AeroAssist AI - Email Escalation Notification Service
Sends automated email notifications to airport human support desk when tickets are escalated.
Reports genuine status and does not fabricate sent emails when SMTP is unconfigured.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def build_email_body(ticket_data: dict, escalation_payload: dict) -> str:
    """Builds comprehensive plain-text body containing passenger details and full AI trace."""
    ticket_id = ticket_data.get("ticket_id", "N/A")
    title = ticket_data.get("title", "N/A")
    desc = ticket_data.get("description", "N/A")
    passenger_name = ticket_data.get("passenger_name", "Anonymous Passenger")
    passenger_email = ticket_data.get("passenger_email", "passenger@aeroassist.ai")
    category = ticket_data.get("category", "N/A")
    priority = ticket_data.get("priority", "Medium")
    severity = ticket_data.get("severity", "Moderate")
    flight_str = ticket_data.get("flight_number") or "N/A"
    booking_ref = ticket_data.get("booking_ref") or "N/A"
    airport = ticket_data.get("airport") or "N/A"
    travel_date = ticket_data.get("travel_date") or "N/A"

    diag_text = escalation_payload.get("diagnosis_text") or escalation_payload.get("diagnosis_intent") or "N/A"
    diag_conf = escalation_payload.get("diagnosis_confidence")
    diag_conf_str = f"{diag_conf * 100:.1f}%" if diag_conf is not None else "N/A"

    kb_id = escalation_payload.get("retrieved_kb_id") or "None"
    kb_title = escalation_payload.get("retrieved_kb_title")
    kb_str = f"{kb_id} - {kb_title}" if kb_title and kb_id != "None" else kb_id

    sim_score = escalation_payload.get("retrieval_similarity")
    sim_score_str = f"{sim_score * 100:.1f}%" if sim_score is not None else "N/A"

    gen_res = escalation_payload.get("resolution_text") or "N/A"
    res_comp = escalation_payload.get("resolution_completeness")
    res_comp_str = f"{res_comp * 100:.1f}%" if res_comp is not None else "N/A"

    final_conf = escalation_payload.get("final_confidence")
    final_conf_str = f"{final_conf * 100:.1f}%" if final_conf is not None else "N/A"

    thresh = escalation_payload.get("threshold", 0.70)
    thresh_str = f"{thresh * 100:.0f}%" if isinstance(thresh, (int, float)) else str(thresh)

    esc_reason = escalation_payload.get("escalation_reason") or "Confidence below required decision threshold."

    body = (
        "AeroAssist AI - Human Support Escalation Notice\n"
        "================================================\n"
        f"Ticket ID: {ticket_id}\n"
        f"Title: {title}\n"
        f"Passenger: {passenger_name} <{passenger_email}>\n"
        f"Category: {category} | Priority: {priority} | Severity: {severity}\n"
        f"Flight Number: {flight_str} | Booking PNR: {booking_ref}\n"
        f"Airport: {airport} | Travel Date: {travel_date}\n\n"
        "Passenger Issue:\n"
        f"{desc}\n\n"
        "AI PIPELINE CONTEXT\n"
        "-------------------\n"
        f"Diagnosis: {diag_text}\n"
        f"Diagnosis Confidence: {diag_conf_str}\n"
        f"Retrieved KB Article: {kb_str}\n"
        f"Retrieval Similarity: {sim_score_str}\n"
        f"Generated Resolution: {gen_res}\n"
        f"Resolution Completeness: {res_comp_str}\n"
        f"Final AI Confidence: {final_conf_str}\n"
        f"Decision Threshold: {thresh_str}\n"
        f"Escalation Reason: {esc_reason}\n\n"
        "Action Required: Human support agent review and take over passenger ticket."
    )
    return body


def send_escalation_email(ticket_data: dict, escalation_payload: dict) -> dict:
    """
    Attempts to dispatch an escalation alert email to the human support queue.
    Returns:
        {
            "status": "Sent" | "Failed" | "Not Configured",
            "recipient": str or None,
            "message": str
        }
    """
    smtp_host = (os.getenv("SMTP_HOST") or "").strip()
    smtp_port = (os.getenv("SMTP_PORT") or "587").strip()
    smtp_user = (os.getenv("SMTP_USER") or "").strip()
    smtp_pass = (os.getenv("SMTP_PASSWORD") or "").strip()
    support_recipient = (os.getenv("SUPPORT_ESCALATION_EMAIL") or "human-support@aeroassist.ai").strip()

    if not smtp_host or not smtp_user or not smtp_pass:
        return {
            "status": "Not Configured",
            "recipient": support_recipient,
            "message": "SMTP email service is not configured (missing SMTP_HOST / SMTP_USER / SMTP_PASSWORD in environment)."
        }

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = support_recipient
        msg["Subject"] = f"[ESCALATION REQUIRED] {ticket_data.get('ticket_id', 'TKT')} - {ticket_data.get('title', 'Passenger Support Request')}"

        body = build_email_body(ticket_data, escalation_payload)
        msg.attach(MIMEText(body, "plain"))

        port = int(smtp_port) if smtp_port.isdigit() else 587
        with smtplib.SMTP(smtp_host, port, timeout=5) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        return {
            "status": "Sent",
            "recipient": support_recipient,
            "message": f"Escalation notification email successfully sent to {support_recipient}."
        }
    except Exception as e:
        safe_err = str(e).replace(smtp_pass, "[REDACTED]") if smtp_pass else str(e)
        return {
            "status": "Failed",
            "recipient": support_recipient,
            "message": f"SMTP dispatch error: {safe_err}"
        }

