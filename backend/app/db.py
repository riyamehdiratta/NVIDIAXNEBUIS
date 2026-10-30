import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import DATA_DIR, DB_PATH


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def initialize():
    with connect() as db:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version < 1:
            db.executescript(
                """
                CREATE TABLE sources (
                    id TEXT PRIMARY KEY, filename TEXT NOT NULL, kind TEXT NOT NULL,
                    title TEXT NOT NULL, content TEXT NOT NULL, digest TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL, origin TEXT NOT NULL DEFAULT 'manual',
                    scanned INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE loops (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '',
                    kind TEXT NOT NULL DEFAULT 'task', status TEXT NOT NULL DEFAULT 'open',
                    due_at TEXT, owner TEXT, confidence REAL NOT NULL DEFAULT 0.5,
                    evidence TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, source_id TEXT REFERENCES sources(id) ON DELETE SET NULL
                );
                CREATE TABLE skills (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
                    instructions TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE policies (
                    action_type TEXT PRIMARY KEY, mode TEXT NOT NULL DEFAULT 'ask',
                    approved_count INTEGER NOT NULL DEFAULT 0, rejected_count INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE actions (
                    id TEXT PRIMARY KEY, loop_id TEXT REFERENCES loops(id) ON DELETE CASCADE,
                    action_type TEXT NOT NULL, title TEXT NOT NULL, payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL,
                    decided_at TEXT, result TEXT
                );
                CREATE TABLE reminders (
                    id TEXT PRIMARY KEY, action_id TEXT NOT NULL REFERENCES actions(id) ON DELETE CASCADE,
                    title TEXT NOT NULL, due_at TEXT, created_at TEXT NOT NULL
                );
                CREATE TABLE egress_events (
                    id TEXT PRIMARY KEY, model TEXT NOT NULL, source_ids TEXT NOT NULL,
                    redacted_fields INTEGER NOT NULL, payload TEXT NOT NULL,
                    status TEXT NOT NULL, created_at TEXT NOT NULL, response_summary TEXT
                );
                CREATE TABLE activity (
                    id TEXT PRIMARY KEY, event_type TEXT NOT NULL, detail TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE daily_reviews (
                    review_date TEXT PRIMARY KEY, open_count INTEGER NOT NULL,
                    generated_at TEXT NOT NULL
                );
                CREATE INDEX idx_loops_status_due ON loops(status, due_at);
                CREATE INDEX idx_actions_status ON actions(status, created_at);
                CREATE INDEX idx_activity_created ON activity(created_at DESC);
                PRAGMA user_version = 1;
                """
            )
            version = 1
        if version < 2:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS scan_previews (
                    id TEXT PRIMARY KEY, source_ids TEXT NOT NULL, source_digests TEXT NOT NULL,
                    skill_id TEXT NOT NULL, model TEXT NOT NULL, request_body TEXT NOT NULL,
                    redacted_fields INTEGER NOT NULL, created_at TEXT NOT NULL, used_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_scan_previews_created ON scan_previews(created_at);
                PRAGMA user_version = 2;
                """
            )
            version = 2
        if version < 3:
            db.executescript(
                """
                ALTER TABLE policies ADD COLUMN autonomy_level INTEGER NOT NULL DEFAULT 1;
                ALTER TABLE policies ADD COLUMN shadow_mode INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE policies ADD COLUMN shadow_samples INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE policies ADD COLUMN shadow_agreements INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE policies ADD COLUMN life_area TEXT NOT NULL DEFAULT 'personal';
                ALTER TABLE policies ADD COLUMN max_actions_per_day INTEGER NOT NULL DEFAULT 10;
                ALTER TABLE actions ADD COLUMN shadow_prediction INTEGER;
                ALTER TABLE actions ADD COLUMN undo_deadline TEXT;
                ALTER TABLE actions ADD COLUMN undo_data TEXT;
                ALTER TABLE actions ADD COLUMN execution_mode TEXT NOT NULL DEFAULT 'manual';
                ALTER TABLE actions ADD COLUMN policy_level INTEGER NOT NULL DEFAULT 1;
                CREATE TABLE app_settings (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                INSERT INTO app_settings(key,value,updated_at) VALUES('autonomy_enabled','1',CURRENT_TIMESTAMP);
                UPDATE policies SET autonomy_level=2 WHERE mode='auto_local';
                UPDATE policies SET life_area='work' WHERE action_type='draft_reply';
                UPDATE policies SET autonomy_level=1,mode='ask' WHERE action_type='calendar_export';
                PRAGMA user_version = 3;
                """
            )
            version = 3
        if version < 4:
            db.executescript(
                """
                CREATE TABLE scam_checks (
                    id TEXT PRIMARY KEY, message_digest TEXT NOT NULL, message_length INTEGER NOT NULL,
                    score INTEGER NOT NULL, band TEXT NOT NULL, signals TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE family_profiles (
                    id TEXT PRIMARY KEY, display_name TEXT NOT NULL, relationship TEXT NOT NULL,
                    phrase_salt TEXT NOT NULL, phrase_digest TEXT NOT NULL, created_at TEXT NOT NULL
                );
                PRAGMA user_version = 4;
                """
            )
            version = 4
        if version < 5:
            db.executescript(
                """
                CREATE TABLE contracts (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, statement TEXT NOT NULL,
                    start_time TEXT NOT NULL, end_time TEXT NOT NULL, scope TEXT NOT NULL,
                    red_team TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                ALTER TABLE actions ADD COLUMN contract_id TEXT REFERENCES contracts(id) ON DELETE SET NULL;
                ALTER TABLE actions ADD COLUMN override_reason TEXT;
                PRAGMA user_version = 5;
                """
            )
            version = 5
        if version < 6:
            db.executescript(
                """
                CREATE TABLE workflow_runs (
                    id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, workflow_version INTEGER NOT NULL,
                    status TEXT NOT NULL, inputs TEXT NOT NULL, outputs TEXT NOT NULL DEFAULT '{}',
                    error TEXT, idempotency_key TEXT UNIQUE, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE workflow_node_runs (
                    run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
                    node_id TEXT NOT NULL, status TEXT NOT NULL, output TEXT,
                    error TEXT, started_at TEXT, completed_at TEXT,
                    PRIMARY KEY(run_id,node_id)
                );
                CREATE INDEX idx_workflow_runs_updated ON workflow_runs(updated_at DESC);
                PRAGMA user_version = 6;
                """
            )
            version = 6
        if version < 7:
            db.executescript(
                """
                CREATE TABLE workflow_run_sources (
                    run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
                    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
                    PRIMARY KEY(run_id,source_id)
                );
                CREATE TRIGGER delete_workflow_runs_with_source
                BEFORE DELETE ON sources
                BEGIN
                    DELETE FROM workflow_runs
                    WHERE id IN (SELECT run_id FROM workflow_run_sources WHERE source_id=OLD.id);
                END;
                PRAGMA user_version = 7;
                """
            )
            version = 7
        if version < 8:
            db.executescript(
                """
                CREATE TABLE workflow_definitions (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
                    active_version INTEGER NOT NULL, is_skill INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE workflow_versions (
                    workflow_id TEXT NOT NULL REFERENCES workflow_definitions(id) ON DELETE CASCADE,
                    version INTEGER NOT NULL, spec TEXT NOT NULL, source_request TEXT NOT NULL,
                    created_at TEXT NOT NULL, PRIMARY KEY(workflow_id,version)
                );
                CREATE TABLE workflow_compile_previews (
                    id TEXT PRIMARY KEY, workflow_name TEXT NOT NULL, request_text TEXT NOT NULL,
                    update_workflow_id TEXT, request_body TEXT NOT NULL, model TEXT NOT NULL,
                    redacted_fields INTEGER NOT NULL, save_as_skill INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL, used_at TEXT
                );
                CREATE INDEX idx_workflow_versions ON workflow_versions(workflow_id,version DESC);
                CREATE INDEX idx_workflow_compile_previews ON workflow_compile_previews(created_at);
                PRAGMA user_version = 8;
                """
            )
            version = 8
        if version < 9:
            db.executescript(
                """
                ALTER TABLE actions ADD COLUMN workflow_operation_key TEXT;
                CREATE UNIQUE INDEX idx_actions_workflow_operation ON actions(workflow_operation_key);
                PRAGMA user_version = 9;
                """
            )
            version = 9
        if version < 10:
            db.executescript(
                """
                ALTER TABLE workflow_runs ADD COLUMN repair_attempts INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE workflow_runs ADD COLUMN compensation_status TEXT;
                ALTER TABLE workflow_definitions ADD COLUMN lifecycle TEXT NOT NULL DEFAULT 'published';

                CREATE TABLE IF NOT EXISTS workflow_repair_logs (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
                    attempt INTEGER NOT NULL,
                    failed_node_id TEXT NOT NULL,
                    original_error TEXT NOT NULL,
                    patch_summary TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workflow_schedules (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL REFERENCES workflow_definitions(id) ON DELETE CASCADE,
                    cron_expression TEXT,
                    event_type TEXT,
                    default_inputs TEXT NOT NULL DEFAULT '{}',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    last_run TEXT,
                    next_run TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workflow_test_cases (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL REFERENCES workflow_definitions(id) ON DELETE CASCADE,
                    version INTEGER NOT NULL,
                    inputs TEXT NOT NULL,
                    expected_outputs TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_workflow_schedules ON workflow_schedules(enabled, next_run);
                PRAGMA user_version = 10;
                """
            )
            version = 10
        if version < 11:
            db.executescript(
                """
                -- 1. Ambient Apprenticeship: Universal OS Traces
                CREATE TABLE IF NOT EXISTS apprenticeship_traces (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    process_name TEXT NOT NULL,
                    window_title TEXT NOT NULL,
                    events TEXT NOT NULL,
                    synthesized_spec TEXT,
                    variables TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'recorded',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                -- 2. Conformal Risk Control Calibration Data
                CREATE TABLE IF NOT EXISTS crc_calibration_points (
                    id TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    feature_vector TEXT NOT NULL,
                    predicted_prob REAL NOT NULL,
                    non_conformity_score REAL NOT NULL,
                    user_decision INTEGER NOT NULL,
                    loss REAL NOT NULL DEFAULT 0.0,
                    context_source_id TEXT REFERENCES sources(id) ON DELETE SET NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS crc_policy_thresholds (
                    action_type TEXT PRIMARY KEY,
                    risk_budget_alpha REAL NOT NULL DEFAULT 0.02,
                    calibrated_tau REAL,
                    sample_size INTEGER NOT NULL DEFAULT 0,
                    empirical_risk REAL NOT NULL DEFAULT 0.0,
                    martingale_drift_statistic REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'collecting_data',
                    last_calibrated_at TEXT,
                    updated_at TEXT NOT NULL
                );

                -- 3. Self-Extension: Synthesized Tools Registry
                CREATE TABLE IF NOT EXISTS synthesized_tools (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    source_code TEXT NOT NULL,
                    manifest TEXT NOT NULL,
                    inverse_code TEXT,
                    sandbox_test_result TEXT NOT NULL,
                    verified INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                -- 4. Lifelong Causal World Model: Knowledge Triples with Provenance
                CREATE TABLE IF NOT EXISTS world_model_triples (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
                    evidence TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                -- 5. Causal Experiments (N-of-1 Personal Trials)
                CREATE TABLE IF NOT EXISTS causal_experiments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    intervention TEXT NOT NULL,
                    outcome_metric TEXT NOT NULL,
                    sample_size INTEGER NOT NULL DEFAULT 0,
                    treatment_mean REAL NOT NULL DEFAULT 0.0,
                    control_mean REAL NOT NULL DEFAULT 0.0,
                    causal_effect REAL NOT NULL DEFAULT 0.0,
                    p_value REAL,
                    status TEXT NOT NULL DEFAULT 'running',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_crc_cal_pts ON crc_calibration_points(action_type, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_world_model_subj ON world_model_triples(subject, predicate);
                PRAGMA user_version = 11;
                """
            )
            version = 11
        if version < 12:
            db.executescript(
                """
                -- Universal MCP Server & App Connectors Hub
                CREATE TABLE IF NOT EXISTS mcp_connectors (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    kind TEXT NOT NULL, -- 'mcp_stdio' | 'mcp_sse' | 'app_connector' | 'synthetic'
                    description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'connected',
                    config TEXT NOT NULL DEFAULT '{}',
                    tools TEXT NOT NULL DEFAULT '[]',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_mcp_connectors_enabled ON mcp_connectors(enabled);
                PRAGMA user_version = 12;
                """
            )
            version = 12

        if version < 13:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS device_action_receipts (
                    id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    task_category TEXT NOT NULL,
                    rung_used TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    verified INTEGER NOT NULL DEFAULT 1,
                    undo_available INTEGER NOT NULL DEFAULT 1,
                    undo_payload TEXT,
                    promoted_skill_id TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_device_receipts_created ON device_action_receipts(created_at);
                PRAGMA user_version = 13;
                """
            )
            version = 13

        if version < 14:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS backtest_experiments (
                    id TEXT PRIMARY KEY,
                    policy_name TEXT NOT NULL,
                    candidate_skill_id TEXT,
                    target_autonomy_level INTEGER NOT NULL,
                    time_window_days INTEGER NOT NULL DEFAULT 90,
                    total_eval_samples INTEGER NOT NULL,
                    agreements INTEGER NOT NULL,
                    rejections INTEGER NOT NULL,
                    ucb_error_rate REAL NOT NULL,
                    alpha_threshold REAL NOT NULL,
                    status TEXT NOT NULL,
                    worst_case_trace TEXT,
                    counterexamples_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dream_reports (
                    id TEXT PRIMARY KEY,
                    dream_date TEXT NOT NULL,
                    memories_consolidated_json TEXT NOT NULL,
                    draft_skills_json TEXT NOT NULL,
                    sandbox_rehearsals_json TEXT NOT NULL,
                    conflicts_caught_json TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS privacy_proof_chain (
                    block_index INTEGER PRIMARY KEY,
                    prev_hash TEXT NOT NULL,
                    block_hash TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    egress_bytes INTEGER NOT NULL DEFAULT 0,
                    raw_pii_detected INTEGER NOT NULL DEFAULT 0,
                    redaction_hash TEXT NOT NULL,
                    openshell_signature TEXT NOT NULL,
                    payload_summary TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chaos_stress_runs (
                    id TEXT PRIMARY KEY,
                    total_probes INTEGER NOT NULL,
                    blocked_count INTEGER NOT NULL,
                    bypassed_count INTEGER NOT NULL,
                    resilience_score REAL NOT NULL,
                    attacks_json TEXT NOT NULL,
                    policy_patches_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_backtest_policy ON backtest_experiments(policy_name);
                CREATE INDEX IF NOT EXISTS idx_dream_reports_created ON dream_reports(created_at);
                CREATE INDEX IF NOT EXISTS idx_privacy_chain_hash ON privacy_proof_chain(block_hash);
                CREATE INDEX IF NOT EXISTS idx_chaos_runs_created ON chaos_stress_runs(created_at);
                PRAGMA user_version = 14;
                """
            )
            version = 14
    ensure_defaults()


def ensure_defaults():
    t = now_iso()
    defaults = [
        ("daily-reset", "Daily reset", "Turn the latest updates into a calm, prioritized day plan.",
         "Review open loops. Group by due date and waiting state. Suggest the smallest useful next action. Cite sources. Ask before changing any external state."),
        ("follow-up-draft", "Follow-up draft", "Draft a concise follow-up grounded in the selected source.",
         "Draft a short, polite follow-up using only facts present in the linked source and memory. Do not send it. Flag missing details with brackets."),
        ("commitment-scan", "Commitment scan", "Find promises, requests, deadlines, and things you are waiting on.",
         "Extract actionable commitments and their evidence. Keep dates exact when explicit. Use null when uncertain and explain uncertainty. Do not invent owners or deadlines."),
    ]
    with connect() as db:
        for id_, name, description, instructions in defaults:
            db.execute(
                "INSERT OR IGNORE INTO skills(id,name,description,instructions,updated_at) VALUES(?,?,?,?,?)",
                (id_, name, description, instructions, t),
            )
        areas = {"create_reminder": "personal", "draft_reply": "work", "calendar_export": "personal"}
        for action_type in ("create_reminder", "draft_reply", "calendar_export"):
            db.execute(
                "INSERT OR IGNORE INTO policies(action_type,mode,updated_at,life_area) VALUES(?,?,?,?)",
                (action_type, "ask", t, areas[action_type]),
            )

        # Seed default MCP Connectors
        default_connectors = [
            ("conn_github", "github", "GitHub Connector", "app_connector", "Search code, issues, PRs, and commit history across repositories.", "connected", "{}", json.dumps([
                {"name": "github.search_issues", "description": "Search repository issues and pull requests by query", "args": {"query": "string", "repo": "string"}},
                {"name": "github.get_repo_summary", "description": "Fetch repository status, open PRs, and branch details", "args": {"repo": "string"}},
                {"name": "github.create_issue_draft", "description": "Draft a bug report or feature request issue", "args": {"title": "string", "body": "string"}}
            ])),
            ("conn_gsuite", "google_workspace", "Google Workspace", "app_connector", "Search Google Docs, Sheets, Slides, and Calendar events.", "connected", "{}", json.dumps([
                {"name": "gsuite.search_docs", "description": "Search Google Drive documents and notes", "args": {"query": "string"}},
                {"name": "gsuite.read_sheet_rows", "description": "Read rows from a Google Sheet spreadsheet", "args": {"sheet_id": "string", "range": "string"}},
                {"name": "gsuite.list_calendar_events", "description": "List upcoming Google Calendar meetings and events", "args": {"days": "integer"}}
            ])),
            ("conn_slack", "slack", "Slack Team Hub", "app_connector", "Search channel message history and draft team announcements.", "connected", "{}", json.dumps([
                {"name": "slack.search_messages", "description": "Search messages across Slack public and private channels", "args": {"query": "string", "channel": "string"}},
                {"name": "slack.draft_channel_update", "description": "Draft a team standup or status announcement", "args": {"channel": "string", "topics": "string"}}
            ])),
            ("conn_fs", "filesystem", "Local Filesystem MCP", "mcp_stdio", "Local host filesystem inspector for workspace notes, markdown, and code.", "connected", json.dumps({"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"]}), json.dumps([
                {"name": "fs.list_directory", "description": "List files and subfolders in workspace directory", "args": {"path": "string"}},
                {"name": "fs.read_file", "description": "Read content of local text, markdown, or JSON files", "args": {"path": "string"}},
                {"name": "fs.search_files", "description": "Search across workspace files for matching keywords", "args": {"pattern": "string"}}
            ])),
            ("conn_db", "database", "Database Inspector MCP", "mcp_stdio", "Direct read and schema queries across SQLite and PostgreSQL databases.", "connected", "{}", json.dumps([
                {"name": "db.execute_query", "description": "Execute safe read-only SQL queries against registered database", "args": {"query": "string"}},
                {"name": "db.inspect_schema", "description": "Inspect database tables, column types, and foreign keys", "args": {"table_name": "string"}}
            ])),
            ("conn_web", "web_search", "Web Knowledge & Search", "app_connector", "Live web search, documentation fetching, and citation retrieval.", "connected", "{}", json.dumps([
                {"name": "web.search", "description": "Search the public web for real-time facts, APIs, and docs", "args": {"query": "string", "limit": "integer"}},
                {"name": "web.fetch_url", "description": "Fetch article text and extract citations from a web page", "args": {"url": "string"}}
            ]))
        ]

        for cid, cname, dname, ckind, cdesc, cstatus, ccfg, ctools in default_connectors:
            db.execute(
                """INSERT OR IGNORE INTO mcp_connectors(id, name, display_name, kind, description, status, config, tools, enabled, created_at, updated_at)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
                (cid, cname, dname, ckind, cdesc, cstatus, ccfg, ctools, t, t)
            )


def rowdict(row):
    return dict(row) if row is not None else None


def json_value(value, fallback=None):
    try:
        return json.loads(value) if value else fallback
    except (TypeError, json.JSONDecodeError):
        return fallback
