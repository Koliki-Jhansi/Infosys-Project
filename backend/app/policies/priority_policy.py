from typing import Tuple, List
import re

SECURITY_KEYWORDS = [
    "cve", "vulnerability", "exploit", "breach", "unauthorized", "ransomware",
    "malware", "compromised", "exfiltration", "ddos", "sql injection", "xss",
    "privilege escalation", "credential leak", "phishing", "backdoor"
]

def detect_security_signals(text: str) -> List[str]:
    found = []
    lower = text.lower()
    for kw in SECURITY_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', lower):
            found.append(kw)
    return found

def calculate_priority_and_criticality(
    urgency: str,
    business_impact: str,
    environment: str,
    affected_users: int,
    category: str,
    title: str,
    description: str,
    error_logs: str = ""
) -> Tuple[str, str, List[str], str]:
    """
    Enforces deterministic priority and escalation matrix.
    Returns: (priority, criticality, detected_security_flags, escalation_reason)
    """
    combined_text = f"{title} {description} {error_logs}"
    sec_signals = detect_security_signals(combined_text)
    is_security_category = category.lower() == "security"
    
    # Base weight scoring
    # Urgency weights
    urgency_scores = {
        "Critical": 40,
        "High": 30,
        "Medium": 20,
        "Low": 10
    }
    # Business impact weights
    impact_scores = {
        "Extensive / Organization-wide": 40,
        "Significant / Department-wide": 30,
        "Moderate / Team or Group": 20,
        "Minor / Single user": 10
    }
    
    score = urgency_scores.get(urgency, 20) + impact_scores.get(business_impact, 20)
    
    # Environment boost: production failures carry significant escalation
    is_prod = environment.lower() == "production"
    if is_prod:
        score += 15
        
    # Affected users scaling
    if affected_users >= 500:
        score += 20
    elif affected_users >= 100:
        score += 15
    elif affected_users >= 20:
        score += 10
    elif affected_users >= 5:
        score += 5

    # Security escalation
    if sec_signals or is_security_category:
        score += 35
        
    escalation_reason = ""
    
    # Determine Priority and Criticality
    if sec_signals or (is_security_category and is_prod):
        priority = "P1 Critical"
        criticality = "Critical"
        escalation_reason = f"Security incident detected ({', '.join(sec_signals) if sec_signals else 'Security category in Production'}). Mandatory escalation."
    elif score >= 85:
        priority = "P1 Critical"
        criticality = "Critical"
        escalation_reason = f"Combined severity score {score} (Urgency: {urgency}, Impact: {business_impact}, Users: {affected_users}, Env: {environment})"
    elif score >= 65:
        priority = "P2 High"
        criticality = "High"
        escalation_reason = f"High operational impact score {score}"
    elif score >= 45:
        priority = "P3 Medium"
        criticality = "Medium"
        escalation_reason = "Standard operational priority"
    else:
        priority = "P4 Low"
        criticality = "Low"
        escalation_reason = "Low impact / single user request"
        
    return priority, criticality, sec_signals, escalation_reason
