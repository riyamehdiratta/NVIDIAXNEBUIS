# Iteration 15 - User-demand workflow compiler

**Date:** 2026-10-29 | **SRS:** 1.5

## Changes

- Added a Nemotron workflow compiler that receives a redacted user request, a fixed tool manifest, and the versioned JSON Schema. It receives no source or memory content.
- Added manifest-declared output types and taint; the validator checks node references, required dependencies, type compatibility, and taint declarations before saving generated workflows.
- Added registered reminder and draft proposal tools that call the existing action API, preserving action autonomy levels, pause, quiet hours, caps, review queue, and undo instead of writing actions directly.
- Added a two-step compile preview/confirm API. The exact OpenAI-compatible request is visible before confirmation; the confirmed request is written to the existing egress ledger.
- Added versioned workflow definitions. A user can save a one-off task or a reusable skill; revising a saved custom skill creates a new version. Built-ins can seed a new copy.
- Extended the deterministic executor to run saved custom DAGs, check wall budgets between nodes, inspect versions, and delete custom definitions and run history.
- Added the **Agent workflows** screen with task description, skill naming, base workflow selection, exact egress preview, workflow spec inspection, run inputs, dry-run, explicit local-write approval, and checkpoint receipt.
- Blocked custom planner compilation in public synthetic-demo mode so an anonymous visitor cannot spend the hosted Token Factory key.
- Bumped SQLite to schema version 8; updated generated schema, README, architecture notes, SRS, and submission draft.

## Acceptance evidence

- Backend modules compile, and the frontend production build succeeds.
- Live API returned a compiler preview using `nvidia/Nemotron-3_5-Lightning`. The preview contained the redacted synthetic task, tool manifests, and JSON Schema; it explicitly reported `source_context_included=false`.
- A synthetic email was redacted in the preview. Submitting `confirmed=false` returned HTTP 400; the egress ledger count did not change, confirming the preview itself does not call Nebius.
- A local mock model response exercised compile persistence, custom-workflow execution, checkpoint receipt, and skill revision from version 1 to version 2 without network calls or mock egress receipts.
- Static API checks rejected an output-type mismatch (`string_list` passed where `loop_list` is required) and a node that downgraded untrusted source text to trusted.
- In an isolated synthetic database, a reminder proposal under L1 stayed pending; under L2 it executed through the existing autonomy API and received an undo deadline. No network calls were made.
- The compile-confirm endpoint was not used with the live model. Generated-spec quality, latency, schema success rate, and actual egress receipt for compilation remain unmeasured.
- Existing built-in workflow validation/execution and source-deletion behavior remained covered by Iteration 14 runtime evidence.

## Decisions and limits

- A user must separately approve model egress to compile, then review the generated plan and approve a run containing local writes.
- Compilation is constrained to registered local tools. The system cannot create a new capability by generating a new tool name.
- The current registry and executor have no general `map`, branch, loop, arbitrary code, web, OAuth, external writes, or schedule node. Requests outside current tools must be described as unsupported rather than silently simulated as completed.
- This is a bounded personal task agent, not near-AGI. Live model compilation is the next proof step and remains behind the visible confirmation control.
