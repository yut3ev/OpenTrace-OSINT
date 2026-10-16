# Module Development Guide

Every module must declare what it does and does not establish. Tests must use mocked responses by default.

## Username module
- Accept a normalized username and build URLs only from fixed, trusted templates.
- Do not accept user-supplied URLs in a username field.
- Validate characters and length before requests.
- Never follow arbitrary user-controlled URLs.
- Set connect/read/overall timeouts, redirects policy, bounded concurrency and per-host request budget.
- Interpret response codes conservatively; a 200 can still be a login page or soft-404, so test platform semantics.
- Return public profile URL and minimal public metadata only.
- Do not scrape private content or bypass defenses.

## Email modules
- Syntax and IDNA/domain normalization.
- MX DNS query with bounded lifetime and explicit timeout handling.
- No SMTP RCPT probing or account existence enumeration.
- No password, breach, or credential leak lookups.
- Optional external provider integrations require documented API, opt-in configuration and clear disclosure.

## Phone module
- Use libphonenumber-derived numbering metadata only.
- No carrier subscriber lookup, person lookup, precise geolocation or live status claims.
- Preserve user input only as long as necessary; redact logs.

## Test contract
For each module, cover: valid input, invalid input, success, not-found, throttled, forbidden, timeout, malformed response, and source-specific ambiguous behavior.
