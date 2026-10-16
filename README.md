# OpenTrace OSINT — Full Build Specification

OpenTrace is a modular, evidence-first public digital-footprint investigation platform focused on usernames, email addresses, and phone-number metadata. This repository contains the complete implementation brief for an AI coding agent. The agent must build and test the application, not merely repeat this document.

## Non-negotiable principles
- Only public sources and integrations the operator is authorized to use.
- Never bypass authentication, paywalls, CAPTCHAs, access controls, or rate limits.
- No leaked credential databases, password discovery, private account access, stalking, doxxing, or covert tracking.
- A username match is a candidate, not proof that accounts belong to one person.
- Every finding must have provenance, observation time, status, and an evidence explanation.
- `unknown` is different from `not_found`.
- Never fabricate data, sources, tests, coverage, or success metrics.
- In-memory storage is the default. Persistence is opt-in.
- The app must be usable locally and easy to deploy for authorized research.

## Product target
Build a polished open-source project with:
1. Web dashboard
2. Python CLI
3. REST API with OpenAPI docs
4. Plugin/module system
5. Concurrent investigation orchestrator
6. Evidence normalization and conservative correlation
7. In-memory default storage and optional SQLite
8. JSON, CSV, and HTML report export
9. Unit, integration, and API tests
10. Docker and GitHub Actions
11. Clear source coverage matrix and privacy/security docs

## Required stack
- Python 3.11+
- FastAPI + Pydantic v2
- httpx async
- Typer + Rich CLI
- SQLAlchemy 2.x or a carefully isolated sqlite3 store
- pytest + pytest-asyncio + respx (or equivalent HTTP mocking)
- React + TypeScript + Vite for the dashboard
- Tailwind CSS optional; do not sacrifice accessibility
- Docker Compose
- GitHub Actions

## Supported first-release modules
### Username
- Use an explicit, documented source registry.
- Implement only public profile endpoints whose terms and access patterns permit the checks.
- Initial adapters can include GitHub and GitLab public profile URLs. Any additional source must be individually implemented and tested.
- Do not infer ownership from profile existence.
- Treat 401, 403, 429, 5xx, timeout, redirects to login, and unexpected response shapes as `unknown`.
- 404 may be `not_found` only when the source's behavior has been tested and documented.
- Respect per-host rate limits and set an honest User-Agent.

### Email
- Syntax parsing and domain normalization.
- DNS MX lookup, with clear `unknown` handling for timeouts and DNS errors.
- Optional integration with documented, authorized provider APIs through environment-configured keys.
- No SMTP probing, mailbox enumeration, account recovery probing, or breach credential searches.
- Never claim mailbox existence or ownership from syntax/MX alone.

### Phone
- Parse and normalize using `phonenumbers`.
- Return only numbering-plan metadata such as E.164 format, country calling code, region and possible number type when available.
- Do not claim subscriber identity, live status, precise location, or account associations.

### Cross-source correlation
- Link only when explicit evidence supports the relationship.
- Similar usernames, display names, avatars, or names alone are weak signals and must not create a confirmed identity link.
- Every edge must contain `basis`, `confidence`, and evidence references.
- Label candidate relationships as candidates.

## Deliverables
The AI coding agent must create every file in `PROJECT_TREE.md`, then implement in stages defined in `IMPLEMENTATION_PLAN.md`. It must run formatting, linting, type checks where configured, and tests. It must report exactly which commands ran and their results. Do not say tests passed if they were not run.

## Local quick start (target)
```bash
python -m venv .venv
# activate venv for your OS
python -m pip install -e ".[dev]"
uvicorn opentrace.api.app:app --reload
```

In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```

## API target
- `GET /health`
- `GET /api/v1/modules`
- `POST /api/v1/investigations`
- `GET /api/v1/investigations`
- `GET /api/v1/investigations/{investigation_id}`
- `DELETE /api/v1/investigations/{investigation_id}`
- `GET /api/v1/investigations/{investigation_id}/events` (SSE)
- `GET /api/v1/investigations/{investigation_id}/export?format=json|csv|html`

See `docs/API.md` for schemas and semantics.

## Security warning
Do not expose the API publicly without authentication, authorization, rate limiting, secure secret management, and an explicit retention policy. The local development build may run without authentication only when bound to localhost.
