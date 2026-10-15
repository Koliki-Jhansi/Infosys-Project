from typing import Dict, Any, List, Tuple
import re

# Category keyword fingerprints to evaluate signal agreement
CATEGORY_FINGERPRINTS = {
    # IT Categories (preserved)
    "Network": ["dns", "vpn", "latency", "packet loss", "firewall", "router", "switch", "gateway", "subnet", "bandwidth", "ip address"],
    "Application": ["crash", "500 internal server error", "exception", "nullpointer", "stack trace", "api error", "frontend", "ui bug", "timeout"],
    "Database": ["postgres", "mysql", "mongodb", "deadlock", "query timeout", "connection pool", "slow query", "migration", "redis", "disk full"],
    "Authentication and access": ["login", "sso", "saml", "okta", "oauth", "password", "mfa", "2fa", "jwt", "unauthorized", "permission denied", "forbidden", "role"],
    "Infrastructure": ["kubernetes", "pod", "node", "cpu spike", "memory leak", "oom", "disk space", "aws", "azure", "docker", "ec2", "cluster"],
    "Hardware": ["printer", "laptop", "monitor", "docking station", "keyboard", "battery", "hard drive failure", "screen", "overheating"],
    "Deployment": ["ci/cd", "github actions", "gitlab", "pipeline", "release", "rollback", "build failure", "helm", "container registry"],
    "Security": ["vulnerability", "cve", "breach", "phishing", "malware", "ransomware", "unauthorized access", "exfiltration", "certificate expired", "tls"],
    # Airline Categories
    "Booking and Reservation": ["booking", "reservation", "pnr", "ticket", "name change", "modify flight", "infant", "itinerary", "date change", "flight change"],
    "Cancellation and Refund": ["cancel", "cancellation", "refund", "24-hour rule", "fare refund", "chargeback", "voucher", "voluntary", "tax refund", "credit"],
    "Flight Delay": ["delayed", "delay", "tarmac", "hours late", "schedule change", "waiting", "meal voucher", "duty of care", "compensation", "ec261", "late"],
    "Flight Cancellation": ["cancelled flight", "flight cancellation", "rebooking", "stranded", "involuntary", "alternate flight", "rescheduled", "cancelled"],
    "Baggage": ["baggage", "luggage", "lost bag", "delayed baggage", "pir", "carousel", "damaged bag", "allowance", "carry-on", "checked bag", "suitcase"],
    "Check-in and Boarding": ["check-in", "boarding", "boarding pass", "gate", "counter", "mobile check-in", "barcode", "cutoff time", "timatic", "passport"],
    "Seat Selection": ["seat", "seat selection", "exit row", "extra legroom", "aisle", "window", "upgrade", "business class", "seat pitch"],
    "Payment": ["payment", "credit card", "billing", "declined", "charge", "receipt", "currency", "invoice", "transaction"],
    "Special Assistance": ["wheelchair", "wchr", "wchs", "wchc", "disability", "unaccompanied minor", "umnr", "medif", "medical clearance", "oxygen", "service animal"],
    "Other": ["inquiry", "general", "feedback", "complaint", "contact"]
}

def calculate_explainable_confidence(
    reported_category: str,
    predicted_category: str,
    title: str,
    description: str,
    error_logs: str,
    affected_users: int,
    affected_service: str,
    has_valid_structured_output: bool = True
) -> Tuple[float, Dict[str, Any], List[str]]:
    """
    Computes an explainable estimated confidence score (0 - 100) based on 4 calibrated dimensions:
    1. Structured Output Validity (up to 15 pts)
    2. Input Completeness & Evidence (up to 30 pts)
    3. Signal Agreement (reported category vs description symptoms) (up to 35 pts)
    4. Diagnostic Consistency (service, error logs, specificity) (up to 20 pts)
    """
    missing_info = []
    breakdown = {}

    # Dimension 1: Structured Output Validity (15 max)
    struct_score = 15.0 if has_valid_structured_output else 0.0
    breakdown["structured_validity"] = {
        "score": struct_score,
        "max": 15.0,
        "detail": "Model provided fully compliant structured schema" if struct_score > 0 else "Schema parse degradation"
    }

    # Dimension 2: Input Completeness & Evidence (30 max)
    input_score = 0.0
    # Description depth
    desc_words = len(description.strip().split())
    if desc_words >= 40:
        input_score += 12.0
    elif desc_words >= 20:
        input_score += 8.0
    elif desc_words >= 10:
        input_score += 4.0
    else:
        input_score += 2.0
        missing_info.append("Detailed steps to reproduce or symptom narrative")

    # Affected service specific
    if affected_service and len(affected_service.strip()) > 2 and affected_service.lower() not in ["n/a", "none", "unknown", "all"]:
        input_score += 8.0
    else:
        missing_info.append("Specific affected service or application component")

    # Error logs / stack trace present
    if error_logs and len(error_logs.strip()) > 15:
        input_score += 10.0
    else:
        # Not strictly missing for some user requests, but adds evidence
        if "error" in description.lower() or "fail" in description.lower() or "500" in description:
            missing_info.append("Actual error logs or stack trace snippets")

    breakdown["input_completeness"] = {
        "score": input_score,
        "max": 30.0,
        "detail": f"Word count: {desc_words}, service specified: {bool(affected_service)}, logs present: {bool(error_logs and len(error_logs.strip()) > 15)}"
    }

    # Dimension 3: Signal Agreement (35 max)
    signal_score = 0.0
    combined_text = f"{title} {description} {error_logs}".lower()
    
    # Check if category matches predicted
    category_match = reported_category.lower() == predicted_category.lower()
    if category_match:
        signal_score += 15.0
    else:
        signal_score += 5.0  # slight agreement penalty

    # Keyword fingerprint matches for predicted category
    keywords = CATEGORY_FINGERPRINTS.get(predicted_category, [])
    matches = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', combined_text)]
    
    if len(matches) >= 3:
        signal_score += 20.0
    elif len(matches) == 2:
        signal_score += 15.0
    elif len(matches) == 1:
        signal_score += 10.0
    else:
        signal_score += 3.0
        missing_info.append(f"Domain-specific keywords matching category '{predicted_category}'")

    breakdown["signal_agreement"] = {
        "score": signal_score,
        "max": 35.0,
        "matched_keywords": matches,
        "category_match": category_match,
        "detail": f"Matched {len(matches)} category symptom fingerprints ({', '.join(matches[:3]) if matches else 'none'})"
    }

    # Dimension 4: Diagnostic Specificity & Consistency (20 max)
    diagnostic_score = 0.0
    # User count specified
    if affected_users > 0:
        diagnostic_score += 6.0
    else:
        missing_info.append("Count of affected users")

    # Title conciseness and relevance
    if len(title.strip()) >= 10:
        diagnostic_score += 7.0
    else:
        missing_info.append("Descriptive ticket summary")

    # Check for ambiguous or generic phrases
    ambiguous_terms = ["not working", "broken", "help", "issue", "bug", "it failed", "something wrong"]
    is_ambiguous = any(term == description.strip().lower() for term in ambiguous_terms)
    if not is_ambiguous and desc_words >= 15:
        diagnostic_score += 7.0
    else:
        missing_info.append("Specific context rather than generic 'not working' report")

    breakdown["diagnostic_consistency"] = {
        "score": diagnostic_score,
        "max": 20.0,
        "detail": "Clear symptom specificity and operational metrics"
    }

    total_confidence = round(struct_score + input_score + signal_score + diagnostic_score, 1)
    total_confidence = max(0.0, min(100.0, total_confidence))

    return total_confidence, breakdown, missing_info

def evaluate_ticket_confidence_policy(
    confidence_score: float,
    threshold: float,
    priority: str,
    criticality: str,
    category: str,
    detected_security_signals: List[str]
) -> Tuple[str, bool, str]:
    """
    Evaluates confidence score against threshold and enforces safety escalation rules.
    Returns: (status, requires_human_review, reason)
    """
    is_critical_or_p1 = (priority == "P1 Critical" or criticality == "Critical")
    is_security = (category.lower() == "security" or len(detected_security_signals) > 0)

    # Mandatory Human Review for Critical or Security incidents regardless of confidence
    if is_critical_or_p1 or is_security:
        reasons = []
        if is_critical_or_p1:
            reasons.append("P1 Critical severity requires mandatory engineer oversight")
        if is_security:
            reasons.append("Security incident requires security team authorization")
        return "NEEDS_REVIEW", True, "; ".join(reasons)

    # Standard confidence threshold rule
    if confidence_score < threshold:
        return "NEEDS_REVIEW", True, f"Estimated confidence score ({confidence_score}%) is below automation threshold ({threshold}%)."
    else:
        return "CLASSIFIED", False, f"Estimated confidence score ({confidence_score}%) satisfies automation threshold ({threshold}%)."
