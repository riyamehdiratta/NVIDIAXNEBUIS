# Iteration 02 — assistant UI, skills, and action controls

**Date:** 2026-10-28 · **SRS:** 0.2

## Changes

- Added the six-view React workspace: Today, Open Loops, Skills, Permissions, Sources, and Privacy & Activity.
- Added request preflight, email/phone/SSN/long-number pattern redaction, explicit remote-send confirmation, and local-only extraction.
- Added evidence correction fallback, action approval history, local reminder/draft/calendar export, per-action trust history, and editable skill instructions.
- Added the synthetic workspace and responsive layout.
- Bound each remote scan to a persisted, single-use, ten-minute preview containing exact request JSON, selected source digests, skill, and model. Changed/deleted sources, edited skills, replayed previews, and mismatched source lists are rejected before model egress.
- Added explicit skill run controls for imported sources, local export of auto-approved calendar actions, and a visible action receipt history with draft-copy and calendar-download controls.
- Clarified the permission UI and runtime docs: application policy constrains local actions; only the separately deployed OpenShell runtime can provide an OS/network boundary.

## Acceptance evidence

- `npm run build` passed with Vite; production UI served from FastAPI returned HTTP 200.
- Local API acceptance flow imported pasted text, `.eml`, and `.ics`; previewed three sources; asserted email/phone redaction; extracted five evidence-linked open loops; approved a local reminder; and confirmed one reminder, zero egress events, and intact evidence.
- No remote model request has been made because `NEBIUS_API_KEY` is not configured in this workspace.

## Decisions and limits

- Repeated approvals prompt a possible policy change after three accepts; the permission never changes automatically.
- Action policies are application-level restrictions for local tools. OpenShell is the separate OS/network boundary for a sandboxed runtime.
- Browser-based visual QA could not run because the in-app browser exposed no available browser session; build and HTTP checks passed.
