# OpenTrace OSINT — Known Limitations & Operational Boundaries

OpenTrace OSINT is designed as an evidence-first, privacy-aware public intelligence tool. To preserve legal compliance, operator safety, and forensic integrity, the platform enforces strict boundaries.

---

## 1. Evidence Provenance vs. Identity Proof

> **Core Principle:** A profile match or digital signal is a lead, never proof of personal identity.

- **Username Collisions:** Common handles (e.g. `alex`, `john`, `dev`) are routinely claimed by different unrelated individuals across various platforms. OpenTrace emits `verification_status: "candidate"` for ambiguous matches.
- **Biographical Name Ambiguities:** Scholarly and biographical records (Wikipedia, DBLP, OpenAlex) frequently match multiple living individuals with identical names. Automatic merging is strictly prohibited.
- **Correlations:** Correlations established in graph edges denote observed co-occurrence or structural similarity, not definitive real-world person linkage.

---

## 2. Ethical, Legal & Platform-Policy Restrictions

OpenTrace explicitly refuses to implement invasive or unauthorized intrusion mechanisms:

- **No SMTP Mailbox Probing:** OpenTrace validates RFC 5321 syntax and queries DNS MX/TXT records. It does **not** connect to mail servers to probe recipient existence via `RCPT TO`, as this constitutes intrusive port scanning, triggers blacklisting, and violates provider Acceptable Use Policies.
- **No Password Breach Dump Scraping:** OpenTrace does not bundle or query illicit password databases, plaintext leak archives, or stolen credentials. Authorized breach lookups are supported exclusively through official partner APIs (e.g. HaveIBeenPwned API with explicit API key).
- **No CAPTCHA or Cloudflare Bypass:** If a target service challenges requests with Cloudflare Turnstile, reCAPTCHA, or browser fingerprints, OpenTrace classifies the source as `blocked` or `rate_limited`. It does not attempt automated solver bypasses or proxy rotation.
- **No Private Account Scraping or OTP Probing:** OpenTrace does not attempt account password recovery flows, SMS OTP triggers, or unauthenticated private account enumeration.

---

## 3. Platform Rate Limits & Network Throttling

When running unauthenticated lookups, public platforms impose strict quotas:

| Platform | Public Limit | Observed Impact |
|---|---|---|
| **GitHub** | 60 requests / hour / IP | Exceeding this returns HTTP 403 `rate_limited`. |
| **Reddit** | ~1 request / second | Generic user agents receive HTTP 429; OpenTrace uses unique identifier headers. |
| **Chess.com** | 1 request / second | Platform throttling if bursts exceed 2 req/s. |
| **Lichess** | 15–20 requests / minute | Public player API throttles excessive concurrency. |
| **Wikipedia** | Max 5–10 requests / second | Monitored by MediaWiki bot protection. |

The OpenTrace `BoundedScheduler` regulates global and per-host concurrency to stay well within standard safe thresholds.

---

## 4. Protected Platforms with Authentication Walls

Several high-visibility consumer networks enforce strict login walls or WAF policies that prevent direct unauthenticated scraping:

- **LinkedIn, Instagram, Facebook:** Require authenticated user sessions or enterprise partner Graph APIs. Automated requests receive redirect to login checkpoints.
- **X (Twitter):** Requires Twitter Developer API v2 subscription (`Bearer Token`). Public web profiles are protected by login walls.
- **Discord:** Requires bot authorization within a mutual server to look up tags.
- **TikTok:** Emits WAF challenge pages to non-browser user agents.

These platforms are cataloged in `sources/manifest.yaml` as `planned` or `requires_api_key`. OpenTrace will never report these platforms as operational without authenticated API integration.

---

## 5. Phone & Numbering Limitations

- **Number Portability:** ITU-T E.164 analysis via `phonenumbers` validates geographic prefix, country code, and numbering structure. It **cannot** detect subsequent number porting across cellular carriers without access to SS7/HLR network lookup providers.
- **Subscriber Activity:** A structurally valid phone number does not imply an active subscriber, live cellular connection, or registered WhatsApp/Telegram account.
