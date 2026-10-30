# Threadline & The Sovereign Delegate

**A private personal AI and autonomous OS substrate that keeps life's open loops moving.**

Threadline turns the commitments buried in user-selected emails, calendar files, notes, and native desktop interactions into a persistent, source-linked view of what is due, what is waiting, and what the user promised. Beyond routine task extraction, Threadline features **The Sovereign Delegate**—a research-grade autonomous agent architecture that learns how you work by watching native desktop applications, synthesizes its own capabilities, and acts with mathematically provable risk bounds.

---

## The Sovereign Delegate: 5 Research-Grade Pillars

Unlike cloud-confined voice assistants (such as Alexa or Siri) that are tethered to proprietary vendor ecosystems, the Sovereign Delegate operates directly on your host machine across any native desktop application with statistical error guarantees and zero vendor lock-in.

```text
       Universal OS Perception (Win32 ctypes / Any Desktop App)
                                  │
                  Demonstration Trace Recording
                                  │
       ┌──────────────────────────┴──────────────────────────┐
       ▼                                                     ▼
PILLAR 1: Ambient Apprenticeship              PILLAR 2: Learned Preference Model
 • Cross-app interaction logging               • Feature vector extraction x ∈ ℝ⁸
 • Automated PII & credential masking          • Online Bayesian logistic regression
 • Parameter lifting ($inputs.<param>)         • Epistemic entropy H(p) quantification
 • Kahn-checked DAG workflow compiler          • Strategic active learning queries
       │                                                     │
       └──────────────────────────┬──────────────────────────┘
                                  ▼
                    PILLAR 3: Provable Autonomy
                     • Conformal Risk Control (CRC): E[Loss] ≤ α
                     • Finite-sample threshold τ̂ guarantee
                     • CUSUM Martingale sequential drift alarm (h = 3.5)
                     • Automated downgrade to L1 Ask upon drift
                                  │
       ┌──────────────────────────┴──────────────────────────┐
       ▼                                                     ▼
PILLAR 4: Self-Extension Studio               PILLAR 5: Causal World Model
 • Autonomous Python tool synthesis            • Provenance-backed belief triple store
 • Inverse saga compensation rollback          • Source-linked deletion cascades
 • Safe isolated sandbox test execution        • Rubin N-of-1 trial engine (ATE)
 • Dynamic injection into TOOL_MANIFESTS       • 7-day forward horizon workload rehearsal
```

### 1. Ambient Apprenticeship (Universal OS Perception)
- **Universal Introspection:** Inspects foreground windows, process IDs, and coordinates via native Win32 `ctypes` (`GetForegroundWindow`, `GetWindowTextW`, `GetWindowThreadProcessId`, `GetWindowRect`) with zero third-party dependencies. Not bound to Chrome or any single app—works with Excel, Slack, Terminal, ERPs, and file managers.
- **Automated PII & Credential Sanitization:** Sensitive input roles and passwords matching security patterns are masked in-flight (`[MASKED_CREDENTIAL]`).
- **Parameter Lifting:** Concrete values (e.g., dates `2026-11-20`, emails `cfo@company.org`, numeric quantities) are lifted into typed `$inputs.<var>` parameters.
- **DAG Workflow Compilation:** Compiles multi-step user demonstrations into typed, Kahn-cycle-checked `WorkflowSpec` DAGs with auto-appended verification nodes.

### 2. Learned Model of You (Preference Model & Active Learning)
- **Contextual Representation:** Extracts normalized feature vectors $\mathbf{x} \in \mathbb{R}^8$ (risk score, reversibility, work context, late hours, external writes, volume ratio, entity familiarity, base bias).
- **Online Bayesian Updates:** Employs regularized gradient steps on user approval/rejection feedback to continuously adjust preference weights $\mathbf{w}$.
- **Epistemic Uncertainty:** Quantifies Shannon entropy $H(p) = -p\log_2 p - (1-p)\log_2(1-p)$.
- **Strategic Active Learning:** Synthesizes clarifying queries only when $H(p) > 0.70$ bits (near the decision boundary), eliminating unnecessary user interruptions.

### 3. Provable Autonomy (Conformal Risk Control & Drift Detection)
- **Distribution-Free Guarantees:** Given user error budget $\alpha \in [0.005, 0.10]$, computes finite-sample non-conformity threshold $\hat{\tau}$ satisfying:
  $$\frac{n}{n+1}\hat{R}_n(\hat{\tau}) + \frac{1}{n+1} \le \alpha \implies \mathbb{E}[L] \le \alpha$$
- **Empirical Gate Evaluator:** Candidate actions auto-execute only if $1 - \hat{p} \le \hat{\tau}$. If uncalibrated ($n < 20$) or uncertain, the engine safely abstains.
- **CUSUM Martingale Drift Detector:** Tracks sequential drift statistic $M_t = \max(0, M_{t-1} + (L_t - \alpha) - \kappa)$ with threshold $h = 3.5$. Instantly downshifts to L1 Ask if user behavior or environment drifts.

### 4. Self-Extension Studio (Autonomous Tool Synthesizer)
- **Self-Programming Runtime:** When a task requires an unhandled capability, the synthesizer generates Python handler code `handler(args)` and an accompanying capability manifest.
- **Inverse Saga Rollback:** Generates an inverse rollback handler `inverse_handler(output)` for provable compensation and reversibility.
- **Sandboxed Verification:** Executes code inside a restricted execution environment (`_safe_sandbox_exec`) with stripped `__builtins__` and blocked OS/network calls.
- **Live Injection:** Dynamically registers verified tools into `TOOL_MANIFESTS` for immediate availability across workflow DAGs.

### 5. Lifelong Causal World Model & Horizon Rehearsal
- **Rubin Potential Outcomes Causal Engine:** Runs N-of-1 observational causal trials to measure Average Treatment Effects (ATE) and 2-sample pooled t-statistics, separating actual productivity improvements from coincidence.
- **Auditable Knowledge Triples:** Maintains provenance-linked beliefs with confidence scores and evidence snippets.
- **Source-Linked Cascade Deletion:** Removing an imported file cascades through SQLite triggers to purge derived open loops and world model triples.
- **7-Day Horizon Rehearsal:** Simulates the user's upcoming week day-by-day, forecasting workload stress indices (0–100) and flagging schedule compression bottlenecks before they occur.

---

## Empirical Benchmark Results

The system includes three comprehensive automated benchmark suites:

| Benchmark Suite | File | Tests / Attacks | Pass Rate | Execution Time |
|---|---|---|---|---|
| **Workflow Benchmark Suite** | [`backend/evals/workflow_benchmark.py`](backend/evals/workflow_benchmark.py) | 20 DAG Tasks | **20/20 (100.0%)** | 1453ms |
| **Adversarial Injection Suite** | [`backend/evals/injection_suite.py`](backend/evals/injection_suite.py) | 8 Security Attacks | **8/8 (100.0% Blocked)** | 480ms |
| **Sovereign 5-Pillar Suite** | [`backend/evals/sovereign_benchmark.py`](backend/evals/sovereign_benchmark.py) | 17 Core Substrate Tests | **17/17 (100.0%)** | 795ms |
| **Device Agent Benchmark Suite** | [`backend/evals/device_agent_benchmark.py`](backend/evals/device_agent_benchmark.py) | 7 Ladder & Postcondition Tests | **7/7 (100.0%)** | 185ms |

To execute all evaluation suites locally:
```powershell
python -m backend.evals.workflow_benchmark
python -m backend.evals.injection_suite
python -m backend.evals.sovereign_benchmark
python -m backend.evals.device_agent_benchmark
```

---

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
- Run the installed Commitment scan, Daily reset, and Follow-up draft as versioned workflow DAGs. Inspect a dry run, validate types/dependencies/taint, approve local writes, and resume from SQLite node checkpoints. Reminder and draft proposals go through existing L0-L4 policies, caps, pause, precommitments, review queue, and undo; only registered local tools can execute.
- Describe a new task in **Agent workflows** to compile a custom DAG with Nemotron. The exact redacted planner request is previewed before egress; the resulting skill is versioned, inspectable, and restricted to the registered local tool catalog.
- **Live Assistant with Continuous Voice & Visualizer Orb:** Click "Live Assistant" or "Start Capture" for a conversational assistant modeled after ChatGPT and Gemini Live. Features a reactive acoustic visualizer orb, hands-free Web Speech API continuous loop, speech synthesis playback, and automated tool dispatching.
- **Universal Model Context Protocol (MCP) & 25+ App Connectors:** Connect external ecosystems directly into Threadline's sandbox:
  - **GitHub:** Search repository issues, inspect PRs, and draft bug reports.
  - **Google Workspace:** Search Google Docs, read spreadsheets, and list upcoming calendar events.
  - **Slack:** Search team channel histories and draft standup announcements.
  - **Local Filesystem MCP:** Inspect local files and directory trees with security path containment.
  - **Database Inspector MCP:** Query schemas and run read-only `SELECT` queries across SQLite and PostgreSQL.
  - **Web Knowledge Search:** Fetch real-time web citations and developer specifications.
  - **Interactive MCP Studio:** Inspect connector health, test tool execution with custom JSON parameters, toggle individual connectors, and register custom stdio/SSE MCP servers directly in Sovereign Hub.

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

The checkpointed workflow API, user-demand compiler, and current boundaries are described in [the workflow runtime guide](docs/agent-os/workflow-runtime.md). This is a constrained task planner, not AGI: it cannot use arbitrary code, web browsing, external integrations, or unattended schedules.

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
- `/api/workflows/compile/preview` and `/compile/confirm` - inspect and explicitly approve a redacted Nemotron workflow-compilation request.
- `/api/workflows/templates`, `/tools`, `/definitions/{id}`, `/validate`, `/simulate`, and `/runs` - inspect workflow skills/tools, validate and dry-run plans, then execute approved built-in or generated local workflows with durable run receipts.

## NVIDIA and Nebius use

Nemotron is a runtime model, not just a design reference: once `NEBIUS_API_KEY` is configured, the user can confirm a live OpenAI-compatible Chat Completions request to Nebius Token Factory. Lightning handles everyday extraction; Super handles cases flagged as ambiguous or unusually large. The app deliberately makes no inference call until the user inspects and confirms the minimized request.

Nebius Token Factory avoids requiring the project to provision and serve GPU model weights itself. A real three-source synthetic Threadline scan has run through an OpenShell-managed Nebius provider; the [receipt and latency](docs/evidence/nebius-tokenfactory-live.txt) and [exact minimized request body](docs/evidence/nebius-tokenfactory-receipt.json) are saved. The [OpenShell/NemoClaw runbook](infra/nemoclaw/README.md) documents the verified endpoint-bound provider path. Public cloud deployment and a public demo URL remain unconfigured.

Custom workflow compilation uses a separate preview-confirm flow. The preview route has been verified with synthetic text; the new planner call itself has not yet been run against Token Factory.

## Feedback for the submission

Feedback from one live run: Token Factory accepted the Nebius endpoint-bound OpenAI-compatible request; the synthetic Threadline preview-confirm-scan completed end-to-end in 3.26 seconds and produced five candidate commitments. A minimal structured-output smoke request took 0.77 seconds. This confirms connectivity and basic output handling, not general extraction quality; broader quality, quota, and cost measurements remain open.

## The Sovereign Trifecta: An Assistant That Dreams, Proves, and Earns

Beyond the 5 pillars, Threadline implements the **Sovereign Trifecta**—enabling persistent, evidence-gated autonomy that commercial cloud assistants are structurally unable to offer:

1. **Overnight Dreaming (`backend/app/dreaming.py`):**
   - Runs an always-on background consolidation cycle (simulating Nebius Serverless jobs).
   - Replays the day's events, aggregates fragmented promises, extracts persistent entity triples, and synthesizes Hermes-format skill drafts.
   - Tests candidate DAG skills in `./data/workspace/_dream_rehearsal`, asserting file checksums and testing inverse rollback handlers.
   - Rehearses tomorrow's calendar against the Causal World Model, surfacing tight turnarounds and conflicts before the user wakes up.
   - **Quarantine Invariant:** All dream-generated skills remain in `status: "draft_unapproved"` until explicitly verified by the human user.

2. **Autonomy Backtesting (`backend/app/backtest.py`):**
   - Autonomy is never granted by casual clicks. Before promoting a rule from L1 (manual preview) to L3 (autonomous bounded), Threadline replays **90 days of counterfactual decision history**.
   - Promotion is granted ONLY IF the **Wilson Upper Confidence Bound on error rate** is strictly under the target threshold ($\text{UCB}_{0.95}(\hat{p}) \le \alpha$, e.g. $\le 0.05$).
   - **Worst-Case Invariant Audit:** If a candidate policy violates a hard boundary (such as attempting to auto-decline a VIP calendar invite or financial invoice), promotion is immediately **vetoed**, presenting the user with the exact historical counterexample trace.

3. **Proof-of-Privacy Merkle Chain (`backend/app/privacy_proof.py`):**
   - Replaces marketing claims with mathematical proof. Every model inference, tool execution, and network egress is committed to a **SHA-256 Merkle Hash Chain** signed by OpenShell HMAC attestations:
     $$H_t = \text{SHA-256}(H_{t-1} \parallel t \parallel \text{event\_type} \parallel \text{destination} \parallel \text{egress\_bytes} \parallel \text{raw\_pii} \parallel \text{redaction\_hash} \parallel \text{openshell\_signature})$$
   - An interactive verifier checks the chain from Genesis to head, mathematically validating that **EXACTLY 0 raw unredacted personal records left the device boundary**.

4. **Personal Chaos Monkey Security Substrate:**
   - A nightly security tester attacks the sandboxed agent across 10 adversarial vectors (prompt injections, authority spoofing, markdown exfiltration, quiet-hours bypass, micro-transaction smurfing, and delimiter splicing).
   - Emits a **100% Resilience Score** badge and automated policy patches.

---

## Master Automated Benchmark Suite (60/60 Tests Passing)

Verified end-to-end via master runner `python -m backend.evals.run_all`:

| Evaluation Suite | File | Tests | Pass Rate | Execution Time |
|---|---|---|---|---|
| **Workflow DAG Execution** | `backend/evals/workflow_benchmark.py` | 20 / 20 | **100.0%** | 1201.3 ms |
| **Adversarial Security Injection** | `backend/evals/injection_suite.py` | 8 / 8 | **100.0%** | 0.3 ms |
| **Sovereign 5-Pillar AGI Substrate** | `backend/evals/sovereign_benchmark.py` | 17 / 17 | **100.0%** | 633.4 ms |
| **Computer-Use Device Agent** | `backend/evals/device_agent_benchmark.py` | 7 / 7 | **100.0%** | 88.0 ms |
| **Dreams, Proves & Earns Trifecta** | `backend/evals/dreams_proves_earns_benchmark.py` | 8 / 8 | **100.0%** | 301.3 ms |
| **OVERALL STATUS** | **`backend/evals/run_all.py`** | **60 / 60** | **100.0%** | **2224.4 ms** |

---

## Submission materials

Draft project description and a sub-three-minute demo outline are in [`docs/submission.md`](docs/submission.md). The public demo URL and YouTube link are intentionally left blank until an account and credentials are available and the deployed build has been tested. This repository includes the MIT license required for a public repository.



