# AI Agent Implementation Plan

Implement in order and keep each phase green.

## Phase 1 — Repository and models
- Create `pyproject.toml`, settings, logging, typed Pydantic schemas, errors and common enums.
- Add lint, format, type-check and pytest configuration.
- Build normalized entity, finding, evidence and investigation models.

## Phase 2 — Module framework
- Define `OSINTModule` protocol/base class.
- Build registry that verifies unique module IDs and declared capabilities.
- Add per-module timeout, concurrency and request budget.
- Build normalization and deduplication without dropping provenance.

## Phase 3 — Source adapters
- Implement username GitHub and GitLab adapters using fixed URL templates or documented official APIs.
- Implement email syntax and MX lookup.
- Implement phone numbering metadata.
- Add mocked tests for success, 404, 403, 429, 5xx, timeout, malformed responses and DNS errors.
- Do not add any source that cannot be tested honestly.

## Phase 4 — Orchestrator and events
- Concurrently run selected compatible modules with global/per-host limits.
- Publish investigation/module/finding events.
- Support cancellation and maximum runtime.
- Correctly distinguish partial results from total failure.

## Phase 5 — Storage and exports
- Memory store default; SQLite opt-in.
- CRUD and retention hooks.
- JSON/CSV/HTML exports with HTML escaping and CSV formula injection protection.

## Phase 6 — API
- Implement routes from `docs/API.md`.
- Add validation, pagination bounds, consistent errors, request IDs and safe logging.
- SSE event endpoint with heartbeats and disconnect handling.
- Use dependency injection for store and engine in tests.

## Phase 7 — CLI
- Commands: `investigate`, `modules`, `show`, `delete`, `export`.
- Support JSON output and readable Rich tables.
- Exit codes: 0 success, 1 investigation failed, 2 invalid input/configuration.

## Phase 8 — Frontend
- React + TypeScript + Vite.
- Dashboard form, recent investigations, detail view, findings filtering and evidence panel.
- Use API client module and typed schemas.
- Add loading, empty, partial-failure and API-error states.
- Accessible labels, keyboard navigation and responsive layout.
- Do not use fake sample findings in normal mode.

## Phase 9 — Delivery
- Dockerfile and Compose.
- GitHub Actions for Python tests/lint/type-check and frontend lint/build.
- Security, privacy, source coverage, deployment and contributor docs.
- Run all checks and report exact results.

## Completion criteria
The project is complete only if:
- All required paths exist and contain meaningful implementation.
- `pip install -e ".[dev]"` succeeds in a clean environment.
- API starts and health/docs endpoints work.
- CLI help and basic commands work.
- Frontend builds.
- All unit and integration tests pass.
- All report formats are tested.
- No untested module is advertised as supported.
- The final response lists actual files, actual commands run and exact test results.
