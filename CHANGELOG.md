# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-16

### Initial Release — Multi-Source OSINT Search Platform

#### Core Engine & Multi-Target Architecture
- **Multi-Target OSINT Search Engine:** Supports searching across 5 distinct target modalities:
  - **Username:** Queries across social media, developer ecosystems, gaming networks, blogging platforms, design forums, and communities.
  - **Email:** Queries authorized DNS records (MX, SPF, DMARC), Gravatar, GitHub commits search, and format validity checks.
  - **Phone:** E.164 normalization, carrier and geographical metadata derivation, and country calling code lookup.
  - **Name:** DuckDuckGo HTML scraping, Wikipedia entity search, and GitHub user registry lookup.
  - **Web:** Multi-engine passive discovery across DuckDuckGo, Wikipedia, and public registry indexes.
- **Bounded Concurrency & Egress Controls:**
  - Configurable global concurrency (`OPENTRACE_MAX_CONCURRENCY`) and per-host concurrency caps (`OPENTRACE_PER_HOST_CONCURRENCY`).
  - Strict Anti-SSRF validation (`src/opentrace/core/ssrf.py`) blocking private IP subnets, loopback, link-local, and cloud metadata hostnames.
  - Polite crawling mechanisms with customizable `User-Agent` and respect for HTTP 429 rate limit responses.
- **Adapter Registry:**
  - Standardized BaseAdapter interface with typed findings, confidence scoring, evidence provenance, and conservative status categorization (`found`, `not_found`, `rate_limited`, `error`, `unsupported`).
  - Total of 149 fully implemented and registered free source adapters.

#### Web Platform & REST API
- **FastAPI Application:**
  - Asynchronous endpoints for investigations (`/api/v1/investigations`), targets, findings, event streams, and metrics.
  - Strict request validation using Pydantic models.
  - OpenAPI and Swagger documentation auto-generated at `/api/docs`.
- **User Authentication & Tenant Isolation:**
  - JWT-based authentication (`/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/me`).
  - Passwords hashed with `bcrypt` (12 salt rounds).
  - Anti-brute-force login rate limiting with sliding window.
  - Cryptographically secure password reset flow (`secrets.token_urlsafe(32)` hashed with SHA-256).
  - Strict user-level investigation isolation: cross-tenant access returns HTTP 404 to prevent resource enumeration.
- **Storage Subsystems:**
  - Pluggable storage architecture: SQLite persistence (`OPENTRACE_STORAGE_MODE=sqlite`) with foreign key cascades and versioned migrations, and high-performance in-memory storage (`OPENTRACE_STORAGE_MODE=memory`).
- **Reporting & Exporting:**
  - Structured exports in JSON, CSV, and self-contained HTML report formats.
  - Mitigation against CSV formula injection (escaping leading `=`, `+`, `-`, `@`).

#### Frontend User Interface
- **Modern React 18 + TypeScript + Vite Dashboard:**
  - Responsive, dark-themed cyber UI built with Tailwind CSS and Lucide React icons.
  - Dedicated pages for Search Console, Active Investigation Monitoring, Multi-format Findings Browser, Sources Catalog, System Settings, and User Authentication.
  - Real-time investigation progress tracking with reactive polling and error recovery.
  - Client-side export triggers and filter controls (by source, category, confidence).

#### CLI & Automation
- **Python CLI Tooling:**
  - Command-line interface (`opentrace`) supporting headless investigation execution, target querying, and local report generation.
  - Machine-readable JSON output mode for CI/CD and automated pipeline integrations.

#### Testing & CI/CD
- **Comprehensive Automated Test Suite:**
  - 136 unit, integration, and API tests executed via `pytest`.
  - 100% mocked network and DNS interactions for reproducible offline testing.
  - Strict type verification with `mypy` across all 82 source files.
  - Python linting and formatting enforced with `ruff`.
  - Frontend TypeScript validation and build verification with `npm run build`.
- **Containerization & Deployment:**
  - Multi-stage Dockerfile and Docker Compose configurations for seamless local or cloud deployment.
  - GitHub Actions CI workflow covering linting, type checks, and tests across Python and Node.js runtimes.
