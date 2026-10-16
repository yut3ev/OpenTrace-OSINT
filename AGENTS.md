# Instructions for AI Coding Agents

You are implementing OpenTrace OSINT from the repository specification. Do not stop after writing a plan or a scaffold. Write the actual source code, tests, frontend and docs.

1. Read `README.md`, `PROJECT_TREE.md`, `docs/ARCHITECTURE.md`, `docs/API.md`, and `docs/IMPLEMENTATION_PLAN.md` first.
2. Inspect the existing repository before editing; preserve useful code and reconcile inconsistencies.
3. Work phase-by-phase from `docs/IMPLEMENTATION_PLAN.md`.
4. Implement a coherent, runnable project, not pseudocode. Avoid empty placeholder files and TODO-only functions.
5. Use conservative source semantics and cite provenance for every finding.
6. Never invent findings, integrations, API keys, tests, test output, coverage or benchmarks.
7. Do not add invasive capabilities such as credential theft, breach-password search, authentication bypass, private account access, CAPTCHA bypass, rate-limit evasion, covert tracking or doxxing workflows.
8. Add tests before claiming a module works. Mock network and DNS in unit tests.
9. Run all checks available in the environment. If a command cannot run, state the exact blocker.
10. Keep `.env`, databases, generated reports and secrets out of Git.
11. Make the UI usable and accessible; avoid fake results.
12. At the end, summarize implementation, run commands, test results, unsupported sources, and remaining limitations.
