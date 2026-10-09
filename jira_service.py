"""
AeroAssist AI - Jira Cloud REST API v3 Integration Service
Handles automated issue creation for escalated support tickets during Agent 5 execution.
Supports Atlassian Document Format (ADF), duplicate issue prevention, resilient error handling,
and secure credential redaction.
"""
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
from dotenv import load_dotenv

load_dotenv()


def build_jira_description(ticket_data: Dict[str, Any], escalation_payload: Dict[str, Any]) -> str:
    """Builds plain-text representation of the Jira escalation report."""
    ticket_id = ticket_data.get("ticket_id", "N/A")
    title = ticket_data.get("title", "N/A")
    desc = ticket_data.get("description", "N/A")
    category = ticket_data.get("category", "General Support")
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


def build_jira_adf_description(ticket_data: Dict[str, Any], escalation_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds structured Atlassian Document Format (ADF) description for Jira Cloud REST API v3.
    Includes full diagnostic and RAG context while omitting sensitive passenger data.
    """
    ticket_id = ticket_data.get("ticket_id", "N/A")
    title = ticket_data.get("title", "N/A")
    desc = ticket_data.get("description", "N/A")
    category = ticket_data.get("category", "General Support")
    priority = ticket_data.get("priority", "Medium")
    severity = ticket_data.get("severity", "Medium")
    flight_num = ticket_data.get("flight_number") or "N/A"
    airport = ticket_data.get("airport") or "N/A"

    diag_text = escalation_payload.get("diagnosis_text") or escalation_payload.get("diagnosis_intent") or "N/A"
    diag_conf = escalation_payload.get("diagnosis_confidence")
    diag_conf_str = f"{diag_conf * 100:.1f}%" if diag_conf is not None else "N/A"

    kb_id = escalation_payload.get("retrieved_kb_id") or "None"
    kb_title = escalation_payload.get("retrieved_kb_title")
    kb_str = f"{kb_id} — {kb_title}" if kb_title and kb_id != "None" else str(kb_id)

    sim_score = escalation_payload.get("retrieval_similarity")
    sim_score_str = f"{sim_score * 100:.1f}%" if sim_score is not None else "N/A"

    gen_res = escalation_payload.get("resolution_text") or "N/A"
    res_comp = escalation_payload.get("resolution_completeness")
    res_comp_str = f"{res_comp * 100:.1f}%" if res_comp is not None else "N/A"

    final_conf = escalation_payload.get("final_confidence")
    final_conf_str = f"{final_conf * 100:.1f}%" if final_conf is not None else "N/A"

    thresh = escalation_payload.get("threshold", 0.70)
    thresh_str = f"{thresh * 100:.0f}%" if isinstance(thresh, (int, float)) else str(thresh)

    esc_reason = escalation_payload.get("escalation_reason") or "Confidence score fell below quality threshold."

    adf_content = [
        {
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": "AeroAssist AI — Passenger Escalation Report"}]
        },
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "AeroAssist Ticket ID: ", "marks": [{"type": "strong"}]},
                {"type": "text", "text": str(ticket_id)},
                {"type": "text", "text": "   |   Category: ", "marks": [{"type": "strong"}]},
                {"type": "text", "text": str(category)},
                {"type": "text", "text": "   |   Priority: ", "marks": [{"type": "strong"}]},
                {"type": "text", "text": str(priority)},
                {"type": "text", "text": "   |   Severity: ", "marks": [{"type": "strong"}]},
                {"type": "text", "text": str(severity)}
            ]
        },
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Flight / Airport Context: ", "marks": [{"type": "strong"}]},
                {"type": "text", "text": f"Flight {flight_num} at {airport}"}
            ]
        },
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "Passenger Issue Summary"}]
        },
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": str(desc)}
            ]
        },
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "Five-Agent AI Pipeline Context"}]
        },
        {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "1. Diagnosis Agent: ", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": f"{diag_text} (Confidence: {diag_conf_str})"}
                            ]
                        }
                    ]
                },
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "2. Retrieval Agent: ", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": f"Top Knowledge Article {kb_str} (Similarity: {sim_score_str})"}
                            ]
                        }
                    ]
                },
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "3. Resolution Agent: ", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": f"Proposed draft: \"{gen_res[:200]}...\" (Completeness: {res_comp_str})"}
                            ]
                        }
                    ]
                },
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "4. Validation Agent: ", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": f"Final Weighted Confidence: {final_conf_str} (Required Threshold: {thresh_str}) — ESCALATE"}
                            ]
                        }
                    ]
                },
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "5. Escalation Rationale: ", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": str(esc_reason)}
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "Human Support Action Requested"}]
        },
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Please inspect the passenger inquiry and airline domain context above to complete manual resolution and reach out to the passenger."}
            ]
        }
    ]

    return {
        "version": 1,
        "type": "doc",
        "content": adf_content
    }


def is_placeholder(val: Optional[str]) -> bool:
    """Detects whether a configuration string contains placeholder template tokens."""
    if not val:
        return True
    val_lower = val.lower().strip()
    placeholders = [
        "your-domain.atlassian.net",
        "your-domain",
        "your_domain",
        "your-jira-email",
        "your_jira_email",
        "your-api-token",
        "your_api_token",
        "your_token_here",
        "example.com",
        "your_email_here"
    ]
    return any(p in val_lower for p in placeholders)


def sanitize_message(msg: str, tokens: List[Optional[str]]) -> str:
    """Redacts sensitive credentials and tokens from messages."""
    result = str(msg)
    for tok in tokens:
        if tok and len(tok) >= 4:
            result = result.replace(tok, "[REDACTED]")
    return result


def get_jira_config() -> Dict[str, Any]:
    """Reads Jira Cloud configuration from environment variables with backwards-compatible fallbacks."""
    base_url = (os.getenv("JIRA_BASE_URL") or os.getenv("JIRA_URL") or "").strip()
    email = (os.getenv("JIRA_EMAIL") or os.getenv("JIRA_USER_EMAIL") or "").strip()
    token = (os.getenv("JIRA_API_TOKEN") or os.getenv("JIRA_TOKEN") or "").strip()
    project_key = (os.getenv("JIRA_PROJECT_KEY") or "SUP").strip().upper()
    issue_type = (os.getenv("JIRA_ISSUE_TYPE") or "Task").strip()

    is_configured = (
        bool(base_url)
        and bool(email)
        and bool(token)
        and not is_placeholder(base_url)
        and not is_placeholder(email)
        and not is_placeholder(token)
    )

    return {
        "base_url": base_url,
        "email": email,
        "token": token,
        "project_key": project_key,
        "issue_type": issue_type,
        "is_configured": is_configured
    }


def create_jira_issue(
    ticket_data: Dict[str, Any],
    escalation_payload: Dict[str, Any],
    existing_issue_key: Optional[str] = None,
    existing_issue_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates an issue in Jira Cloud using REST API v3 with Atlassian Document Format (ADF).
    Guarantees duplicate prevention if an issue key was already recorded.
    
    Returns:
        {
            "status": "Created" | "Pending" | "Failed" | "Not Configured",
            "jira_created": bool,
            "issue_key": str or None,
            "issue_id": str or None,
            "issue_url": str or None,
            "sync_status": "Created" | "Pending" | "Failed" | "Not Configured",
            "last_error": str or None,
            "created_at": str or None,
            "message": str
        }
    """
    config = get_jira_config()
    jira_base_url = config["base_url"]
    jira_email = config["email"]
    jira_token = config["token"]
    project_key = config["project_key"]
    issue_type = config["issue_type"]

    # 1. Duplicate Protection: If an issue already exists for this ticket, reuse it
    if existing_issue_key:
        issue_url = existing_issue_url or (
            f"{jira_base_url.rstrip('/')}/browse/{existing_issue_key}" if jira_base_url else None
        )
        return {
            "status": "Created",
            "jira_created": True,
            "issue_key": existing_issue_key,
            "issue_id": None,
            "issue_url": issue_url,
            "sync_status": "Created",
            "last_error": None,
            "created_at": None,
            "message": f"Reused existing Jira escalation issue {existing_issue_key}."
        }

    # 2. Check if Jira integration credentials are configured
    if not config["is_configured"]:
        return {
            "status": "Not Configured",
            "jira_created": False,
            "issue_key": None,
            "issue_id": None,
            "issue_url": None,
            "sync_status": "Not Configured",
            "last_error": "Jira integration is not configured in server environment.",
            "created_at": None,
            "message": "Jira integration is not configured (missing or placeholder JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN)."
        }

    # 3. Prepare Jira Cloud REST API v3 Payload
    ticket_id = ticket_data.get("ticket_id", "TKT")
    title = ticket_data.get("title", "Support Request")
    summary = f"[AeroAssist Escalation] Ticket #{ticket_id} — {title}"[:250]

    adf_description = build_jira_adf_description(ticket_data, escalation_payload)

    # Priority mapping
    priority_map = {
        "Critical": "Highest",
        "High": "High",
        "Medium": "Medium",
        "Low": "Low"
    }
    ticket_priority = ticket_data.get("priority", "Medium")
    jira_priority_name = priority_map.get(ticket_priority, "Medium")

    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": adf_description,
            "issuetype": {"name": issue_type},
            "priority": {"name": jira_priority_name}
        }
    }

    endpoint = f"{jira_base_url.rstrip('/')}/rest/api/3/issue"
    auth = (jira_email, jira_token)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(
            endpoint,
            json=payload,
            auth=auth,
            headers=headers,
            timeout=10
        )

        # Handle project priority field mismatch: if priority caused error, retry without priority
        if response.status_code == 400 and "priority" in response.text.lower():
            del payload["fields"]["priority"]
            response = requests.post(
                endpoint,
                json=payload,
                auth=auth,
                headers=headers,
                timeout=10
            )

        if response.status_code in [200, 201]:
            resp_data = response.json()
            key = resp_data.get("key")
            issue_id = str(resp_data.get("id")) if resp_data.get("id") else None
            issue_url = f"{jira_base_url.rstrip('/')}/browse/{key}" if key else None
            now_str = datetime.now().isoformat()

            return {
                "status": "Created",
                "jira_created": True,
                "issue_key": key,
                "issue_id": issue_id,
                "issue_url": issue_url,
                "sync_status": "Created",
                "last_error": None,
                "created_at": now_str,
                "message": f"Successfully created Jira issue {key} in project {project_key}."
            }
        else:
            raw_err = response.text[:250]
            sanitized_err = sanitize_message(raw_err, [jira_token, jira_email])
            err_msg = f"Jira Cloud API HTTP {response.status_code}: {sanitized_err}"
            
            return {
                "status": "Failed",
                "jira_created": False,
                "issue_key": None,
                "issue_id": None,
                "issue_url": None,
                "sync_status": "Failed",
                "last_error": err_msg,
                "created_at": None,
                "message": err_msg
            }

    except requests.exceptions.Timeout:
        err_msg = "Jira API connection timed out (10s timeout exceeded)."
        return {
            "status": "Failed",
            "jira_created": False,
            "issue_key": None,
            "issue_id": None,
            "issue_url": None,
            "sync_status": "Failed",
            "last_error": err_msg,
            "created_at": None,
            "message": err_msg
        }

    except requests.exceptions.ConnectionError:
        err_msg = "Could not connect to Jira Cloud endpoint (network connection error)."
        return {
            "status": "Failed",
            "jira_created": False,
            "issue_key": None,
            "issue_id": None,
            "issue_url": None,
            "sync_status": "Failed",
            "last_error": err_msg,
            "created_at": None,
            "message": err_msg
        }

    except Exception as e:
        sanitized_err = sanitize_message(str(e), [jira_token, jira_email])
        err_msg = f"Jira request exception: {sanitized_err}"
        return {
            "status": "Failed",
            "jira_created": False,
            "issue_key": None,
            "issue_id": None,
            "issue_url": None,
            "sync_status": "Failed",
            "last_error": err_msg,
            "created_at": None,
            "message": err_msg
        }
