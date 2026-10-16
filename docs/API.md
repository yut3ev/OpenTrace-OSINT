# API Contract

Base prefix: `/api/v1`. FastAPI publishes OpenAPI docs at `/docs`.

## POST `/investigations`
Request:
```json
{
  "username": "octocat",
  "email": null,
  "phone": null,
  "modules": ["username.github", "username.gitlab"],
  "max_runtime_seconds": 30
}
```
At least one target is required. `modules` is optional; when omitted, use only enabled compatible modules. Enforce server-side maximums regardless of client values.

Response:
```json
{
  "id": "uuid",
  "status": "completed",
  "created_at": "ISO-8601",
  "request": {"username": "octocat"},
  "findings": [],
  "entities": [],
  "edges": [],
  "summary": {"total": 0, "by_status": {}},
  "warnings": []
}
```

## GET `/investigations`
Return recent investigations, newest first. Support `limit` with a strict maximum of 100.

## GET `/investigations/{id}`
Return one investigation or 404.

## DELETE `/investigations/{id}`
Delete an investigation and its persisted data, return 404 when missing.

## GET `/investigations/{id}/events`
Server-Sent Events with event types `investigation.started`, `module.started`, `finding.created`, `module.completed`, `module.failed`, and `investigation.completed`. Include heartbeat events. Disconnects must not crash the job. Document whether work continues after clients disconnect.

## GET `/investigations/{id}/export?format=json|csv|html`
Return safe downloadable report. HTML must escape all untrusted content to prevent XSS. CSV must neutralize spreadsheet formula injection in cells starting with `=`, `+`, `-`, or `@`.

## GET `/modules`
Return module IDs, names, versions, supported target types, enabled status, source and a truthful implementation status.

## GET `/health`
Return service status and storage mode. Do not leak secrets, file paths, environment variables or stack traces.

## Error format
Use a consistent JSON shape:
```json
{"error":{"code":"VALIDATION_ERROR","message":"Readable explanation","request_id":"..."}}
```
Do not include secrets or raw tracebacks in API responses.
