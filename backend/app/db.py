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


def rowdict(row):
    return dict(row) if row is not None else None


def json_value(value, fallback=None):
    try:
        return json.loads(value) if value else fallback
    except (TypeError, json.JSONDecodeError):
        return fallback
