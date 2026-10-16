# OpenTrace OSINT

[![CI Pipeline](https://github.com/opentrace-osint/opentrace/actions/workflows/ci.yml/badge.svg)](https://github.com/opentrace-osint/opentrace/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178C6.svg?logo=typescript)](https://www.typescriptlang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**OpenTrace OSINT** is a modular, evidence-first public digital-footprint investigation platform. Inspired by the clarity and multi-source breadth of modern intelligence tools, OpenTrace performs structured investigations across usernames, email addresses, phone-number metadata, and public author records using strictly lawful, public, and operator-authorized sources.

---

## Key Highlights

- **Evidence-First Provenance**: Every observation includes raw cryptographic hashes (`SHA-256`), canonical target references, HTTP status codes, retrieval timestamps, and transparent confidence ratings.
- **Honest Status Taxonomy**: Distinguishes verified presence (`found`) from clean absence (`no_match`), while explicitly recording service rate-limiting (`rate_limited`), access blocks (`blocked`), network timeouts (`unavailable`), and missing credentials (`skipped`).
- **Recursive Multi-Layer Pivoting**: Automatically extracts typed entities (usernames, emails, phones) from confirmed findings and recursively explores them with configurable depth, budget bounds, and loop prevention.
- **Source Validation Engine**: Includes an integrated verification utility (`opentrace validate-sources`) to deterministically test adapters against fixtures or live endpoints.
- **Bounded Concurrency & Throttling**: Asynchronous pipeline with global execution bounds and per-host rate limiting, preventing Denial-of-Service or IP ban risks against public endpoints.
- **No Private Probing / Breach Scraping**: Complies with strict ethical standards. Does not perform SMTP mailbox probing, password guessing, credential scraping, or paywall/CAPTCHA bypass.
- **Zero-Footprint Storage Default**: In-memory storage by default; opt-in SQLite persistence available via environment variable.
- **Unified Tri-Interface**: Web Dashboard (React + TypeScript + Vite), Python CLI (`opentrace` via Typer and Rich), and REST API with live Server-Sent Events (SSE).
- **Secure Report Exporters**: Generate sanitized JSON, CSV, or standalone single-file HTML reports hardened with Content Security Policy (CSP) and strict HTML escaping.

---

## Primary Search Modes & Source Coverage

OpenTrace includes **149 active, tested source adapters** operating 100% free with zero paid API dependencies, registered across five investigation modes:

### 1. Username Discovery (`TargetType.username` — 118 Platforms)
Searches public profile endpoints with custom response validation to eliminate false positives from soft-404s and redirect loops:
- **Developer & Code Registries (37 platforms)**: GitHub, GitLab, Bitbucket, Docker Hub, PyPI, npm, Hugging Face, Codeberg, Hashnode, Kaggle, Replit, SourceForge, Packagist, RubyGems, Crates.io, Stack Exchange, Devpost, HackerRank, Codewars, Codecademy, GeeksforGeeks, Topcoder, WakaTime, Hack The Box, Bugcrowd, Launchpad, asciinema, AnkiWeb, freeCodeCamp, Coderwall, Lobsters, MIT Scratch, Exercism, Weblate, Gitea, SourceHut, Pastebin.
- **Social, Publishing & Communities (45 platforms)**: Mastodon, Bluesky, Reddit, Keybase, Hacker News, Wikipedia, DEV.to, Medium, Substack, Tumblr, Disqus, Product Hunt, About.me, Linktree, Buy Me a Coffee, Patreon, Pinterest, Flickr, Vimeo, Quora, Discourse Meta, F-Droid Community, Bitwarden Forum, Wikiquote, Wiktionary, Wikivoyage, WordPress.com, Blogger, LiveJournal, Telegra.ph, Vero, Gravatar Profiles, OpenSea, Trello, Scratch Community, Goodreads, Letterboxd, Last.fm, Strava, Duolingo, TryHackMe, LeetCode, Codeforces, Telegram.
- **Creative, Audio, Media & Gaming (36 platforms)**: Behance, Dribbble, DeviantArt, ArtStation, 500px, SmugMug, Pixiv, Wattpad, Internet Archive, Instructables, SoundCloud, Bandcamp, Mixcloud, Audiomack, ReverbNation, Freesound, Audioboom, Trakt.tv, MyAnimeList, AniList, Chess.com, Lichess, Steam Community, Twitch, itch.io, Speedrun.com, Roblox, osu!, NameMC, Kongregate, Newgrounds, BoardGameGeek, Chessgames, SpigotMC, Nexus Mods.

### 2. Email Address Metadata & Discovery (`TargetType.email` — 13 Modules)
- **RFC Syntax & Domain Validation**: Full RFC 5321 syntax verification and IDNA internationalized domain support.
- **DNS MX Infrastructure**: Queries mail exchange records without intrusive SMTP mailbox handshakes.
- **Disposable Provider Detection**: Identifies 500+ throwaway, burner, and temporary email domains.
- **Public Gravatar Profiles**: Locates public user profiles and avatar metadata associated with hashed emails.
- **Domain Security Posture**: Evaluates SPF, DMARC, and DKIM email security and spoofing defenses.
- **GitHub Commit Attribution**: Discovers public commits and associated profile handles linked to the email.
- **PGP Key Server Discovery**: Queries public HKP keyservers for public cryptographic keys and identities.
- **CrossRef Author Records**: Searches academic paper publications and author digital object identifiers (DOIs).
- **ICANN RDAP Domain Records**: Queries public RDAP gateways for official domain registry and registrar info.
- **RFC 9116 security.txt**: Discovers published vulnerability disclosure policies and security contacts.
- **Certificate Transparency (crt.sh)**: Inspects public TLS certificate logs for domain infrastructure.
- **Authorized Verifiers (Optional)**: HaveIBeenPwned (`email.hibp`) and Hunter (`email.hunter_verifier`).

### 3. Phone Number Metadata (`TargetType.phone` — 7 Modules)
- **ITU-T E.164 Normalization**: Country code extraction, region detection, and numbering plan validation.
- **International Dialing Formats**: Derives RFC 3966 URI, national, and international E.164 representations.
- **Carrier Prefix Allocation**: Resolves telecom operator assignment from public national numbering plans.
- **Geographic Timezone Mapping**: Resolves primary and applicable timezones from telephone numbering plans.
- **ITU-T Number Type & Validation**: Audits numbering rules for mobile, fixed-line, toll-free, and VoIP allocations.
- **Authorized Carrier Lookups (Optional)**: Real-time carrier & line-type lookups via Numverify and Twilio HLR.

### 4. Name, Scholar & Public Records (`TargetType.name` — 9 Modules)
- **Wikidata Biographical Entities**: Resolves public Q-identities, descriptors, and Wikimedia concept links.
- **Wikipedia Notable Biographies**: Searches encyclopedic entries and extracts biographical notability data.
- **Wikipedia Full-Text Search**: Full-text keyword searches across encyclopedic article bodies.
- **Semantic Scholar Academic Graph**: Queries academic authors, citation counts, paper volumes, and h-index.
- **DBLP Bibliography**: Searches verified computer science publications and author entries.
- **OpenAlex Scholarly Index**: Queries global scientific research, publication counts, and institutional affiliations.
- **CrossRef Academic Metadata**: Discovers academic papers and researcher profile records.
- **arXiv Preprint Authors**: Searches math, physics, and computer science preprint archives.
- **Search Query Builder**: Formulates targeted, lawful boolean queries for public web search engines.

### 5. Public Web Search (`TargetType.web` — 2 Modules)
- **DuckDuckGo Instant Answer API**: Queries public instant answers, entity definitions, and verified topic abstracts.
- **Open Web Search Gateway**: Formulates safe, targeted boolean operators for search engines and open gateways.


---

## Architecture Overview

```
                      +------------------------------------------+
                      |         OpenTrace User Interfaces         |
                      |   React Web UI  |  Typer CLI  | REST API |
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |        Investigation Orchestrator        |
                      |  - Target Normalization & Validation     |
                      |  - Module Selection & Eligibility        |
                      |  - Event Bus (SSE Real-time Streaming)   |
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |       Bounded Concurrency Scheduler      |
                      |  - Global Semaphore (default: 5)         |
                      |  - Per-Host Semaphore (default: 2)       |
                      |  - Real-time Partial Result Retention    |
                      +------------------------------------------+
                                           |
                    +----------------------+----------------------+
                    |                      |                      |
                    v                      v                      v
             [ Username Modules ]   [ Email Modules ]    [ Phone & Name ]
                    |                      |                      |
                    +----------------------+----------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |     Correlation & Correlation Engine     |
                      |  - Finding Deduplication                 |
                      |  - Entity Extraction & Graph Edges       |
                      |  - Honest Source Coverage Metrics        |
                      +------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |     Storage & Multi-Format Exporters     |
                      |  - MemoryStore / SQLiteStore             |
                      |  - JSON / CSV / Hardened HTML Exporters  |
                      +------------------------------------------+
```

---

## Quickstart

### Prerequisites
- **Python**: 3.11, 3.12, or 3.13
- **Node.js**: 18+ (for building the frontend dashboard)

### 1. Clone & Install

```bash
# Clone the repository
git clone https://github.com/opentrace-osint/opentrace.git
cd opentrace

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install backend in editable mode with development dependencies
pip install -e ".[dev]"

# Install and build frontend dashboard
cd frontend
npm install
npm run build
cd ..
```

### 2. Run the API Server

```bash
uvicorn opentrace.api.app:app --host 0.0.0.0 --port 8000 --reload
```

- API Base URL: `http://localhost:8000`
- Interactive Swagger Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

### 3. Run the Web Dashboard

To run the frontend dev server with live hot-reloading:

```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` to explore investigations, view real-time findings, examine the entity graph, and download audit reports.

---

## Running with Docker Compose

OpenTrace includes a production-ready `Dockerfile` and `docker-compose.yml`:

```bash
# Build and start all services
docker compose up --build -d

# View application logs
docker compose logs -f

# Stop services
docker compose down
```

The containerized service runs on port `8000`, serving both the FastAPI backend and built frontend assets.

---

## CLI Usage

The OpenTrace CLI is powered by Typer and Rich:

```bash
# Run a username search across all platforms
opentrace investigate -u octocat

# Run an investigation with recursive multi-layer pivoting
opentrace investigate -u octocat --pivot --pivot-depth 2 --pivot-budget 15

# Run an email metadata check
opentrace investigate -e developer@example.com

# Run a phone numbering investigation
opentrace investigate -p "+14155552671"

# Run a multi-target investigation
opentrace investigate -u octocat -e developer@example.com

# Validate all source adapters against deterministic fixtures
opentrace validate-sources --fixtures

# Validate specific sources or live public endpoints
opentrace validate-sources --category username --live

# Export investigation results
opentrace export <INVESTIGATION_ID> -f html -o report.html
opentrace export <INVESTIGATION_ID> -f json -o report.json
opentrace export <INVESTIGATION_ID> -f csv -o report.csv

# List all supported source adapters
opentrace sources list

# View platform coverage metrics
opentrace stats
```

---

## Configuration & Environment Variables

OpenTrace supports canonical configuration keys as well as backwards-compatible deployment aliases:

| Variable | Alias | Default | Description |
|:---|:---|:---|:---|
| `OPENTRACE_STORAGE_MODE` | `OPENTRACE_STORAGE` | `memory` | Storage backend: `memory` or `sqlite` |
| `OPENTRACE_SQLITE_PATH` | - | `opentrace.db` | File path for SQLite database when mode is `sqlite` |
| `OPENTRACE_MAX_CONCURRENCY` | - | `5` | Maximum global concurrent module executions |
| `OPENTRACE_PER_HOST_CONCURRENCY` | - | `2` | Maximum concurrent requests to the same hostname |
| `OPENTRACE_DEFAULT_TIMEOUT` | `OPENTRACE_REQUEST_TIMEOUT_SECONDS` | `10.0` | Default HTTP timeout per module request (seconds) |
| `OPENTRACE_MAX_RUNTIME` | `OPENTRACE_MAX_RUNTIME_SECONDS` | `60.0` | Maximum investigation timeout (seconds) |
| `OPENTRACE_API_KEY` | - | `None` | Optional API key protecting `/api/v1/*` routes |
| `OPENTRACE_CORS_ORIGINS` | - | `http://localhost:5173,...` | Comma-separated list of allowed CORS origins |
| `OPENTRACE_LOG_LEVEL` | - | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `HIBP_API_KEY` | - | `None` | HaveIBeenPwned API key for authorized email breach lookups |
| `HUNTER_API_KEY` | - | `None` | Hunter.io API key for professional email validation |
| `NUMVERIFY_API_KEY` | - | `None` | Numverify API key for real-time carrier lookup |
| `TWILIO_ACCOUNT_SID` | - | `None` | Twilio SID for live HLR carrier lookups |
| `TWILIO_AUTH_TOKEN` | - | `None` | Twilio Auth Token for live HLR carrier lookups |

Copy `.env.example` to `.env` to configure your local settings:

```bash
cp .env.example .env
```

---

## REST API Overview

All protected endpoints accept authentication via `X-API-Key: <KEY>` or `Authorization: Bearer <KEY>` when `OPENTRACE_API_KEY` is configured.

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/health` | Service health status and version info |
| `POST` | `/api/v1/investigations` | Start a new synchronous or queued investigation |
| `GET` | `/api/v1/investigations/{id}` | Retrieve full investigation results and findings |
| `GET` | `/api/v1/investigations/{id}/events` | SSE stream for real-time finding and progress updates |
| `POST` | `/api/v1/investigations/{id}/cancel` | Cancel an ongoing investigation (retains partial findings) |
| `GET` | `/api/v1/sources` | Search and filter the full source manifest registry |
| `GET` | `/api/v1/sources/{id}` | Inspect metadata, limits, and capabilities of a source |
| `GET` | `/api/v1/stats` | Platform statistics, coverage by category, and status distribution |
| `GET` | `/api/v1/exports/{id}.json` | Download sanitized JSON investigation report |
| `GET` | `/api/v1/exports/{id}.csv` | Download CSV findings report |
| `GET` | `/api/v1/exports/{id}.html` | Download hardened single-file HTML report with CSP protection |

---

## Testing & Quality Assurance

OpenTrace maintains a comprehensive automated test suite with full HTTP and DNS mocking:

```bash
# Run the complete test suite (129 passing tests)
pytest -v

# Run with coverage reporting
pytest --cov=opentrace --cov-report=term-missing

# Run source validation utility
opentrace validate-sources

# Run code formatting and lint checks
ruff check .
ruff format --check .

# Run static type checks
mypy src/opentrace
```

---

## Legal & Ethical Guidelines

OpenTrace is built strictly for lawful digital forensics, authorized security investigations, research, and personal privacy audits.

1. **Lawful Sources Only**: Only public, unauthenticated web pages or APIs explicitly permitted by terms of service are queried.
2. **No Intrusion**: OpenTrace does not bypass logins, paywalls, CAPTCHAs, or rate limits.
3. **No Private Scraping**: Does not scrape private social profiles, access stolen credential databases, or perform unauthorized account enumeration.
4. **Correlation Disclaimer**: A username matching across multiple platforms is a candidate discovery, never conclusive proof of common ownership. Analysts must manually verify identity links.

---

## License

This project is licensed under the [MIT License](LICENSE).
