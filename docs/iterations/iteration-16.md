# Iteration 16: Threadline Agent OS — Dynamic Control Flow, Verifier, Saga Rollback, and Self-Extension

## Objectives
Bridge the gap from linear deterministic workflows to a complete, flexible, and robust autonomous Agent OS:
1. **Dynamic Control Flow**: Support `map` (fan-out over lists), `branch` (conditional paths), and bounded `loop` iterations.
2. **Independent Verifier & Bounded Repair**: Automated verification nodes plus self-repair loops capped at 2 attempts with durable repair logs.
3. **Saga Compensation Engine**: Inverse tool execution and rollback for multi-step workflows.
4. **Scheduled & Event Triggers**: Background worker poll loop firing cron and source-triggered workflows.
5. **Skill Promotion Pipeline**: Wilson 95% lower-bound eligibility checking, automated regression test snapshots, and versioned lifecycle tracking.
6. **Empirical Verification**: 20-task benchmark suite and 8-attack adversarial injection test suite.

---

## Deliverables & Changes

### 1. Database Schema Migration (v9 → v10)
- `ALTER TABLE workflow_runs ADD COLUMN repair_attempts INTEGER NOT NULL DEFAULT 0`
- `ALTER TABLE workflow_runs ADD COLUMN compensation_status TEXT`
- `ALTER TABLE workflow_definitions ADD COLUMN lifecycle TEXT NOT NULL DEFAULT 'published'`
- Table `workflow_repair_logs` (id, run_id, attempt, failed_node_id, original_error, patch_summary, result, created_at)
- Table `workflow_schedules` (id, workflow_id, cron_expression, event_type, default_inputs, enabled, last_run, next_run, created_at)
- Table `workflow_test_cases` (id, workflow_id, version, inputs, expected_outputs, created_at)

### 2. Backend Workflow Engine (`backend/app/workflows.py`)
- **`WorkflowNode` Extensions**:
  - `type`: Extended to `Literal["tool", "map", "branch", "loop", "verify", "approval"]`.
  - Added `over`, `do_tool`, `do_args`, `max_items` (capped at 50) for `map` fan-out.
  - Added `condition`, `then_node`, `else_node` for deterministic branching.
  - Added `loop_until`, `max_iterations` (capped at 10), `loop_body` for bounded cycles.
  - Added `verify_against` for verifier nodes.
- **Evaluation & Helpers**:
  - `_eval_condition()`: Deterministic, safe expression evaluator for comparisons (`==`, `!=`, `<`, `>`, `<=`, `>=`) without `eval()`.
  - `_resolve_item()`: Nested item placeholder resolver for `$item` and `$item.<field>` in map loops.
  - `TOOL_MANIFESTS["verify.check_output"]`: Automated completeness and schema validator.
  - `_compensate()`: Reverse-order saga rollback handler for side-effect nodes (`remove_derived_loops`, `delete_local_draft`, `undo_action`).
- **New API Endpoints**:
  - `POST /api/workflows/runs/{run_id}/repair`: Bounded self-repair loop (max 2 attempts).
  - `POST /api/workflows/runs/{run_id}/rollback`: User-triggered compensation rollback.
  - `GET /api/workflows/schedules` & `POST /api/workflows/schedules`: Scheduled trigger management.
  - `POST /api/workflows/schedules/{id}/toggle` & `DELETE /api/workflows/schedules/{id}`: Schedule controls.
  - `GET /api/workflows/definitions/{id}/promotion`: Wilson 95% bound and promotion eligibility calculation.
  - `POST /api/workflows/definitions/{id}/promote`: Skill promotion with regression test case capture.
  - `GET /api/workflows/definitions/{id}/test_cases`: Inspection of captured regression test fixtures.

### 3. Background Scheduler (`backend/app/worker.py`)
- Added `_run_scheduled_workflows()` to the 20-second background poll loop.
- Supports cron-like hourly/daily execution and reactive triggers on file imports (`event_type='source_added'`).

### 4. Evaluation Benchmark & Security Suites
- **`backend/evals/workflow_benchmark.py`**:
  - 20 comprehensive tasks measuring commitment scanning, daily reset, map fan-out, branch evaluation, verifier nodes, bounded loops, idempotency deduplication, checkpoint resume, saga rollback, bounded repair, simulation preview, budget limits, skill promotion, and end-to-end multi-step pipelines.
  - **Results**: **20/20 Passed (100.0%)** in 890ms.
- **`backend/evals/injection_suite.py`**:
  - 8 adversarial attacks (unregistered tools, egress bypass, spend bypass, token bypass, graph cycles, untrusted taint flow into privileged writes, map item bombs, and unbounded loop iterations).
  - **Results**: **8/8 Attacks Blocked (100.0%)**.

### 5. Frontend Enhancements (`frontend/src/components/WorkflowLab.jsx`)
- Enriched simulation preview with color-coded type pills: `MAP`, `BRANCH`, `LOOP`, `VERIFY`, `TOOL`.
- Durable run receipt shows `repair_attempts` and `compensation_status`.
- Integrated "Auto-repair failing node" and "Rollback side effects" buttons on run receipts.
- "Promotion status" modal calculating real-time Wilson 95% confidence intervals and 1-click promotion to published skill.
- "Scheduled Workflows" panel showing background triggers, next run times, and toggle controls.

---

## Verification
- Pytest / benchmark run: `20/20 PASSED (100.0%) in 890.0ms`
- Injection security run: `8/8 ATTACKS BLOCKED (100.0%)`
- Production Vite build: `dist/index.html` built cleanly in 3.08s with zero errors.
- API status: All FastAPI routes verified 200 OK via `TestClient`.

