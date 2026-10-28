# Iteration 09 - distribution prerequisites and demo safety

**Date:** 2026-10-29 (OpenShell proof completed) | **SRS:** 1.2

## Changes

- Confirmed the configured Lightning and Super model IDs in Nebius's official Token Factory model cookbook.
- Added `.env` loading for local development, matching the setup guide, and pinned `python-dotenv`.
- Added a synthetic-demo mode that blocks pasted and file imports at the API and disables the local folder watcher.
- Added `docker-compose.demo.yml`: demo mode enabled, import watcher disabled, and database stored in temporary filesystem storage.
- Added public-demo state and upload capability metadata to the health response.
- Installed NVIDIA OpenShell 0.1.6 in Ubuntu WSL and enabled its local systemd user gateway.
- Configured the Docker Desktop supervisor bridge mode in `~/.config/openshell/gateway.toml`; this was needed because the default host-mode callback could not reach the WSL gateway from the sandbox.
- Added a read-only `/bin` path to Threadline's runtime policy so a shell-based startup/health check can execute while keeping the system tree immutable.
- Added a synthetic, repeatable verification policy and script under `infra/openshell/`.

## Acceptance evidence

- Nebius catalog pages verify both configured model IDs; no Token Factory API call was made in this iteration.
- Isolated API test with demo mode enabled confirmed pasted and file imports return HTTP 403; synthetic curated sample data remains available.
- `openshell status` reports the local gateway connected and authenticated via mTLS; `openshell gateway info` reports healthy, version 0.1.6, Docker driver 0.1.6.
- `openshell doctor check` passes with Docker Desktop engine version 28.5.1.
- The verification sandbox logged `ALLOWED /bin/busybox -> example.com:80` and `ALLOWED GET http://example.com/`; it logged `DENIED example.org [reason:policy_dns_ineligible]` and `DENIED /bin/busybox -> example.org:80 [reason:transparent_tcp_policy_denied]`. The command printed `ALLOW_OK` and `DENY_BLOCKED`.
- A second disposable sandbox accepted `infra/openshell/threadline-policy.yaml`, started its shell after the `/bin` read-only addition, and blocked an unlisted `example.org` request.
- Repeat the isolated network test in WSL with `bash infra/openshell/verify-network-policy.sh`. Sandbox logs are available via `openshell logs tl-policy-proof --source all` while a proof sandbox is alive.
- `docker compose -p threadline-demo -f docker-compose.demo.yml up --build -d` built and started successfully. `/api/health` reported demo mode on and uploads disabled; a posted text import returned HTTP 403, the synthetic workspace remained available, and the egress summary reported zero remote attempts. The container and network were removed with `docker compose ... down` after verification.
- An unauthenticated GitHub page request for the target repository returned 404, so public visibility is not confirmed even though `main` was pushed successfully.

## Decisions and blockers

- Do not claim live Token Factory inference until a real preview-confirm-scan has succeeded and its receipt, exact model ID, and latency are saved.
- The Nebius key must be stored in the ignored local `.env`; it was not present when this record was written.
- The repository's MIT license and setup guide are committed, but the repository does not currently appear publicly accessible. GitHub visibility settings require an authenticated account workflow.
- The OpenShell policy file was accepted by 0.1.6 and enforcement was verified in a synthetic sandbox. The proof uses a synthetic allowlisted endpoint, not the Nebius Token Factory inference route.
- WSL2 + Docker Desktop is an experimental OpenShell host combination. Use a native Linux VM for personal data or a judged production-like run.
- Follow-up installation and app-container verification are recorded in [iteration 12](iteration-12.md).
- Public hosting credentials and target deployment project are not configured. The compose demo profile prepares a synthetic-only container but is not a public URL.
