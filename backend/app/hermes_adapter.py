"""Hermes Agent Tool Calling & Persistent Memory Standard Adapter.

Provides structured XML/JSON function calling serialization and parsing adhering to
the Hermes Agent specification (<thought>, <tool_call>, <tool_response>), bridging
NVIDIA Nemotron 3.5 Lightning and local intelligence with Threadline's persistent memory,
Open Loops substrate, and 25+ MCP connectors.
"""

import json
import re
from typing import Any
from uuid import uuid4

from .db import connect, now_iso
from .mcp_connectors import get_all_available_tools, execute_universal_tool
from .device_agent import DEVICE_PRIMITIVES, execute_device_goal_engine


HERMES_SYSTEM_PROMPT = """You are Threadline Sovereign Delegate, a private local autonomous personal AI operating system adhering to the Hermes Agent specification.
You possess durable persistent memory across sessions and direct access to the user's Open Loops substrate.

Persistent Memory & Open Loops Capabilities:
1. When the user specifies any task, commitment, promise, or waiting item, record it into their Open Loops using `memory.add_open_loop`.
2. When the user provides personal preferences, facts, or instructions (e.g. tools used, favorite settings, names, roles), retain them in long-term memory via `memory.store_memory`.
3. To recall past commitments, facts, or context, use `memory.recall_memories`.

You have access to the following tools:

<tools>
{tools_json}
</tools>

To call a tool, respond using the following XML format:
<thought>
Reason about what to do next based on user intent, persistent memory, and available tools.
</thought>
<tool_call>
{{"name": "tool_name", "arguments": {{"arg_name": "arg_value"}}}}
</tool_call>

Always confirm task persistence and verify postconditions before finalizing your response."""


def store_hermes_memory(key: str, value: str, category: str = "fact", evidence: str = "") -> dict[str, Any]:
    """Persist long-term user memory, fact, or preference in SQLite."""
    mem_id = "mem_" + uuid4().hex[:10]
    t_now = now_iso()
    with connect() as db:
        db.execute(
            """INSERT INTO hermes_memories(id, category, key, value, confidence, evidence, created_at, updated_at)
               VALUES(?, ?, ?, ?, 1.0, ?, ?, ?)""",
            (mem_id, category, key, value, evidence, t_now, t_now)
        )
        db.execute(
            """INSERT INTO world_model_triples(id, subject, predicate, object, confidence, evidence, created_at, updated_at)
               VALUES(?, 'user', ?, ?, 1.0, ?, ?, ?)""",
            ("trip_" + uuid4().hex[:10], key, value, evidence, t_now, t_now)
        )
    return {"id": mem_id, "key": key, "value": value, "category": category, "stored": True}


def recall_hermes_memories(query: str = "") -> list[dict[str, Any]]:
    """Retrieve persistent memories from Hermes long-term store."""
    with connect() as db:
        if query:
            rows = db.execute(
                "SELECT * FROM hermes_memories WHERE lower(key) LIKE ? OR lower(value) LIKE ? ORDER BY updated_at DESC LIMIT 25",
                (f"%{query.lower()}%", f"%{query.lower()}%")
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM hermes_memories ORDER BY updated_at DESC LIMIT 25").fetchall()
    return [dict(r) for r in rows]


def add_open_loop_from_hermes(title: str, detail: str = "", due_at: str | None = None, kind: str = "task", evidence: str = "") -> dict[str, Any]:
    """Durable commitment entry into the loops database table."""
    loop_id = "loop_live_" + uuid4().hex[:8]
    t_now = now_iso()
    clean_title = title.strip().capitalize()
    evidence_json = json.dumps([{"source": "Hermes Agent", "quote": evidence or title}])
    with connect() as db:
        db.execute(
            """INSERT INTO loops(id, title, detail, kind, status, due_at, confidence, evidence, created_at, updated_at)
               VALUES(?, ?, ?, ?, 'open', ?, 0.98, ?, ?, ?)""",
            (loop_id, clean_title, detail or f"Created via Hermes Agent: {title}", kind, due_at, evidence_json, t_now, t_now)
        )
        db.execute(
            "INSERT INTO activity(id, event_type, detail, created_at) VALUES(?, 'loop_created', ?, ?)",
            (str(uuid4()), f"Added commitment: {clean_title}", t_now)
        )
        db.execute(
            """INSERT INTO world_model_triples(id, subject, predicate, object, confidence, evidence, created_at, updated_at)
               VALUES(?, 'user', 'committed_to', ?, 0.98, ?, ?, ?)""",
            ("trip_" + uuid4().hex[:10], clean_title, evidence_json, t_now, t_now)
        )
        db.execute(
            """INSERT INTO hermes_memories(id, category, key, value, confidence, evidence, created_at, updated_at)
               VALUES(?, 'task', ?, ?, 1.0, ?, ?, ?)""",
            ("mem_" + uuid4().hex[:10], f"task:{loop_id}", clean_title, evidence_json, t_now, t_now)
        )
    return {
        "loop_id": loop_id,
        "title": clean_title,
        "due_at": due_at,
        "kind": kind,
        "status": "open",
        "message": f"I've added '{clean_title}' to your open loops{f' due {due_at}' if due_at else ''}."
    }


def get_hermes_memory_context() -> str:
    """Format active open loops and persistent memories into context for Hermes agent."""
    with connect() as db:
        loops = db.execute("SELECT id, title, kind, due_at FROM loops WHERE status='open' ORDER BY due_at IS NULL, due_at LIMIT 10").fetchall()
        memories = db.execute("SELECT category, key, value FROM hermes_memories ORDER BY updated_at DESC LIMIT 15").fetchall()

    lines = ["### Active Open Loops:"]
    if loops:
        for l in loops:
            due_str = f" (Due: {l['due_at']})" if l['due_at'] else ""
            lines.append(f"- [{l['kind'].upper()}] {l['title']}{due_str}")
    else:
        lines.append("- (No active open loops)")

    lines.append("\n### Persistent User Memories & Facts:")
    if memories:
        for m in memories:
            lines.append(f"- [{m['category']}] {m['key']}: {m['value']}")
    else:
        lines.append("- (No user memories stored yet)")

    return "\n".join(lines)


def build_hermes_tools_manifest() -> str:
    """Build unified tools manifest formatted for Hermes tool schemas."""
    manifests = []
    
    # 1. MCP & Built-in tools
    for tool in get_all_available_tools():
        manifests.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": tool.get("args", {}),
                }
            }
        })
        
    # 2. Device primitives
    for dname, dinfo in DEVICE_PRIMITIVES.items():
        manifests.append({
            "type": "function",
            "function": {
                "name": dname,
                "description": f"[{dinfo['rung']}] {dinfo['description']}",
                "parameters": {
                    "type": "object",
                    "properties": dinfo.get("args", {}),
                }
            }
        })
        
    return json.dumps(manifests, indent=2)


def parse_hermes_response(model_output: str) -> dict[str, Any]:
    """Extract <thought> and <tool_call> from a Hermes-formatted agent response."""
    thought_match = re.search(r"<thought>(.*?)</thought>", model_output, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else ""

    tool_call_match = re.search(r"<tool_call>(.*?)</tool_call>", model_output, re.DOTALL)
    tool_call = None
    if tool_call_match:
        raw_call = tool_call_match.group(1).strip()
        try:
            tool_call = json.loads(raw_call)
        except json.JSONDecodeError:
            # Fallback regex extraction
            name_m = re.search(r'"name":\s*"([^"]+)"', raw_call)
            tool_call = {"name": name_m.group(1) if name_m else "unknown", "arguments": {}}

    # Clean text response (removing XML tags)
    clean_text = re.sub(r"<thought>.*?</thought>", "", model_output, flags=re.DOTALL)
    clean_text = re.sub(r"<tool_call>.*?</tool_call>", "", clean_text, flags=re.DOTALL).strip()

    return {
        "thought": thought,
        "tool_call": tool_call,
        "clean_text": clean_text or "Processed agent step."
    }


def format_hermes_tool_response(tool_name: str, result: Any) -> str:
    """Format tool execution output into a Hermes <tool_response> payload."""
    return f"<tool_response>\n{{\"name\": \"{tool_name}\", \"content\": {json.dumps(result)}}}\n</tool_response>"


def execute_hermes_tool_call(tool_call: dict[str, Any]) -> dict[str, Any]:
    """Execute a parsed Hermes tool call across device primitives or universal MCP tools."""
    name = tool_call.get("name", "")
    args = tool_call.get("arguments", {})

    if name.startswith("device."):
        # Route to computer-use device engine
        return execute_device_goal_engine(
            goal=f"Execute {name}",
            task_category="auto",
            params=args,
            autonomy_level=1
        )
    else:
        # Route to universal MCP connector engine
        return execute_universal_tool(tool_name=name, args=args, caller="hermes_agent")

