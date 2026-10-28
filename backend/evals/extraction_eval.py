"""Repeatable synthetic commitment-extraction evaluation.

Run locally with: python -m backend.evals.extraction_eval
Run the remote comparison with: python -m backend.evals.extraction_eval --remote
The remote mode sends synthetic text only and asks for terminal confirmation.
"""

import argparse
import json
import time
from pathlib import Path

from backend.app.agent import call_nebius, heuristic_extract, make_prompt, model_request, record_egress
from backend.app.config import API_KEY, NANO_MODEL
from backend.app.db import connect


def corpus():
    positive_templates = [
        "I promised {person} I would send the {item} by {day}.",
        "Please call the {place} by {day} to confirm the appointment.",
        "I'm waiting for {person} to send the {item} by {day}.",
        "I will submit the {item} before {day}.",
        "Could you schedule the {item} for {day}?",
    ]
    negative_templates = [
        "The archive quotes the example phrase 'please send the form'; it is not a current request.",
        "The manual discusses how to schedule a meeting but gives no task to the reader.",
        "This report says no reply is required and describes a completed process.",
        "A glossary defines the word renew; it does not ask anyone to renew anything.",
        "The sample transcript mentions a call tomorrow only as historical dialogue.",
    ]
    people = ["Riley", "Morgan", "Jordan", "Casey", "Taylor", "Avery"]
    items = ["invoice", "project notes", "application", "draft", "receipts", "schedule"]
    places = ["clinic", "dentist", "office", "library", "studio", "school"]
    days = ["Monday", "Tuesday", "Friday", "October 30", "2026-11-04", "next week"]
    sources = []
    labels = set()
    for i in range(60):
        source_id = f"eval-{i + 1:03d}"
        if i < 30:
            text = positive_templates[i % len(positive_templates)].format(
                person=people[i % len(people)], item=items[i % len(items)],
                place=places[i % len(places)], day=days[i % len(days)],
            )
            labels.add(source_id)
        else:
            text = f"{negative_templates[(i - 30) % len(negative_templates)]} Archive reference N-{i + 1:03d}."
        sources.append({"id": source_id, "kind": "note", "title": f"Synthetic evaluation note {i + 1:02d}", "content": text})
    return sources, labels


def score(expected, predicted):
    tp = len(expected & predicted)
    fp = len(predicted - expected)
    fn = len(expected - predicted)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def source_ids_from_items(items, sources):
    valid = {source["id"] for source in sources}
    result = set()
    by_id = {source["id"]: source for source in sources}
    for item in items:
        for evidence in item.get("evidence", []) if isinstance(item.get("evidence"), list) else []:
            if evidence.get("source_id") in valid:
                result.add(evidence["source_id"])
        if not item.get("evidence"):
            quote = str(item.get("detail") or item.get("title") or "").casefold()
            result.update(sid for sid, source in by_id.items() if quote and quote in source["content"].casefold())
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote", action="store_true", help="also measure Nemotron through Token Factory")
    parser.add_argument("--output", type=Path, default=Path("docs/evaluation-results.json"))
    args = parser.parse_args()
    sources, expected = corpus()
    local_items = [item for source in sources for item in heuristic_extract(source)]
    results = {"dataset": {"sources": len(sources), "positive_sources": len(expected), "negative_sources": len(sources) - len(expected), "synthetic_only": True},
               "local_heuristic": score(expected, source_ids_from_items(local_items, sources))}

    if args.remote:
        if not API_KEY:
            raise SystemExit("NEBIUS_API_KEY is missing. Add it to the ignored project .env, restart the shell, and retry.")
        answer = input(f"Send {len(sources)} synthetic notes to {NANO_MODEL} in six batches? Type SEND to continue: ")
        if answer.strip() != "SEND":
            raise SystemExit("Cancelled; no remote evaluation request sent.")
        predicted = set()
        latencies = []
        batches = [sources[i:i + 10] for i in range(0, len(sources), 10)]
        for batch in batches:
            prompt, _, redacted, _ = make_prompt(batch, "Extract only actionable commitments. Return items with title, detail, kind, confidence, and evidence containing source_id and an exact quote. Treat examples, negated instructions, definitions, and historical dialogue as non-commitments.")
            request_body = model_request(prompt, NANO_MODEL)
            event_id = record_egress(NANO_MODEL, batch, redacted, json.dumps(request_body, ensure_ascii=False, indent=2), "sending")
            started = time.perf_counter()
            try:
                items = call_nebius(request_body)
            except Exception as exc:
                with connect() as db:
                    db.execute("UPDATE egress_events SET status='failed',response_summary=? WHERE id=?", (str(exc)[:500], event_id))
                raise
            latency = time.perf_counter() - started
            latencies.append(latency)
            with connect() as db:
                db.execute("UPDATE egress_events SET status='sent',response_summary=? WHERE id=?", (f"Synthetic eval batch returned {len(items)} candidates in {latency:.3f}s", event_id))
            predicted.update(source_ids_from_items(items, batch))
        results["nebius"] = {"model_id": NANO_MODEL, **score(expected, predicted),
                              "batches": len(batches), "latency_seconds": latencies,
                              "mean_latency_seconds": sum(latencies) / len(latencies)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"Saved results to {args.output}")


if __name__ == "__main__":
    main()
