#!/usr/bin/env python3
"""Two-step synthetic Threadline scan for an OpenShell Nebius provider sandbox."""

import hashlib
import json
import sys
import time
import urllib.request

API = "http://127.0.0.1:8000"
PENDING = "/tmp/threadline-pending-preview.json"


def request(path: str, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        API + path,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def preview():
    request("/api/demo/load", {})
    sources = request("/api/sources")
    # The sample calendar's 10:30 clock value currently triggers phone redaction.
    source_ids = [s["id"] for s in sources if not s["scanned"] and s["kind"] != "calendar"]
    pending = {"source_ids": source_ids, "skill_id": "commitment-scan"}
    result = request("/api/scan/preview", pending)
    # The API canonicalizes source order in the preview response. Confirmation
    # must use that exact ordered ID list or the API correctly rejects it.
    pending["source_ids"] = result["source_ids"]
    pending["preview_id"] = result["preview_id"]
    with open(PENDING, "w", encoding="utf-8") as stream:
        json.dump(pending, stream)
    print(json.dumps({
        "stage": "PREVIEW_ONLY",
        "source_count": result["source_count"],
        "model": result["model"],
        "api_key_configured": result["api_key_configured"],
        "redaction_counts": result["redaction_counts"],
        "payload": json.loads(result["payload"]),
    }, indent=2))


def confirm():
    with open(PENDING, encoding="utf-8") as stream:
        pending = json.load(stream)
    started = time.perf_counter()
    result = request("/api/scan", {**pending, "allow_remote": True})
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    receipt = request("/api/egress")[0]
    print(json.dumps({
        "stage": "CONFIRMED_SCAN",
        "result": result,
        "latency_ms": elapsed_ms,
        "receipt": {
            "id": receipt["id"],
            "model": receipt["model"],
            "status": receipt["status"],
            "source_ids": receipt["source_ids"],
            "redacted_fields": receipt["redacted_fields"],
            "payload_characters": len(receipt["payload"]),
            "payload_sha256": hashlib.sha256(receipt["payload"].encode()).hexdigest(),
            "response_summary": receipt["response_summary"],
            "created_at": receipt["created_at"],
        },
    }, indent=2))


def receipt():
    event = request("/api/egress")[0]
    print(json.dumps({
        "id": event["id"],
        "model": event["model"],
        "status": event["status"],
        "source_ids": event["source_ids"],
        "redacted_fields": event["redacted_fields"],
        "payload_characters": len(event["payload"]),
        "payload_sha256": hashlib.sha256(event["payload"].encode()).hexdigest(),
        "response_summary": event["response_summary"],
        "created_at": event["created_at"],
    }, indent=2))


def receipt_json():
    event = request("/api/egress")[0]
    event["payload"] = json.loads(event["payload"])
    print(json.dumps(event, indent=2))


commands = {"preview": preview, "confirm": confirm, "receipt": receipt, "receipt-json": receipt_json}
if len(sys.argv) != 2 or sys.argv[1] not in commands:
    raise SystemExit("Usage: threadline-live-scan.py preview|confirm|receipt|receipt-json")
commands[sys.argv[1]]()
