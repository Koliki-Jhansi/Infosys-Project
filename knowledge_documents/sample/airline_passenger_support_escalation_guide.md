# AeroAssist Airline Policy: Passenger Support Escalation & Governance Guide

## Document Overview
- **Document ID:** DOC-AIR-008
- **Category:** Other / Support Governance
- **Target Service:** Customer Relations & Duty Station Management
- **Threshold Policy:** 70% Confidence / Safety Boundary Standard

---

## 1. Automated Resolution vs. Human Escalation Criteria

AeroAssist AI automatically classifies, grounds, validates, and recommends resolutions for passenger inquiries. To safeguard flight safety, passenger rights, and airline commercial integrity, tickets are routed according to strict governance criteria:

### Criteria for Automatic AI Resolution:
- Ticket Classification Confidence $\ge 70\%$.
- RAG Knowledge Base Retrieval Relevance $\ge 50\%$.
- Validation Agent returns **PASS** (zero hallucinations, zero contradictions, complete policy backing).
- Inquiry involves standard informational assistance (baggage allowances, check-in cutoff times, rebooking rules, seating policies, flight schedule confirmation).

### Mandatory Criteria for Human Support Agent Escalation:
1. **Low Confidence Score:** Classification or grounding confidence $< 70\%$.
2. **Failed Validation:** Response failed validation due to missing policy citations, ambiguity, or unsupported claims.
3. **Financial / Monetary Decisions:**
   - Direct cash refund processing over $100 USD.
   - Statutory delay compensation claims (EU261 / DOT claims).
   - Lost baggage compensation settlements exceeding $250 USD.
4. **Safety & Sensitive Incident Alerts:**
   - Unaccompanied minor custody disputes or travel document anomalies.
   - Medical emergency or oxygen apparatus requests.
   - Denied boarding due to overbooking (involuntary bumps).
   - Inflight disruptive passenger reports or security interventions.
5. **Operational Disruptions:** Mass cancellations affecting $> 50$ passengers simultaneously.

---

## 2. Escalation Workflow Handover Protocol
When the Escalation Agent triggers human review:
1. Complete ticket summary, passenger details, PNR, and flight number are compiled into the escalation dossier.
2. The specific reason for escalation (e.g. *Low confidence score (62%)*, *Financial refund threshold exceeded*, *Medical MEDIF review required*) is tagged.
3. The ticket status transitions to `Escalated`.
4. Assigned Tier 2 Support Agent reviews AI diagnosis, retrieved knowledge chunks, and draft response, then approves, overrides, or contacts the passenger directly.
