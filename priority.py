"""
AeroAssist AI - Ticket Priority Engine
Calculates passenger ticket priority based on domain rules and urgency signals.
"""
from datetime import datetime, date

PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]

def calculate_priority(title: str, description: str, category: str, travel_date: str = None) -> str:
    """
    Computes priority based on domain-specific rules:
    - Critical: Immediate travel disruption (boarding now, missed flight, emergency assistance, stranded passenger)
    - High: Near-term travel disruption (flight delay today/tomorrow, lost baggage PIR needed, payment failure on check-in)
    - Medium: Routine flight inquiries, luggage allowances, lounge queries, schedule updates
    - Low: General feedback, duty free inquiries, long-term parking, VAT refund info
    """
    text = f"{title} {description}".lower()

    # Rule 1: Critical urgency keywords
    critical_signals = [
        "emergency", "medical", "stranded", "gate closing", "missed connection",
        "denied boarding", "stuck at airport", "wheelchair missing", "immobile",
        "flight departing now", "boarded wrong", "passport stolen"
    ]
    if any(sig in text for sig in critical_signals):
        return "Critical"

    # Rule 2: Travel date proximity (if today or tomorrow)
    if travel_date:
        try:
            t_date = datetime.strptime(travel_date, "%Y-%m-%d").date()
            days_diff = (t_date - date.today()).days
            if days_diff <= 0 and ("delay" in text or "cancel" in text or "check-in" in text or "baggage" in text):
                return "Critical"
            elif 0 <= days_diff <= 2:
                return "High"
        except Exception:
            pass

    # Rule 3: High urgency domain keywords
    high_signals = [
        "lost baggage", "delayed baggage", "cancelled flight", "flight cancelled",
        "payment failed", "charged twice", "booking not confirmed", "web check-in failed",
        "wheelchair assistance", "special assistance", "unaccompanied minor"
    ]
    if any(sig in text for sig in high_signals):
        return "High"

    # Rule 4: Category-based baseline
    if category in ["Delays & Cancellations", "Passenger Assistance"]:
        return "High"
    elif category in ["Baggage", "Check-in & Boarding", "Refunds & Payments", "Booking & Confirmation"]:
        return "Medium"
    elif category in ["Airport Facilities", "Shopping & Services", "General Support"]:
        return "Low"

    return "Medium"
