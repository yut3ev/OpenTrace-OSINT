# Threat Model

## Assets
- Investigation targets and findings
- API keys for optional integrations
- Stored reports and SQLite database
- Service availability and source reputation

## Threats and mitigations
- **SSRF**: no arbitrary URL input; source URLs built from fixed templates and validated domains.
- **XSS**: escape all target/source values in the UI and HTML exports; use safe DOM rendering.
- **CSV formula injection**: prefix dangerous spreadsheet cells.
- **Denial of service**: input limits, global/per-host concurrency, timeouts, request budgets, maximum runtime.
- **Secret leakage**: `.env` ignored, `.env.example` placeholders only, redact secrets from logs and error messages.
- **Unauthorized access**: local-only default. Public deployment requires authentication, authorization and rate limiting.
- **Privacy over-collection**: collect minimum data, configurable retention, delete endpoint, no covert enrichment.
- **False attribution**: label candidates, preserve evidence and avoid treating name similarity as identity proof.
- **Malicious source responses**: treat remote text as untrusted data; limit response sizes and parse defensively.

## Deployment rule
Bind development server to `127.0.0.1` by default. If binding to `0.0.0.0`, show a warning and require the operator to configure authentication and rate limiting before production exposure.
