import asyncio
import hashlib
import logging
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from .api import _store_source
from .config import DEMO_MODE, IMPORT_DIR, WATCH_IMPORTS
from .db import connect, now_iso
from .parsers import parse_source

log = logging.getLogger("threadline.worker")
ALLOWED = {".txt", ".md", ".csv", ".log", ".eml", ".ics"}


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
                    _store_source(path.name, kind, title, content, origin="folder")
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
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=20)
        except asyncio.TimeoutError:
            pass
