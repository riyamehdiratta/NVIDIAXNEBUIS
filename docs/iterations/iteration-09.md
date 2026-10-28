# Iteration 09 - distribution prerequisites and demo safety

**Date:** 2026-10-28 | **SRS:** 0.8

## Changes

- Confirmed the configured Lightning and Super model IDs in Nebius's official Token Factory model cookbook.
- Added `.env` loading for local development, matching the setup guide, and pinned `python-dotenv`.
- Added a synthetic-demo mode that blocks pasted and file imports at the API and disables the local folder watcher.
- Added `docker-compose.demo.yml`: demo mode enabled, import watcher disabled, and database stored in temporary filesystem storage.
- Added public-demo state and upload capability metadata to the health response.
- Began installing NVIDIA OpenShell v0.1.6 in Ubuntu WSL from the official installer; the package manager was still running Ubuntu unattended upgrades when recorded.

## Acceptance evidence

- Nebius catalog pages verify both configured model IDs; no Token Factory API call was made in this iteration.
- Isolated API test with demo mode enabled confirmed pasted and file imports return HTTP 403; synthetic curated sample data remains available.
- Docker Desktop's Windows Docker engine reported version 28.5.1. Ubuntu WSL package installation was waiting on automatic package updates; no OpenShell sandbox allow/deny result exists yet.
- `docker compose -p threadline-demo -f docker-compose.demo.yml up --build -d` built and started successfully. `/api/health` reported demo mode on and uploads disabled; a posted text import returned HTTP 403, the synthetic workspace remained available, and the egress summary reported zero remote attempts. The container and network were removed with `docker compose ... down` after verification.
- An unauthenticated GitHub page request for the target repository returned 404, so public visibility is not confirmed even though `main` was pushed successfully.

## Decisions and blockers

- Do not claim live Token Factory inference until a real preview-confirm-scan has succeeded and its receipt, exact model ID, and latency are saved.
- The Nebius key must be stored in the ignored local `.env`; it was not present when this record was written.
- The repository's MIT license and setup guide are committed, but the repository does not currently appear publicly accessible. GitHub visibility settings require an authenticated account workflow.
- The OpenShell policy and CLI must be validated against the installed runtime. No allow or deny proof is claimed until it runs and logs a denied destination.
- Public hosting credentials and target deployment project are not configured. The compose demo profile prepares a synthetic-only container but is not a public URL.
