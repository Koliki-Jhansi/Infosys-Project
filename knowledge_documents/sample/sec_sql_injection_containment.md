# Incident Postmortem & Runbook: WAF SQL Injection Attack Mitigation

**Document ID:** SEC-RUNBOOK-019  
**Category:** Security  
**Service:** Web Application Firewall & API Gateway  
**Owner:** Security Operations Center (SecOps)  
**Version:** 1.2  

## 1. Incident Context & Threat Assessment
Attacker automated scanning detected injecting `UNION SELECT` and `OR 1=1` clauses into HTTP query parameters and headers, attempting database metadata extraction and unauthorized credential exfiltration.

Critical Policy:
- Any active exploit attempt or SQL injection pattern mandates immediate P1 Critical incident status and SecOps lead notification.
- Remediation requires human verification before applying permanent WAF blocklists or database connection drops.

## 2. Emergency Containment Steps
1. Isolate offending source IP subnets on Cloudflare / AWS WAF:
   Deploy an immediate block rule for the source IP range with a 24-hour TTL:
   `aws wafv2 update-ip-set --name "Emergency-Sec-Blocklist" --addresses "198.51.100.0/24"`
2. Revoke active JWT session tokens issued during the compromise window:
   Invalidate authentication session store: `redis-cli KEYS "user_session:*" | xargs redis-cli DEL`
3. Audit database transaction logs for data exfiltration:
   Query audit log for queries returning > 1,000 rows in under 50ms from unauthenticated API endpoints.

## 3. Permanent Code Remediation
1. Verify all backend queries utilize SQLAlchemy bound parameters or parameterized prepared statements. No f-string interpolation or concatenated SQL strings.
2. Ensure least-privilege database user permissions (application users must not have `SUPERUSER` or `pg_read_all_data` grants).

## 4. Verification and Rollback
- Verification: Re-run penetration test payloads through WAF to verify 403 Forbidden responses.
- Rollback: Remove IP blocks if false positives impact legitimate partner integrations.
