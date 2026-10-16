# OpenTrace OSINT — Verification & Test Results Report

> **Execution Date:** 2026-10-16  
> **Environment:** Python 3.13.13 (win32), Node.js v24.16.0, npm 11.13.0  
> **Backend Framework:** FastAPI 0.115+, Pydantic v2, Typer 0.15+, httpx 0.28+  
> **Frontend Stack:** React 18, TypeScript 5.5, Vite 5.4

---

## 1. Executive Summary

| Verification Suite | Tool | Total Items | Passed | Failed | Status |
|---|---|---|---|---|---|
| **Python Unit & Integration Tests** | `pytest 9.1.1` + `respx` | 87 | 87 | 0 | **100% PASS** |
| **Backend Code Coverage** | `pytest-cov` | 2,477 lines | 2,102 lines | - | **85% Overall** |
| **Python Linting** | `ruff 0.8+` | 95 files | 95 files | 0 | **CLEAN** |
| **Python Formatting** | `ruff format` | 95 files | 95 files | 0 | **CLEAN** |
| **Static Type Checking (Strict)** | `mypy 1.13+` | 60 source files | 60 files | 0 | **CLEAN** |
| **Frontend TypeScript Build** | `tsc -b && vite build` | 1,591 modules | 1,591 modules | 0 | **SUCCESS** |
| **Frontend ESLint Checking** | `npm run lint` | Full codebase | All files | 0 | **CLEAN** |

---

## 2. Test Suite Breakdown by Test File

```
tests/integration/test_api_investigations.py ......................... [  4%] (4 passed)
tests/integration/test_exports.py .................................... [  9%] (4 passed)
tests/integration/test_orchestrator.py ............................... [ 11%] (2 passed)
tests/integration/test_sources_and_stats_api.py ...................... [ 19%] (7 passed)
tests/unit/test_cli.py ............................................... [ 26%] (6 passed)
tests/unit/test_correlation.py ....................................... [ 29%] (3 passed)
tests/unit/test_developer_modules.py ................................. [ 41%] (10 passed)
tests/unit/test_email_modules.py ..................................... [ 47%] (5 passed)
tests/unit/test_evidence.py .......................................... [ 51%] (4 passed)
tests/unit/test_gaming_community_modules.py .......................... [ 58%] (6 passed)
tests/unit/test_new_email_modules.py ................................. [ 64%] (5 passed)
tests/unit/test_normalization.py ..................................... [ 72%] (7 passed)
tests/unit/test_people_modules.py .................................... [ 77%] (4 passed)
tests/unit/test_phone_module.py ...................................... [ 81%] (4 passed)
tests/unit/test_social_modules.py .................................... [ 89%] (7 passed)
tests/unit/test_storage.py ........................................... [ 93%] (3 passed)
tests/unit/test_username_modules.py .................................. [100%] (6 passed)

============================= 87 passed in 28.10s =============================
```

---

## 3. Code Coverage by Subsystem

| Package / Module | Lines of Code | Missed | Coverage |
|---|---|---|---|
| `opentrace.api.routes.health` | 15 | 0 | **100%** |
| `opentrace.api.routes.modules` | 23 | 0 | **100%** |
| `opentrace.api.routes.stats` | 31 | 0 | **100%** |
| `opentrace.api.routes.exports` | 30 | 2 | **93%** |
| `opentrace.api.routes.sources` | 46 | 4 | **91%** |
| `opentrace.api.schemas.*` | 145 | 0 | **100%** |
| `opentrace.core.correlation` | 58 | 0 | **100%** |
| `opentrace.core.deduplication` | 17 | 0 | **100%** |
| `opentrace.core.evidence` | 20 | 0 | **100%** |
| `opentrace.core.normalization` | 60 | 8 | **87%** |
| `opentrace.core.orchestrator` | 206 | 55 | **73%** |
| `opentrace.modules.email.disposable` | 25 | 1 | **96%** |
| `opentrace.modules.email.dns` | 55 | 8 | **85%** |
| `opentrace.modules.email.gravatar` | 43 | 2 | **95%** |
| `opentrace.modules.email.security` | 62 | 7 | **89%** |
| `opentrace.modules.email.syntax` | 33 | 2 | **94%** |
| `opentrace.modules.manifest` | 50 | 6 | **88%** |
| `opentrace.modules.people.dblp` | 54 | 6 | **89%** |
| `opentrace.modules.people.openalex` | 54 | 5 | **91%** |
| `opentrace.modules.people.wikipedia` | 47 | 3 | **94%** |
| `opentrace.modules.phone.numbering` | 50 | 1 | **98%** |
| `opentrace.modules.usernames.developer` | 163 | 14 | **91%** |
| `opentrace.modules.usernames.gaming_community` | 112 | 8 | **93%** |
| `opentrace.modules.usernames.github` | 51 | 6 | **88%** |
| `opentrace.modules.usernames.gitlab` | 56 | 18 | **68%** |
| `opentrace.modules.usernames.social` | 117 | 8 | **93%** |
| `opentrace.reports.csv_report` | 22 | 1 | **95%** |
| `opentrace.reports.html_report` | 46 | 2 | **96%** |
| `opentrace.reports.json_report` | 10 | 1 | **90%** |
| `opentrace.storage.memory` | 36 | 3 | **92%** |
| `opentrace.storage.sqlite` | 66 | 7 | **89%** |
| **TOTAL** | **2,477** | **375** | **85%** |

---

## 4. Frontend Compilation & Bundle Verification

Running `npm run build` within `frontend/`:
```
> opentrace-dashboard@0.1.0 build
> tsc -b && vite build

vite v5.4.21 building for production...
transforming...
✓ 1591 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.54 kB │ gzip:  0.33 kB
dist/assets/index-BZX4MzAL.css    5.99 kB │ gzip:  2.00 kB
dist/assets/index-CXIJMp48.js   175.30 kB │ gzip: 53.95 kB
✓ built in 2.35s
```

All React components type-check cleanly under strict TypeScript configuration.
