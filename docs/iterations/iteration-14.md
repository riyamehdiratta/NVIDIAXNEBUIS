# Iteration 14 - Workflow runtime foundation

**Date:** 2026-10-29 | **SRS:** 1.4

## Changes

- Added strict typed, versioned workflow specs and bounded workflow budgets.
- Added a closed local tool registry with manifests for source reads, memory reads, local commitment extraction, follow-up draft creation, and daily reset summaries.
- Added static validation for tool permissions/registration, argument shape, node dependencies, cycles, input types, risk labels, and disabled egress/model budgets.
- Added dry-run simulation and explicit approval for workflows containing local writes.
- Added SQLite schema version 7 with durable workflow and per-node checkpoints, run receipts, idempotency keys, and checkpoint-based resume.
- Added source provenance for workflow runs; source deletion removes linked workflow receipts and derived output. Workflow receipts are included in user export.
- Exposed the installed Commitment scan, Daily reset, and Follow-up draft skills as workflow templates.

## Acceptance evidence

- The backend compiled with the project Python environment; `git diff --check` passed.
- Live API returned all three templates. Commitment scan, Daily reset, and Follow-up draft each passed static validation with suitable inputs.
- All three template simulations returned dry-run plans. Daily reset executed to `completed` with both node checkpoints `completed`; repeating the request with the same idempotency key returned the same run.
- Resuming the completed Daily reset preserved its two checkpoints. Static validation rejected an unregistered `arbitrary.shell` tool.
- A Commitment scan run without `approved=true` returned HTTP 428 before starting because it contains a local write.
- A synthetic follow-up draft completed with `sent=false`; deleting its synthetic source removed the linked run receipt/checkpoints. The workspace export contains workflow runs.
- Database upgraded to schema version 7.

## Decisions and limits

- No model planner is connected to the executor. Existing Nemotron remains behind the explicit scan preview/confirmation flow.
- Only handlers in the local registry can execute. There is no arbitrary code, web access, remote model node, scheduler, or external write.
- Local writes require an explicit approval field after a dry run. Calendar export, email sending, and payments remain excluded.
- Node outputs are checkpointed after execution; exact-once side effects across a crash window require per-tool idempotency and compensation, which remain future work.
