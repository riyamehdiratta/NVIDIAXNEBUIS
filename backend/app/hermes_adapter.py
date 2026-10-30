"""Hermes Agent Tool Calling Standard Adapter.

Provides structured XML/JSON function calling serialization and parsing adhering to
the Hermes Agent specification (<thought>, <tool_call>, <tool_response>), bridging
NVIDIA Nemotron 3.5 Lightning with Threadline's 25+ MCP connectors and device primitives.
"""

import json
import re
from typing import Any

from .mcp_connectors import get_all_available_tools, execute_universal_tool
from .device_agent import DEVICE_PRIMITIVES, execute_device_goal_engine


HERMES_SYSTEM_PROMPT = """You are Threadline Sovereign Delegate, a local autonomous personal AI operating system.
You have access to the following tools:

<tools>
{tools_json}
</tools>

To call a tool, respond using the following XML format:
<thought>
Reason about what to do next based on user intent and available tools.
</thought>
<tool_call>
{{"name": "tool_name", "arguments": {{"arg_name": "arg_value"}}}}
</tool_call>

Always verify postconditions before confirming completion to the user."""


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

