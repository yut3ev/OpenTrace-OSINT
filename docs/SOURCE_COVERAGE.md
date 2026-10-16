# OpenTrace OSINT — Source Coverage Matrix

> **Audit Date:** 2026-10-16  
> **Registry Status:** 85 Cataloged Sources (74 Implemented & Tested, 11 Planned Roadmap)  
> **Test Coverage:** 100% pass rate across 113 automated unit, integration, and adapter tests.  
> **Source Validation Engine:** Integrated CLI validator (`opentrace validate-sources`) supporting deterministic fixtures and live verification.

---

## 1. Executive Summary & Capabilities

OpenTrace OSINT has been architected to provide broad-coverage, multi-source digital footprint discovery inspired by modern intelligence tools. Every source query adheres strictly to ethical and legal standards:
- **No Private Probing / Breach Scraping**: No SMTP mailbox handshake probing, no password guessing, no private credential scraping, and no CAPTCHA/paywall circumvention.
- **Evidence-First Provenance**: Every observation computes a cryptographic `SHA-256` hash of raw data payloads, exact HTTP status codes, timestamped responses, and confidence scoring.
- **Conservative Status Taxonomy**: Explicit distinction between verified presence (`found`), clean absence (`no_match`), platform throttling (`rate_limited`), access blocks (`blocked`), network outages (`unavailable`), unhandled failures (`error`), and unconfigured optional integrations (`skipped`).
- **Recursive Multi-Layer Pivoting**: Automated entity extraction discovers candidate usernames, emails, and phone numbers from confirmed findings and recursively explores them within user-configured depth and budget limits.

---

## 2. Operational & Implemented Sources (74 Active Modules)

All 74 modules listed below are fully implemented in `src/opentrace/modules/`, registered in `get_default_registry()`, validated by automated test suites, and equipped with soft-404 detection, rate limiting, and error containment.

### A. Username Search Adapters (53 Active Platforms)

#### Core Developer & Package Registries (17 Platforms)
| Module ID | Platform | Category | Access Type | Test Status | Boundaries & Privacy Limitations |
|---|---|---|---|---|---|
| `username.github` | GitHub | Developer | Public REST API | **Tested** (100%) | Rate limit: 60 req/hr unauth; profile match $\neq$ identity. |
| `username.gitlab` | GitLab | Developer | Public REST API | **Tested** (100%) | Soft-404 detection; handles private namespaces. |
| `username.bitbucket` | Bitbucket | Developer | Public REST API 2.0 | **Tested** (100%) | Workspace privacy settings may conceal repositories. |
| `username.dockerhub` | Docker Hub | Developer | Public Registry API | **Tested** (100%) | Validates public namespace & container images. |
| `username.pypi` | PyPI | Developer | Public Web | **Tested** (100%) | Validates package author and maintainer presence. |
| `username.npm` | npm Registry | Developer | Public Web | **Tested** (100%) | Validates public package maintainer presence. |
| `username.huggingface` | Hugging Face | Developer | Public Hub API | **Tested** (100%) | Queries public models, datasets, and author spaces. |
| `username.codeberg` | Codeberg | Developer | Forgejo API | **Tested** (100%) | Open-source Git hosting; verifies public profile. |
| `username.hashnode` | Hashnode | Developer | Public Web | **Tested** (100%) | Checks developer blog subdomain and author bio. |
| `username.kaggle` | Kaggle | Developer | Public Web | **Tested** (100%) | Data science profile; verifies tier and datasets. |
| `username.replit` | Replit | Developer | Public Web | **Tested** (100%) | Checks creator repls and public bio. |
| `username.sourceforge` | SourceForge | Developer | Public Web | **Tested** (100%) | Open-source developer and maintainer profile. |
| `username.packagist` | Packagist | Developer | Public API | **Tested** (100%) | PHP package maintainer profile and package index. |
| `username.rubygems` | RubyGems | Developer | Public API | **Tested** (100%) | Ruby gem author profile and releases. |
| `username.cratesio` | Crates.io | Developer | Public API | **Tested** (100%) | Rust crate author profile and publish counts. |
| `username.stackexchange` | Stack Exchange | Developer | Public API | **Tested** (100%) | Developer Q&A user profile across network sites. |
| `username.devpost` | Devpost | Developer | Public Web | **Tested** (100%) | Hackathon portfolios and project submissions. |

#### Social, Community & Creator Platforms (21 Platforms)
| Module ID | Platform | Category | Access Type | Test Status | Boundaries & Privacy Limitations |
|---|---|---|---|---|---|
| `username.mastodon` | Mastodon | Social | Public API | **Tested** (100%) | Resolves account on flagship `mastodon.social` instance. |
| `username.bluesky` | Bluesky | Social | AT Protocol API | **Tested** (100%) | Resolves public AT protocol `.bsky.social` handle. |
| `username.reddit` | Reddit | Social | Public JSON API | **Tested** (100%) | Checks public karma and account timestamp; flags bans. |
| `username.keybase` | Keybase | Social | Public API | **Tested** (100%) | Cryptographic proofs, PGP fingerprints, verified sites. |
| `username.hackernews` | Hacker News | Community | Firebase API | **Tested** (100%) | Y Combinator HN karma and account creation date. |
| `username.wikipedia` | Wikipedia | Community | MediaWiki API | **Tested** (100%) | Registered editor username, edit count, and registration date. |
| `username.devto` | Dev.to | Blogging | Public API | **Tested** (100%) | Validates author existence and joined date. |
| `username.medium` | Medium | Publishing | Public Web | **Tested** (100%) | Detects `@username` author page and custom domain redirects. |
| `username.substack` | Substack | Publishing | Public Web | **Tested** (100%) | Newsletter subdomain availability and publication title. |
| `username.tumblr` | Tumblr | Blogging | Public Web | **Tested** (100%) | Subdomain existence and blog archive status. |
| `username.disqus` | Disqus | Community | Public Web | **Tested** (100%) | Discussion profile and public forum comments. |
| `username.producthunt` | Product Hunt | Community | Public Web | **Tested** (100%) | Product maker profile and hunt submissions. |
| `username.aboutme` | About.me | Identity | Public Web | **Tested** (100%) | Personal landing page and biographical details. |
| `username.linktree` | Linktree | Identity | Public Web | **Tested** (100%) | Public links aggregator profile and social hub. |
| `username.buymeacoffee`| Buy Me a Coffee | Creator | Public Web | **Tested** (100%) | Creator support page and membership info. |
| `username.patreon` | Patreon | Creator | Public Web | **Tested** (100%) | Creator campaign page and public membership tiers. |
| `username.pinterest` | Pinterest | Social | Public Web | **Tested** (100%) | Public pins and profile boards. |
| `username.flickr` | Flickr | Media | Public Web | **Tested** (100%) | Public photography photostream. |
| `username.vimeo` | Vimeo | Media | Public Web | **Tested** (100%) | Public video creator profile and uploads. |
| `username.soundcloud` | SoundCloud | Audio | Public Web | **Tested** (100%) | Public musician or podcaster track profile. |
| `username.bandcamp` | Bandcamp | Audio | Public Web | **Tested** (100%) | Artist or fan collection subdomain. |

#### Creative, Gaming & Technical Communities (15 Platforms)
| Module ID | Platform | Category | Access Type | Test Status | Boundaries & Privacy Limitations |
|---|---|---|---|---|---|
| `username.behance` | Behance | Creative | Public Web | **Tested** (100%) | Adobe creative portfolio and design projects. |
| `username.dribbble` | Dribbble | Creative | Public Web | **Tested** (100%) | Design shots and creative showcase profile. |
| `username.chess_com` | Chess.com | Gaming | Public REST API | **Tested** (100%) | Official published player ratings and membership status. |
| `username.lichess` | Lichess | Gaming | Public API | **Tested** (100%) | Open-source chess profile, bio, and performance stats. |
| `username.steam` | Steam | Gaming | Public Community | **Tested** (100%) | Steam Community public vanity URL and badge stats. |
| `username.twitch` | Twitch | Gaming | Public Web | **Tested** (100%) | Channel stream page; verifies broadcaster existence. |
| `username.goodreads` | Goodreads | Community | Public Web | **Tested** (100%) | Reader profile and public reading bookshelves. |
| `username.letterboxd` | Letterboxd | Media | Public Web | **Tested** (100%) | Film enthusiast diary, reviews, and favorites. |
| `username.lastfm` | Last.fm | Music | Public Web | **Tested** (100%) | Listening scrobbles and favorite artists. |
| `username.strava` | Strava | Fitness | Public Web | **Tested** (100%) | Athlete profile page and public activities. |
| `username.duolingo` | Duolingo | Learning | Public Web | **Tested** (100%) | Language learning streak and experience points. |
| `username.tryhackme` | TryHackMe | Security | Public Web | **Tested** (100%) | Cybersecurity rank, badges, and learning rooms. |
| `username.leetcode` | LeetCode | Technical | Public GraphQL/Web | **Tested** (100%) | Problem-solving ranking and language badges. |
| `username.codeforces` | Codeforces | Technical | Public API | **Tested** (100%) | Competitive programming rating and rank title. |
| `username.telegram` | Telegram | Messaging | Public Channel Web | **Tested** (100%) | Public channel or t.me handle existence. |

---

### B. Email Search & Discovery Adapters (10 Active Modules)

| Module ID | Source Name | Category | Access Type | Status | Test Status | Boundaries & Privacy Limitations |
|---|---|---|---|---|---|---|
| `email.syntax` | RFC 5321 Syntax | Local | Static Analysis | Operational | **Tested** (100%) | Full RFC 5321 & IDNA syntax parsing; zero network. |
| `email.dns` | DNS MX Records | Network | Public DNS | Operational | **Tested** (100%) | Checks mail exchanger existence; **no** SMTP handshakes. |
| `email.disposable` | Disposable Domains | Local | Static List | Operational | **Tested** (100%) | Identifies 500+ throwaway and burner email providers. |
| `email.gravatar` | Gravatar Profile | Network | Public API | Operational | **Tested** (100%) | MD5 hash lookup; only indexes publicly enabled avatars. |
| `email.security` | SPF & DMARC | Network | Public DNS | Operational | **Tested** (100%) | Evaluates domain spoofing protections (SPF, DMARC, DKIM). |
| `email.github_commits`| GitHub Commits | Network | Public REST API | Operational | **Tested** (100%) | Searches public author commits for matching public profiles. |
| `email.pgp_keyserver` | PGP Key Servers | Network | HKP Public Server | Operational | **Tested** (100%) | Resolves public PGP keys associated with email address. |
| `email.crossref_author`| CrossRef Metadata | Network | Public REST API | Operational | **Tested** (100%) | Searches published scientific papers and DOI authors. |
| `email.hibp` | HaveIBeenPwned | Network | Authorized API | Operational (Optional) | **Tested** (100%) | Requires `HIBP_API_KEY`. Safely returns `skipped` when unset. |
| `email.hunter_verifier`| Hunter Verifier | Network | Authorized API | Operational (Optional) | **Tested** (100%) | Requires `HUNTER_API_KEY`. Safely returns `skipped` when unset. |

---

### C. Phone Number Metadata Adapters (5 Active Modules)

| Module ID | Source Name | Category | Access Type | Status | Test Status | Boundaries & Privacy Limitations |
|---|---|---|---|---|---|---|
| `phone.numbering` | ITU-T E.164 Plan | Local | Google Phonenumbers | Operational | **Tested** (100%) | E.164 validation, geographical region, validity check. |
| `phone.international_format`| Dialing Formats | Local | Parsing Engine | Operational | **Tested** (100%) | Derives RFC 3966 URI, national, and international standards. |
| `phone.carrier_prefix`| Allocation Prefix | Local | Public Database | Operational | **Tested** (100%) | Determines assigned telecom operator from national ranges. |
| `phone.provider_api` | Numverify Carrier | Network | Authorized API | Operational (Optional) | **Tested** (100%) | Requires `NUMVERIFY_API_KEY`. Safely returns `skipped` when unset. |
| `phone.hlr_lookup` | Twilio HLR Carrier | Network | Authorized API | Operational (Optional) | **Tested** (100%) | Requires `TWILIO_ACCOUNT_SID`. Safely returns `skipped` when unset. |

---

### D. People, Publication & Search Adapters (6 Active Modules)

| Module ID | Source Name | Category | Access Type | Status | Test Status | Boundaries & Privacy Limitations |
|---|---|---|---|---|---|---|
| `name.wikipedia` | Wikipedia People | Network | MediaWiki API | Operational | **Tested** (100%) | Biographical queries; extracts notability summaries. |
| `name.dblp` | DBLP Computer Science | Network | Public REST API | Operational | **Tested** (100%) | Computer science bibliography author index and publications. |
| `name.openalex` | OpenAlex Scholarly | Network | Public REST API | Operational | **Tested** (100%) | Global scholarly research and citation author catalog. |
| `people.crossref` | CrossRef Academic | Network | Public REST API | Operational | **Tested** (100%) | Cross-references author publications and affiliations. |
| `people.arxiv` | arXiv Author Papers | Network | Public OAI/XML API | Operational | **Tested** (100%) | Queries physics, math, and CS preprint author archives. |
| `people.search_query` | Search Query Generator| Local | Logic Engine | Operational | **Tested** (100%) | Formulates safe, targeted boolean queries for web search engines. |

---

## 3. Planned Roadmap Sources (11 Cataloged Platforms)

These platforms are tracked in `sources/manifest.yaml` as `planned`. They are explicitly distinguished from active modules and are never counted in operational test suites:

- **Social & Messaging:** X (Twitter), Instagram, LinkedIn, Discord, TikTok
- **Creative & Audio:** ArtStation, Freesound
- **Gaming & Communities:** Steam Web API (authenticated)
- **People & Search:** Wikinews Mentions, DuckDuckGo Topic Summary, Google Scholar Scraper

---

## 4. Verification & Testing Methodology

OpenTrace guarantees honest results and deterministic reliability using a three-tier testing framework:

1. **Automated Unit & Integration Suites (`pytest -v`)**:
   - 113 automated tests across orchestrator, scheduler, correlation, storage, exporters, API, CLI, and all module families.
   - 100% mocked network environments preventing flaky network calls and external API hammering.
2. **Deterministic Source Validation (`opentrace validate-sources --fixtures`)**:
   - Tests every individual adapter against synthetic positive, negative, and malformed HTML/JSON payloads.
   - Validates soft-404 detection heuristics, rate-limit isolation, and evidence hashing.
3. **Optional Live Source Validation (`opentrace validate-sources --live`)**:
   - Performs rate-limited, live HTTP probes against official public endpoints to verify upstream schema stability.
   - Safely skips optional authorized modules when API credentials are absent.
