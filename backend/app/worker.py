import asyncio
import hashlib
import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from .api import _log, _store_source
from .config import DEMO_MODE, IMPORT_DIR, WATCH_IMPORTS
from .db import connect, json_value, now_iso
from .parsers import parse_source

log = logging.getLogger("threadline.worker")
ALLOWED = {".txt", ".md", ".csv", ".log", ".eml", ".ics"}


async def _run_scheduled_workflows():
    from .workflows import _execute, _get_spec
    now_str = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect() as db:
        schedules = db.execute(
            "SELECT * FROM workflow_schedules WHERE enabled=1 AND (next_run IS NULL OR next_run <= ?)",
            (now_str,)
        ).fetchall()

    for sch in schedules:
        try:
            spec = _get_spec(sch["workflow_id"])
            if not spec:
                continue
            run_id = str(uuid4())
            inputs = json_value(sch["default_inputs"], {})
            with connect() as db:
                db.execute(
                    "INSERT INTO workflow_runs(id,workflow_id,workflow_version,status,inputs,outputs,created_at,updated_at) VALUES(?,?,?,'queued',?,'{}',?,?)",
                    (run_id, spec.id, spec.version, json.dumps(inputs), now_iso(), now_iso())
                )
            _execute(run_id, spec, inputs)
            next_t = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(timespec="seconds")
            with connect() as db:
                db.execute(
                    "UPDATE workflow_schedules SET last_run=?, next_run=? WHERE id=?",
                    (now_iso(), next_t, sch["id"])
                )
            _log("scheduled_workflow", f"Ran scheduled workflow '{spec.name}'")
        except Exception as exc:
            log.warning("Scheduled workflow %s failed: %s", sch["workflow_id"], exc)


async def background_worker(stop_event: asyncio.Event):
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    last_review_day = None
    while not stop_event.is_set():
        if WATCH_IMPORTS and not DEMO_MODE:
            for path in IMPORT_DIR.iterdir():
                if not path.is_file() or path.suffix.lower() not in ALLOWED or path.stat().st_size > 2_000_000:
                    continue
                try:
                    raw = path.read_bytes()
                    kind, title, content = parse_source(path.name, raw)
                    source_id, created = _store_source(path.name, kind, title, content, origin="folder")
                    if created:
                        with connect() as db:
                            event_schedules = db.execute(
                                "SELECT * FROM workflow_schedules WHERE enabled=1 AND event_type='source_added'"
                            ).fetchall()
                        if event_schedules:
                            from .workflows import _execute, _get_spec
                            for sch in event_schedules:
                                spec = _get_spec(sch["workflow_id"])
                                if spec:
                                    run_id = str(uuid4())
                                    inps = {"source_id": source_id, **json_value(sch["default_inputs"], {})}
                                    with connect() as db:
                                        db.execute(
                                            "INSERT INTO workflow_runs(id,workflow_id,workflow_version,status,inputs,outputs,created_at,updated_at) VALUES(?,?,?,'queued',?,'{}',?,?)",
                                            (run_id, spec.id, spec.version, json.dumps(inps), now_iso(), now_iso())
                                        )
                                    _execute(run_id, spec, inps)
                except (OSError, ValueError) as exc:
                    log.warning("Could not import %s: %s", path.name, exc)
        now = datetime.now().astimezone()
        today = now.date().isoformat()
        if now.hour >= 9 and last_review_day != today:
            with connect() as db:
                exists = db.execute("SELECT 1 FROM daily_reviews WHERE review_date=?", (today,)).fetchone()
                if not exists:
                    count = db.execute("SELECT COUNT(*) FROM loops WHERE status='open'").fetchone()[0]
                    db.execute("INSERT INTO daily_reviews(review_date,open_count,generated_at) VALUES(?,?,?)", (today, count, now_iso()))
                    db.execute("INSERT INTO activity(id,event_type,detail,created_at) VALUES(?,?,?,?)", (str(uuid4()), "daily_review", f"Daily review ready · {count} open loop(s)", now_iso()))
            last_review_day = today

        # Run scheduled workflows
        await _run_scheduled_workflows()

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=20)
        except asyncio.TimeoutError:
            pass
