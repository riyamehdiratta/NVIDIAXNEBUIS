# Iteration 03 - runtime packaging and submission materials

**Date:** 2026-10-28  -  **SRS:** 0.2

## Changes

- Added multi-stage Docker build and loopback-only Docker Compose deployment with persistent local storage.
- Added `.env.example`, MIT license, README, research/architecture/SRS docs, OpenShell/NemoClaw runbook, and Devpost/demo-video draft.
- Added a custom OpenShell policy example that restricts filesystem access and model egress for the containerized app.

## Acceptance evidence

- The local app serves at `http://127.0.0.1:8000`; health and UI return success. Four synthetic sample sources are loaded and a local scan produced eight open loops with zero model egress receipts.
- Frontend production build and isolated API acceptance scenarios passed. The test used a stubbed Nebius response and made no network call.
- Docker daemon and NemoClaw/OpenShell CLI are unavailable in this workspace; container deployment and runtime policy remain unverified.
- Nebius key is absent, so live model output, latency, and feedback metrics remain unverified.
- The repository has not been published and no demo URL/YouTube video exists yet.

## Remaining release work

- Validate a configured Token Factory request and policy-denial case on a supported OpenShell host.
- Provision an isolated public demo instance with synthetic data, then create the public repository URL and demo video.


