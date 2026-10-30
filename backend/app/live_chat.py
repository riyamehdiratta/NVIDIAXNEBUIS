"""Unified Live Sovereign AI Assistant (ChatGPT & Gemini Live Style).

Provides an always-on, conversational and voice-interactive AI delegate.
Coordinates the 5 pillars under the hood (memory, preferences, conformal risk,
synthesizer, causal world model) while presenting a seamless conversational interface
for desktop and mobile users.
"""

import json
import re
import urllib.request
import urllib.error
from datetime import date, datetime, timedelta
from typing import Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .config import API_KEY, NANO_MODEL, SUPER_MODEL, TOKEN_FACTORY_BASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from .db import connect, json_value, now_iso
from .privacy import redact
from .preference_model import extract_features, predict_approval
from .conformal import evaluate_conformal_gate
from .scam import inspect_message
from .world_model import simulate_forward_horizon
from .mcp_connectors import execute_universal_tool, get_all_available_tools
from .apprenticeship import get_native_foreground_window
from .synthesizer import synthesize_tool, SynthesizeToolRequest
from .device_agent import execute_device_goal_engine
from .hermes_adapter import store_hermes_memory, recall_hermes_memories, add_open_loop_from_hermes, get_hermes_memory_context

router = APIRouter(prefix="/api/live", tags=["live_assistant"])


class ChatMessage(BaseModel):
    role: str  # 'user' | 'assistant' | 'system'
    content: str


class LiveChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    history: list[ChatMessage] = Field(default_factory=list)
    continuous_mode: bool = False
    context_hint: str | None = None


def get_user_context_snapshot() -> dict[str, Any]:
    """Retrieve compressed live workspace state for the conversational agent."""
    with connect() as db:
        loops = db.execute(
            "SELECT id, title, kind, due_at, confidence FROM loops WHERE status='open' ORDER BY due_at IS NULL, due_at LIMIT 15"
        ).fetchall()
        sources_count = db.execute("SELECT COUNT(*) as c FROM sources").fetchone()["c"]
        actions_pending = db.execute("SELECT COUNT(*) as c FROM actions WHERE status='pending'").fetchone()["c"]
        recent_sources = db.execute("SELECT title, kind, created_at FROM sources ORDER BY created_at DESC LIMIT 3").fetchall()
        pref_weights = db.execute("SELECT value FROM app_settings WHERE key='bayesian_preference_weights'").fetchone()
        mems = db.execute("SELECT id, category, key, value FROM hermes_memories ORDER BY updated_at DESC LIMIT 20").fetchall()

    horizon = simulate_forward_horizon()
    return {
        "open_loops": [dict(r) for r in loops],
        "hermes_memories": [dict(r) for r in mems],
        "total_sources": sources_count,
        "pending_actions": actions_pending,
        "recent_sources": [dict(r) for r in recent_sources],
        "horizon_summary": horizon.get("morning_recommendation", "Workload steady"),
        "horizon_bottlenecks": horizon.get("bottlenecks", []),
        "weights": json_value(pref_weights["value"], []) if pref_weights else [],
        "today": date.today().isoformat(),
        "day_of_week": datetime.now().strftime("%A"),
    }


def _extract_task_intent(user_text: str) -> dict[str, Any] | None:
    """Intelligently detect tasks, promises, and waiting items from conversational speech or text."""
    text = user_text.strip()
    lower = text.lower()

    # Determine kind
    kind = "task"
    if re.search(r"\b(i promised|i promise|i owe|my promise)\b", lower):
        kind = "promise"
    elif re.search(r"\b(waiting on|waiting for|expecting reply from|waiting to hear from)\b", lower):
        kind = "waiting_on_them"
    elif re.search(r"\b(event|appointment|meeting|conference|presentation|sync)\b", lower):
        kind = "appointment"

    task_body = None

    # Pattern 1: Explicit open loop / task / event / appointment phrases
    # "add my task to my open loop: finish report"
    # "add event: team presentation on 2026-11-02"
    # "schedule meeting with Jordan on Monday"
    cleaned = re.sub(
        r"^(?:please\s+)?(?:add|put|keep|record|track|save|schedule)\s+(?:my\s+|a\s+|this\s+|an\s+)?(?:task|event|appointment|meeting|reminder|commitment)?\s*(?:to|in|into)?\s*(?:my\s+)?(?:open\s+)?(?:loops?|calendar)?\s*(?:to|:|is|about|-)?\s*",
        "",
        text,
        flags=re.I,
    )
    if cleaned != text and len(cleaned.strip()) >= 2:
        task_body = cleaned.strip()

    # Pattern 2: "my task is (to)...", "task: ...", "new task: ...", "todo: ..."
    if not task_body:
        m = re.search(r"\b(?:my task is(?: to)?|(?:new |create |create a )?task\s*[:\-]|todo\s*[:\-])\s*(.+)", text, re.I)
        if m:
            task_body = m.group(1).strip()

    # Pattern 3: "remind me to...", "don't let me forget to...", "remember to...", "need to...", "have to...", "i must...", "track task..."
    if not task_body:
        m = re.search(r"\b(?:remind me to|don'?t let me forget to|remember to|(?:i )?need to|(?:i )?have to|(?:i )?must|track (?:this )?task)\s+(.+)", text, re.I)
        if m:
            task_body = m.group(1).strip()

    # Pattern 4: "i will finish/call/send...", "i promised to..."
    if not task_body:
        m = re.search(r"\b(?:i promised(?: to)?|i will|i'll)\s+(send|reply|finish|call|pay|submit|schedule|review|draft|complete|order|buy|write|deliver|meet)\s+(.+)", text, re.I)
        if m:
            task_body = f"{m.group(1)} {m.group(2)}".strip()

    # Pattern 5: "waiting on/for..."
    if not task_body:
        m = re.search(r"\b(?:waiting on|waiting for)\s+(.+)", text, re.I)
        if m:
            task_body = f"Waiting on {m.group(1)}".strip()

    if not task_body:
        return None

    # Clean leading 'to ' if present
    task_body = re.sub(r"^(?:to\s+|that\s+)", "", task_body, flags=re.I).strip(" :-,")

    # Parse due date from task_body or text
    due_at = None
    today = date.today()

    date_match = re.search(
        r"\b(?:by|before|due(?: on)?|on|until)\s+(today|tomorrow|tonight|this week|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b",
        task_body,
        re.I,
    )
    clean_title = task_body

    if date_match:
        token = date_match.group(1).lower()
        if token in ("today", "tonight"):
            due_at = today.isoformat()
        elif token == "tomorrow":
            due_at = (today + timedelta(days=1)).isoformat()
        elif token in ("this week", "next week"):
            delta = (4 - today.weekday()) % 7 or 7
            if token == "next week":
                delta += 7
            due_at = (today + timedelta(days=delta)).isoformat()
        elif token in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
            weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            delta = (weekdays.index(token) - today.weekday()) % 7 or 7
            due_at = (today + timedelta(days=delta)).isoformat()
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
            due_at = token

        # Strip date phrase from title
        candidate_title = task_body[:date_match.start()].strip(" .,;:-")
        if candidate_title and len(candidate_title) >= 3:
            clean_title = candidate_title
    else:
        # Check simple relative words
        if re.search(r"\btomorrow\b", task_body, re.I):
            due_at = (today + timedelta(days=1)).isoformat()
            clean_title = re.sub(r"\b(?:by|on)?\s*tomorrow\b", "", task_body, flags=re.I).strip(" .,;:-")
        elif re.search(r"\b(?:today|tonight)\b", task_body, re.I):
            due_at = today.isoformat()
            clean_title = re.sub(r"\b(?:by|on)?\s*(?:today|tonight)\b", "", task_body, flags=re.I).strip(" .,;:-")
        elif re.search(r"\bnext week\b", task_body, re.I):
            due_at = (today + timedelta(days=7)).isoformat()
            clean_title = re.sub(r"\b(?:by|on)?\s*next week\b", "", task_body, flags=re.I).strip(" .,;:-")

    if not clean_title or len(clean_title) < 2:
        clean_title = task_body

    if len(clean_title) > 120:
        clean_title = clean_title[:117] + "..."

    return {
        "title": clean_title.capitalize(),
        "detail": f"Captured via Live Voice/Chat (Hermes Agent): {user_text}",
        "due_at": due_at,
        "kind": kind,
    }


def _extract_reminder_intent(user_text: str) -> dict[str, Any] | None:
    """Parse clear reminder requests, including monthly day-of-month repeats."""
    text = user_text.strip()
    monthly = re.search(r"\b(?:every\s+(?:month|monthly)|every\s+(\d{1,2})(?:st|nd|rd|th)?\s+of\s+(?:every\s+)?month)\b", text, re.I)
    if not re.search(r"\b(remind(?:er)?|remind me)\b", text, re.I) or not monthly:
        return None
    day = int(monthly.group(1) or 1)
    if not 1 <= day <= 28:
        return {"error": "Monthly reminders currently support days 1 through 28 so they occur every month."}
    title = re.sub(r"^\s*(?:please\s+)?(?:add|create|set)\s+(?:a\s+)?reminder\s+", "", text, flags=re.I)
    cadence = re.search(r"\bevery\s+(?:(?:month|monthly)|\d{1,2}(?:st|nd|rd|th)?\s+of\s+(?:every\s+)?month)\b", title, re.I)
    if cadence:
        title = title[cadence.end():]
    title = re.sub(r"^(?:\s+)?(?:that\s+)?(?:i\s+(?:have|need)\s+to|to)\s+", "", title, flags=re.I).strip(" .?!")
    title = re.sub(r"^on\s+", "", title, flags=re.I)
    if len(title) < 3:
        return None
    title = title[0].upper() + title[1:]
    today = date.today()
    due = date(today.year, today.month, day)
    if due < today:
        due = date(today.year + (today.month == 12), 1 if today.month == 12 else today.month + 1, day)
    return {"title": title[:180], "due_at": due.isoformat(), "recurrence": "monthly", "recurrence_day": day}


def _extract_memory_intent(user_text: str) -> dict[str, Any] | None:
    """Detect statements meant to be stored in Hermes persistent memory."""
    text = user_text.strip()

    # Trigger: "remember that...", "note that...", "keep in mind that...", "save to persistent memory..."
    m = re.search(
        r"\b(?:remember that|keep in mind that|note that|don't forget that|save (?:this )?to (?:persistent )?memory(?:\s*:\s*|\s+that\s+|\s+)|store (?:this )?in memory(?:\s*:\s*|\s+that\s+|\s+))\s*(.+)",
        text,
        re.I,
    )
    if m:
        fact = m.group(1).strip(" .?!")
        kv_match = re.search(r"(?:my\s+)?([a-z0-9_ -]+)\s+(?:is|are|=|:)\s+(.+)", fact, re.I)
        if kv_match:
            key = kv_match.group(1).strip()
            val = kv_match.group(2).strip()
        else:
            key = fact[:40]
            val = fact
        return {"key": key, "value": val, "category": "user_fact", "fact": fact}

    # "my [property] is [value]" pattern
    m2 = re.search(
        r"\bmy\s+(name|role|timezone|location|team|manager|preferred language|favorite \w+)\s+(?:is|are|=|:)\s+([^,.!?]+)",
        text,
        re.I,
    )
    if m2:
        return {
            "key": m2.group(1).strip(),
            "value": m2.group(2).strip(),
            "category": "user_profile",
            "fact": f"My {m2.group(1).strip()} is {m2.group(2).strip()}",
        }

    return None


def _query_event_or_task(query_topic: str) -> dict[str, Any] | None:
    """Search for specific commitments, events, or memories matching a topic."""
    topic = query_topic.strip(" .?!").lower()
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM loops WHERE lower(title) LIKE ? OR lower(detail) LIKE ? ORDER BY due_at IS NULL, due_at LIMIT 5",
            (f"%{topic}%", f"%{topic}%"),
        ).fetchall()
        if not rows:
            reminder_rows = db.execute("SELECT * FROM reminders WHERE active=1 AND lower(title) LIKE ? ORDER BY due_at LIMIT 5", (f"%{topic}%",)).fetchall()
            if reminder_rows:
                items = []
                for reminder in reminder_rows:
                    item = dict(reminder)
                    if item.get("recurrence") == "monthly":
                        today = date.today()
                        next_date = date(today.year, today.month, item["recurrence_day"])
                        if next_date < today:
                            next_month = 1 if today.month == 12 else today.month + 1
                            next_year = today.year + (today.month == 12)
                            next_date = date(next_year, next_month, item["recurrence_day"])
                        item.update({"kind": "reminder", "status": "active", "due_at": next_date.isoformat(), "detail": f"Repeats monthly on day {item['recurrence_day']}"})
                    else:
                        item.update({"kind": "reminder", "status": "active", "detail": "Reminder"})
                    items.append(item)
                lines = [f"• **{item['title']}** — next due {item['due_at']} ({item['detail']})" for item in items]
                return {"found": True, "items": items, "message": f"Here is what I found for '{query_topic}':\n\n" + "\n".join(lines)}
            mem_rows = db.execute(
                "SELECT * FROM hermes_memories WHERE lower(key) LIKE ? OR lower(value) LIKE ? LIMIT 5",
                (f"%{topic}%", f"%{topic}%"),
            ).fetchall()
            if mem_rows:
                items = [f"• **{m['key']}**: {m['value']}" for m in mem_rows]
                return {
                    "found": True,
                    "items": [dict(m) for m in mem_rows],
                    "message": f"I found the following in your Hermes persistent memory regarding '{query_topic}':\n\n" + "\n".join(items),
                }
            return None

    today = date.today()
    res_lines = []
    for r in rows:
        due = r["due_at"]
        due_str = "No specific deadline"
        if due:
            try:
                due_date = date.fromisoformat(due[:10])
                diff = (due_date - today).days
                if diff == 0:
                    rel = "Today"
                elif diff == 1:
                    rel = "Tomorrow"
                elif diff == -1:
                    rel = "Yesterday (Overdue)"
                elif diff < -1:
                    rel = f"{-diff} days overdue"
                elif diff > 1:
                    rel = f"in {diff} days"
                else:
                    rel = ""
                due_str = f"**{due}** ({rel})" if rel else f"**{due}**"
            except Exception:
                due_str = f"**{due}**"

        res_lines.append(
            f"• [{r['kind'].upper()}] **{r['title']}**\n"
            f"  - **Date / Due:** {due_str}\n"
            f"  - **Status:** {r['status'].capitalize()}\n"
            f"  - **Details:** {r['detail']}"
        )

    return {
        "found": True,
        "items": [dict(r) for r in rows],
        "message": f"Here is what I found for '{query_topic}':\n\n" + "\n\n".join(res_lines),
    }


def _query_schedule_for_date(date_token: str) -> dict[str, Any]:
    """Retrieve all open commitments, appointments, and events scheduled for a date."""
    token = date_token.lower().strip(" .?!")
    today = date.today()
    target_date = None
    if token in ("today", "tonight"):
        target_date = today
    elif token == "tomorrow":
        target_date = today + timedelta(days=1)
    elif token in ("this week", "next week"):
        delta = (4 - today.weekday()) % 7 or 7
        if token == "next week":
            delta += 7
        target_date = today + timedelta(days=delta)
    elif token in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        delta = (weekdays.index(token) - today.weekday()) % 7 or 7
        target_date = today + timedelta(days=delta)
    else:
        try:
            target_date = date.fromisoformat(token)
        except Exception:
            target_date = None

    date_str = target_date.isoformat() if target_date else token
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM loops WHERE status='open' AND due_at LIKE ? ORDER BY title",
            (f"{date_str}%",),
        ).fetchall()
        reminders = db.execute("SELECT id,title,due_at,recurrence,recurrence_day FROM reminders WHERE active=1 AND (due_at LIKE ? OR (recurrence='monthly' AND recurrence_day=?)) ORDER BY title",
                               (f"{date_str}%", target_date.day if target_date else -1)).fetchall()
    rows = [dict(r) for r in rows]
    rows.extend({"kind": "reminder", "title": r["title"], "due_at": r["due_at"], "detail": "Recurring monthly reminder" if r["recurrence"] else "Reminder"} for r in reminders)

    day_label = target_date.strftime("%A, %b %d") if target_date else date_str
    if not rows:
        return {
            "date": date_str,
            "count": 0,
            "items": [],
            "message": f"You have no commitments or events scheduled for **{day_label}**.",
        }

    lines = [f"You have **{len(rows)}** scheduled item(s) on **{day_label}**:\n"]
    for r in rows:
        lines.append(f"• [{r['kind'].upper()}] **{r['title']}** — {r['detail']}")

    return {
        "date": date_str,
        "count": len(rows),
        "items": [dict(r) for r in rows],
        "message": "\n".join(lines),
    }


def _execute_agentic_action(user_text: str, context: dict[str, Any]) -> dict[str, Any] | None:
    """Detect and execute autonomous actions requested by user via voice or chat."""
    lower = user_text.lower().strip()

    # 1. Recurring reminder creation (kept distinct from open-loop capture).
    reminder_intent = _extract_reminder_intent(user_text)
    if reminder_intent:
        if reminder_intent.get("error"):
            return {"type": "reminder_needs_clarification", "message": reminder_intent["error"]}
        reminder_id = "rem_live_" + uuid4().hex[:10]
        action_id = "act_live_" + uuid4().hex[:10]
        now = now_iso()
        with connect() as db:
            db.execute("INSERT INTO actions(id,action_type,title,payload,status,created_at,decided_at,result,execution_mode,policy_level) VALUES(?, 'create_reminder', ?, ?, 'completed', ?, ?, ?, 'manual', 1)",
                       (action_id, reminder_intent["title"], json.dumps(reminder_intent), now, now,
                        json.dumps({"message": "Recurring reminder saved locally", **reminder_intent})))
            db.execute("INSERT INTO reminders(id,action_id,title,due_at,created_at,recurrence,recurrence_day,active) VALUES(?,?,?,?,?,?,?,1)",
                       (reminder_id, action_id, reminder_intent["title"], reminder_intent["due_at"], now,
                        reminder_intent["recurrence"], reminder_intent["recurrence_day"]))
            db.execute("INSERT INTO activity(id,event_type,detail,created_at) VALUES(?, 'reminder_created', ?, ?)",
                       (str(uuid4()), f"Added monthly reminder: {reminder_intent['title']} (day {reminder_intent['recurrence_day']})", now))
        return {"type": "reminder_created", "reminder_id": reminder_id, **reminder_intent,
                "message": f"Added the monthly reminder **{reminder_intent['title']}**, on day {reminder_intent['recurrence_day']} of each month. It is saved in Threadline."}

    # 2. Task creation & Open Loops injection
    task_intent = _extract_task_intent(user_text)
    if task_intent:
        loop_id = "loop_live_" + uuid4().hex[:8]
        t_now = now_iso()
        task_title = task_intent["title"]
        due_at = task_intent["due_at"]
        kind = task_intent["kind"]
        evidence_json = json.dumps([{"source": "Live Assistant (Hermes Agent)", "quote": user_text}])

        with connect() as db:
            db.execute(
                """INSERT INTO loops(id, title, detail, kind, status, due_at, confidence, evidence, created_at, updated_at)
                   VALUES(?, ?, ?, ?, 'open', ?, 0.98, ?, ?, ?)""",
                (loop_id, task_title, task_intent["detail"], kind, due_at, evidence_json, t_now, t_now),
            )
            db.execute(
                "INSERT INTO activity(id, event_type, detail, created_at) VALUES(?, 'loop_created', ?, ?)",
                (str(uuid4()), f"Added commitment: {task_title}", t_now),
            )
            db.execute(
                """INSERT INTO world_model_triples(id, subject, predicate, object, confidence, evidence, created_at, updated_at)
                   VALUES(?, 'user', 'has_open_commitment', ?, 0.98, ?, ?, ?)""",
                ("trip_" + uuid4().hex[:10], task_title, evidence_json, t_now, t_now),
            )
            db.execute(
                """INSERT INTO hermes_memories(id, category, key, value, confidence, evidence, created_at, updated_at)
                   VALUES(?, 'task', ?, ?, 1.0, ?, ?, ?)""",
                ("mem_" + uuid4().hex[:10], f"task:{loop_id}", task_title, evidence_json, t_now, t_now),
            )

        due_text = f" due {due_at}" if due_at else ""
        return {
            "type": "loop_created",
            "loop_id": loop_id,
            "title": task_title,
            "due_at": due_at,
            "kind": kind,
            "message": f"I've added '{task_title}' to your open loops{due_text} and committed it to Hermes persistent memory.",
        }

    # 2. Persistent Memory Storage
    mem_intent = _extract_memory_intent(user_text)
    if mem_intent:
        store_hermes_memory(mem_intent["key"], mem_intent["value"], category=mem_intent["category"], evidence=user_text)
        return {
            "type": "memory_stored",
            "key": mem_intent["key"],
            "value": mem_intent["value"],
            "category": mem_intent["category"],
            "message": f"I've stored that in your Hermes persistent memory: **{mem_intent['key']}** = *{mem_intent['value']}*. This is retained permanently across sessions.",
        }

    # 3. Persistent Memory Recall Inquiry
    if re.search(r"\b(what (?:do you|have you) (?:remember|stored|saved)|show (?:my )?memories|persistent memory|what are my memories)\b", lower):
        mems = recall_hermes_memories()
        if not mems:
            msg = "Your Hermes persistent memory is currently empty. Tell me anything you'd like me to remember (e.g., 'Remember that I am using Hermes agent') and I will store it permanently."
        else:
            items_str = "\n".join([f"• **{m['key']}**: {m['value']}" for m in mems[:10]])
            msg = f"Here is what I have stored in your Hermes persistent memory ({len(mems)} entries):\n\n{items_str}"
        return {
            "type": "memory_recalled",
            "memories": mems,
            "message": msg,
        }

    # 4. Specific Date Schedule Query (e.g. "What do I have tomorrow?", "What events on Monday?")
    date_sched_match = re.search(
        r"\b(?:what (?:do i have|events?|tasks?|commitments?)(?:\s+(?:scheduled|due))?\s+(?:on\s+|for\s+)?(today|tomorrow|tonight|this week|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{4}-\d{2}-\d{2})|what is scheduled (?:for|on)?\s*(today|tomorrow|tonight|this week|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{4}-\d{2}-\d{2}))\b",
        lower,
        re.I,
    )
    if date_sched_match:
        token = (date_sched_match.group(1) or date_sched_match.group(2)).lower()
        sched_res = _query_schedule_for_date(token)
        return {
            "type": "schedule_query",
            "date": sched_res["date"],
            "count": sched_res["count"],
            "items": sched_res.get("items", []),
            "message": sched_res["message"],
        }

    # 5. Specific Event / Task inquiry (e.g. "When is my presentation due?", "Tell me about my project documentation")
    event_query_match = re.search(
        r"\b(?:when is (?:my |the )?(.+?)(?:\s+due|\s+scheduled|\?|$)|tell me about (?:my |the )?(.+?)(?:\?|$)|what about (?:my |the )?(.+?)(?:\?|$))",
        user_text,
        re.I,
    )
    if event_query_match:
        topic = (event_query_match.group(1) or event_query_match.group(2) or event_query_match.group(3)).strip(" .?!")
        if topic and topic.lower() not in {"my schedule", "open loops", "memories", "today", "tomorrow", "this week"}:
            ev_res = _query_event_or_task(topic)
            if ev_res and ev_res.get("found"):
                return {
                    "type": "event_found",
                    "topic": topic,
                    "items": ev_res.get("items", []),
                    "message": ev_res["message"],
                }

    # 6. Open Loops Inquiry (General list)
    if re.search(r"\b(show (?:my )?open loops|list (?:my )?tasks|what are my open loops|what tasks do i have|what's on my to-do|what is due)\b", lower):
        with connect() as db:
            loops = db.execute("SELECT id, title, kind, due_at, confidence FROM loops WHERE status='open' ORDER BY due_at IS NULL, due_at LIMIT 15").fetchall()
        if not loops:
            msg = "You have no open loops currently tracked. Tell me a task (e.g., 'Add my task to my open loop: finish project report by tomorrow') to track one!"
        else:
            loop_lines = []
            for r in loops:
                due_str = f" (Due: {r['due_at']})" if r["due_at"] else ""
                loop_lines.append(f"• [{r['kind'].upper()}] **{r['title']}**{due_str}")
            items_str = "\n".join(loop_lines)
            msg = f"You have {len(loops)} active open loop(s):\n\n{items_str}"
        return {
            "type": "loops_listed",
            "loops": [dict(r) for r in loops],
            "message": msg,
        }

    # 7. Scam triage
    if re.search(r"\b(is this a scam|suspicious message|check this text|check this email|scam check)\b", lower):
        scam_res = inspect_message(user_text)
        return {
            "type": "scam_triaged",
            "score": scam_res["score"],
            "band": scam_res["band"],
            "signals": [s["label"] for s in scam_res["signals"]],
            "advice": scam_res["advice"][:2],
            "message": f"Scam triage complete: Score {scam_res['score']}/100 ({scam_res['band'].upper()}). Found {len(scam_res['signals'])} urgency/pressure signals.",
        }

    # 8. Email / Reply Drafting & Sending with User Verification
    email_match = re.search(
        r"\b(?:send (?:an? )?(?:email|mail) to|write an? email to|email|draft (?:an? )?(?:reply|email|message)(?: to)?)\s+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+|[a-zA-Z]+)(?:\s+(?:about|regarding|saying|for|with)\s+(.+))?",
        user_text,
        re.I,
    )
    if email_match or re.search(r"\b(draft (?:a |an )?(?:reply|email|message|note)|prepare a reply)\b", lower):
        if email_match:
            recipient = email_match.group(1).strip(" .?!,")
            subject_hint = email_match.group(2).strip(" .?!") if email_match.group(2) else "Project Update"
        else:
            m = re.search(r"(?:draft (?:a |an )?(?:reply|email|message) (?:to|for|about)|prepare a reply)\s+(.+)", lower)
            recipient = "Jordan"
            subject_hint = m.group(1).strip(" .?!") if m else "Follow-up"

        if "@" not in recipient:
            return {"type": "email_needs_address", "message": "Please give me the recipient's full email address so I can prepare the message."}

        saying = re.search(r"\bsaying\s+(.+)$", subject_hint, re.I)
        requested_subject = re.search(r"\bsubject\s+(.+?)(?=\s+saying\b|$)", subject_hint, re.I)
        if saying:
            draft_body = saying.group(1).strip(" .?!")
            subject_hint = requested_subject.group(1).strip(" .?!") if requested_subject else "Message from Threadline"
        else:
            draft_body = f"Following up regarding {subject_hint}. Please review and let me know if you would like to proceed with the next steps."

        draft_content = draft_body
        action_id = "act_live_" + uuid4().hex[:8]
        t_now = now_iso()
        gmail_connected = _gmail_connected()
        # Keep the reviewed message as a pending Gmail send action even when
        # OAuth is not connected yet. The user can connect first, then approve
        # the exact saved recipient, subject, and body from the action queue.
        action_type = "send_email"

        # Check Conformal Risk Control & Preference Model
        feats = extract_features("draft_reply", {"content": draft_content}, life_area="work")
        pref_pred = predict_approval(feats)
        gate_eval = evaluate_conformal_gate("draft_reply", pref_pred["predicted_prob"])

        with connect() as db:
            db.execute(
                """INSERT INTO actions(id, action_type, title, payload, status, created_at, execution_mode, policy_level)
                   VALUES(?, ?, ?, ?, 'pending', ?, 'manual', 1)""",
                (
                    action_id,
                    action_type,
                    f"Send Email: Regarding {subject_hint} to {recipient}",
                    json.dumps({
                        "to": recipient,
                        "subject": subject_hint,
                        "draft": draft_content,
                        "action_type": "send_email",
                    }),
                    t_now,
                ),
            )

        return {
            "type": "draft_created",
            "action_id": action_id,
            "title": f"Send email to {recipient}",
            "to": recipient,
            "subject": subject_hint,
            "draft": draft_content,
            "status": "pending_verification",
            "gmail_connected": gmail_connected,
            "gmail_configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
            "action_type": action_type,
            "conformal_gate": gate_eval["status"],
            "can_auto_execute": gate_eval["auto_execute"],
            "message": f"I've prepared an email to **{recipient}**. Review the recipient, subject, and message; approving will send it from your connected Gmail account." if gmail_connected else f"I've prepared an email to **{recipient}**, but nothing has been sent. Connect Gmail, then approve this saved message to send it.",
        }

    # 4. Schedule / Horizon query
    if re.search(r"\b(what('?s| do i have) (?:due|on|scheduled|up next|tomorrow|today|this week)|schedule review|my workload|horizon)\b", lower):
        horizon = simulate_forward_horizon()
        loops = context.get("open_loops", [])
        return {
            "type": "schedule_briefing",
            "open_count": len(loops),
            "recommendation": horizon.get("morning_recommendation", "Workload is balanced."),
            "bottlenecks": horizon.get("bottlenecks", []),
            "message": f"You have {len(loops)} active commitments. {horizon.get('morning_recommendation', 'Everything is steady.')}"
        }

    # 5. GitHub MCP Connector Tool
    if "github" in lower or re.search(r"\b(pull request|repo issues|github issues|github pr)\b", lower):
        m = re.search(r"(?:search (?:github )?(?:for )?|issues (?:about|on|for) )(.+)", lower)
        query = m.group(1).strip(" .?!") if m else "bug"
        res = execute_universal_tool("github.search_issues", {"query": query, "repo": "workspace/core"})
        return {
            "type": "tool_executed",
            "tool_name": "github.search_issues",
            "connector": "GitHub MCP",
            "args": {"query": query},
            "output": res.get("result"),
            "message": f"Connected to GitHub MCP: Found {res.get('result', {}).get('total_count', 0)} matching issue(s) for '{query}'."
        }

    # 6. Google Workspace MCP Connector Tool
    if "google" in lower or re.search(r"\b(gsuite|google docs|google sheets|gdoc|gsheet|drive files)\b", lower):
        m = re.search(r"(?:search (?:docs|gsuite|drive) (?:for )?|find document )(.+)", lower)
        query = m.group(1).strip(" .?!") if m else "notes"
        res = execute_universal_tool("gsuite.search_docs", {"query": query})
        docs = res.get("result", {}).get("matched_documents", [])
        return {
            "type": "tool_executed",
            "tool_name": "gsuite.search_docs",
            "connector": "Google Workspace MCP",
            "args": {"query": query},
            "output": docs,
            "message": f"Connected to Google Workspace: Found {len(docs)} matching document(s) in Drive."
        }

    # 7. Slack Team Hub MCP Tool
    if "slack" in lower:
        m = re.search(r"(?:search slack (?:for )?|slack messages about )(.+)", lower)
        query = m.group(1).strip(" .?!") if m else "general"
        res = execute_universal_tool("slack.search_messages", {"query": query, "channel": "general"})
        msgs = res.get("result", {}).get("messages", [])
        return {
            "type": "tool_executed",
            "tool_name": "slack.search_messages",
            "connector": "Slack MCP",
            "args": {"query": query},
            "output": msgs,
            "message": f"Connected to Slack MCP: Found {len(msgs)} recent message(s) in #general matching '{query}'."
        }

    # 8. Local Filesystem MCP Tool
    if re.search(r"\b(read file|inspect file|list files|list directory|show files)\b", lower):
        if "list" in lower:
            res = execute_universal_tool("fs.list_directory", {"path": "./data"})
            files = res.get("result", {}).get("files", [])
            return {
                "type": "tool_executed",
                "tool_name": "fs.list_directory",
                "connector": "Filesystem MCP",
                "args": {"path": "./data"},
                "output": files,
                "message": f"Filesystem MCP: Listed {len(files)} file(s) in workspace data directory."
            }
        else:
            m = re.search(r"read file\s+([a-zA-Z0-9_./\-]+)", lower)
            fname = m.group(1).strip() if m else "README.md"
            res = execute_universal_tool("fs.read_file", {"path": fname})
            return {
                "type": "tool_executed",
                "tool_name": "fs.read_file",
                "connector": "Filesystem MCP",
                "args": {"path": fname},
                "output": res.get("result"),
                "message": f"Filesystem MCP: Read {res.get('result', {}).get('length', 0)} characters from '{fname}'."
            }

    # 9. Database Inspector MCP Tool
    if re.search(r"\b(query database|sql query|inspect schema|database table)\b", lower):
        res = execute_universal_tool("db.inspect_schema", {"table_name": "loops"})
        return {
            "type": "tool_executed",
            "tool_name": "db.inspect_schema",
            "connector": "Database MCP",
            "args": {"table": "loops"},
            "output": res.get("result"),
            "message": f"Database MCP: Inspected schema for table 'loops'. Columns: {', '.join(res.get('result', {}).get('columns', []))}."
        }

    # 10. Web Knowledge Search Connector
    if re.search(r"\b(search web for|web search|look up online|browse web)\b", lower):
        m = re.search(r"(?:search web for|web search|look up online|browse web)\s+(.+)", lower)
        q = m.group(1).strip(" .?!") if m else "technology"
        res = execute_universal_tool("web.search", {"query": q})
        return {
            "type": "tool_executed",
            "tool_name": "web.search",
            "connector": "Web Search Connector",
            "args": {"query": q},
            "output": res.get("result", {}).get("snippets", []),
            "message": f"Web Knowledge Connector: Retrieved top search citations for '{q}'."
        }

    # 11. Screen Perception / Active Window Tool
    if re.search(r"\b(what('?s| is) (?:on my screen|open)|active window|foreground app|what am i doing)\b", lower):
        win = get_native_foreground_window()
        return {
            "type": "screen_perceived",
            "tool_name": "os.inspect_foreground_window",
            "connector": "Win32 Introspection",
            "window": win,
            "message": f"Active foreground desktop window: '{win.get('window_title')}' ({win.get('process_name', 'native')}, PID {win.get('pid', 'system')})."
        }

    # 12. Synthesize New Tool on Demand
    if re.search(r"\b(synthesize (?:a )?tool|create (?:a )?tool called|program a tool)\b", lower):
        m = re.search(r"(?:synthesize (?:a )?tool|create (?:a )?tool called|program a tool)\s+([a-z0-9_.]+)", lower)
        tname = m.group(1).strip() if m else "custom.util_" + uuid4().hex[:6]
        res = synthesize_tool(SynthesizeToolRequest(
            name=tname,
            description=f"Synthesized on demand from prompt: {user_text}",
            operation_type="computation"
        ))
        return {
            "type": "tool_synthesized",
            "tool_name": res["name"],
            "connector": "Self-Extension Studio",
            "output": res["manifest"],
            "message": f"Synthesized and sandbox-verified new tool '{res['name']}'. Dynamically injected into active TOOL_MANIFESTS."
        }

    # 13. Computer-Use Agent (Device Control: Filesystem, WhatsApp/Messaging, Turn-based Games)
    if re.search(r"\b(create (?:a )?(?:[a-z0-9_-]+ )*(?:folder|directory|workspace|project)|make a folder|open whatsapp|chat with|send (?:a )?whatsapp|play (?:a )?(?:[a-z0-9_-]+ )*(?:game|chess|match|turn)|play with my friend|turn-based)\b", lower):
        category = "general"
        if any(w in lower for w in ["folder", "directory", "workspace", "project"]):
            category = "filesystem"
        elif any(w in lower for w in ["whatsapp", "chat", "message"]):
            category = "messaging"
        elif any(w in lower for w in ["play", "game", "chess", "match", "turn-based"]):
            category = "game"

        res = execute_device_goal_engine(user_text, task_category=category, autonomy_level=1)
        return {
            "type": "device_agent_executed",
            "tool_name": f"device.{category}",
            "connector": "Computer-Use Substrate",
            "rung_used": res.get("rung_used"),
            "verified": res.get("verified"),
            "output": res,
            "message": res.get("message") or f"Executed computer-use task via {res.get('rung_used')} with full verification."
        }

    return None


def _gmail_connected():
    with connect() as db:
        return bool(db.execute("SELECT 1 FROM gmail_accounts LIMIT 1").fetchone())


def _call_nemotron_conversational(user_message: str, history: list[ChatMessage], context: dict[str, Any]) -> str | None:
    """Call Nemotron Token Factory with full workspace context and conversational instructions."""
    if not API_KEY:
        return None

    # Compact context representation
    loops_str = "\n".join([f"- {l['title']} (Due: {l.get('due_at') or 'No date'})" for l in context["open_loops"][:8]]) or "No current open commitments."
    mems_str = "\n".join([f"- {m['key']}: {m['value']}" for m in context.get("hermes_memories", [])[:10]]) or "No stored memories yet."
    available_tools = get_all_available_tools()
    tools_summary = ", ".join([f"{t['name']} ({t.get('connector_name', 'native')})" for t in available_tools[:12]])

    system_prompt = (
        f"You are Threadline Sovereign Delegate, a personal autonomous AI operating directly on the user's device adhering to the Hermes Agent specification. "
        f"Today is {context['day_of_week']}, {context['today']}. "
        f"User Context:\n"
        f"- Active Commitments & Open Loops:\n{loops_str}\n"
        f"- Persistent Hermes Memories:\n{mems_str}\n"
        f"- Workload Status: {context['horizon_summary']}\n"
        f"- Pending Action Approvals: {context['pending_actions']}\n"
        f"- Connected Tools & MCP Servers ({len(available_tools)} total): {tools_summary}\n\n"
        f"Guidelines:\n"
        f"1. Be concise, warm, helpful, and natural (like Gemini Live or ChatGPT voice).\n"
        f"2. Answer user questions directly. You have access to GitHub, Google Workspace, Slack, Filesystem, Database, and Web Search MCP connectors.\n"
        f"3. Offer actionable next steps. Keep spoken responses fluid and easy to listen to.\n"
        f"4. If the user shares information or promises, acknowledge and confirm that you have tracked it into persistent memory."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-6:]:  # Keep recent conversational context
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    request_body = {
        "model": NANO_MODEL,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 800,
        "chat_template_kwargs": {"enable_thinking": False},
    }

    try:
        body_bytes = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{TOKEN_FACTORY_BASE_URL}/chat/completions",
            data=body_bytes,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        # Fallback to local intelligence
        return None


@router.post("/chat")
def live_chat_interaction(body: LiveChatRequest):
    """Universal Conversational & Voice Interaction Endpoint.
    Acts as the single point of entry, dispatching across all 5 Sovereign pillars and persisting conversation."""
    t_now = now_iso()

    # 1. Persist user message to SQLite chat history
    with connect() as db:
        db.execute(
            "INSERT INTO hermes_chat_history(id, role, content, model, action_executed, created_at) VALUES(?, 'user', ?, NULL, NULL, ?)",
            (str(uuid4()), body.message, t_now),
        )

    context = get_user_context_snapshot()
    action_result = _execute_agentic_action(body.message, context)

    # If action was taken directly
    if action_result:
        reply_text = action_result["message"]
        if action_result.get("type") == "draft_created":
            reply_text += f"\n\n```text\n{action_result['draft']}\n```"

        voice_text = re.sub(r"```[\s\S]*?```", "", reply_text).strip()
        model_used = "Hermes Agent & Sovereign Substrate"

        # Persist assistant response
        with connect() as db:
            db.execute(
                "INSERT INTO hermes_chat_history(id, role, content, model, action_executed, created_at) VALUES(?, 'assistant', ?, ?, ?, ?)",
                (str(uuid4()), reply_text, model_used, json.dumps(action_result), now_iso()),
            )

        return {
            "reply": reply_text,
            "voice_summary": voice_text,
            "action_executed": action_result,
            "model_used": model_used,
            "suggestions": ["Show my open loops", "What do you remember about me?", "Review pending approvals", "Capture active window"]
        }

    # Try Nemotron cloud model via Token Factory
    nemotron_reply = _call_nemotron_conversational(body.message, body.history, context)
    if nemotron_reply:
        voice_summary = nemotron_reply[:250].split("\n")[0].strip()
        model_used = "NVIDIA Nemotron 3.5 Lightning"

        with connect() as db:
            db.execute(
                "INSERT INTO hermes_chat_history(id, role, content, model, action_executed, created_at) VALUES(?, 'assistant', ?, ?, NULL, ?)",
                (str(uuid4()), nemotron_reply, model_used, now_iso()),
            )

        return {
            "reply": nemotron_reply,
            "voice_summary": voice_summary,
            "action_executed": None,
            "model_used": model_used,
            "suggestions": ["Tell me about my schedule", "Show my open loops", "Draft a quick follow-up", "Start ambient capture"]
        }

    # Intelligent local fallback response
    lower = body.message.lower()
    if any(greet in lower for greet in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        reply = (
            f"Hello! I'm your Sovereign Delegate powered by the Hermes Agent architecture. You have {len(context['open_loops'])} open loop(s) tracked, "
            f"and {len(context.get('hermes_memories', []))} persistent memories. What task or commitment would you like to capture?"
        )
    elif "status" in lower or "who are you" in lower or "what can you do" in lower:
        reply = (
            "I'm your Sovereign Delegate OS assistant powered by the Hermes Agent standard. I maintain persistent memory across sessions, "
            "track tasks in your Open Loops substrate, synthesize custom tools, and execute actions with mathematical risk bounds."
        )
    else:
        reply = (
            f"Understood. I've noted that in your sovereign context. You have {len(context['open_loops'])} open loop(s) "
            f"and {context['pending_actions']} pending action(s). Would you like to review your open loops or add another task?"
        )

    model_used = "Hermes Agent Local Intelligence"
    with connect() as db:
        db.execute(
            "INSERT INTO hermes_chat_history(id, role, content, model, action_executed, created_at) VALUES(?, 'assistant', ?, ?, NULL, ?)",
            (str(uuid4()), reply, model_used, now_iso()),
        )

    return {
        "reply": reply,
        "voice_summary": reply,
        "action_executed": None,
        "model_used": model_used,
        "suggestions": ["Show my open commitments", "What do you remember about me?", "Draft follow-up email", "Check for bottlenecks"]
    }


@router.get("/history")
def get_live_history(limit: int = 50):
    """Retrieve persistent conversational history for the live assistant."""
    with connect() as db:
        rows = db.execute(
            "SELECT id, role, content, model, action_executed, created_at FROM hermes_chat_history ORDER BY created_at ASC LIMIT ?",
            (limit,)
        ).fetchall()
    return [{
        "id": r["id"],
        "role": r["role"],
        "content": r["content"],
        "model": r["model"] or "Hermes Agent",
        "action_executed": json_value(r["action_executed"], None),
        "created_at": r["created_at"]
    } for r in rows]


@router.delete("/history")
def clear_live_history():
    """Clear chat history while preserving underlying open loops and memories."""
    with connect() as db:
        db.execute("DELETE FROM hermes_chat_history")
    return {"cleared": True}


@router.get("/memories")
def list_live_memories():
    """Retrieve all persistent memories stored by Hermes Agent."""
    return recall_hermes_memories()


@router.delete("/memories/{memory_id}")
def delete_live_memory(memory_id: str):
    """Delete a persistent memory entry."""
    with connect() as db:
        db.execute("DELETE FROM hermes_memories WHERE id=?", (memory_id,))
    return {"deleted": True, "id": memory_id}
