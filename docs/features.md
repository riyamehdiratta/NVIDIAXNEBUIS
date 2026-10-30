# Threadline feature guide

This guide describes features in the current local build. “Available” means implemented in the application; optional remote model calls still need a Nebius Token Factory API key.

## Capture and organize information

- **Import sources:** Paste a note or import `.txt`, `.md`, `.csv`, `.log`, `.eml`, and `.ics` files. A local worker can also watch `data/imports/` while Threadline is running.
- **Find commitments:** Local extraction identifies candidate tasks, promises, waiting items, and events. If configured, a user-approved Nemotron scan can analyze selected sources. Results retain evidence links and confidence so the user can inspect and correct them.
- **Open Loops:** Review, search, filter, correct, dismiss, or complete commitments. The dashboard shows upcoming work and waiting items.
- **Daily reset:** The reusable daily-reset skill prepares a prioritized view from selected, unscanned sources. Preview the payload before any remote request.
- **Delete and export:** Delete a source and its directly derived loops, or export workspace records as JSON.

## Reusable skills

Threadline includes editable `Commitment scan`, `Daily reset`, and `Follow-up draft` skills. Users can inspect instructions, edit or disable skills, and rerun them on imported sources. A skill can suggest work but cannot grant itself new tool permissions.

## Agent workflows

The **Agent workflows** view accepts a natural-language task and asks Nemotron 3.5 Lightning to compose a typed workflow from Threadline's registered tools. The exact redacted compile request is shown before the user confirms model egress. The compiler receives no sources or memory. The validated workflow can be saved as a one-off task or reusable skill; a saved skill can be revised into a new version. Before every run, Threadline shows the tool sequence and side effects. The user approves a workflow plan containing writes; reminder and draft proposals then pass through per-action L0-L4, pause, quiet-hours, caps, review queue, and undo controls. Email remains unsent. The executor cannot invent tools, run arbitrary code, browse the web, or use external connectors. The public synthetic-data demo disables custom compilation to protect its hosted provider key. The preview path is implemented; a live compiler call and generated-plan quality are not yet measured.

Workflow specs and runs are stored locally in SQLite. Per-node checkpoints support resume, idempotency keys prevent duplicate run creation, and deleting a source removes linked derived workflow receipts. See [the workflow runtime guide](agent-os/workflow-runtime.md).

## Local actions and autonomy

Threadline can create local reminders, save unsent reply drafts, and export calendar `.ics` files. It never sends email or performs payments. The Permissions view provides:

- Per-action autonomy levels L0-L4 and life-area labels.
- Shadow mode that scores a majority-choice baseline against later explicit decisions. Wilson lower-bound evidence may suggest promotion; only the user can change the level.
- A global pause, daily action caps, and a ten-minute undo for automatic reminders and drafts. Undo records an inverse receipt and lowers the action level.
- Local quiet-hours precommitments. The narrow compiler checks supported time windows at proposal and approval; manual override asks for a reason and logs it.

These are application-level checks around Threadline's own local tools, not a deployed OS sandbox.

## Scam check and trusted contacts

Scam Check locally flags common urgency, impersonation, credential, payment, remote-access, secrecy, and shortened-link patterns. The score is a heuristic signal score, not a probability or verdict. The pasted text is not retained; history stores a digest and signal labels. Trusted-contact phrases are salted PBKDF2 hashes and can be checked locally.

## Privacy and model access

Sources and memory are stored in a local SQLite database. Before a remote scan, Threadline shows the exact minimized request and applies pattern-based redaction; the user must confirm. A local egress receipt stores the request and result status. Local extraction works without a model key. The configured models are NVIDIA Nemotron 3.5 Lightning for routine extraction and Nemotron 3 Super for larger or ambiguous scans via Nebius Token Factory.

The application does not encrypt the SQLite database itself. Redaction is incomplete. Only send data after reviewing the preview.

## Background work

While the host process is running, a local worker checks the import folder about every 20 seconds and writes a daily review summary at its scheduled poll. It does not call a model on its own. This is a local background worker, not a cloud-hosted always-on service.

## Not included in this build

Direct Gmail/Google Calendar/Outlook connectors, external message sending, payment actions, Nebius Serverless schedules, Hermes Agent runtime integration in the app, arbitrary-code/web workflow nodes, general natural-language policy compilation, encrypted database storage, and public hosting are not currently implemented. OpenShell's managed provider path has separate local verification but is not the current standalone app's process boundary.
