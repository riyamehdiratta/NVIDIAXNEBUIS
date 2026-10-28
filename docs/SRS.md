# Threadline Software Requirements Specification

**Version:** 0.9 | **Status:** Local autonomy, scam triage, precommitments, synthetic demo guard, seven-day replay, local extraction evaluation, and source-view runtime fix implemented; live Token Factory/OpenShell proof and public hosting pending | **Updated:** 2026-10-28

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
| FR-12 | Keep data local by default; export and delete. | JSON export includes source memory, policies, autonomy setting, actions/undo receipts, reminders, activity, scam-check receipts, non-secret family profile metadata, precommitments, and egress ledger; no model call occurs without explicit confirmation. |
| FR-13 | Run a local import watcher and daily review. | Worker records local activity; it never sends content to a model. |
| FR-14 | Triage suspicious message text locally. | Explainable pressure signals and safety steps are returned; only a digest, length, and signal labels are stored, with zero model egress. |
| FR-15 | Verify a trusted contact with a private phrase. | Phrase is PBKDF2 salted-hashed and never returned by profile APIs; verified and failed checks are logged locally. It is static in this iteration, so it must be shared through a trusted channel and is not a rotating challenge. |
| FR-16 | Compile a supported plain-language quiet-hours precommitment. | Red-team boundary checks pass; the API checks active rules when proposing and approving actions, blocks automatic execution, and requires/logs a typed reason to override manually. |
| FR-17 | Keep hosted demo ingestion synthetic-only. | With `THREADLINE_DEMO_MODE=1`, pasted/file imports return 403, the folder watcher is disabled, and only curated demo samples can be loaded. |
| FR-18 | Show aggregate model data movement. | The privacy panel reports file attachments, request attempts, successful responses, regex redaction matches, local scans, and request payload characters; local-only scans produce no egress request. |
| FR-19 | Replay earned autonomy over a synthetic week. | A seven-day replay uses the live Wilson/majority helper functions, presents the threshold evidence and an unearned approval-only example, and writes no workspace records. |
| FR-20 | Measure local extraction on a labeled synthetic corpus. | A repeatable 60-source command reports source-level precision, recall, and F1 for local heuristics and offers an opt-in, explicitly confirmed Nebius comparison on synthetic data. |
| FR-21 | Render the source import guide without runtime errors. | The Sources view resolves all file-format icons and renders with both empty and populated source lists. |

## 3. Autonomy state and limits

- **L0 Observe:** extraction/search only; action proposals are rejected.
- **L1 Ask:** actions wait in the review queue.
- **L2 Undo window:** opted-in reversible local reminder/draft actions may run automatically and can be undone for ten minutes.
- **L3 Daily report:** same bounded local execution as L2, with an additional activity report entry.
- **L4 Capped:** same local tool allowlist, checked per-action daily cap, global pause, and undo.

Shadow mode uses an interpretable majority-choice baseline, not an LLM claim about user intent. It abstains until five prior explicit choices exist. Scored prediction data is not shown on pending actions. Current policy controls are application/database enforcement; they are not a substitute for OpenShell or OS-level isolation. Manual user approvals remain possible while the global automation switch is paused.

## 4. Data model and interfaces

SQLite schema version 5 stores `sources`, `loops`, `skills`, `policies`, `actions`, `reminders`, `egress_events`, `scan_previews`, `daily_reviews`, `app_settings`, `scam_checks`, `family_profiles`, and `contracts`. Policies contain autonomy level, life area, shadow aggregates, and daily cap. Action rows store execution mode, policy level, shadow comparison, undo deadline, inverse receipt, applicable contract, and manual override reason.

Main interfaces include `GET/PUT /api/policies/{action_type}`, `GET/PUT /api/autonomy`, `POST /api/actions/{id}/undo`, action proposal/decision routes, source/skill/loop routes, and the exact-preview scan routes.
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

## 7. Known limits and next work

No OAuth connectors, Gmail/Calendar write integration, Nebius Serverless schedule, Hermes process integration, or active NemoClaw/OpenShell sandbox is implemented yet. Iteration 07 delivers only quiet-hours precommitments, not the broader Ulysses vision or a general constitution compiler. Bi-temporal belief revision is also pending. The Scam Antibody slice only includes local message triage and static trusted-contact phrases; it has no rotating challenge protocol, browser sandbox, or personalized susceptibility profile. These remain future iterations and must not be described as working features. The current workspace has no Nebius key, Docker runtime, or public Git remote, so live Token Factory behavior, cloud deployment, and external policy-denial tests remain unverified.
