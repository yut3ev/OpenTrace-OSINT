# OpenTrace OSINT — Security Architecture & Policy

This document describes the security architecture, threat model mitigations, and responsible vulnerability disclosure policy for OpenTrace OSINT.

---

## 1. Security Architecture Principles

OpenTrace is designed for defensive intelligence and digital footprint analysis. The platform enforces multi-layered defense-in-depth across authentication, data isolation, network egress, and data storage.

```
+-----------------------------------------------------------------------+
|                             Client Layer                              |
|          React 18 Dashboard / CLI / Headless Automation API           |
+-----------------------------------------------------------------------+
                                   | (HTTPS + Bearer JWT / X-API-Key)
                                   v
+-----------------------------------------------------------------------+
|                            Security Layer                             |
|  - CORS Filter (Allowed Origins)                                      |
|  - Anti-Brute-Force Rate Limiter (Sliding Window per IP/Key)          |
|  - Input Validation & Normalization (RFC 5321, E.164, Regex)          |
|  - Anti-SSRF Host Resolution Guard                                     |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                    Tenant Isolation & Authorization                   |
|  - User Ownership Verification (All Queries Scoped to user_id)        |
|  - Anti-Enumeration (404 Not Found on Unauthorized Investigation IDs) |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                        Data Persistence Layer                         |
|  - SQLite (WAL mode, Foreign Key Cascades, Versioned Migrations)      |
|  - Memory Storage (Thread-safe Async Locks, FIFO eviction)            |
+-----------------------------------------------------------------------+
```

---

## 2. Authentication & Credential Security

- **Password Hashing:** Passwords are never stored in plaintext. OpenTrace uses `bcrypt` with 12 salt rounds (NIST-compliant).
- **JWT Tokens:** Authenticated sessions issue signed JSON Web Tokens (`HS256`) containing `sub` (User UUID), `email`, and `role`, expiring in 7 days by default (`OPENTRACE_ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Token Secrets:** Secrets are loaded exclusively from server environment variables (`OPENTRACE_JWT_SECRET`). Development defaults raise warnings if not changed in production.
- **Password Resets:** Reset tokens are generated via cryptographically secure pseudo-random generators (`secrets.token_urlsafe(32)`). Tokens are stored in the database exclusively as `SHA-256` hashes with 1-hour expiration.

---

## 3. Strict User Ownership Isolation

To preserve researcher privacy and prevent cross-tenant data leakage:

1. **Scoped Database Access:** Every database query for investigations (`get`, `list`, `delete`, `export`, `events`, `retry`) checks `user_id == current_user["id"]`.
2. **Anti-Enumeration Protection:** When a user attempts to access or delete an investigation ID belonging to another user, the API responds with `404 Not Found` (never `403 Forbidden`). This prevents malicious actors from determining whether an investigation ID exists.
3. **Cascade Erasure:** Deleting an account immediately cascades to purge all owned investigations, findings, reset tokens, and audit events.

---

## 4. Anti-SSRF (Server-Side Request Forgery) Egress Controls

OpenTrace incorporates egress guards in `src/opentrace/core/ssrf.py` to ensure user inputs cannot coerce the server into scanning private internal networks:

- **Prohibited Schemes:** Only `http://` and `https://` are permitted. Schemes like `file://`, `gopher://`, `ftp://`, or `dict://` are rejected.
- **Private IP Blocking:** The server resolves target domains via DNS prior to connection and blocks:
  - Loopback (`127.0.0.0/8`, `::1`)
  - Private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`)
  - Link-local and cloud metadata addresses (`169.254.0.0/16`, `169.254.169.254`)
  - Prohibited internal hostnames (`localhost`, `metadata.google.internal`)

---

## 5. Rate Limiting & Abuse Prevention

- **Authentication Rate Limiting:** Login and registration endpoints are protected by `AuthRateLimiter` with an in-memory sliding window (maximum 10 attempts per minute per IP address).
- **Global Concurrency Caps:** Outbound scans are bounded by global (`OPENTRACE_MAX_CONCURRENCY`) and per-host (`OPENTRACE_PER_HOST_CONCURRENCY`) semaphores to protect third-party public services from overload.
- **Respectful Crawling:** All outgoing HTTP requests broadcast polite user-agent headers (`OPENTRACE_USER_AGENT`) and respect upstream rate-limit headers.

---

## 6. Vulnerability Disclosure Policy

If you discover a security vulnerability in OpenTrace, please report it privately:

- **Email:** `security@opentrace.dev` (or open a confidential security advisory on GitHub).
- **Response SLA:** Acknowledgement within 48 hours; status update and remediation plan within 5 business days.
- **Safe Harbor:** Security researchers acting in good faith who follow responsible disclosure practices will not face legal action.
