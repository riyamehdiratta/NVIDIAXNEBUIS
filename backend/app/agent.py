import json
import re
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from uuid import uuid4

from .config import API_KEY, NANO_MODEL, SUPER_MODEL, TOKEN_FACTORY_BASE_URL
from .db import connect, json_value, now_iso
from .privacy import redact


ACTION_WORDS = re.compile(r"\b(send|reply|respond|submit|schedule|book|call|pay|confirm|share|finish|complete|renew|review|follow up|follow-up|remind|bring|pick up|drop off|waiting for|owe|promised|need to|please)\b", re.I)
DATE_HINT = re.compile(r"\b(today|tomorrow|tonight|this week|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}(?:/\d{2,4})?|\w+ \d{1,2})\b", re.I)


def _due_date(text: str):
    hit = re.search(r"\b(?:by|before|due(?: on)?|on|until)\s+(today|tomorrow|this week|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}(?:/\d{2,4})?|\w+ \d{1,2})\b", text, re.I)
    if not hit:
        return None
    token = hit.group(1).lower()
    today = date.today()
    if token == "today":
        d = today
    elif token == "tomorrow":
        d = today + timedelta(days=1)
    elif token in {"this week", "next week"}:
        d = today + timedelta(days=(4 - today.weekday()) % 7 or 7)
        if token == "next week":
            d += timedelta(days=7)
    elif token in {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}:
        weekday = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"].index(token)
        delta = (weekday - today.weekday()) % 7 or 7
        d = today + timedelta(days=delta)
    else:
        try:
            d = datetime.strptime(token, "%Y-%m-%d").date() if re.fullmatch(r"\d{4}-\d{2}-\d{2}", token) else None
            if d is None:
                for fmt in ("%m/%d/%Y", "%m/%d/%y", "%m/%d", "%B %d", "%b %d"):
                    try:
                        parsed = datetime.strptime(token, fmt).date()
                        d = parsed.replace(year=today.year) if fmt in {"%m/%d", "%B %d", "%b %d"} else parsed
                        break
                    except ValueError:
                        pass
            if d is None:
                return None
        except ValueError:
            return None
    return d.isoformat()


def heuristic_extract(source: dict):
    output = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", source["content"]):
        text = re.sub(r"\s+", " ", sentence).strip(" •-\t")
        if len(text) < 12 or not ACTION_WORDS.search(text):
            continue
        low = text.lower()
        kind = "waiting_on_them" if re.search(r"waiting for|they (?:will|should)|expect(?:ing)? (?:a|the|their) reply", low) else "promise" if re.search(r"i (?:will|can|promised|owe)|i'll\b|my promise", low) else "task"
        due = _due_date(text)
        output.append({
            "title": text[:115].rstrip(".,;"),
            "detail": text,
            "kind": kind,
            "due_at": due,
            "owner": None,
            "confidence": 0.68 if due or kind != "task" else 0.53,
            "evidence": [{"source_id": source["id"], "quote": text[:220]}],
        })
    return output


def make_prompt(sources: list[dict], instructions: str):
    safe_sources = []
    total_redacted = 0
    redaction_counts = {}
    for source in sources:
        safe, count, counts = redact(source["content"][:4500])
        total_redacted += count
        for key, value in counts.items():
            redaction_counts[key] = redaction_counts.get(key, 0) + value
        safe_sources.append({"id": source["id"], "kind": source["kind"], "title": source["title"], "content": safe})
    prompt = {
        "task": "Extract only open commitments from the provided user-selected items. Return JSON with an items array. Each item needs title, detail, kind (task, promise, waiting_on_them, appointment), due_at (ISO date or null), owner (string or null), confidence (0..1), and evidence [{source_id, quote}]. Never invent facts, people, or dates. If uncertain, lower confidence and use null.",
        "skill_instructions": instructions,
        "sources": safe_sources,
    }
    pretty = json.dumps(prompt, ensure_ascii=False, indent=2)
    # The preview is the exact user content included in the model request.
    return prompt, pretty, total_redacted, redaction_counts


def _model_for(sources, prompt):
    joined = " ".join(s["content"] for s in sources)
    ambiguous = len(re.findall(r"\b(?:maybe|might|possibly|if|unless|not sure|unclear|tentative)\b", joined, re.I)) >= 2 or len(sources) > 8
    return SUPER_MODEL if ambiguous else NANO_MODEL


def model_request(prompt: dict, model: str):
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are Threadline, a careful personal assistant. Extract structured facts only; do not infer missing deadlines or claim an action was completed."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0.1,
        "max_tokens": 3000,
        # The Nebius-hosted Nemotron Lightning endpoint otherwise spends the
        # completion budget on chain-of-thought text and may never return JSON.
        "chat_template_kwargs": {"enable_thinking": False},
    }


def call_nebius_json(request_body: dict):
    if not API_KEY:
        raise RuntimeError("NEBIUS_API_KEY is not configured. Choose local-only analysis or add the key to your environment.")
    body = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{TOKEN_FACTORY_BASE_URL}/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Token Factory returned HTTP {exc.code}: {message}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Token Factory is unavailable: {exc}") from exc
    content = response_data["choices"][0]["message"]["content"]
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I)
    return json.loads(content)


def call_nebius(request_body: dict):
    parsed = call_nebius_json(request_body)
    if isinstance(parsed, list):
        items = parsed
    else:
        items = parsed.get("items", [])
    if not isinstance(items, list):
        raise RuntimeError("Model response did not contain a valid items array")
    return items


def record_egress(model, sources, count, payload, status, summary=None):
    event_id = str(uuid4())
    with connect() as db:
        db.execute(
        "INSERT INTO egress_events(id,model,source_ids,redacted_fields,payload,status,created_at,response_summary) VALUES(?,?,?,?,?,?,?,?)",
            (event_id, model, json.dumps([s["id"] for s in sources]), count, payload, status, now_iso(), summary),
        )
        db.execute("INSERT INTO activity(id,event_type,detail,created_at) VALUES(?,?,?,?)", (str(uuid4()), "model_egress", f"{status} · {model} · {len(sources)} source(s)", now_iso()))
    return event_id
