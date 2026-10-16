# Architecture

## Layers
1. **Interfaces**: React dashboard, Typer CLI, FastAPI REST API.
2. **Application core**: orchestrator, bounded scheduler, event publisher, cancellation, normalization and deduplication.
3. **Source modules**: independent adapters that implement the `OSINTModule` contract.
4. **Evidence model**: immutable provenance records, observation time, status, confidence, source URL and explanation.
5. **Storage**: memory by default; SQLite opt-in; persistence is behind a storage interface.
6. **Reporting**: JSON, CSV, HTML export.

## Execution flow
1. Validate the request and normalize input.
2. Select only modules supporting each input type.
3. Schedule independent modules concurrently with a global and per-host concurrency limit.
4. Emit progress events as modules start, finish, or fail.
5. Normalize each module response into `Finding` objects.
6. Deduplicate identical findings without deleting provenance.
7. Correlate entities conservatively; all links are evidence-backed candidates unless the source explicitly establishes a relationship.
8. Save results only according to configured storage policy.
9. Return the investigation ID and results; clients can subscribe to events.

## Module contract
Each module must expose:
- stable `id`, `name`, `version`
- supported input types
- source description and source URL template or official API documentation
- `async run(target, context) -> list[Finding]`
- health/capability metadata
- timeout, request budget and rate-limit policy
- tests with mocked network responses

A module must not be enabled merely because its name appears in a registry. Registry entries must be tied to imported implementations and tests.

## Error semantics
- `found`: source provides a meaningful public result.
- `not_found`: only when the source semantics make absence reasonably clear.
- `unknown`: blocked, rate-limited, timed out, malformed or ambiguous response.
- `info`: useful technical metadata that is not a presence claim.
- `error`: invalid input or module execution error.

A failed source never implies a negative identity result.
