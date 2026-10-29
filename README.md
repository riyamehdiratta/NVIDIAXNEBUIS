# Threadline

**A private personal AI that keeps life's open loops moving.**

Threadline turns the commitments buried in user-selected emails, calendar files, and notes into a persistent, source-linked view of what is due, what is waiting, and what the user promised. Its earned-autonomy engine measures shadow agreement, enforces per-action levels and caps, and lets the user pause or undo local actions. Model requests show their exact minimized payload before sending it to NVIDIA Nemotron through Nebius Token Factory.

## Why Threadline

AI assistants can summarize individual messages. Threadline keeps the follow-up alive after the chat: every open loop is linked to evidence, every skill is inspectable, and every action follows a user-controlled policy. Its memory is portable across `.eml`, `.ics`, and text files instead of being tied to a single provider's account.

The project addresses interruptions and information overload documented in Microsoft 365 work telemetry and a 2025 employee survey on email overload. These findings establish a common pain, not market-size estimates. See [the research notes](docs/research.md).

## What works

- Import pasted notes and `.txt`, `.md`, `.csv`, `.log`, `.eml`, or `.ics` files. A local background worker also watches `data/imports/`.
- Extract tasks, promises, waiting items, and events. Review evidence and confidence before acting.
- Search and correct open loops; mark them done, dismiss them, or delete their source and derived memory.
- Edit and reuse the included `Commitment scan`, `Daily reset`, and `Follow-up draft` skills.
- Run a skill over imported sources again from the Skills view. Existing source-linked loops are deduplicated.
- Check suspicious text locally for urgency, impersonation, credential, payment, remote-access, secrecy, and shortened-link signals. History keeps only a digest and signal labels; it is a warning aid, not a verdict. A trusted-contact phrase can be stored as a salted hash.
- Propose local reminders, calendar exports, and reply drafts. Actions wait for approval unless the user explicitly enables local automation for that action type.
- Assign L0-L4 autonomy by action type and life area. Shadow mode privately compares a majority-choice baseline to later decisions; a 95% Wilson lower bound informs, but never triggers, promotion.
- Pause autonomous execution instantly. Opted-in reminders and unsent drafts have a ten-minute undo window; undo demotes that action type. Per-tool daily caps are enforced by the API.
- Write a quiet-hours precommitment in supported plain language. Boundary tests run before saving; the API blocks matching auto-actions and requires a reason before a manual override.
- Calendar exports stay approval-only because Threadline cannot recall a downloaded file. The policy gate applies to local app tools and is not an OS sandbox.
- Use local heuristics without a model key. With a Nebius Token Factory key, preview a minimized/redacted request and explicitly confirm before calling Nemotron 3.5 Lightning or Nemotron 3 Super. Remote approvals are bound to a single-use, ten-minute preview; changed sources or skill instructions invalidate it. In an OpenShell deployment, a managed provider keeps the real key outside the sandbox and the policy allows only the Token Factory host/path.
- Inspect a log containing the exact request body, selected model, source IDs, redaction counts, status, and response summary. Completed draft/calendar tool results can be copied or downloaded from action history.
- Export memory and configuration to JSON.
- Run the installed Commitment scan, Daily reset, and Follow-up draft as versioned workflow DAGs. Inspect a dry run, validate tools and dependencies, approve local writes, and resume from SQLite node checkpoints; only registered local tools can execute.

## Quick start: local development

Requirements: Python 3.10+, Node.js 20+, and npm. A Nebius Token Factory account/key is needed for remote Nemotron inference; local-only mode works without it.

1. Create a Python environment and install the backend dependencies:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   ```

2. Start the API in one terminal:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   uvicorn backend.app.main:app --reload --port 8000
   ```

3. Start the UI in a second terminal:

   ```powershell
   cd frontend
   npm ci
   npm run dev
   ```

4. Open `http://localhost:5173`, select **Try the sample workspace**, then use **Review new information**. Choose **Local-only scan** or inspect the full request and explicitly confirm a Nebius scan.

To enable Nebius, copy `.env.example` to `.env`, add `NEBIUS_API_KEY`, stop and restart the API. Never commit `.env`. The app defaults to `https://api.tokenfactory.nebius.com/v1/`, model `nvidia/Nemotron-3_5-Lightning` for routine scans and `nvidia/nemotron-3-super-120b-a12b` when the source set is classified as ambiguous or large. These IDs were checked against the [Nebius NVIDIA Nemotron catalog](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference); availability can change. The exact model IDs and API path are configurable via environment variables.

## Docker

```powershell
Copy-Item .env.example .env
# Add NEBIUS_API_KEY to .env when available.
docker compose up --build
```

Open `http://localhost:8000`. Docker maps the app to loopback only and persists the SQLite database and import folder in `./data/`. The default hosted-style demo mode is off; click **Try the sample workspace** to add synthetic records.

For a disposable synthetic-data build, use `docker compose -f docker-compose.demo.yml up --build`. Demo mode disables pasted/file imports and the watched-folder importer; its SQLite data lives in a temporary filesystem. Configure a Nebius key in `.env` only if you intend to enable confirmed model scans in that demo.

## Data and privacy

- SQLite data and imported source text stay in the configured local data directory. This MVP does **not** encrypt that database itself; use device-level disk encryption and do not import sensitive data into a public demo.
- No Google, email, or calendar account is connected. Imports are explicit and user-selected.
- The remote scan preview shows the complete request JSON Threadline sends, excluding the authentication header. Email addresses, phone numbers, SSNs, and long digit sequences are replaced with placeholders. Redaction is pattern-based and cannot guarantee that every personal detail is removed.
- Scam Check makes no model call and does not retain the pasted message; its local history stores a digest, length, score, and signal labels. Family phrases are static in this MVP and hashed in the unencrypted SQLite database. Choose a unique phrase and continue verifying high-risk requests independently.
- Threadline sends no source files as attachments. If the user confirms, the selected, minimized text is sent to the chosen Nebius Token Factory model. The request and result status are recorded in the local egress log.
- If inference fails, local source data remains intact and no external action is performed. Local-only extraction remains available.
- Local action automation is limited to data in Threadline: reminders, `.ics` exports, and unsent drafts. Email is never sent, and no payment or external change is performed. These app checks do not replace OS-level sandboxing.

## Architecture

```text
React/Vite UI
    | JSON API
FastAPI ---- SQLite + local import watcher
    |---- parsers (.eml / .ics / text)
    |---- local extraction or Nebius Token Factory adapter
    |---- source-linked memory and editable skills
    `---- local action policy, approval queue, egress ledger
```

Backend modules are split by concern in `backend/app/`; the interface is split into workspace views and components in `frontend/src/`. Database schema changes are versioned through SQLite `user_version` migrations.

See [the feature guide](docs/features.md), [SRS](docs/SRS.md), [architecture and runtime notes](docs/architecture.md), [research](docs/research.md), [iteration records](docs/iterations/), and the [OpenShell/NemoClaw runbook](infra/nemoclaw/README.md). The shadow predictor is a majority-choice baseline, not an LLM accuracy claim. OpenShell 0.1.6 is installed with a local WSL gateway and has been verified with a managed Nebius Token Factory provider, a confirmed synthetic Nemotron scan, and a blocked unlisted destination. WSL2 + Docker Desktop remains an experimental OpenShell host combination.

The initial checkpointed workflow API and its boundaries are described in [the workflow runtime guide](docs/agent-os/workflow-runtime.md).

## API overview

- `POST /api/sources` and `POST /api/sources/text` - add a selected file or pasted text.
- `POST /api/scan/preview` - return the redacted model request and model choice before inference.
- `POST /api/scan` - perform local extraction or a user-confirmed remote inference call.
- `GET /api/loops`, `GET /api/loops/{id}`, `POST /api/loops/{id}/decision` - inspect and review memory.
- `GET /api/skills`, `PUT /api/skills/{id}`, `POST /api/skills/{id}/run` - inspect and reuse skills.
- `GET /api/policies`, `PUT /api/policies/{action_type}` - inspect or change local action policy.
- `GET /api/actions`, `POST /api/actions`, `POST /api/actions/{id}/decision` - propose and review local actions.
- `GET/POST/DELETE /api/contracts` - compile, inspect, and remove supported quiet-hours precommitments.
- `GET /api/egress`, `GET /api/export` - inspect model request receipts or export workspace data.
- `/api/workflows/templates`, `/tools`, `/validate`, `/simulate`, and `/runs` - inspect workflow skills/tools, validate and dry-run workflow plans, then execute approved local templates with durable run receipts.

## NVIDIA and Nebius use

Nemotron is a runtime model, not just a design reference: once `NEBIUS_API_KEY` is configured, the user can confirm a live OpenAI-compatible Chat Completions request to Nebius Token Factory. Lightning handles everyday extraction; Super handles cases flagged as ambiguous or unusually large. The app deliberately makes no inference call until the user inspects and confirms the minimized request.

Nebius Token Factory avoids requiring the project to provision and serve GPU model weights itself. A real three-source synthetic Threadline scan has run through an OpenShell-managed Nebius provider; the [receipt and latency](docs/evidence/nebius-tokenfactory-live.txt) and [exact minimized request body](docs/evidence/nebius-tokenfactory-receipt.json) are saved. The [OpenShell/NemoClaw runbook](infra/nemoclaw/README.md) documents the verified endpoint-bound provider path. Public cloud deployment and a public demo URL remain unconfigured.

## Feedback for the submission

Feedback from one live run: Token Factory accepted the Nebius endpoint-bound OpenAI-compatible request; the synthetic Threadline preview-confirm-scan completed end-to-end in 3.26 seconds and produced five candidate commitments. A minimal structured-output smoke request took 0.77 seconds. This confirms connectivity and basic output handling, not general extraction quality; broader quality, quota, and cost measurements remain open.

## Submission materials

Draft project description and a sub-three-minute demo outline are in [`docs/submission.md`](docs/submission.md). The public demo URL and YouTube link are intentionally left blank until an account and credentials are available and the deployed build has been tested. This repository includes the MIT license required for a public repository.



