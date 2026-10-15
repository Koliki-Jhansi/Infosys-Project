# Runbook: SSO and SAML 2.0 Authentication Token Failure Resolution

**Document ID:** RUNBOOK-AUTH-008  
**Category:** Authentication and access  
**Service:** Okta SSO & SAML Identity Provider  
**Owner:** Identity & Access Management (IAM)  
**Version:** 2.0  

## 1. Overview
Users encounter `Invalid SAML Response: Signature verification failed` or `401 Unauthorized: AudienceRestriction mismatch` when attempting Single Sign-On.

Common Triggers:
- Identity Provider (IdP) X.509 signing certificate has expired or rotated without SP trust update.
- System clock skew between IdP and Service Provider exceeding the 120-second tolerance window.
- Missing email or employeeID attribute statements in Okta SAML assertion.

## 2. Diagnostic Steps
1. Capture raw SAML response using browser developer tools and decode from Base64:
   Inspect `<saml2:Conditions NotBefore="..." NotOnOrAfter="...">` and verify server timestamp alignment.
2. Check NTP daemon synchronization status on authentication servers:
   `chronyc tracking` or `ntpq -p`. Clock offset must be under 50 milliseconds.
3. Verify public key fingerprint of current IdP certificate against SP metadata configuration.

## 3. Remediation Procedure
1. Clock Drift Fix:
   Force immediate NTP sync: `systemctl restart chronyd && chronyc makestep`
2. IdP Certificate Rotation:
   Export current X.509 certificate from Okta Admin Console -> Applications -> SAML Setup -> View Setup Instructions.
   Upload the new certificate into the SP configuration portal and save.
3. Session Purge:
   Flush stale user sessions in Redis cache: `redis-cli DEL "saml_session_*"`

## 4. Verification and Rollback
- Verification: Perform incognito login flow and verify successful assertion exchange.
- Rollback: Keep previous signing certificate in fallback trust bundle during rolling rotation.
