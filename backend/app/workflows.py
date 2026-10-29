"""Threadline's first deterministic, checkpointed workflow runtime.

The executor intentionally supports only registered local tools. Specs may describe
tool, approval, and verify nodes; model/code/web execution is rejected until those
capabilities have independent privacy and sandbox gates.
"""

import json
import re
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .db import connect, json_value, now_iso

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


class InputSpec(BaseModel):
    type: Literal["string", "string_list", "integer"]
    required: bool = True
    max_length: int = Field(default=500, ge=1, le=10000)


class WorkflowBudgets(BaseModel):
    tokens: int = Field(default=0, ge=0, le=100000)
    wall_seconds: int = Field(default=30, ge=1, le=300)
    egress_kb: int = Field(default=0, ge=0, le=1024)
    spend: float = Field(default=0, ge=0, le=10)


class WorkflowNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    type: Literal["tool", "approval", "verify"]
    tool: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    risk: Literal["low", "medium", "high"] = "low"
    input_taint: Literal["trusted", "untrusted", "derived"] = "trusted"


class WorkflowSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,63}$")
    version: int = Field(ge=1)
    origin: Literal["user_request", "skill", "schedule", "event", "repair"] = "user_request"
    trigger: Literal["on_demand"] = "on_demand"
    inputs: dict[str, InputSpec] = Field(default_factory=dict)
    budgets: WorkflowBudgets = Field(default_factory=WorkflowBudgets)
    nodes: list[WorkflowNode] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def unique_nodes(self):
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("Workflow node IDs must be unique")
        return self


TOOL_MANIFESTS: dict[str, dict[str, Any]] = {
    "source.list": {"side_effects": "read", "risk": "low", "inverse": None, "needs_scope": "memory.read", "data_egress": "none", "taint_out": "untrusted", "args": {}},
    "source.get": {"side_effects": "read", "risk": "low", "inverse": None, "needs_scope": "memory.read", "data_egress": "none", "taint_out": "untrusted", "args": {"source_id": "string"}},
    "memory.open_loops": {"side_effects": "read", "risk": "low", "inverse": None, "needs_scope": "memory.read", "data_egress": "none", "taint_out": "derived", "args": {}},
    "skill.scan_local": {"side_effects": "local_write", "risk": "low", "inverse": "remove_derived_loops", "needs_scope": "memory.write", "data_egress": "none", "taint_out": "derived", "args": {"skill_id": "string"}},
    "draft.follow_up": {"side_effects": "local_write", "risk": "low", "inverse": "delete_local_draft", "needs_scope": "draft.write", "data_egress": "none", "taint_out": "derived", "args": {"source_id": "string"}},
    "report.daily_reset": {"side_effects": "read", "risk": "low", "inverse": None, "needs_scope": "memory.read", "data_egress": "none", "taint_out": "derived", "args": {}},
}


def validate_spec(spec: WorkflowSpec, input_values: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    nodes = {node.id: node for node in spec.nodes}
    if spec.budgets.egress_kb != 0:
        errors.append("Remote model egress is disabled in this workflow runtime")
    if spec.budgets.tokens != 0 or spec.budgets.spend != 0:
        errors.append("Model token and spend budgets must be zero until a confirmed model node is implemented")
    for name, definition in spec.inputs.items():
        if input_values is not None:
            value = input_values.get(name)
            if definition.required and value is None:
                errors.append(f"Missing required input: {name}")
            if value is not None:
                valid = ((definition.type == "string" and isinstance(value, str)) or
                         (definition.type == "string_list" and isinstance(value, list) and all(isinstance(v, str) for v in value)) or
                         (definition.type == "integer" and isinstance(value, int) and not isinstance(value, bool)))
                if not valid:
                    errors.append(f"Input {name} must have type {definition.type}")
                if isinstance(value, str) and len(value) > definition.max_length:
                    errors.append(f"Input {name} exceeds max_length")
    if input_values is not None:
        extra = set(input_values) - set(spec.inputs)
        if extra:
            errors.append(f"Unknown inputs: {', '.join(sorted(extra))}")

    for node in spec.nodes:
        if node.type == "tool":
            if not node.tool or node.tool not in TOOL_MANIFESTS:
                errors.append(f"Node {node.id} uses an unregistered tool")
                continue
            manifest = TOOL_MANIFESTS[node.tool]
            unknown = set(node.args) - set(manifest["args"])
            missing = set(manifest["args"]) - set(node.args)
            if unknown:
                errors.append(f"Node {node.id} has unsupported arguments: {', '.join(sorted(unknown))}")
            if missing:
                errors.append(f"Node {node.id} is missing arguments: {', '.join(sorted(missing))}")
            if node.risk != manifest["risk"]:
                errors.append(f"Node {node.id} risk must match tool manifest ({manifest['risk']})")
            for key, value in node.args.items():
                expected = manifest["args"].get(key)
                if expected and not (isinstance(value, str) and value.startswith("$")) and not isinstance(value, str):
                    errors.append(f"Node {node.id} argument {key} must be a string reference/value")
                if isinstance(value, str) and value.startswith("$"):
                    parts = value[1:].split(".")
                    if parts[0] == "inputs":
                        ref = parts[1] if len(parts) > 1 else ""
                        known = ref in spec.inputs
                    else:
                        ref = parts[0]
                        known = ref in nodes
                        if known and ref not in node.depends_on:
                            errors.append(f"Node {node.id} must depend on referenced node {ref}")
                    if not known:
                        errors.append(f"Node {node.id} references unknown value {value}")
        elif node.tool is not None:
            errors.append(f"Node {node.id} may only set tool for type=tool")
        for dependency in node.depends_on:
            if dependency not in nodes:
                errors.append(f"Node {node.id} depends on unknown node {dependency}")
        if node.input_taint == "untrusted" and node.type == "tool" and node.risk != "low":
            errors.append(f"Untrusted input cannot flow into privileged tool node {node.id}")

    # Kahn's algorithm rejects cycles and produces useful validation feedback.
    indegree = {node_id: 0 for node_id in nodes}
    children = {node_id: [] for node_id in nodes}
    for node in spec.nodes:
        for dep in node.depends_on:
            if dep in nodes:
                indegree[node.id] += 1
                children[dep].append(node.id)
    ready = [node_id for node_id, degree in indegree.items() if degree == 0]
    visited = 0
    while ready:
        node_id = ready.pop()
        visited += 1
        for child in children[node_id]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if visited != len(nodes):
        errors.append("Workflow contains a dependency cycle")
    return errors


def _template_specs() -> dict[str, WorkflowSpec]:
    return {
        "commitment-scan": WorkflowSpec(id="commitment-scan", version=1, origin="skill", inputs={}, nodes=[
            WorkflowNode(id="scan", type="tool", tool="skill.scan_local", args={"skill_id": "commitment-scan"})]),
        "daily-reset": WorkflowSpec(id="daily-reset", version=1, origin="skill", nodes=[
            WorkflowNode(id="read", type="tool", tool="memory.open_loops"),
            WorkflowNode(id="plan", type="tool", tool="report.daily_reset", depends_on=["read"])]),
        "follow-up-draft": WorkflowSpec(id="follow-up-draft", version=1, origin="skill",
            inputs={"source_id": InputSpec(type="string", max_length=80)}, nodes=[
                WorkflowNode(id="read", type="tool", tool="source.get", args={"source_id": "$inputs.source_id"}, input_taint="untrusted"),
                WorkflowNode(id="draft", type="tool", tool="draft.follow_up", args={"source_id": "$inputs.source_id"}, depends_on=["read"], input_taint="derived")]),
    }


def _ordered_nodes(spec: WorkflowSpec) -> list[WorkflowNode]:
    pending = {node.id: node for node in spec.nodes}
    done: set[str] = set()
    ordered = []
    while pending:
        ready = [node for node in pending.values() if set(node.depends_on) <= done]
        if not ready:
            raise ValueError("Workflow has a cycle or unknown dependency")
        for node in ready:
            ordered.append(node)
            done.add(node.id)
            del pending[node.id]
    return ordered


def _resolve(value: Any, inputs: dict, outputs: dict) -> Any:
    if not isinstance(value, str) or not value.startswith("$"):
        return value
    path = value[1:].split(".")
    current: Any = inputs if path[0] == "inputs" else outputs.get(path[0])
    if path[0] == "inputs":
        path = path[1:]
    else:
        path = path[1:]
    for part in path:
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"Could not resolve workflow reference {value}")
        current = current[part]
    return current


def _run_tool(tool: str, args: dict) -> dict:
    if tool == "source.list":
        with connect() as db:
            rows = db.execute("SELECT id,filename,kind,title,created_at,scanned FROM sources ORDER BY created_at DESC LIMIT 100").fetchall()
        return {"sources": [dict(row) for row in rows]}
    if tool == "source.get":
        with connect() as db:
            row = db.execute("SELECT id,filename,kind,title,created_at FROM sources WHERE id=?", (args["source_id"],)).fetchone()
        if not row:
            raise ValueError("Source not found")
        return dict(row)
    if tool == "memory.open_loops":
        with connect() as db:
            rows = db.execute("SELECT id,title,detail,kind,status,due_at,confidence,source_id FROM loops WHERE status='open' ORDER BY due_at IS NULL,due_at LIMIT 100").fetchall()
        return {"loops": [dict(row) for row in rows]}
    if tool == "report.daily_reset":
        with connect() as db:
            rows = db.execute("SELECT id,title,kind,due_at,source_id FROM loops WHERE status='open' ORDER BY due_at IS NULL,due_at LIMIT 100").fetchall()
        return {"open_count": len(rows), "priority": [dict(row) for row in rows], "note": "Review overdue and dated items first; follow up on waiting items next."}
    if tool == "draft.follow_up":
        with connect() as db:
            source = db.execute("SELECT id,content FROM sources WHERE id=?", (args["source_id"],)).fetchone()
        if not source:
            raise ValueError("Source not found")
        excerpt = re.sub(r"\s+", " ", source["content"]).strip()[:600]
        draft = f"Hi,\n\nI’m following up on: {excerpt}\n\nCould you share an update when you have a chance?\n\nThanks"
        return {"source_id": source["id"], "draft": draft, "sent": False}
    if tool == "skill.scan_local":
        # Reuse the existing local-only scan implementation and its evidence checks.
        from .api import run_skill
        return run_skill(args["skill_id"])
    raise ValueError("Tool is not registered")


def _public_run(run_id: str) -> dict | None:
    with connect() as db:
        row = db.execute("SELECT * FROM workflow_runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            return None
        nodes = db.execute("SELECT * FROM workflow_node_runs WHERE run_id=? ORDER BY rowid", (run_id,)).fetchall()
    result = dict(row)
    result["inputs"] = json_value(result["inputs"], {})
    result["outputs"] = json_value(result["outputs"], {})
    result["nodes"] = [{**dict(node), "output": json_value(node["output"], None)} for node in nodes]
    return result


def _execute(run_id: str, spec: WorkflowSpec, inputs: dict) -> dict:
    outputs = {}
    try:
        with connect() as db:
            run = db.execute("SELECT outputs FROM workflow_runs WHERE id=?", (run_id,)).fetchone()
        outputs = json_value(run["outputs"], {})
        for node in _ordered_nodes(spec):
            with connect() as db:
                checkpoint = db.execute("SELECT status,output FROM workflow_node_runs WHERE run_id=? AND node_id=?", (run_id, node.id)).fetchone()
            if checkpoint and checkpoint["status"] == "completed":
                outputs[node.id] = json_value(checkpoint["output"], {})
                continue
            started = now_iso()
            with connect() as db:
                db.execute("INSERT INTO workflow_node_runs(run_id,node_id,status,started_at) VALUES(?,?,'running',?) ON CONFLICT(run_id,node_id) DO UPDATE SET status='running',error=NULL,started_at=excluded.started_at", (run_id, node.id, started))
                db.execute("UPDATE workflow_runs SET status='running',updated_at=? WHERE id=?", (started, run_id))
            try:
                if node.type == "tool":
                    args = {key: _resolve(value, inputs, outputs) for key, value in node.args.items()}
                    output = _run_tool(node.tool, args)
                elif node.type == "verify":
                    output = {"verified": all(dep in outputs for dep in node.depends_on), "checked_nodes": node.depends_on}
                else:
                    raise ValueError("Approval nodes must be paused for explicit review and are not runnable in this initial release")
                encoded = json.dumps(output, ensure_ascii=False)
                completed = now_iso()
                outputs[node.id] = output
                with connect() as db:
                    source_ids = []
                    if node.tool in {"source.get", "draft.follow_up"}:
                        source_ids = [args["source_id"]]
                    elif node.tool == "skill.scan_local":
                        source_ids = output.get("source_ids", [])
                    for source_id in source_ids:
                        if db.execute("SELECT 1 FROM sources WHERE id=?", (source_id,)).fetchone():
                            db.execute("INSERT OR IGNORE INTO workflow_run_sources(run_id,source_id) VALUES(?,?)", (run_id, source_id))
                    db.execute("UPDATE workflow_node_runs SET status='completed',output=?,completed_at=? WHERE run_id=? AND node_id=?", (encoded, completed, run_id, node.id))
                    db.execute("UPDATE workflow_runs SET outputs=?,updated_at=? WHERE id=?", (json.dumps(outputs, ensure_ascii=False), completed, run_id))
            except Exception as exc:
                failed = now_iso()
                with connect() as db:
                    db.execute("UPDATE workflow_node_runs SET status='failed',error=?,completed_at=? WHERE run_id=? AND node_id=?", (str(exc)[:500], failed, run_id, node.id))
                    db.execute("UPDATE workflow_runs SET status='failed',error=?,updated_at=? WHERE id=?", (str(exc)[:500], failed, run_id))
                return _public_run(run_id)
        with connect() as db:
            db.execute("UPDATE workflow_runs SET status='completed',error=NULL,updated_at=? WHERE id=?", (now_iso(), run_id))
        return _public_run(run_id)
    except Exception as exc:
        with connect() as db:
            db.execute("UPDATE workflow_runs SET status='failed',error=?,updated_at=? WHERE id=?", (str(exc)[:500], now_iso(), run_id))
        return _public_run(run_id)


class RunRequest(BaseModel):
    workflow_id: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=120, pattern=r"^[A-Za-z0-9._:-]+$")
    approved: bool = False


class SpecRequest(BaseModel):
    spec: WorkflowSpec
    inputs: dict[str, Any] = Field(default_factory=dict)


@router.get("/templates")
def list_templates():
    return [{"id": spec.id, "version": spec.version, "spec": spec.model_dump(), "tools": sorted({n.tool for n in spec.nodes if n.tool})} for spec in _template_specs().values()]


@router.get("/tools")
def list_tools():
    return TOOL_MANIFESTS


@router.post("/validate")
def validate_workflow(body: SpecRequest):
    errors = validate_spec(body.spec, body.inputs)
    return {"valid": not errors, "errors": errors, "workflow_id": body.spec.id, "node_order": [node.id for node in _ordered_nodes(body.spec)] if not errors else []}


@router.post("/simulate")
def simulate_workflow(body: RunRequest):
    spec = _template_specs().get(body.workflow_id)
    if not spec:
        raise HTTPException(404, "Unknown workflow template")
    errors = validate_spec(spec, body.inputs)
    if errors:
        raise HTTPException(422, {"errors": errors})
    effects = []
    for node in _ordered_nodes(spec):
        manifest = TOOL_MANIFESTS[node.tool]
        effects.append({"node_id": node.id, "tool": node.tool, "side_effects": manifest["side_effects"], "risk": manifest["risk"], "data_egress": manifest["data_egress"], "needs_scope": manifest["needs_scope"]})
    return {"workflow_id": spec.id, "version": spec.version, "dry_run": True, "would_execute": effects, "requires_approval": any(item["side_effects"] != "read" for item in effects)}


@router.post("/runs")
def start_workflow(body: RunRequest):
    spec = _template_specs().get(body.workflow_id)
    if not spec:
        raise HTTPException(404, "Unknown workflow template")
    errors = validate_spec(spec, body.inputs)
    if errors:
        raise HTTPException(422, {"errors": errors})
    has_local_writes = any(TOOL_MANIFESTS[node.tool]["side_effects"] != "read" for node in spec.nodes if node.tool)
    if has_local_writes and not body.approved:
        raise HTTPException(428, "Run the simulation, review its local writes, then retry with approved=true")
    if body.workflow_id == "commitment-scan":
        from .config import DEMO_MODE
        from .db import connect as db_connect
        if DEMO_MODE:
            raise HTTPException(403, "The commitment scan workflow is disabled in the synthetic public demo")
        with db_connect() as db:
            if not db.execute("SELECT 1 FROM sources WHERE scanned=0 LIMIT 1").fetchone():
                raise HTTPException(400, "No unprocessed sources are available")
    run_id = str(uuid4())
    try:
        with connect() as db:
            db.execute("INSERT INTO workflow_runs(id,workflow_id,workflow_version,status,inputs,outputs,idempotency_key,created_at,updated_at) VALUES(?,?,?,'queued',?,'{}',?,?,?)",
                       (run_id, spec.id, spec.version, json.dumps(body.inputs), body.idempotency_key, now_iso(), now_iso()))
    except Exception:
        if body.idempotency_key:
            with connect() as db:
                existing = db.execute("SELECT id,workflow_id,inputs FROM workflow_runs WHERE idempotency_key=?", (body.idempotency_key,)).fetchone()
            if existing:
                if existing["workflow_id"] != body.workflow_id or json_value(existing["inputs"], {}) != body.inputs:
                    raise HTTPException(409, "Idempotency key was already used for a different workflow request")
                return _public_run(existing["id"])
        raise
    return _execute(run_id, spec, body.inputs)


@router.post("/runs/{run_id}/resume")
def resume_workflow(run_id: str):
    run = _public_run(run_id)
    if not run:
        raise HTTPException(404, "Workflow run not found")
    if run["status"] == "completed":
        return run
    spec = _template_specs().get(run["workflow_id"])
    if not spec or spec.version != run["workflow_version"]:
        raise HTTPException(409, "The versioned workflow template is unavailable")
    return _execute(run_id, spec, run["inputs"])


@router.get("/runs/{run_id}")
def get_workflow_run(run_id: str):
    result = _public_run(run_id)
    if not result:
        raise HTTPException(404, "Workflow run not found")
    return result


@router.get("/runs")
def list_workflow_runs():
    with connect() as db:
        ids = db.execute("SELECT id FROM workflow_runs ORDER BY created_at DESC LIMIT 50").fetchall()
    return [_public_run(row["id"]) for row in ids]
