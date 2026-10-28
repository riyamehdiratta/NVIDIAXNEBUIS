# Iteration 04 - release readiness and model verification

**Date:** 2026-10-28 | **SRS:** 0.3

## Changes

- Checked the configured Nebius Token Factory model IDs against Nebius's current NVIDIA Nemotron inference catalog. `nvidia/Nemotron-3_5-Lightning` and `nvidia/nemotron-3-super-120b-a12b` are the IDs used by the current configuration. See [Nebius's model catalog](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference).
- Recorded release blockers explicitly instead of representing setup documentation as a live integration.

## Acceptance evidence

- The app has no `NEBIUS_API_KEY`; no live model request, measured latency, or inference output was produced in this iteration.
- Docker is unavailable and this directory is not a Git repository; no public deployment or repository URL could be published from this environment.
- Synthetic local demo remains available at `http://127.0.0.1:8000`; no personal data is included in the demo seed.

## Remaining release work

- Supply a Token Factory key, then verify one real request and capture latency, output quality, and cost feedback.
- Provision an isolated synthetic-data host and public Git remote before publishing the demo and code.
- Test NemoClaw/OpenShell network denial on its supported Linux runtime. The sample policy is not yet an active boundary here.
