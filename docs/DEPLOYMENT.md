# Deployment

## Local development
Install Python dependencies, run `uvicorn opentrace.api.app:app --reload`, then run the frontend using Vite.

## Docker
- Multi-stage build where practical.
- Non-root user.
- Health check.
- No secrets baked into image.
- Default bind should be localhost in local instructions.
- Persist SQLite only when explicitly enabled and mounted as a volume.
- Provide `.env.example`; never commit `.env`.

## Production requirements
Before public exposure: authentication, role-based authorization, rate limiting, TLS termination, secret management, audit logs, retention/deletion policy, backup policy and monitoring. State clearly that these are not implied by the local developer mode.
