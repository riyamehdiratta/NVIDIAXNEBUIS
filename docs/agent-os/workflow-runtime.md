# Threadline workflow runtime (Iterations 14-15)

Threadline has a deterministic workflow substrate and an opt-in Nemotron compiler. The compiler receives the redacted user request, the fixed tool manifests, and the workflow schema. When revising a saved workflow, its selected existing spec is also included. It does not receive source or memory content. The exact outgoing request is previewed and requires a separate confirmation. Specs are versioned data; the server validates them and dispatches only named tools from a closed registry. A model cannot add a tool, Python code, or a network destination by writing a workflow.

## Current API

- `GET /api/workflows/templates` lists the built-in workflows and saved custom workflows.
- `GET /api/workflows/tools` returns the runtime tool manifests.
- `POST /api/workflows/compile/preview` builds the exact minimized Nemotron planner request; it does not send it.
- `POST /api/workflows/compile/confirm` sends a previously previewed request only when `confirmed: true`, validates the returned spec, and saves a new workflow or version.
- `DELETE /api/workflows/compile/previews/{id}` deletes an unconfirmed preview and its locally retained task text.
- `GET /api/workflows/definitions/{id}` inspects the active spec and saved version history; `DELETE` removes a custom workflow and its run history.
- `POST /api/workflows/validate` statically checks a submitted spec and input values.
- `POST /api/workflows/simulate` returns the ordered nodes, local effects, risk, and data-egress declaration without running tools.
- `POST /api/workflows/runs` executes a built-in or saved custom workflow and checkpoints each completed node in SQLite. Pass an `idempotency_key` to return the existing run for a repeated request.
- `GET /api/workflows/runs` and `GET /api/workflows/runs/{id}` inspect durable run receipts.
- `POST /api/workflows/runs/{id}/resume` resumes from completed node checkpoints.

The installed templates map Commitment scan to the existing local-only source scanner, Daily reset to open-loop retrieval and prioritization, and Follow-up draft to a source-grounded unsent local draft. In the Agent Workflows view, a user can compile a one-off task or save it as a reusable skill; selecting a saved custom skill as the starting point creates a new numbered version. Any workflow containing a local write requires the caller to review simulation and set `approved: true` on the run request. Registered reminder/draft proposal tools go through the existing action API, which enforces per-action L0-L4, global pause, quiet-hours precommitments, daily caps, approval queues, and undo. Email drafts remain unsent.

## Spec and validation rules

The Pydantic `WorkflowSpec` in `backend/app/workflows.py` is the source of truth for the JSON structure; its generated [JSON Schema](workflow-spec.schema.json) and [tool manifests](tool-manifests.json) are published alongside this guide. Specs have an ID/version, origin, on-demand trigger, typed inputs, explicit budgets, and an ordered DAG of registered `tool` nodes. Extra fields are rejected. Validation checks duplicate IDs, dependencies, cycles, tool registration, declared argument and output types, risk labels, input types, references, and declared taint. Workflow execution budgets require zero model tokens, spend, and egress. `approval` is a run-level user checkpoint; unsupported node types such as `code`, `web`, `model`, loops, schedules, and subworkflows cannot compile or execute.

Tool manifests declare side effects, risk, inverse, permission scope, egress, typed outputs, and output taint. Values flow from upstream outputs only across declared dependency edges. The registry contains local source/memory reads, local heuristic scan, source-grounded draft generation, and local reminder/draft proposals routed through Threadline's policy API. Unknown tools, incompatible value types, or taint downgrades fail validation and cannot execute.

## Durability and safety limits

SQLite schema version 8 stores run/node checkpoints, source provenance, saved workflow definitions and versions, and compiler previews. The runner persists node start, output, completion, and error around each step. Resume skips completed nodes. Idempotency keys prevent duplicate run creation and reject key reuse with different inputs. Deleting a source cascades to linked workflow receipts/checkpoints, including derived draft output. This first runtime is synchronous, runs one local step at a time, and does not yet guarantee exactly-once behavior if the process crashes during a tool's side effect before its checkpoint is committed. Existing scan deduplication makes its local retry safe; future side-effecting tools need durable idempotency and compensation before they enter the registry.

Simulation is descriptive; it is not a sandbox. OpenShell remains the runtime network/filesystem boundary for the deployed inference configuration. The planner request has a separate user confirmation and fixed maximum output budget; the compiler preview API and UI have been verified, but the compiler itself has not yet been verified with a live model call. There are no external writes, OAuth scopes, arbitrary code, bounded repair, independent verifier model, or scheduled workflow triggers in this release. This is a constrained agent system, not AGI.

## Example

```json
{
  "workflow_id": "follow-up-draft",
  "inputs": {"source_id": "<local-source-id>"}
}
```

Call `/simulate` first. If the preview matches the intended source, execute with `approved: true`. The returned receipt keeps the draft local and explicitly reports `sent: false`.
