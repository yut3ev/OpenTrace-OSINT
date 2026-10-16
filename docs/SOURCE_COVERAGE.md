# OpenTrace OSINT — Source Coverage Matrix

> **Audit Date:** 2026-10-16  
> **Registry Status:** 51 Cataloged Sources (25 Implemented & Tested, 2 Requires API Key, 24 Planned Roadmap)  
> **Test Coverage:** 85% overall coverage across 87 automated unit & integration tests.

---

## 1. Operational & Implemented Sources (25 Active Adapters)

All 25 sources below have active adapter implementations registered in `opentrace.modules.registry`, pass automated mocked test suites, and feature soft-404, rate-limiting, and error isolation handling.

### A. Username Search Adapters (16 Active Platforms)

| Module ID | Source Name | Category | Access Type | Status | Test Status | Boundaries & Privacy Limitations |
|---|---|---|---|---|---|---|
| `username.github` | GitHub | Developer | Public API / Web | Implemented | **Tested** (100%) | Rate limit: 60 req/hr unauth; profile match $\neq$ identity. |
| `username.gitlab` | GitLab | Developer | Public API | Implemented | **Tested** (100%) | Soft-404 detection; handles private profiles. |
| `username.bitbucket` | Bitbucket | Developer | Public API 2.0 | Implemented | **Tested** (100%) | Account privacy settings may hide repositories. |
| `username.dockerhub` | Docker Hub | Developer | Public Registry API | Implemented | **Tested** (100%) | Only public container images and namespace verified. |
| `username.pypi` | PyPI | Developer | Public Web | Implemented | **Tested** (100%) | Validates maintainer profile page with package heuristics. |
| `username.npm` | npm | Developer | Public Web | Implemented | **Tested** (100%) | Validates public package maintainer presence. |
| `username.huggingface` | Hugging Face | Developer | Public API | Implemented | **Tested** (100%) | Public models, datasets, spaces, and profile bio. |
| `username.devto` | Dev.to | Blogging | Public API | Implemented | **Tested** (100%) | Validates author existence and joined date. |
| `username.mastodon` | Mastodon | Social | Public API | Implemented | **Tested** (100%) | Flags account on flagship `mastodon.social` instance. |
| `username.bluesky` | Bluesky | Social | AT Protocol API | Implemented | **Tested** (100%) | Resolves public AT protocol `.bsky.social` handle. |
| `username.reddit` | Reddit | Social | Public API | Implemented | **Tested** (100%) | Checks public karma and account creation date. |
| `username.keybase` | Keybase | Social | Public API | Implemented | **Tested** (100%) | Cryptographic identity proofs and PGP keys. |
| `username.chesscom` | Chess.com | Gaming | Public API | Implemented | **Tested** (100%) | Official published player ratings and membership status. |
| `username.lichess` | Lichess | Gaming | Public API | Implemented | **Tested** (100%) | Open-source chess profile, bio, and performance stats. |
| `username.hackernews` | Hacker News | Community | Firebase API | Implemented | **Tested** (100%) | Y Combinator HN karma and account timestamp. |
| `username.wikipedia` | Wikipedia User | Community | MediaWiki API | Implemented | **Tested** (100%) | Registered editor username, edit count, and reg date. |

### B. Email Investigation Adapters (5 Active Modules)

| Module ID | Module Name | Category | Access Type | Status | Test Status | Boundaries & Privacy Limitations |
|---|---|---|---|---|---|---|
| `email.syntax` | RFC 5321 Syntax | Email | Local Analysis | Implemented | **Tested** (100%) | Validates syntax and IDNA; **no** mailbox probing. |
| `email.dns` | DNS MX Lookup | Email | Public DNS | Implemented | **Tested** (100%) | Checks mail server reachability; does not verify inbox. |
| `email.disposable` | Disposable Detection | Email | Local Analysis | Implemented | **Tested** (100%) | Detects 500+ throwaway and burner inbox providers. |
| `email.gravatar` | Gravatar Profile | Email | Public API | Implemented | **Tested** (100%) | MD5 hash lookup; only indexes publicly shared avatars. |
| `email.security` | SPF & DMARC Security | Email | Public DNS | Implemented | **Tested** (100%) | Evaluates domain email security; not individual account. |

### C. Phone Investigation Adapters (1 Active Module)

| Module ID | Module Name | Category | Access Type | Status | Test Status | Boundaries & Privacy Limitations |
|---|---|---|---|---|---|---|
| `phone.numbering` | ITU-T Numbering Plan | Phone | Local Library | Implemented | **Tested** (100%) | E.164 parsing via `phonenumbers`; **no** subscriber ID. |

### D. Name / People Investigation Adapters (3 Active Modules)

| Module ID | Module Name | Category | Access Type | Status | Test Status | Boundaries & Privacy Limitations |
|---|---|---|---|---|---|---|
| `name.wikipedia` | Wikipedia Notable People | People | MediaWiki API | Implemented | **Tested** (100%) | Encyclopedic biographical query; candidate matches. |
| `name.dblp` | DBLP Computer Science | People | Public API | Implemented | **Tested** (100%) | Computer science bibliography author index. |
| `name.openalex` | OpenAlex Scholarly | People | Public API | Implemented | **Tested** (100%) | Global scholarly research and citation author catalog. |

---

## 2. API-Key Required Stubs (2 Adapters)

These adapters are cataloged in `sources/manifest.yaml` and reported to users as `requires_api_key`. They will run when valid credentials are provided in the environment.

| Source ID | Provider | Target | Env Variable | Status | Behavior When Unset |
|---|---|---|---|---|---|
| `email.hibp` | HaveIBeenPwned | Email | `HIBP_API_KEY` | `requires_api_key` | Emits `skipped` / `requires_api_key` finding with setup documentation. |
| `phone.provider_api` | Numverify / Twilio | Phone | `NUMVERIFY_API_KEY` or `TWILIO_ACCOUNT_SID` | `requires_api_key` | Emits `skipped` / `requires_api_key` finding with setup documentation. |

---

## 3. Planned Roadmap Sources (24 Cataloged Platforms)

These sources are cataloged in `sources/manifest.yaml` for transparent tracking. They are marked `planned` and are never claimed as active or operational.

- **Developer:** Kaggle, Replit, Codeberg, Hashnode
- **Social / Messaging:** X (Twitter), Instagram, LinkedIn, Discord, TikTok, Telegram, Linktree
- **Blogging & Publishing:** Medium, Substack
- **Creative & Audio:** Behance, Dribbble, ArtStation, SoundCloud, Bandcamp, Freesound
- **Gaming & Communities:** Steam Community, Product Hunt
- **Phone / Telecom:** Carrier Prefix Allocation (`phone.prefix_metadata`)
- **People Search:** Wikinews Mentions (`name.wikinews`), DuckDuckGo Topic Summary (`name.duckduckgo`)

---

## 4. Source Lifecycle & State Transition Model

Every execution of a source adapter transitions through the explicit state machine:

```
[registered in catalog] 
       │
       ▼
   [queued]
       │
       ▼
   [running]
       │
       ├─────────────────┬──────────────────┬─────────────────┐
       ▼                 ▼                  ▼                 ▼
  [succeeded]       [no_match]        [rate_limited]       [blocked]
       │                 │                  │                 │
       └─────────────────┴──────────────────┴─────────────────┘
                                 │
             ┌───────────────────┴───────────────────┐
             ▼                                       ▼
       [unavailable]                              [error]
```

- **succeeded:** The source executed successfully and validated a public finding.
- **no_match:** The source confirmed that the identifier does not exist on the platform.
- **rate_limited:** Platform rate limit reached (HTTP 429).
- **blocked:** Automated lookup denied or challenged by WAF/CAPTCHA (HTTP 403). Never reported as negative match.
- **unavailable:** Network timeout or service outage (HTTP 502/503/504).
- **error:** Unhandled parsing or protocol exception.
