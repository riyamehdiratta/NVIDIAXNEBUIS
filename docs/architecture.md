# Architecture and operational boundaries

## Components

- **React/Vite:** Dashboard, Open Loops, Skills, Permissions, Sources, and Privacy & Activity views.
- **FastAPI:** JSON APIs, parsers, extraction adapter, action policy, and static production UI serving.
- **SQLite:** Sources, extracted open loops, skills, per-action policies, shadow evidence, action receipts, local reminders, daily reviews, and model egress receipts. Schema versions use `PRAGMA user_version`.
- **Scam triage (`scam.py`):** Deterministic local checks for authority threats, urgency, credential requests, payment pressure, remote-access requests, secrecy pressure, and shortened links. Only a digest and matched signal labels are retained. Trusted-contact phrases are salted-hashed locally.
- **Autonomy engine (`autonomy.py` + API checks):** L0-L4 per action type, shadow baseline scoring, Wilson confidence summary, daily caps, global pause, undo receipts, and demotion. This is application enforcement for Threadline's local handlers, not a kernel sandbox.
- **Precommitment compiler (`contracts.py` + API gate):** Parses a deliberately narrow quiet-hours statement, runs boundary checks at start/interior/end, and stores the resulting time range. The action API checks it both before automatic execution and at manual approval; an override reason is persisted in the action receipt.
- **Background worker:** Polls the selected import folder every 20 seconds. At the first 9 a.m. poll each day it writes a daily review summary. It never sends content to a model itself.
- **Model adapter:** Calls the OpenAI-compatible Nebius Token Factory Chat Completions endpoint after explicit UI confirmation. When no key is configured, the local heuristic parser remains available.

## Data flow

1. User selects a file or text. The API parses supported source types and stores the normalized text and a content digest locally.
2. A preview builds a prompt from selected unscanned sources, applies pattern-based redaction to email, phone, SSN, and long-number patterns, and returns the exact request JSON and selected Nemotron model.
3. The preview also creates a ten-minute, single-use token bound to source digests, selected skill instructions, model, and exact request body. Only after the user confirms, the API validates those bindings, consumes the token, records the request body, and calls Token Factory. The response is parsed into candidate open loops. Evidence references are checked against local source text; unsupported model quotations are replaced by a local matching excerpt.
4. The user reviews each loop and any proposed action. Approved local reminders/drafts/calendar exports are written to the local database or returned as downloadable files.
5. Before automatic execution, the API checks the global switch, per-action level, reversible-tool allowlist, and that tool's UTC-day cap. Shadow mode leaves actions in the review queue, compares a private majority-choice prediction with the later decision, and accumulates statistical evidence. The system never raises the level automatically.
6. Active precommitments are checked against the host's local clock at proposal and approval time. A matching rule disables automatic execution; manual approval requires a reason of at least 20 characters, which is stored with the action.

## Failure behavior

- Unsupported file formats return HTTP 415; imports over 2 MB return HTTP 413; duplicate text content is deduplicated by SHA-256 digest.
- A Token Factory timeout, provider error, or malformed model response leaves sources unscanned for retry, records a failed egress receipt where a request was attempted, and does not mutate external systems.
- A model-supplied quote not found in the original source is not shown as verified evidence. Low-confidence loops are explicitly flagged for review.
- Deleting a source deletes loops derived directly from it. It does not delete user-approved reminders already created from those loops.
- The public/demo deployment must use synthetic data and must not accept sensitive records. Personal deployments should stay on a user-managed host.

## Runtime and security

Direct local mode uses the user's environment key and sends one approved request to Token Factory. The in-app policy checks constrain Threadline's own local action handlers; they are not an OS-level sandbox. A NemoClaw/OpenShell deployment must keep the provider credential in OpenShell and route inference through the sandbox-managed provider; do not place a real key in the image or source. The sample runbook describes the intended configuration but still requires setup and verification on a supported Linux host. Windows WSL2 is experimental for OpenShell. Hermes is not currently launched by this application.

This app's database is not encrypted by the application, and the regex redactor is not a complete de-identification system. See the UI's privacy notice and README.


## Earned autonomy

L0 is observe-only; L1 queues actions; L2 allows opted-in reversible local actions with a ten-minute undo; L3 adds a report entry; L4 applies the configured per-tool daily cap. Only reminders and unsent drafts are reversible in this build. Calendar exports always require approval. Shadow mode abstains before five prior decisions; after a comparison, the API updates a Wilson 95% lower bound. Promotion is suggested only after 40 predictions and a bound of at least 0.80. Shadow predictions use a majority of historical explicit choices, not an LLM, and are hidden until the action decision is recorded.


## Local scam triage

The scam checker uses a small, inspectable set of text patterns and returns signals plus general verification steps. The score is a heuristic signal score, not a probability and not proof of fraud. It does not follow links, inspect attachments, call a model, or retain the pasted message; the local history stores its SHA-256 digest, length, score, and signal labels. Family verification phrases are static in this MVP, PBKDF2-hashed with a random salt, and stored in the same unencrypted local SQLite database. Choose a unique phrase and share it through a trusted channel.

## Precommitments

Iteration 07 supports quiet-hour rules such as “No automatic actions from 22:00 to 07:00.” The compiler requires an explicit blocker phrase, supported action scope, and a 24-hour time range. It tests the inclusive start, an interior time, the final minute before end, the exclusive end, and a point after end. This is a narrow rule compiler, not general natural-language understanding. Times use the host's local timezone. The override path adds friction and an audit receipt; it is not an unbreakable safety boundary.
