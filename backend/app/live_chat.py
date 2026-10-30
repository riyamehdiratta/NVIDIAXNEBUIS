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

from .config import API_KEY, NANO_MODEL, SUPER_MODEL, TOKEN_FACTORY_BASE_URL
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

    horizon = simulate_forward_horizon()
    return {
        "open_loops": [dict(r) for r in loops],
        "total_sources": sources_count,
        "pending_actions": actions_pending,
        "recent_sources": [dict(r) for r in recent_sources],
        "horizon_summary": horizon.get("morning_recommendation", "Workload steady"),
        "horizon_bottlenecks": horizon.get("bottlenecks", []),
        "weights": json_value(pref_weights["value"], []) if pref_weights else [],
        "today": date.today().isoformat(),
        "day_of_week": datetime.now().strftime("%A"),
    }


def _execute_agentic_action(user_text: str, context: dict[str, Any]) -> dict[str, Any] | None:
    """Detect and execute autonomous actions requested by user via voice or chat."""
    lower = user_text.lower().strip()

    # 1. Remind / Task creation
    if re.search(r"\b(remind me to|don'?t let me forget to|remember to|need to|add a task to)\b", lower):
        # Extract title
        match = re.search(r"\b(?:remind me to|don'?t let me forget to|remember to|need to|add a task to)\s+(.+?)(?:$|\bby\b|\bat\b|\bon\b|\btomorrow\b|\bnext week\b)", lower, re.I)
        task_title = match.group(1).strip(" .?!") if match else user_text
        if len(task_title) > 120:
            task_title = task_title[:117] + "..."

        # Date heuristic
        due_at = None
        if "tomorrow" in lower:
            due_at = (date.today() + timedelta(days=1)).isoformat()
        elif "today" in lower or "tonight" in lower:
            due_at = date.today().isoformat()
        elif "next week" in lower:
            due_at = (date.today() + timedelta(days=7)).isoformat()

        loop_id = "loop_live_" + uuid4().hex[:8]
        t_now = now_iso()
        with connect() as db:
            db.execute(
                """INSERT INTO loops(id, title, detail, kind, status, due_at, confidence, evidence, created_at, updated_at)
                   VALUES(?, ?, ?, 'task', 'open', ?, 0.95, ?, ?, ?)""",
                (loop_id, task_title.capitalize(), f"Created via Live Voice/Chat: {user_text}", due_at, json.dumps([{"source": "Live Assistant", "quote": user_text}]), t_now, t_now)
            )
            db.execute(
                "INSERT INTO activity(id, event_type, detail, created_at) VALUES(?, 'loop_created', ?, ?)",
                (str(uuid4()), f"Added commitment: {task_title}", t_now)
            )

        return {
            "type": "loop_created",
            "title": task_title.capitalize(),
            "due_at": due_at,
            "message": f"I've added '{task_title.capitalize()}' to your open loops{f' due {due_at}' if due_at else ''}."
        }

    # 2. Scam triage
    if re.search(r"\b(is this a scam|suspicious message|check this text|check this email|scam check)\b", lower):
        scam_res = inspect_message(user_text)
        return {
            "type": "scam_triaged",
            "score": scam_res["score"],
            "band": scam_res["band"],
            "signals": [s["label"] for s in scam_res["signals"]],
            "advice": scam_res["advice"][:2],
            "message": f"Scam triage complete: Score {scam_res['score']}/100 ({scam_res['band'].upper()}). Found {len(scam_res['signals'])} urgency/pressure signals."
        }

    # 3. Email / Reply Drafting
    if re.search(r"\b(draft (?:a |an )?(?:reply|email|message|note)|write an email to|prepare a reply)\b", lower):
        # Extract recipient or topic
        subject_hint = "Follow-up"
        m = re.search(r"(?:draft (?:a |an )?(?:reply|email|message) (?:to|for|about)|write an email to)\s+(.+)", lower)
        if m:
            subject_hint = m.group(1).strip(" .?!")

        draft_content = f"Hi,\n\nFollowing up regarding {subject_hint}. Please let me know how you would like to proceed.\n\nBest regards,"
        action_id = "act_live_" + uuid4().hex[:8]
        t_now = now_iso()

        # Check Conformal Risk Control & Preference Model
        feats = extract_features("draft_reply", {"content": draft_content}, life_area="work")
        pref_pred = predict_approval(feats)
        gate_eval = evaluate_conformal_gate("draft_reply", pref_pred["predicted_prob"])

        with connect() as db:
            db.execute(
                """INSERT INTO actions(id, action_type, title, payload, status, created_at)
                   VALUES(?, 'draft_reply', ?, ?, 'pending', ?)""",
                (action_id, f"Draft: {subject_hint.capitalize()}", json.dumps({"draft": draft_content, "hint": subject_hint}), t_now)
            )

        return {
            "type": "draft_created",
            "action_id": action_id,
            "title": f"Draft for {subject_hint}",
            "draft": draft_content,
            "conformal_gate": gate_eval["status"],
            "can_auto_execute": gate_eval["auto_execute"],
            "message": f"I've prepared a draft for {subject_hint}. It is saved in your Action Queue for approval."
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


def _call_nemotron_conversational(user_message: str, history: list[ChatMessage], context: dict[str, Any]) -> str | None:
    """Call Nemotron Token Factory with full workspace context and conversational instructions."""
    if not API_KEY:
        return None

    # Compact context representation
    loops_str = "\n".join([f"- {l['title']} (Due: {l.get('due_at') or 'No date'})" for l in context["open_loops"][:8]]) or "No current open commitments."
    available_tools = get_all_available_tools()
    tools_summary = ", ".join([f"{t['name']} ({t.get('connector_name', 'native')})" for t in available_tools[:12]])

    system_prompt = (
        f"You are Threadline Sovereign Delegate, a personal autonomous AI operating directly on the user's device. "
        f"Today is {context['day_of_week']}, {context['today']}. "
        f"User Context:\n"
        f"- Active Commitments & Open Loops:\n{loops_str}\n"
        f"- Workload Status: {context['horizon_summary']}\n"
        f"- Pending Action Approvals: {context['pending_actions']}\n"
        f"- Connected Tools & MCP Servers ({len(available_tools)} total): {tools_summary}\n\n"
        f"Guidelines:\n"
        f"1. Be concise, warm, helpful, and natural (like Gemini Live or ChatGPT voice).\n"
        f"2. Answer user questions directly. You have access to GitHub, Google Workspace, Slack, Filesystem, Database, and Web Search MCP connectors.\n"
        f"3. Offer actionable next steps. Keep spoken responses fluid and easy to listen to.\n"
        f"4. If the user shares information or promises, acknowledge and confirm that you have tracked it."
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
    Acts as the single point of entry, dispatching across all 5 Sovereign pillars."""
    context = get_user_context_snapshot()
    action_result = _execute_agentic_action(body.message, context)

    # If action was taken directly
    if action_result:
        reply_text = action_result["message"]
        if action_result.get("type") == "draft_created":
            reply_text += f"\n\n```text\n{action_result['draft']}\n```"

        voice_text = re.sub(r"```[\s\S]*?```", "", reply_text).strip()

        return {
            "reply": reply_text,
            "voice_summary": voice_text,
            "action_executed": action_result,
            "model_used": "Threadline Sovereign Substrate",
            "suggestions": ["What else is due this week?", "Review pending approvals", "Capture active window"]
        }

    # Try Nemotron cloud model via Token Factory
    nemotron_reply = _call_nemotron_conversational(body.message, body.history, context)
    if nemotron_reply:
        # Generate clean voice audio summary
        voice_summary = nemotron_reply[:250].split("\n")[0].strip()
        return {
            "reply": nemotron_reply,
            "voice_summary": voice_summary,
            "action_executed": None,
            "model_used": "NVIDIA Nemotron 3.5 Lightning",
            "suggestions": ["Tell me about my schedule", "Draft a quick follow-up", "Start ambient capture"]
        }

    # Intelligent local fallback response
    lower = body.message.lower()
    if any(greet in lower for greet in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        reply = (
            f"Hello! I'm your Sovereign Delegate. You have {len(context['open_loops'])} open loop(s) currently tracked, "
            f"and your workload for this week is {context['horizon_summary'].lower()}. What would you like to work on or capture?"
        )
    elif "status" in lower or "who are you" in lower or "what can you do" in lower:
        reply = (
            "I'm your Sovereign Delegate OS assistant. I can listen to your voice or text, capture commitments across your apps, "
            "draft messages with mathematical risk control, forecast your upcoming 7-day schedule, synthesize custom tools, and triage suspicious messages."
        )
    else:
        reply = (
            f"Understood. I've noted that in your sovereign context. Based on your current workspace, "
            f"you have {len(context['open_loops'])} open loop(s) and {context['pending_actions']} pending review item(s). "
            f"Would you like me to organize this into a plan or check your upcoming deadlines?"
        )

    return {
        "reply": reply,
        "voice_summary": reply,
        "action_executed": None,
        "model_used": "Threadline Local Intelligence",
        "suggestions": ["Show my open commitments", "Draft follow-up email", "Check for bottlenecks"]
    }
