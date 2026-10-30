import hashlib
import hmac
import json
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from .agent import call_nebius, heuristic_extract, make_prompt, model_request, record_egress, _model_for
from .autonomy import can_execute_automatically, shadow_prediction, shadow_summary
from .config import API_KEY, DEMO_MODE, IMPORT_DIR, NANO_MODEL, SUPER_MODEL
from .contracts import compile_quiet_hours, is_quiet
from .db import connect, json_value, now_iso, rowdict
from .parsers import parse_source
from .scam import inspect_message
from .simulation import simulate_week
from .schemas import ActionRequest, AutonomyControlRequest, DecisionRequest, FamilyProfileRequest, FamilyVerifyRequest, PolicyRequest, QuietHoursContractRequest, ScamCheckRequest, ScanRequest, SkillRequest, TextSource


router = APIRouter(prefix="/api")
SUPPORTED_ACTIONS = {"create_reminder", "draft_reply", "calendar_export"}
ACTION_LABELS = {"create_reminder": "Create reminder", "draft_reply": "Draft reply", "calendar_export": "Calendar event"}


def _log(kind, detail):
    with connect() as db:
        db.execute("INSERT INTO activity(id,event_type,detail,created_at) VALUES(?,?,?,?)", (str(uuid4()), kind, detail, now_iso()))


def _guard_public_demo_ingest():
    if DEMO_MODE:
        raise HTTPException(403, "Uploads are disabled in the synthetic-data demo. Use the sample workspace.")


def _quiet_contract(db, action_type, moment=None):
    current = moment or datetime.now().astimezone()
    minute = current.hour * 60 + current.minute
    rows = db.execute("SELECT * FROM contracts WHERE active=1 ORDER BY created_at").fetchall()
    for row in rows:
        if row["scope"] not in {"all_auto", action_type}:
            continue
        if is_quiet(row["start_time"], row["end_time"], minute):
            return row
    return None


def _source_row(source_id):
    with connect() as db:
        row = db.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Source not found")
    return dict(row)


def _get_scan_sources(source_ids):
    with connect() as db:
        if source_ids:
            placeholders = ",".join("?" for _ in source_ids)
            rows = db.execute(f"SELECT * FROM sources WHERE id IN ({placeholders}) ORDER BY created_at", source_ids).fetchall()
        else:
            rows = db.execute("SELECT * FROM sources WHERE scanned=0 ORDER BY created_at LIMIT 30").fetchall()
    return [dict(row) for row in rows]


def _store_source(filename: str, kind: str, title: str, content: str, origin="manual"):
    digest = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
    with connect() as db:
        existing = db.execute("SELECT id FROM sources WHERE digest=?", (digest,)).fetchone()
        if existing:
            return existing["id"], False
        source_id = str(uuid4())
        db.execute("INSERT INTO sources(id,filename,kind,title,content,digest,created_at,origin) VALUES(?,?,?,?,?,?,?,?)",
                   (source_id, filename[:250], kind, title[:250], content[:100_000], digest, now_iso(), origin))
    _log("source_added", f"Added {kind} · {filename[:80]}")
    return source_id, True


@router.get("/health")
def health():
    with connect() as db:
        loops = db.execute("SELECT COUNT(*) FROM loops WHERE status='open'").fetchone()[0]
        sources = db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    return {"ok": True, "product": "Threadline", "api_key_configured": bool(API_KEY), "demo_mode": DEMO_MODE,
            "uploads_enabled": not DEMO_MODE, "model": NANO_MODEL, "open_loops": loops, "sources": sources}


@router.get("/dashboard")
def dashboard():
    today = date.today().isoformat()
    with connect() as db:
        open_count = db.execute("SELECT COUNT(*) FROM loops WHERE status='open'").fetchone()[0]
        overdue = db.execute("SELECT COUNT(*) FROM loops WHERE status='open' AND due_at IS NOT NULL AND due_at < ?", (today,)).fetchone()[0]
        waiting = db.execute("SELECT COUNT(*) FROM loops WHERE status='open' AND kind='waiting_on_them'").fetchone()[0]
        pending_actions = db.execute("SELECT COUNT(*) FROM actions WHERE status='pending'").fetchone()[0]
        reminders = db.execute("SELECT COUNT(*) FROM reminders WHERE due_at IS NOT NULL AND due_at <= ?", (today,)).fetchone()[0]
        latest_review = db.execute("SELECT * FROM daily_reviews ORDER BY review_date DESC LIMIT 1").fetchone()
        activity = db.execute("SELECT * FROM activity ORDER BY created_at DESC LIMIT 8").fetchall()
    return {"open_loops": open_count, "overdue": overdue, "waiting_on_them": waiting,
            "pending_actions": pending_actions, "reminders_due": reminders,
            "latest_review": rowdict(latest_review), "activity": [dict(r) for r in activity]}


@router.get("/sources")
def list_sources():
    with connect() as db:
        rows = db.execute("SELECT id,filename,kind,title,digest,created_at,origin,scanned FROM sources ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@router.get("/sources/{source_id}")
def source_detail(source_id: str):
    return _source_row(source_id)


@router.post("/sources/text")
def add_text(body: TextSource):
    _guard_public_demo_ingest()
    kind, title, content = parse_source(body.filename, body.text.encode("utf-8"))
    source_id, created = _store_source(body.filename, kind, title, content)
    return {"id": source_id, "created": created}


@router.post("/sources")
async def add_file(file: UploadFile = File(...)):
    _guard_public_demo_ingest()
    filename = Path(file.filename or "upload.txt").name
    raw = await file.read(2_000_001)
    if len(raw) > 2_000_000:
        raise HTTPException(413, "Keep each import under 2 MB")
    try:
        kind, title, content = parse_source(filename, raw)
    except ValueError as exc:
        raise HTTPException(415, str(exc)) from exc
    source_id, created = _store_source(filename, kind, title, content)
    return {"id": source_id, "created": created}


@router.delete("/sources/{source_id}")
def delete_source(source_id: str):
    with connect() as db:
        row = db.execute("SELECT filename FROM sources WHERE id=?", (source_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Source not found")
        db.execute("DELETE FROM loops WHERE source_id=?", (source_id,))
        db.execute("DELETE FROM sources WHERE id=?", (source_id,))
    _log("source_deleted", f"Deleted source and its extracted loops · {row['filename'][:80]}")
    return {"ok": True}


@router.get("/loops")
def list_loops(status: str = "open", kind: str | None = None, q: str | None = None):
    clauses, args = [], []
    if status != "all":
        clauses.append("l.status=?")
        args.append(status)
    if kind:
        clauses.append("l.kind=?")
        args.append(kind)
    if q:
        clauses.append("(l.title LIKE ? OR l.detail LIKE ? OR s.title LIKE ? OR s.content LIKE ?)")
        args.extend([f"%{q}%"] * 4)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connect() as db:
        rows = db.execute(f"SELECT l.*,s.filename,s.title AS source_title,s.kind AS source_kind FROM loops l LEFT JOIN sources s ON s.id=l.source_id{where} ORDER BY CASE WHEN l.due_at IS NULL THEN 1 ELSE 0 END,l.due_at,l.created_at DESC LIMIT 200", args).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["evidence"] = json_value(item.pop("evidence"), [])
        result.append(item)
    return result


@router.get("/loops/{loop_id}")
def loop_detail(loop_id: str):
    with connect() as db:
        row = db.execute("SELECT l.*,s.filename,s.title AS source_title,s.content AS source_content FROM loops l LEFT JOIN sources s ON s.id=l.source_id WHERE l.id=?", (loop_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Open loop not found")
    item = dict(row)
    item["evidence"] = json_value(item["evidence"], [])
    return item


@router.post("/loops/{loop_id}/decision")
def decide_loop(loop_id: str, body: DecisionRequest):
    decisions = {"done": "completed", "keep": "open", "dismiss": "dismissed"}
    if body.decision not in decisions and body.decision != "edit":
        raise HTTPException(422, "decision must be done, keep, dismiss, or edit")
    with connect() as db:
        row = db.execute("SELECT * FROM loops WHERE id=?", (loop_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Open loop not found")
        if body.decision == "edit":
            db.execute("UPDATE loops SET title=?,detail=?,due_at=?,owner=?,confidence=1.0,updated_at=? WHERE id=?",
                       (body.title or row["title"], body.detail if body.detail is not None else row["detail"], body.due_at if body.due_at is not None else row["due_at"], body.owner if body.owner is not None else row["owner"], now_iso(), loop_id))
        else:
            db.execute("UPDATE loops SET status=?,updated_at=? WHERE id=?", (decisions[body.decision], now_iso(), loop_id))
    _log("loop_reviewed", f"{body.decision} · {row['title'][:100]}")
    return {"ok": True}


@router.get("/skills")
def list_skills():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM skills ORDER BY name").fetchall()]


@router.put("/skills/{skill_id}")
def update_skill(skill_id: str, body: SkillRequest):
    with connect() as db:
        cur = db.execute("UPDATE skills SET name=?,description=?,instructions=?,enabled=?,updated_at=? WHERE id=?",
                         (body.name[:100], body.description[:240], body.instructions[:5000], int(body.enabled), now_iso(), skill_id))
        if not cur.rowcount:
            raise HTTPException(404, "Skill not found")
    _log("skill_updated", f"Updated skill · {body.name[:80]}")
    return {"ok": True}


@router.get("/policies")
def policies():
    with connect() as db:
        rows = db.execute("SELECT * FROM policies ORDER BY action_type").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item.update(shadow_summary(item["shadow_agreements"], item["shadow_samples"]))
        item["mode"] = "auto_local" if item["autonomy_level"] >= 2 else "ask"
        item["label"] = ACTION_LABELS.get(item["action_type"], item["action_type"])
        item["reversible"] = item["action_type"] in {"create_reminder", "draft_reply"}
        result.append(item)
    return result


@router.put("/policies/{action_type}")
def update_policy(action_type: str, body: PolicyRequest):
    if action_type not in SUPPORTED_ACTIONS:
        raise HTTPException(422, "Use a supported local action")
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "Provide a policy field to update")
    if "mode" in changes:
        if changes["mode"] not in {"ask", "auto_local"}:
            raise HTTPException(422, "mode must be ask or auto_local")
        changes["autonomy_level"] = 2 if changes.pop("mode") == "auto_local" else 1
    if "autonomy_level" in changes:
        level = changes["autonomy_level"]
        if level >= 2 and action_type not in {"create_reminder", "draft_reply"}:
            raise HTTPException(422, "Calendar exports are not reversible and cannot run autonomously")
        changes["mode"] = "auto_local" if level >= 2 else "ask"
    if "life_area" in changes and changes["life_area"] not in {"work", "money", "family", "health", "personal"}:
        raise HTTPException(422, "life_area must be work, money, family, health, or personal")
    changes["updated_at"] = now_iso()
    with connect() as db:
        current = db.execute("SELECT 1 FROM policies WHERE action_type=?", (action_type,)).fetchone()
        if not current:
            raise HTTPException(404, "Policy not found")
        columns = ",".join(f"{key}=?" for key in changes)
        db.execute(f"UPDATE policies SET {columns} WHERE action_type=?", (*changes.values(), action_type))
    _log("policy_changed", f"{ACTION_LABELS[action_type]} policy updated")
    return {"ok": True, "policy": next(p for p in policies() if p["action_type"] == action_type)}


@router.get("/autonomy")
def get_autonomy_control():
    with connect() as db:
        row = db.execute("SELECT value,updated_at FROM app_settings WHERE key='autonomy_enabled'").fetchone()
    return {"enabled": bool(int(row["value"])) if row else True, "updated_at": row["updated_at"] if row else None}


@router.put("/autonomy")
def set_autonomy_control(body: AutonomyControlRequest):
    with connect() as db:
        db.execute("INSERT INTO app_settings(key,value,updated_at) VALUES('autonomy_enabled',?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                   ("1" if body.enabled else "0", now_iso()))
    _log("autonomy_resumed" if body.enabled else "autonomy_paused", "Global autonomous actions enabled" if body.enabled else "Global kill switch paused autonomous actions")
    return get_autonomy_control()


@router.post("/scan/preview")
def scan_preview(body: ScanRequest):
    sources = _get_scan_sources(body.source_ids)
    if not sources:
        raise HTTPException(400, "No unprocessed sources. Import a note, email, or calendar first.")
    with connect() as db:
        skill = db.execute("SELECT * FROM skills WHERE id=?", (body.skill_id,)).fetchone()
    if not skill or not skill["enabled"]:
        raise HTTPException(404, "Choose an enabled skill")
    prompt, _, redacted_count, counts = make_prompt(sources, skill["instructions"])
    model = _model_for(sources, prompt)
    request_body = model_request(prompt, model)
    text = json.dumps(request_body, ensure_ascii=False, indent=2)
    preview_id = str(uuid4())
    with connect() as db:
        db.execute("INSERT INTO scan_previews(id,source_ids,source_digests,skill_id,model,request_body,redacted_fields,created_at) VALUES(?,?,?,?,?,?,?,?)",
                   (preview_id, json.dumps([s["id"] for s in sources]), json.dumps({s["id"]: s["digest"] for s in sources}), skill["id"], model, json.dumps(request_body, ensure_ascii=False), redacted_count, now_iso()))
    return {"preview_id": preview_id, "source_ids": [s["id"] for s in sources], "source_count": len(sources), "model": model,
            "api_key_configured": bool(API_KEY), "payload": text, "redacted_count": redacted_count,
            "redaction_counts": counts, "skill": skill["name"], "skill_id": skill["id"]}


def _normalize_item(item, sources):
    if not isinstance(item, dict) or not str(item.get("title", "")).strip():
        return None
    title = re.sub(r"\s+", " ", str(item.get("title", ""))).strip()[:180]
    detail = str(item.get("detail") or title).strip()[:3000]
    kind = item.get("kind", "task")
    if kind not in {"task", "promise", "waiting_on_them", "appointment"}:
        kind = "task"
    due = item.get("due_at")
    if due and not re.match(r"^\d{4}-\d{2}-\d{2}", str(due)):
        due = None
    try:
        confidence = max(0.0, min(1.0, float(item.get("confidence", 0.5))))
    except (ValueError, TypeError):
        confidence = 0.5
    source_map = {s["id"]: s for s in sources}
    evidence = item.get("evidence") if isinstance(item.get("evidence"), list) else []
    safe_evidence = []
    for e in evidence[:4]:
        if not isinstance(e, dict) or e.get("source_id") not in source_map:
            continue
        source = source_map[e["source_id"]]
        quote = str(e.get("quote", "")).strip()
        if not quote or quote.casefold() not in source["content"].casefold():
            sentences = re.split(r"(?<=[.!?])\s+|\n+", source["content"])
            terms = {t.casefold() for t in re.findall(r"[\w']{4,}", title) if t.casefold() not in {"send", "please", "could", "would", "about", "follow"}}
            scored = sorted(((sum(term in sentence.casefold() for term in terms), sentence.strip()) for sentence in sentences), reverse=True)
            quote = scored[0][1] if scored and scored[0][0] else source["content"].strip()[:220]
        safe_evidence.append({"source_id": e["source_id"], "quote": quote[:220]})
    evidence = safe_evidence
    source_id = evidence[0]["source_id"] if evidence else sources[0]["id"]
    return {"title": title, "detail": detail, "kind": kind, "due_at": str(due)[:40] if due else None,
            "owner": str(item["owner"])[:100] if item.get("owner") else None,
            "confidence": confidence, "evidence": evidence, "source_id": source_id}


@router.post("/scan")
def scan(body: ScanRequest):
    if body.allow_remote:
        if not API_KEY:
            raise HTTPException(400, "Nebius is not configured. Add NEBIUS_API_KEY or choose local-only analysis.")
        if not body.preview_id:
            raise HTTPException(428, "Create and review a scan preview before sending content to Nebius.")
        with connect() as db:
            preview = db.execute("SELECT * FROM scan_previews WHERE id=?", (body.preview_id,)).fetchone()
            if not preview:
                raise HTTPException(404, "Scan preview not found")
            if preview["used_at"]:
                raise HTTPException(409, "This scan preview was already used. Create a new preview before retrying.")
            created = datetime.fromisoformat(preview["created_at"])
            if (datetime.now(timezone.utc) - created.astimezone(timezone.utc)).total_seconds() > 600:
                raise HTTPException(409, "This scan preview expired. Create a new preview before sending.")
            preview_sources = json_value(preview["source_ids"], [])
            if body.skill_id != preview["skill_id"] or body.source_ids != preview_sources:
                raise HTTPException(409, "The selected sources or skill changed. Create a new preview before sending.")
            digests = json_value(preview["source_digests"], {})
            current_sources = _get_scan_sources(preview_sources)
            if len(current_sources) != len(preview_sources) or any(s["digest"] != digests.get(s["id"]) for s in current_sources):
                raise HTTPException(409, "A source changed or was deleted after preview. Create a new preview before sending.")
            skill = db.execute("SELECT * FROM skills WHERE id=?", (preview["skill_id"],)).fetchone()
            request_body = json_value(preview["request_body"], {})
            messages = request_body.get("messages", [])
            try:
                frozen_prompt = json.loads(messages[1]["content"])
            except (IndexError, KeyError, TypeError, json.JSONDecodeError):
                frozen_prompt = {}
            if not skill or not skill["enabled"] or frozen_prompt.get("skill_instructions") != skill["instructions"]:
                raise HTTPException(409, "The selected skill changed after preview. Create a new preview before sending.")
            model = preview["model"]
            redacted_count = preview["redacted_fields"]
            payload_text = json.dumps(request_body, ensure_ascii=False, indent=2)
            consumed = db.execute("UPDATE scan_previews SET used_at=? WHERE id=? AND used_at IS NULL", (now_iso(), body.preview_id))
            if consumed.rowcount != 1:
                raise HTTPException(409, "This scan preview was already used. Create a new preview before retrying.")
        sources = current_sources
        prompt = json_value(request_body.get("messages", [{}, {}])[1].get("content", "{}"), {})
    else:
        sources = _get_scan_sources(body.source_ids)
        if not sources:
            raise HTTPException(400, "No unprocessed sources to scan")
        with connect() as db:
            skill = db.execute("SELECT * FROM skills WHERE id=?", (body.skill_id,),).fetchone()
        if not skill or not skill["enabled"]:
            raise HTTPException(404, "Choose an enabled skill")
        prompt, _, redacted_count, _ = make_prompt(sources, skill["instructions"])
        model = _model_for(sources, prompt)
        request_body = model_request(prompt, model)
        payload_text = json.dumps(request_body, ensure_ascii=False, indent=2)
    try:
        if body.allow_remote:
            event_id = record_egress(model, sources, redacted_count, payload_text, "sending")
            try:
                items = call_nebius(request_body)
                with connect() as db:
                    db.execute("UPDATE egress_events SET status='sent',response_summary=? WHERE id=?", (f"Returned {len(items)} candidate item(s)", event_id))
            except Exception as exc:
                with connect() as db:
                    db.execute("UPDATE egress_events SET status='failed',response_summary=? WHERE id=?", (str(exc)[:500], event_id))
                raise HTTPException(502, str(exc)) from exc
            source_mode = "Nebius Token Factory · " + model
        else:
            items = []
            for source in sources:
                items.extend(heuristic_extract(source))
            source_mode = "Local-only extraction"
    except HTTPException:
        raise
    normalized = [_normalize_item(item, sources) for item in items]
    normalized = [x for x in normalized if x]
    added, duplicates = 0, 0
    with connect() as db:
        for item in normalized:
            exists = db.execute("SELECT id FROM loops WHERE source_id=? AND lower(title)=lower(?) AND status!='dismissed'", (item["source_id"], item["title"])).fetchone()
            if exists:
                duplicates += 1
                continue
            db.execute("INSERT INTO loops(id,title,detail,kind,due_at,owner,confidence,evidence,created_at,updated_at,source_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                       (str(uuid4()), item["title"], item["detail"], item["kind"], item["due_at"], item["owner"], item["confidence"], json.dumps(item["evidence"], ensure_ascii=False), now_iso(), now_iso(), item["source_id"]))
            added += 1
        for source in sources:
            db.execute("UPDATE sources SET scanned=1 WHERE id=?", (source["id"],))
        db.execute("INSERT INTO activity(id,event_type,detail,created_at) VALUES(?,?,?,?)", (str(uuid4()), "scan_completed", f"{source_mode} · {added} open loop(s)", now_iso()))
    return {"added": added, "duplicates": duplicates, "mode": source_mode, "source_ids": [s["id"] for s in sources]}


@router.post("/skills/{skill_id}/run")
def run_skill(skill_id: str):
    return scan(ScanRequest(skill_id=skill_id, allow_remote=False))


@router.get("/egress")
def egress():
    with connect() as db:
        rows = db.execute("SELECT * FROM egress_events ORDER BY created_at DESC LIMIT 100").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["source_ids"] = json_value(item["source_ids"], [])
        result.append(item)
    return result


@router.get("/egress/summary")
def egress_summary():
    with connect() as db:
        row = db.execute("""
            SELECT COUNT(*) AS attempts,
                   SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent,
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed,
                   SUM(CASE WHEN status='sending' THEN 1 ELSE 0 END) AS in_flight,
                   SUM(redacted_fields) AS redaction_matches,
                   SUM(LENGTH(payload)) AS payload_characters
            FROM egress_events
        """).fetchone()
        local_scans = db.execute("SELECT COUNT(*) FROM activity WHERE event_type='scan_completed' AND detail LIKE '%Local-only extraction%'").fetchone()[0]
    return {**dict(row), "attempts": row["attempts"] or 0, "sent": row["sent"] or 0,
            "failed": row["failed"] or 0, "in_flight": row["in_flight"] or 0,
            "redaction_matches": row["redaction_matches"] or 0,
            "payload_characters": row["payload_characters"] or 0,
            "local_only_scans": local_scans, "source_files_uploaded": 0,
            "note": "Original files are not uploaded as attachments. Confirmed requests send minimized text shown in the receipt; redaction matches count pattern replacements, not guaranteed removed identities."}


@router.post("/scam/check")
def scam_check(body: ScamCheckRequest):
    result = inspect_message(body.message)
    check_id = str(uuid4())
    with connect() as db:
        db.execute("INSERT INTO scam_checks(id,message_digest,message_length,score,band,signals,created_at) VALUES(?,?,?,?,?,?,?)",
                   (check_id, result["message_digest"], result["message_length"], result["score"], result["band"], json.dumps(result["signals"]), now_iso()))
    _log("scam_check", f"Local message triage · {result['band']} · {len(result['signals'])} signal(s)")
    return {"id": check_id, **result, "stored_message": False, "model_egress": False}


@router.get("/scam/checks")
def list_scam_checks():
    with connect() as db:
        rows = db.execute("SELECT * FROM scam_checks ORDER BY created_at DESC LIMIT 50").fetchall()
    return [{**dict(row), "signals": json_value(row["signals"], [])} for row in rows]


@router.delete("/scam/checks/{check_id}")
def delete_scam_check(check_id: str):
    with connect() as db:
        cur = db.execute("DELETE FROM scam_checks WHERE id=?", (check_id,))
    if not cur.rowcount:
        raise HTTPException(404, "Scam check not found")
    return {"ok": True}


@router.get("/family")
def list_family_profiles():
    with connect() as db:
        rows = db.execute("SELECT id,display_name,relationship,created_at FROM family_profiles ORDER BY display_name COLLATE NOCASE").fetchall()
    return [dict(row) for row in rows]


@router.post("/family")
def add_family_profile(body: FamilyProfileRequest):
    member_id = str(uuid4())
    salt = secrets.token_bytes(16)
    phrase = body.verification_phrase.strip().casefold().encode("utf-8")
    digest = hashlib.pbkdf2_hmac("sha256", phrase, salt, 180_000)
    with connect() as db:
        db.execute("INSERT INTO family_profiles(id,display_name,relationship,phrase_salt,phrase_digest,created_at) VALUES(?,?,?,?,?,?)",
                   (member_id, body.display_name.strip(), body.relationship.strip(), salt.hex(), digest.hex(), now_iso()))
    _log("family_contact_added", f"Added local verification profile · {body.display_name[:50]}")
    return {"id": member_id, "display_name": body.display_name.strip(), "relationship": body.relationship.strip(), "created": True}


@router.delete("/family/{member_id}")
def delete_family_profile(member_id: str):
    with connect() as db:
        cur = db.execute("DELETE FROM family_profiles WHERE id=?", (member_id,))
    if not cur.rowcount:
        raise HTTPException(404, "Trusted contact not found")
    _log("family_contact_deleted", "Deleted a local verification profile")
    return {"ok": True}


@router.post("/family/verify")
def verify_family_phrase(body: FamilyVerifyRequest):
    with connect() as db:
        row = db.execute("SELECT phrase_salt,phrase_digest FROM family_profiles WHERE id=?", (body.member_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Trusted contact not found")
    salt = bytes.fromhex(row["phrase_salt"])
    phrase = body.verification_phrase.strip().casefold().encode("utf-8")
    supplied = hashlib.pbkdf2_hmac("sha256", phrase, salt, 180_000).hex()
    verified = hmac.compare_digest(supplied, row["phrase_digest"])
    _log("family_phrase_verified" if verified else "family_phrase_failed", "Local trusted-contact phrase check")
    next_step = ("Continue only if you are comfortable; independently verify money or account requests by calling a known number."
                 if verified else "Do not act on the request. Call the person using a number you already trust.")
    return {"verified": verified, "next_step": next_step}


@router.get("/contracts")
def list_contracts():
    with connect() as db:
        rows = db.execute("SELECT * FROM contracts ORDER BY created_at DESC").fetchall()
    return [{**dict(row), "red_team": json_value(row["red_team"], {}),
             "scope_label": "All automatic local actions" if row["scope"] == "all_auto" else ACTION_LABELS.get(row["scope"], row["scope"])} for row in rows]


@router.post("/contracts")
def create_contract(body: QuietHoursContractRequest):
    try:
        compiled = compile_quiet_hours(body.statement, body.scope)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    contract_id = str(uuid4())
    with connect() as db:
        db.execute("INSERT INTO contracts(id,title,statement,start_time,end_time,scope,red_team,created_at) VALUES(?,?,?,?,?,?,?,?)",
                   (contract_id, body.title.strip(), body.statement.strip(), compiled["start"], compiled["end"], compiled["scope"], json.dumps(compiled["red_team"]), now_iso()))
    _log("contract_created", f"Added quiet-hours precommitment · {body.title[:60]} · red-team boundaries passed")
    return {"id": contract_id, "title": body.title.strip(), **compiled, "active": True}


@router.delete("/contracts/{contract_id}")
def delete_contract(contract_id: str):
    with connect() as db:
        cur = db.execute("DELETE FROM contracts WHERE id=?", (contract_id,))
    if not cur.rowcount:
        raise HTTPException(404, "Precommitment not found")
    _log("contract_deleted", "Removed a quiet-hours precommitment")
    return {"ok": True}


def _execute_local_action(db, action, execution_mode="manual", autonomy_level=1):
    payload = json_value(action["payload"], {})
    result = {}
    if action["action_type"] == "create_reminder":
        reminder_id = str(uuid4())
        db.execute("INSERT INTO reminders(id,action_id,title,due_at,created_at) VALUES(?,?,?,?,?)",
                   (reminder_id, action["id"], action["title"], payload.get("due_at"), now_iso()))
        result = {"message": "Reminder saved locally", "reminder_id": reminder_id, "due_at": payload.get("due_at")}
    elif action["action_type"] == "draft_reply":
        result = {"message": "Draft saved in your local workspace. It was not sent.", "draft": payload.get("draft", "")}
    elif action["action_type"] == "calendar_export":
        due = payload.get("due_at") or date.today().isoformat()
        try:
            dt = datetime.fromisoformat(due)
            stamp = dt.strftime("%Y%m%dT%H%M%S") if "T" in due else dt.strftime("%Y%m%d")
        except ValueError:
            stamp = date.today().strftime("%Y%m%d")
        ics = "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Threadline//Personal AI//EN", "BEGIN:VEVENT", f"UID:{action['id']}@threadline.local", f"DTSTART:{stamp}", f"SUMMARY:{action['title']}", f"DESCRIPTION:{str(payload.get('description', ''))[:500].replace(chr(10), ' ')}", "END:VEVENT", "END:VCALENDAR", ""])
        result = {"message": "Calendar event exported locally", "filename": "threadline-reminder.ics", "content": ics}
    completed_at = datetime.now(timezone.utc)
    undo_deadline = (completed_at + timedelta(minutes=10)).isoformat(timespec="seconds") if action["action_type"] in {"create_reminder", "draft_reply"} else None
    db.execute("UPDATE actions SET status='completed',decided_at=?,result=?,undo_deadline=?,execution_mode=?,policy_level=? WHERE id=?",
               (completed_at.isoformat(timespec="seconds"), json.dumps(result, ensure_ascii=False), undo_deadline, execution_mode, autonomy_level, action["id"]))
    return result


@router.get("/actions")
def list_actions():
    with connect() as db:
        rows = db.execute("SELECT a.*,l.title AS loop_title,c.title AS contract_title FROM actions a LEFT JOIN loops l ON l.id=a.loop_id LEFT JOIN contracts c ON c.id=a.contract_id ORDER BY a.created_at DESC LIMIT 100").fetchall()
    items = []
    for row in rows:
        item = {**dict(row), "payload": json_value(row["payload"], {}), "result": json_value(row["result"], {}), "undo_data": json_value(row["undo_data"], {})}
        if item["status"] == "pending":
            item["shadow_prediction"] = None
        items.append(item)
    return items


@router.post("/actions")
def propose_action(body: ActionRequest):
    if body.action_type not in SUPPORTED_ACTIONS:
        raise HTTPException(422, "This action is not supported in the local MVP")
    action_id = str(uuid4())
    with connect() as db:
        if body.loop_id and not db.execute("SELECT 1 FROM loops WHERE id=?", (body.loop_id,)).fetchone():
            raise HTTPException(404, "Open loop not found")
        policy = db.execute("SELECT * FROM policies WHERE action_type=?", (body.action_type,)).fetchone()
        if not policy or policy["autonomy_level"] == 0:
            raise HTTPException(403, "This action type is observe-only. Raise its autonomy level before proposing actions.")
        control = db.execute("SELECT value FROM app_settings WHERE key='autonomy_enabled'").fetchone()
        autonomy_enabled = bool(int(control["value"])) if control else True
        day_start = datetime.now(timezone.utc).date().isoformat()
        auto_count = db.execute("SELECT COUNT(*) FROM actions WHERE execution_mode='autonomous' AND status IN ('completed','undone') AND created_at>=? AND action_type=?", (day_start, body.action_type)).fetchone()[0]
        reversible = body.action_type in {"create_reminder", "draft_reply"}
        contract = _quiet_contract(db, body.action_type)
        can_auto = (not contract and can_execute_automatically(autonomy_enabled, bool(policy["shadow_mode"]), reversible,
                                                               policy["autonomy_level"], auto_count, policy["max_actions_per_day"]))
        prediction = None
        if policy["shadow_mode"]:
            prediction = shadow_prediction(policy["approved_count"], policy["rejected_count"])
        db.execute("INSERT INTO actions(id,loop_id,action_type,title,payload,status,created_at,shadow_prediction,execution_mode,policy_level,contract_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                   (action_id, body.loop_id, body.action_type, body.title[:180], json.dumps(body.payload, ensure_ascii=False), "pending", now_iso(), None if prediction is None else int(prediction), "pending", policy["autonomy_level"], contract["id"] if contract else None))
        action = dict(db.execute("SELECT * FROM actions WHERE id=?", (action_id,)).fetchone())
        result = _execute_local_action(db, action, "autonomous", policy["autonomy_level"]) if can_auto else None
        final_action = db.execute("SELECT undo_deadline FROM actions WHERE id=?", (action_id,)).fetchone()
    _log("action_proposed", f"{ACTION_LABELS[body.action_type]} · {body.title[:80]}")
    if result and policy["autonomy_level"] >= 3:
        _log("autonomy_report", f"L{policy['autonomy_level']} completed {ACTION_LABELS[body.action_type]} · {body.title[:80]}")
    return {"id": action_id, "status": "completed" if result else "pending", "result": result,
            "execution_mode": "autonomous" if result else "pending", "undo_deadline": final_action["undo_deadline"],
            "reason": f"Precommitment protects {contract['title']} during this quiet window; review is required" if contract else "Daily automation cap reached; review required" if autonomy_enabled and policy["autonomy_level"] >= 2 and reversible and auto_count >= policy["max_actions_per_day"] else "Global autonomy is paused; review required" if not autonomy_enabled and policy["autonomy_level"] >= 2 else None}


@router.post("/actions/{action_id}/decision")
def decide_action(action_id: str, body: DecisionRequest):
    if body.decision not in {"approve", "reject"}:
        raise HTTPException(422, "decision must be approve or reject")
    with connect() as db:
        action = db.execute("SELECT * FROM actions WHERE id=?", (action_id,)).fetchone()
        if not action:
            raise HTTPException(404, "Action not found")
        if action["status"] != "pending":
            raise HTTPException(409, "Action has already been decided")
        policy = db.execute("SELECT * FROM policies WHERE action_type=?", (action["action_type"],)).fetchone()
        if body.decision == "approve":
            contract = _quiet_contract(db, action["action_type"])
            if contract and len((body.override_reason or "").strip()) < 20:
                raise HTTPException(409, f"Precommitment '{contract['title']}' is active. Wait until its window ends or provide a reason of at least 20 characters to override.")
            result = _execute_local_action(db, dict(action), "manual", policy["autonomy_level"])
            if contract:
                db.execute("UPDATE actions SET contract_id=?,override_reason=? WHERE id=?",
                           (contract["id"], body.override_reason.strip(), action_id))
            db.execute("UPDATE policies SET approved_count=approved_count+1,updated_at=? WHERE action_type=?", (now_iso(), action["action_type"]))
        else:
            result = None
            db.execute("UPDATE actions SET status='rejected',decided_at=? WHERE id=?", (now_iso(), action_id))
            db.execute("UPDATE policies SET rejected_count=rejected_count+1,updated_at=? WHERE action_type=?", (now_iso(), action["action_type"]))
        prediction = action["shadow_prediction"]
        if prediction is not None:
            agreement = int((prediction == 1) == (body.decision == "approve"))
            db.execute("UPDATE policies SET shadow_samples=shadow_samples+1,shadow_agreements=shadow_agreements+?,updated_at=? WHERE action_type=?",
                       (agreement, now_iso(), action["action_type"]))
        count = db.execute("SELECT approved_count FROM policies WHERE action_type=?", (action["action_type"],)).fetchone()[0]
    _log("action_approved" if body.decision == "approve" else "action_rejected", f"{body.decision} · {action['title'][:80]}")
    with connect() as db:
        p = dict(db.execute("SELECT * FROM policies WHERE action_type=?", (action["action_type"],)).fetchone())
    summary = shadow_summary(p["shadow_agreements"], p["shadow_samples"])
    return {"ok": True, "result": result, "promotion_suggested": summary["promotion_suggested"], **summary}


@router.post("/actions/{action_id}/undo")
def undo_action(action_id: str):
    with connect() as db:
        action = db.execute("SELECT * FROM actions WHERE id=?", (action_id,)).fetchone()
        if not action:
            raise HTTPException(404, "Action not found")
        if action["status"] != "completed":
            raise HTTPException(409, "Only completed actions can be undone")
        if action["action_type"] not in {"create_reminder", "draft_reply"}:
            raise HTTPException(422, "This action has no supported inverse")
        deadline = datetime.fromisoformat(action["undo_deadline"]) if action["undo_deadline"] else None
        if not deadline or datetime.now(timezone.utc) > deadline.astimezone(timezone.utc):
            raise HTTPException(409, "The ten-minute undo window expired")
        old_result = json_value(action["result"], {})
        if action["action_type"] == "create_reminder":
            db.execute("DELETE FROM reminders WHERE action_id=?", (action_id,))
        result = {"message": "Undone locally", "undone_at": now_iso()}
        db.execute("UPDATE actions SET status='undone',undo_data=?,result=?,undo_deadline=NULL WHERE id=?",
                   (json.dumps(old_result, ensure_ascii=False), json.dumps(result), action_id))
        policy = db.execute("SELECT autonomy_level FROM policies WHERE action_type=?", (action["action_type"],)).fetchone()
        demoted_level = max(1, policy["autonomy_level"] - 1)
        db.execute("UPDATE policies SET autonomy_level=?,mode='ask',updated_at=? WHERE action_type=?",
                   (demoted_level, now_iso(), action["action_type"]))
    _log("action_undone", f"Undid {ACTION_LABELS[action['action_type']]} and demoted autonomy to L{demoted_level}")
    return {"ok": True, "autonomy_level": demoted_level, "result": result}


@router.get("/reminders")
def reminders():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM reminders ORDER BY CASE WHEN due_at IS NULL THEN 1 ELSE 0 END,due_at DESC").fetchall()]


@router.post("/demo/load")
def load_demo():
    samples = [
        ("Email · Monday", "email", "Quote for the studio project", "Subject: Updated quote\nFrom: Sam Chen\n\nHi, could you send the revised quote to me by Friday? Please include the installation line item. Thanks!"),
        ("Calendar · This week", "calendar", "Team sync", "Team sync | When: 2026-10-29 10:30 | Where: Online | Bring the first draft and ask Priya to confirm the review date."),
        ("Note · Weekend", "note", "Personal notes", "Call the dentist tomorrow to reschedule. I promised Jordan I would share the launch notes by Friday. Waiting for Casey to send the venue options."),
        ("Email · Last week", "email", "Re: Travel details", "Subject: Re: Travel details\nFrom: Alex Morgan\n\nCould you confirm the pickup time by Thursday? If you need me, reply to alex.morgan@example.test or call +1 (415) 555-0142."),
    ]
    source_ids = []
    for filename, kind, title, content in samples:
        sid, _ = _store_source(filename, kind, title, content, origin="demo")
        source_ids.append(sid)
    _log("demo_loaded", "Loaded four synthetic sample sources")
    return {"source_ids": source_ids}


@router.post("/demo/simulated-week")
def demo_simulated_week():
    return simulate_week()


@router.post("/demo/reset")
def reset_demo():
    with connect() as db:
        db.execute("DELETE FROM sources WHERE origin='demo'")
        db.execute("DELETE FROM activity WHERE event_type='demo_loaded'")
    _log("demo_reset", "Removed synthetic sample data")
    return {"ok": True}


@router.get("/export")
def export_data():
    with connect() as db:
        actions = [dict(r) for r in db.execute("SELECT * FROM actions ORDER BY created_at").fetchall()]
        for action in actions:
            action["payload"] = json_value(action["payload"], {})
            action["result"] = json_value(action["result"], {})
            action["undo_data"] = json_value(action["undo_data"], {})
            if action["status"] == "pending":
                action["shadow_prediction"] = None
        autonomy = db.execute("SELECT value,updated_at FROM app_settings WHERE key='autonomy_enabled'").fetchone()
        workflow_runs = []
        for run in db.execute("SELECT * FROM workflow_runs ORDER BY created_at").fetchall():
            item = dict(run)
            item["inputs"] = json_value(item["inputs"], {})
            item["outputs"] = json_value(item["outputs"], {})
            item["nodes"] = [{**dict(node), "output": json_value(node["output"], None)} for node in db.execute("SELECT * FROM workflow_node_runs WHERE run_id=? ORDER BY rowid", (item["id"],)).fetchall()]
            item["source_ids"] = [row["source_id"] for row in db.execute("SELECT source_id FROM workflow_run_sources WHERE run_id=?", (item["id"],)).fetchall()]
            workflow_runs.append(item)
        workflow_definitions = [{**dict(row), "versions": [{**dict(version), "spec": json_value(version["spec"], {})}
                                   for version in db.execute("SELECT * FROM workflow_versions WHERE workflow_id=? ORDER BY version", (row["id"],)).fetchall()]}
                                 for row in db.execute("SELECT * FROM workflow_definitions ORDER BY created_at").fetchall()]
        return {
            "sources": [dict(r) for r in db.execute("SELECT id,filename,kind,title,content,digest,created_at,origin FROM sources").fetchall()],
            "loops": [{**dict(r), "evidence": json_value(r["evidence"], [])} for r in db.execute("SELECT * FROM loops").fetchall()],
            "skills": [dict(r) for r in db.execute("SELECT * FROM skills").fetchall()],
            "policies": [dict(r) for r in db.execute("SELECT * FROM policies").fetchall()],
            "actions": actions,
            "reminders": [dict(r) for r in db.execute("SELECT * FROM reminders").fetchall()],
            "egress_events": [dict(r) for r in db.execute("SELECT * FROM egress_events ORDER BY created_at").fetchall()],
            "scam_checks": [{**dict(r), "signals": json_value(r["signals"], [])} for r in db.execute("SELECT * FROM scam_checks ORDER BY created_at").fetchall()],
            "family_profiles": [dict(r) for r in db.execute("SELECT id,display_name,relationship,created_at FROM family_profiles ORDER BY created_at").fetchall()],
            "contracts": [{**dict(r), "red_team": json_value(r["red_team"], {})} for r in db.execute("SELECT * FROM contracts ORDER BY created_at").fetchall()],
            "workflow_runs": workflow_runs,
            "workflow_definitions": workflow_definitions,
            "activity": [dict(r) for r in db.execute("SELECT * FROM activity ORDER BY created_at").fetchall()],
            "autonomy_control": {"enabled": bool(int(autonomy["value"])) if autonomy else True,
                                 "updated_at": autonomy["updated_at"] if autonomy else None},
            "exported_at": now_iso(),
        }
