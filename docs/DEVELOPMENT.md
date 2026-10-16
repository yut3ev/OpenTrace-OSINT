# Development

## Required checks
```bash
ruff check .
ruff format --check .
mypy src/opentrace
pytest --cov=opentrace --cov-report=term-missing
npm --prefix frontend run lint
npm --prefix frontend run build
```

If a check is not configured, either configure it or explicitly report that it was not run. Do not fabricate output.

## Test design
- Unit tests must not depend on live internet.
- HTTP calls should be mocked with respx or a similar library.
- DNS calls should be injected behind an interface and mocked.
- Add integration tests for API and storage.
- Keep a small optional live-test suite disabled by default and clearly label it as network-dependent.
