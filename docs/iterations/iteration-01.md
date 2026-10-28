# Iteration 01 — requirements and local memory/import

**Date:** 2026-10-28 · **SRS:** 0.1 baseline

## Changes

- Added SQLite schema v1 for sources, open loops, skills, policies, actions, reminders, egress receipts, activity, and daily reviews.
- Added `.txt`, `.md`, `.csv`, `.log`, `.eml`, and `.ics` parsing plus content-hash deduplication.
- Added local heuristic extraction and API routes for source intake, memory listing/review/deletion, export, and dashboard state.
- Added import-folder polling and a daily review entry after the host's 9 a.m. local time.

## Acceptance evidence

- Static inspection confirms foreign keys, schema version, import size/type validation, content digest deduplication, and a local-only extraction path.
- Runtime acceptance is scheduled after the isolated Python environment is installed. Results are recorded in Iteration 02 rather than inferred from code inspection.

## Decisions and limits

- Source text is stored in local SQLite without app-layer encryption. This is disclosed in UI and docs.
- PDF/OCR and OAuth connectors were excluded to keep imports portable and the local workflow installable.
