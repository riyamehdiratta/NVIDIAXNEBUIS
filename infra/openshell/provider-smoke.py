#!/usr/bin/env python3
"""Synthetic OpenAI-compatible Token Factory smoke request from an OpenShell sandbox."""

import json
import os
import sys
import time
import urllib.error
import urllib.request


base = os.environ.get(
    "NEBIUS_TOKEN_FACTORY_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
).rstrip("/")
model = sys.argv[1] if len(sys.argv) > 1 else "nvidia/Nemotron-3_5-Lightning"
body = {
    "model": model,
    "messages": [
        {"role": "system", "content": "Return exactly one valid JSON object and no other text."},
        {"role": "user", "content": 'Return this exact JSON object: {"items":[]}'},
    ],
    "temperature": 0,
    "max_tokens": 64,
    "chat_template_kwargs": {"enable_thinking": False},
}
request = urllib.request.Request(
    f"{base}/chat/completions",
    data=json.dumps(body).encode("utf-8"),
    headers={
        "Authorization": "Bearer " + os.environ.get("NEBIUS_API_KEY", "unused"),
        "Content-Type": "application/json",
    },
    method="POST",
)
started = time.perf_counter()
try:
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
        status = response.status
except urllib.error.HTTPError as error:
    print(f"HTTP_STATUS={error.code}")
    print("ERROR_BODY=" + error.read().decode("utf-8", errors="replace")[:400])
    raise SystemExit(1)

choice = payload.get("choices", [{}])[0]
print(f"HTTP_STATUS={status}")
print(f"MODEL={payload.get('model', model)}")
print(f"LATENCY_MS={(time.perf_counter() - started) * 1000:.1f}")
print("CONTENT=" + repr(choice.get("message", {}).get("content")))
print(f"FINISH_REASON={choice.get('finish_reason')}")
print("USAGE=" + json.dumps(payload.get("usage")))
