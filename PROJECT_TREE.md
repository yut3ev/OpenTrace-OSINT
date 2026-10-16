# Required Project Tree

The AI agent must create and implement this structure. If it changes a path, it must update docs and imports consistently.

```text
opentrace/
├── README.md
├── LICENSE
├── NOTICE.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── PRIVACY.md
├── pyproject.toml
├── Makefile
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── codeql.yml
│   │   └── release.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── MODULES.md
│   ├── DATA_MODEL.md
│   ├── THREAT_MODEL.md
│   ├── DEPLOYMENT.md
│   ├── DEVELOPMENT.md
│   ├── ROADMAP.md
│   └── SOURCE_COVERAGE.md
├── src/opentrace/
│   ├── __init__.py
│   ├── config.py
│   ├── logging_config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── dependencies.py
│   │   ├── error_handlers.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── modules.py
│   │   │   ├── investigations.py
│   │   │   └── exports.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── common.py
│   │       ├── investigation.py
│   │       └── finding.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── scheduler.py
│   │   ├── events.py
│   │   ├── normalization.py
│   │   ├── correlation.py
│   │   ├── evidence.py
│   │   ├── deduplication.py
│   │   └── errors.py
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── usernames/
│   │   │   ├── __init__.py
│   │   │   ├── github.py
│   │   │   └── gitlab.py
│   │   ├── email/
│   │   │   ├── __init__.py
│   │   │   ├── syntax.py
│   │   │   └── dns.py
│   │   └── phone/
│   │       ├── __init__.py
│   │       └── numbering.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── interface.py
│   │   ├── memory.py
│   │   ├── sqlite.py
│   │   └── migrations/
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── json_report.py
│   │   ├── csv_report.py
│   │   └── html_report.py
│   └── web/
│       └── static/  # optional production frontend build output
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/client.ts
│       ├── types.ts
│       ├── styles.css
│       ├── components/
│       │   ├── Layout.tsx
│       │   ├── InvestigationForm.tsx
│       │   ├── FindingsList.tsx
│       │   ├── FindingCard.tsx
│       │   ├── EvidencePanel.tsx
│       │   ├── ModuleStatus.tsx
│       │   └── HistoryList.tsx
│       └── pages/
│           ├── Dashboard.tsx
│           └── InvestigationDetail.tsx
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_normalization.py
    │   ├── test_evidence.py
    │   ├── test_correlation.py
    │   ├── test_username_modules.py
    │   ├── test_email_modules.py
    │   ├── test_phone_module.py
    │   └── test_storage.py
    ├── integration/
    │   ├── test_orchestrator.py
    │   ├── test_api_investigations.py
    │   └── test_exports.py
    └── frontend/
        └── README.md
```

Do not create fake files with only TODO comments. Implement all core modules and user-facing routes. If a source integration is intentionally deferred, document it in `docs/SOURCE_COVERAGE.md`.
