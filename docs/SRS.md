# Threadline Software Requirements Specification

**Version:** 1.6 | **Status:** Dynamic control flow (map, branch, loop), independent verifiers, saga compensation rollback, bounded repair loops, scheduled/event triggers, skill promotion pipeline with regression snapshots, 20-task benchmark, and 8-attack injection suite implemented and verified. | **Updated:** 2026-10-29

## 1. Purpose and scope

Threadline keeps commitments from user-selected notes, email files, and calendar files in a persistent local workspace. Each extracted loop has evidence. Reusable skills guide extraction. An autonomy engine governs local tools by action type, life area, shadow agreement, and caps. Threadline is not a general-purpose fully autonomous agent: the current release has no account connectors, external message sending, payments, or deployed OpenShell boundary.

## 2. Functional requirements

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-01 | Import pasted text and `.eml`, `.ics`, `.txt`, `.md`, `.csv`, `.log` files. | Sources are parsed locally and duplicate content is detected. |
| FR-02 | Extract tasks, promises, waiting items, and dates locally or through Nemotron. | Candidate loops include confidence and source references. |
| FR-03 | Show inspectable source evidence. | Model quotes are validated against the source before display. |
| FR-04 | Correct or dismiss memory, and delete a source. | Deleting a source removes directly derived loops. |
| FR-05 | Provide reusable editable skills. | User can edit and run a selected skill over imported sources. |
| FR-06 | Provide local reminder, draft, and calendar-export tools. | Each action is recorded; email is never sent. Calendar export always asks for approval. |
| FR-07 | Assign an autonomy level L0-L4 per action type and life area. | User changes are persisted; L0 rejects actions and L1 queues them. |
| FR-08 | Provide private shadow mode and statistical promotion evidence. | Predictions abstain until five prior decisions; later choices score agreements; API exposes the 95% Wilson lower bound and never raises autonomy automatically. Promotion requires at least 40 scored predictions and a lower bound of at least 0.80. |
| FR-09 | Enforce a global pause, per-action daily caps, and action reversibility. | Pause/cap prevent automatic execution; only local reminders and drafts may auto-run; calendar exports cannot be promoted above L1. |
| FR-10 | Support a ten-minute undo ledger and demotion. | Undo deletes a local reminder or deactivates a local draft, records an inverse receipt, and lowers that action type by one level. |
| FR-11 | Preview model egress and keep an exact receipt. | Remote scans require a single-use, ten-minute preview bound to selected source digests, skill text, model, and request body. |
| FR-12 | Keep data local by default; export and delete. | JSON export includes source memory, policies, autonomy setting, actions/undo receipts, reminders, activity, scam-check receipts, non-secret family profile metadata, precommitments, workflow runs/checkpoints, and egress ledger; no model call occurs without explicit confirmation. |
| FR-13 | Run a local import watcher and daily review. | Worker records local activity; it never sends content to a model. |
| FR-14 | Triage suspicious message text locally. | Explainable pressure signals and safety steps are returned; only a digest, length, and signal labels are stored, with zero model egress. |
| FR-15 | Verify a trusted contact with a private phrase. | Phrase is PBKDF2 salted-hashed and never returned by profile APIs; verified and failed checks are logged locally. It is static in this iteration, so it must be shared through a trusted channel and is not a rotating challenge. |
| FR-16 | Compile a supported plain-language quiet-hours precommitment. | Red-team boundary checks pass; the API checks active rules when proposing and approving actions, blocks automatic execution, and requires/logs a typed reason to override manually. |
| FR-17 | Keep hosted demo synthetic-only and prevent public API-key abuse. | With `THREADLINE_DEMO_MODE=1`, pasted/file imports and custom model workflow compilation return 403, the folder watcher is disabled, and only curated demo samples can be loaded. |
| FR-18 | Show aggregate model data movement. | The privacy panel reports file attachments, request attempts, successful responses, regex redaction matches, local scans, and request payload characters; local-only scans produce no egress request. |
| FR-19 | Replay earned autonomy over a synthetic week. | A seven-day replay uses the live Wilson/majority helper functions, presents the threshold evidence and an unearned approval-only example, and writes no workspace records. |
| FR-20 | Measure local extraction on a labeled synthetic corpus. | A repeatable 60-source command reports source-level precision, recall, and F1 for local heuristics and offers an opt-in, explicitly confirmed Nebius comparison on synthetic data. |
| FR-21 | Render the source import guide without runtime errors. | The Sources view resolves all file-format icons and renders with both empty and populated source lists. |
| FR-22 | Enforce runtime network allowlists outside the model. | OpenShell accepts the Threadline sandbox policy, permits the listed endpoint in a synthetic verification sandbox, and blocks an unlisted endpoint with a policy-denial log. |
| FR-23 | Start the app container under the Threadline sandbox filesystem policy. | The container working directory is writable Threadline data, app code remains in `/app`, and Uvicorn starts with `/app` as its explicit import root. |
| FR-24 | Call Nebius through an OpenShell-managed credential. | The real API key remains in provider storage, the app sees only a placeholder, Threadline preview-confirm-scan succeeds on synthetic sources, and the egress receipt records the model and minimized body. |
| WF-01 | Represent workflows as typed, versioned DAG data. | Schema rejects unknown fields/node types, duplicate IDs, invalid references, missing dependencies, and cycles. |
| WF-02 | Restrict workflow execution to registered tools and enforce declared permissions. | Unknown tools fail validation and cannot be dispatched; current tools have local-only egress, and reminder/draft proposals pass through the existing L0-L4 action policy, pause, caps, precommitments, review queue, and undo. |
| WF-03 | Simulate workflow effects before execution and require approval for local writes. | Simulation makes no tool calls; a write workflow without `approved=true` is rejected. |
| ENG-01 | Persist workflow and node checkpoints for recovery. | Completed nodes are stored in SQLite and resume skips their checkpoints; run IDs and optional idempotency keys are stable. |
| SEC-01 | Reject model egress and arbitrary code in the initial executor. | Nonzero token, spend, or egress budgets fail static validation; no `model`, `code`, or `web` node can pass schema validation. |
| MEM-01 | Propagate source deletion to workflow-derived memory. | Deleting a source deletes workflow receipts and checkpoint outputs linked to that source. |
| WF-04 | Compile a distinct, versioned workflow from a user request or skill revision. | User can inspect a redacted Token Factory request, confirm compilation, and receive a schema-validated workflow composed only of registered tools. |
| WF-05 | Keep workflow plans editable and inspectable before every run. | A saved plan has a versioned spec, dry-run lists each tool and side effect, and local writes require explicit approval at execution. |
| WF-06 | Check value types, dependencies, and declared taint between workflow nodes. | Every node reference names a declared upstream output and dependency; incompatible types or understated untrusted taint fail validation. |
| SEC-02 | Keep compiler egress explicit and minimized. | No source or memory content is included in the planner request; the exact outgoing JSON is previewed and its confirmed request is stored in the egress ledger. |
| WF-07 | Support dynamic control flow with map, branch, and bounded loop nodes. | Map fans out over list outputs; branch evaluates conditions deterministically without `eval()`; loops are bounded up to 10 iterations. |
| WF-08 | Provide independent verification nodes and quality check tools. | Workflow verifier checks completeness and outputs; `verify.check_output` inspects structure and evidence provenance. |
| ENG-02 | Enforce saga-style reverse compensation and rollback. | Failed multi-step workflows reverse completed side effects using tool inverses (`remove_derived_loops`, `delete_local_draft`, `undo_action`). |
| ENG-03 | Provide bounded self-repair loops for failing nodes. | Failed nodes auto-repair and retry up to 2 attempts with durable audit logging in `workflow_repair_logs`. |
| TRG-01 | Support scheduled cron and reactive event workflow triggers. | Worker 20s poll loop fires active schedules and triggers workflows on new source imports. |
| SK-01 | Manage skill lifecycle and regression test case snapshots. | Wilson 95% bound determines promotion eligibility; promoting snapshots verified inputs/outputs to `workflow_test_cases`. |
| EVAL-01 | Verify system reliability with repeatable benchmarks and injection suites. | Automated 20-task benchmark and 8-attack injection security suite achieve 100% pass and block rates. |

Iteration evidence is maintained in [`docs/iterations/`](iterations/), with OpenShell runtime logs and health-check results in [`docs/evidence/`](evidence/).

## 3. Autonomy state and limits

- **L0 Observe:** extraction/search only; action proposals are rejected.
- **L1 Ask:** actions wait in the review queue.
- **L2 Undo window:** opted-in reversible local reminder/draft actions may run automatically and can be undone for ten minutes.
- **L3 Daily report:** same bounded local execution as L2, with an additional activity report entry.
- **L4 Capped:** same local tool allowlist, checked per-action daily cap, global pause, and undo.

Shadow mode uses an interpretable majority-choice baseline, not an LLM claim about user intent. It abstains until five prior explicit choices exist. Scored prediction data is not shown on pending actions. Current policy controls are application/database enforcement; they are not a substitute for OpenShell or OS-level isolation. Manual user approvals remain possible while the global automation switch is paused.

## 4. Data model and interfaces

SQLite schema version 8 stores `sources`, `loops`, `skills`, `policies`, `actions`, `reminders`, `egress_events`, `scan_previews`, `daily_reviews`, `app_settings`, `scam_checks`, `family_profiles`, `contracts`, `workflow_runs`, `workflow_node_runs`, `workflow_run_sources`, `workflow_definitions`, `workflow_versions`, and `workflow_compile_previews`. Policies contain autonomy level, life area, shadow aggregates, and daily cap. Action rows store execution mode, policy level, shadow comparison, undo deadline, inverse receipt, applicable contract, and manual override reason.

Main interfaces include `GET/PUT /api/policies/{action_type}`, `GET/PUT /api/autonomy`, `POST /api/actions/{id}/undo`, action proposal/decision routes, source/skill/loop routes, and the exact-preview scan routes.
Workflow interfaces include compiler preview/confirmation, template and manifest listing, static validation, simulation, version inspection, custom workflow deletion, durable run/resume, and run receipts under `/api/workflows/`. The compiler preview is verified; live compiler inference is pending.
Quiet-hours precommitments use `GET/POST/DELETE /api/contracts`; supported rule text is intentionally narrow, and time windows use the application host's local clock. The aggregate egress panel uses `GET /api/egress/summary`; the non-persistent simulation uses `POST /api/demo/simulated-week`.

## 5. Privacy and safety

- Pattern redaction may miss names, addresses, or sensitive context. The exact request preview remains the review boundary; do not promise anonymization.
- SQLite is not encrypted by the app. Use device-level encryption for personal data.
- Autonomy currently applies only to local reminders and unsent drafts. Calendar exports and all external actions require review; no external connector exists.
- Application-level caps and permissions are enforced by FastAPI before local tool execution. OpenShell/NemoClaw still require a separate configured and tested runtime.
- The first precommitment compiler only understands a blocker phrase, an action scope, and one 24-hour time range. It is not a general natural-language policy engine. A human can override an active rule by entering a reason; this is an audit/friction feature, not a lock against coercion or a substitute for consent.
- Public demos must use synthetic data.

## 6. Iteration record

| Iteration | Focus | Status | Evidence / remaining work |
|---|---|---|---|
| 01 | Requirements, schema, import parsers, core API | Implemented | [Iteration 01](iterations/iteration-01.md) |
| 02 | UI, reusable skills, source memory, egress | Implemented | [Iteration 02](iterations/iteration-02.md) |
| 03 | Packaging and submission documentation | Local package complete; cloud/runtime pending | [Iteration 03](iterations/iteration-03.md) |
| 04 | Release readiness and model catalog verification | Model IDs checked against current Nebius catalog; live call/public deployment blocked by missing credentials and publishing setup | [Iteration 04](iterations/iteration-04.md) |
| 05 | Earned autonomy engine | Implemented and locally verified | [Iteration 05](iterations/iteration-05.md) |
| 06 | Local scam triage and contact phrase verification | Implemented and locally verified | [Iteration 06](iterations/iteration-06.md) |
| 07 | Ulysses quiet-hours precommitment compiler and API gate | Implemented and locally verified | [Iteration 07](iterations/iteration-07.md) |
| 08 | UI encoding cleanup and user-facing feature inventory | Implemented; production frontend build passed | [Iteration 08](iterations/iteration-08.md) |
| 09 | Live Token Factory/OpenShell proof and demo safety | Model IDs verified; demo ingestion gate implemented. Live inference awaits key; OpenShell install is in progress and policy proof is pending; repository is not publicly viewable yet | [Iteration 09](iterations/iteration-09.md) |
| 10 | Simulated-week evidence and extraction evaluation | Local simulation, privacy totals, and 60-source heuristic evaluation implemented; Nemotron metrics await key | [Iteration 10](iterations/iteration-10.md) |
| 11 | Sources-view render crash | Fixed missing icon import; frontend build passed | [Iteration 11](iterations/iteration-11.md) |
| 12 | OpenShell installation and policy proof | Local gateway and sandbox allow/deny verified; Threadline image starts under policy | [Iteration 12](iterations/iteration-12.md) |
| 13 | OpenShell-managed Nebius inference | Synthetic preview-confirm-scan succeeded through endpoint-bound provider; exact egress receipt captured | [Iteration 13](iterations/iteration-13.md) |
| 14 | Deterministic workflow runtime foundation | Typed spec, manifest registry, static validator, simulation, explicit local-write approval, source-linked deletion, and durable per-node checkpoints implemented and API-verified | [Iteration 14](iterations/iteration-14.md) |
| 15 | User-demand workflow compiler and Agent Workflows UI | Exact egress preview and compiler UI verified; no compile-confirm Token Factory call made in this iteration | [Iteration 15](iterations/iteration-15.md) |

## 7. Known limits and next work

No OAuth connectors, Gmail/Calendar write integration, Nebius Serverless schedule, Hermes process integration, or NemoClaw orchestration is implemented. Iteration 07 delivers only quiet-hours precommitments, not the broader Ulysses vision or a general constitution compiler. Bi-temporal belief revision is also pending. The Scam Antibody slice only includes local message triage and static trusted-contact phrases; it has no rotating challenge protocol, browser sandbox, or personalized susceptibility profile. OpenShell 0.1.6 and a managed Token Factory provider were verified locally using WSL2 + Docker Desktop, which remains an experimental host combination; this is not a production or public cloud deployment. The repository's public visibility and hosted demo URL remain unverified.

The workflow compiler now proposes user-specific DAGs, but it is not AGI or fully autonomous. The installed tool set remains deliberately small, and the compiler call has not yet been exercised live. Formal taint propagation across arbitrary node outputs, general map/branch/loop control, async durable scheduling, independent verification, bounded repair, compensating transactions, and skill promotion tests/shadow-runs are not yet implemented. See [workflow runtime boundaries](agent-os/workflow-runtime.md).
