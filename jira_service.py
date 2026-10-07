"""
AeroAssist AI - Jira Escalation Service
Modular Jira integration for human support handoff during Agent 5 escalation.
Follows strict security practices: no hard-coded credentials, uses environment variables,
duplicate issue prevention, and reports genuine status without fabricating issue keys.
"""
import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


def build_jira_description(ticket_data: Dict[str, Any], escalation_payload: Dict[str, Any]) -> str:
    """Builds structured plain-text description containing original ticket details and AI trace context."""
    ticket_id = ticket_data.get("ticket_id", "N/A")
    title = ticket_data.get("title", "N/A")
    desc = ticket_data.get("description", "N/A")
    category = ticket_data.get("category", "N/A")
    priority = ticket_data.get("priority", "Medium")
    flight_str = ticket_data.get("flight_number") or "N/A"
    
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

    description_text = (
        "AeroAssist Human Support Escalation\n\n"
        f"Ticket ID: {ticket_id}\n"
        f"Ticket Title: {title}\n"
        f"Passenger Issue: {desc}\n"
        f"Category: {category}\n"
        f"Priority: {priority}\n"
        f"Flight Number: {flight_str}\n\n"
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
        "Human support action: Review context and proceed with manual resolution."
    )
    return description_text


def is_placeholder(val: str) -> bool:
    """Checks if an environment variable contains placeholder template text."""
    if not val:
        return True
    val_lower = val.lower().strip()
    placeholders = [
        "your-domain.atlassian.net",
        "your_jira_api_token_here",
        "your_jira_api_token",
        "your_token_here",
        "your-domain",
        "your_domain",
        "example.com",
        "your_email_here"
    ]
    return any(p in val_lower for p in placeholders)


def create_jira_issue(ticket_data: Dict[str, Any], escalation_payload: Dict[str, Any], existing_issue_key: Optional[str] = None, existing_issue_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Attempts to create a Jira issue for escalated passenger tickets.
    Includes duplicate protection if a Jira issue was already created for this ticket.
    Returns:
        {
            "status": "Created" | "Failed" | "Not Configured",
            "jira_created": bool,
            "issue_key": str or None,
            "issue_url": str or None,
            "message": str
        }
    """
    # Read exact required environment variables
    jira_url = (os.getenv("JIRA_URL") or "").strip()
    jira_email = (os.getenv("JIRA_USER_EMAIL") or os.getenv("JIRA_EMAIL") or "").strip()
    jira_token = (os.getenv("JIRA_API_TOKEN") or os.getenv("JIRA_TOKEN") or "").strip()
    project_key = (os.getenv("JIRA_PROJECT_KEY") or "AERO").strip()

    # Duplicate protection check: Reuse existing Jira issue if already created
    if existing_issue_key:
        url = existing_issue_url or (f"{jira_url.rstrip('/')}/browse/{existing_issue_key}" if jira_url else None)
        return {
            "status": "Created",
            "jira_created": True,
            "issue_key": existing_issue_key,
            "issue_url": url,
            "message": f"Reused existing Jira escalation issue {existing_issue_key}."
        }

    # Verify configuration and detect template placeholders
    if (
        not jira_url
        or not jira_token
        or not jira_email
        or is_placeholder(jira_url)
        or is_placeholder(jira_token)
        or is_placeholder(jira_email)
    ):
        return {
            "status": "Not Configured",
            "jira_created": False,
            "issue_key": None,
            "issue_url": None,
            "message": "Jira integration is not configured (missing or placeholder JIRA_URL / JIRA_USER_EMAIL / JIRA_API_TOKEN in environment)."
        }

    try:
        endpoint = f"{jira_url.rstrip('/')}/rest/api/2/issue"
        auth = (jira_email, jira_token)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        ticket_id = ticket_data.get("ticket_id", "TKT")
        title = ticket_data.get("title", "Support Request")
        summary = f"[AeroAssist] {ticket_id} - {title}"[:250]
        description_text = build_jira_description(ticket_data, escalation_payload)

        # Priority mapping
        priority_map = {
            "Critical": "Highest",
            "High": "High",
            "Medium": "Medium",
            "Low": "Low"
        }
        ticket_priority = ticket_data.get("priority", "Medium")
        jira_prio_name = priority_map.get(ticket_priority, "Medium")

        body = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description_text,
                "issuetype": {"name": "Task"},
                "priority": {"name": jira_prio_name}
            }
        }

        response = requests.post(endpoint, json=body, auth=auth, headers=headers, timeout=8)

        # If priority caused an error, retry without priority
        if response.status_code == 400 and "priority" in response.text.lower():
            del body["fields"]["priority"]
            response = requests.post(endpoint, json=body, auth=auth, headers=headers, timeout=8)

        if response.status_code in [200, 201]:
            data = response.json()
            key = data.get("key")
            issue_url = f"{jira_url.rstrip('/')}/browse/{key}"
            return {
                "status": "Created",
                "jira_created": True,
                "issue_key": key,
                "issue_url": issue_url,
                "message": f"Successfully created Jira ticket {key}"
            }
        else:
            # Safe sanitized error
            safe_error = response.text[:200].replace(jira_token, "[REDACTED]").replace(jira_email, "[REDACTED]")
            return {
                "status": "Failed",
                "jira_created": False,
                "issue_key": None,
                "issue_url": None,
                "message": f"Jira API HTTP {response.status_code}: {safe_error}"
            }

    except Exception as e:
        safe_err_str = str(e).replace(jira_token, "[REDACTED]") if jira_token else str(e)
        return {
            "status": "Failed",
            "jira_created": False,
            "issue_key": None,
            "issue_url": None,
            "message": f"Jira request exception: {safe_err_str}"
        }
