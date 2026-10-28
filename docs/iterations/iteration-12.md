# Iteration 12 - OpenShell runtime installation and policy proof

**Date:** 2026-10-29 | **SRS:** 1.1

## Root cause and resolution

- The earlier installer was blocked on an interactive `sudo` prompt; Ubuntu's unattended upgrades had already finished. Installed the checksum-verified OpenShell 0.1.6 package as WSL root, then started and enabled the `openshell-gateway` user service.
- The gateway was healthy on `https://127.0.0.1:17670`, but the default supervisor host-network mode could not call back from Docker Desktop into WSL. Set `supervisor_network_mode = 'bridge'` in `~/.config/openshell/gateway.toml`; the supervisor now uses `host.docker.internal` and retrieves its policy successfully.
- Added `/bin` to the Threadline policy's read-only paths and set `include_workdir: false`. An actual Threadline image initially failed workspace validation because `/app` was both the image working directory and read-only. The Docker image now starts in `/var/lib/threadline` (already an allowed writable data path) and explicitly points Uvicorn at `/app`.
- Added the resolved `/usr/local/bin/python3.12` executable path to the inference network policy as well as the stable `/usr/local/bin/python` symlink. OpenShell logs the resolved executable path for this image, so the explicit binary identity must match it.

## Acceptance evidence

- `openshell --version`: 0.1.6; `openshell status`: connected, authenticated over mTLS; `openshell gateway info`: healthy, Docker driver 0.1.6.
- `openshell doctor check`: all prerequisites pass; Docker Desktop engine 28.5.1.
- `infra/openshell/verify-network-policy.sh` succeeds. OpenShell logs an allow for `/bin/busybox` to `example.com:80` and a policy denial for `example.org:80`. Captured log excerpts and the app sandbox result are in [openshell-policy-allow-deny.txt](../evidence/openshell-policy-allow-deny.txt).
- Built `threadline:openshell-check`; the Threadline sandbox reached `Ready` under the project policy. `GET /api/health` returned HTTP 200 with demo mode enabled, uploads disabled, four synthetic sources, and no API key. A Python request to `example.org:443` was denied by policy.

## Decisions and limits

- The real Token Factory route remains unconfigured: no Nebius key/provider exists in the local `.env` or OpenShell provider store. A synthetic request to `inference.local` could not resolve upstream, so no live Nemotron inference or allowed Token Factory transaction is claimed.
- The explicit allow/deny proof is a synthetic policy probe that allows only `example.com` over HTTP and blocks `example.org`. The Threadline policy sandbox separately proves runtime startup and denial of an unlisted destination.
- WSL2 + Docker Desktop is experimental for OpenShell. The gateway service starts with the WSL user session; it is not a public or cloud deployment.
- The Threadline app sandbox was deleted after the health and network checks. The user can rerun the policy proof with `bash infra/openshell/verify-network-policy.sh` inside WSL.
