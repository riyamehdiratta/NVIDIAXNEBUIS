# Threadline workflow runtime (Iteration 14)

Threadline now has a deterministic workflow substrate. Specs are versioned data; the server validates them and dispatches only named tools from a closed registry. A model cannot add a tool, Python code, or a network destination by writing a workflow.

## Current API

- `GET /api/workflows/templates` lists the three installed skill workflows.
- `GET /api/workflows/tools` returns the runtime tool manifests.
- `POST /api/workflows/validate` statically checks a submitted spec and input values.
- `POST /api/workflows/simulate` returns the ordered nodes, local effects, risk, and data-egress declaration without running tools.
- `POST /api/workflows/runs` executes an installed template and checkpoints each completed node in SQLite. Pass an `idempotency_key` to return the existing run for a repeated request.
- `GET /api/workflows/runs` and `GET /api/workflows/runs/{id}` inspect durable run receipts.
- `POST /api/workflows/runs/{id}/resume` resumes from completed node checkpoints.

The installed templates map Commitment scan to the existing local-only source scanner, Daily reset to open-loop retrieval and prioritization, and Follow-up draft to a source-grounded unsent local draft. Any workflow containing a local write requires the caller to review simulation and set `approved: true` on the run request. The endpoint still runs only locally registered handlers.

## Spec and validation rules

The Pydantic `WorkflowSpec` in `backend/app/workflows.py` is the source of truth for the JSON structure; its generated [JSON Schema](workflow-spec.schema.json) and [tool manifests](tool-manifests.json) are published alongside this guide. Specs have an ID/version, origin, on-demand trigger, typed inputs, explicit budgets, and an ordered DAG of `tool`, `approval`, or `verify` nodes. Extra fields are rejected. Validation checks duplicate IDs, dependencies, cycles, tool registration, declared arguments, risk labels, input types, and references. Model tokens, spend, and remote egress must be zero in this release. `code`, `web`, `model`, loops, schedules, and subworkflows cannot execute yet.

Tool manifests declare side effects, risk, inverse, permission scope, egress, taint output, and argument types. The first registry contains only local source/memory reads, local heuristic scan, and draft generation. Unknown tools fail validation and cannot execute.

## Durability and safety limits

SQLite schema version 7 stores `workflow_runs`, `workflow_node_runs`, and source provenance in `workflow_run_sources`. The runner persists node start, output, completion, and error around each step. Resume skips completed nodes. Idempotency keys prevent duplicate run creation and reject key reuse with different inputs. Deleting a source cascades to its linked workflow receipts/checkpoints, including derived draft output. This first runtime is synchronous, runs one local step at a time, and does not yet guarantee exactly-once behavior if the process crashes during a tool's side effect before its checkpoint is committed. Existing scan deduplication makes its local retry safe; future side-effecting tools need durable idempotency and compensation before they enter the registry.

Simulation is descriptive; it is not a sandbox. OpenShell remains the runtime network/filesystem boundary for the deployed inference configuration. No model-generated planner is connected to this executor in this iteration. There are no external writes, OAuth scopes, arbitrary code, bounded repair, independent verifier model, or scheduled workflow triggers in this release.

## Example

```json
{
  "workflow_id": "follow-up-draft",
  "inputs": {"source_id": "<local-source-id>"}
}
```

Call `/simulate` first. If the preview matches the intended source, execute with `approved: true`. The returned receipt keeps the draft local and explicitly reports `sent: false`.
