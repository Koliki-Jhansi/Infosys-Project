"""
AeroAssist AI - Ticket Severity Engine
Determines the operational severity and passenger impact level.
"""

SEVERITY_LEVELS = ["Minor", "Moderate", "Major", "Critical"]

def calculate_severity(category: str, priority: str, description: str = "") -> str:
    """
    Evaluates passenger operational impact:
    - Critical: Prevents passenger from traveling or severe accessibility blockade
    - Major: Significant travel disruption (missed bags, cancelled flight without rebooking, payment blockage)
    - Moderate: Standard functional impediment (online checkin error, refund delay, baggage allowance query)
    - Minor: Informational queries (lounges, food courts, parking, duty free)
    """
    text = description.lower()

    if priority == "Critical" or "unable to fly" in text or "stranded" in text:
        return "Critical"

    if priority == "High" or category in ["Delays & Cancellations", "Passenger Assistance"]:
        return "Major"

    if category in ["Baggage", "Check-in & Boarding", "Refunds & Payments", "Booking & Confirmation"]:
        return "Moderate"

    return "Minor"
