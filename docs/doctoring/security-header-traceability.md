# Security header traceability

## 2026-08-20 — Permissions Policy and legacy XSS auditor

### Decision

NewsDOM keeps the restrictive `Permissions-Policy` value
`geolocation=(), camera=(), microphone=()` and explicitly sends
`X-XSS-Protection: 0`.

The empty allowlists are an intentional least-privilege boundary for browser
features that this JSON API does not require. The current W3C Permissions Policy
specification defines an empty origin list as disabling the named feature for the
document and its descendants. The legacy `X-XSS-Protection` auditor is not used
as an XSS control: OWASP recommends omitting the header or explicitly setting it
to `0`, because legacy auditor behavior can introduce vulnerabilities. NewsDOM's
existing restrictive Content Security Policy remains the browser-side
XSS defense-in-depth control.

### Verification contract

`tests/test_parse_endpoint_success.py` exercises a successful `/parse` response
and requires both the feature-denial policy and `X-XSS-Protection: 0`. Changes to
these values therefore require an explicit standards/security decision rather
than silent header drift.

### References

OWASP Foundation. (n.d.). *HTTP security response headers cheat sheet*. OWASP
Cheat Sheet Series. Retrieved August 20, 2026, from
https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html

World Wide Web Consortium. (2025, October 6). *Permissions Policy* (W3C Working
Draft). https://www.w3.org/TR/permissions-policy/
