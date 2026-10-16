# Data Model

## Investigation
- `id`: UUID
- `created_at`, `completed_at`: UTC timestamps
- `status`: queued/running/completed/partial/failed/cancelled
- `request`: normalized target types and enabled module IDs; redact sensitive values in ordinary logs
- `findings`: list of findings
- `entities`: typed entities (username/email/domain/phone/platform/profile URL)
- `edges`: evidence-backed candidate relationships
- `warnings`: source and runtime limitations
- `summary`: counts, duration and module statuses

## Finding
- `id`: UUID
- `investigation_id`
- `module_id`, `module_version`
- `target_type`, `target_fingerprint` (avoid storing raw identifiers in logs)
- `status`: found/not_found/unknown/info/error
- `title`, `evidence`
- `source_name`, `source_url`
- `observed_at`: UTC timestamp
- `confidence`: none/low/medium/high, with documented meaning
- `data`: validated JSON object with a size limit
- `evidence_hash`: optional integrity hash, not proof that the source is truthful

## Entity and Edge
Entity: ID, type, normalized value or privacy-conscious reference, display label.
Edge: source entity ID, destination entity ID, relation, basis, confidence, evidence IDs, candidate/confirmed label.

Do not expose raw secrets. Use retention limits and deletion semantics.
