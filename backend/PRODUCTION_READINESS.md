# Production Readiness

## Core startup requirements

Configure these values in `backend/.env`:

- `SECRET_KEY`: at least 32 characters and unique per deployment.
- `DATABASE_URL`: PostgreSQL connection string.
- `OAUTH_TOKEN_ENCRYPTION_KEY`: valid Fernet key.
- `CORS_ALLOWED_ORIGINS`: comma-separated frontend origins.

Run:

```powershell
alembic upgrade head
uvicorn app.main:app
```

## Diagnostics

- `GET /health` — lightweight liveness response.
- `GET /system/health/ready` — readiness probe; returns HTTP 503 when core dependencies are not ready.
- `GET /system/readiness` — detailed safe diagnostics.
- `GET /job-sources/onboarding` — provider setup requirements.
- `GET /auth/providers/status` — user-specific provider authorization status.

Diagnostics never return provider secrets or OAuth tokens.

## Provider integrations

Each provider remains an adapter. The system does not scrape sites,
automate login pages, bypass CAPTCHA, or use undocumented endpoints.

A provider is considered operational only after its legitimate
authorized integration is implemented and its adapter can successfully
authenticate and retrieve jobs.

The current five-provider architecture is:

- LinkedIn
- Naukri
- Internshala
- Indeed
- Wellfound

Their credentials are intentionally supplied by the deployment rather
than shipped with the application.

## Synchronization

`POST /job-sources/{source_name}/sync` synchronizes one provider.

`POST /job-sources/sync-all` synchronizes all registered providers
independently. One provider failing does not erase successful results
from the others.

Jobs pass through:

provider adapter → `NormalizedJob` → canonical `Job` →
`JobSourceListing` → recommendation/application pipeline.

## Security rules

Never commit:

- `.env`
- OAuth access/refresh tokens
- provider client secrets
- database passwords
- production JWT signing secrets

The repository ignores local archives, caches, uploads, virtual
environments and secret files.
