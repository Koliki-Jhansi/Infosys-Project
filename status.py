"""
AeroAssist AI - Ticket Status Manager
Defines valid lifecycle statuses and transition validation.
"""

TICKET_STATUSES = ["Open", "In Progress", "Resolved", "Escalated"]

ALLOWED_TRANSITIONS = {
    "Open": ["In Progress", "Resolved", "Escalated"],
    "In Progress": ["Resolved", "Escalated", "Open"],
    "Resolved": ["Open", "In Progress"],
    "Escalated": ["In Progress", "Resolved", "Open"]
}

def is_valid_status(status: str) -> bool:
    return status in TICKET_STATUSES

def can_transition(current_status: str, new_status: str) -> bool:
    if current_status == new_status:
        return True
    return new_status in ALLOWED_TRANSITIONS.get(current_status, [])
