"""Sovereign Delegate 5-Pillar Empirical Benchmark Suite.

Validates the complete autonomous OS substrate across:
1. Ambient Apprenticeship (Win32 OS perception, PII masking, parameter lifting, DAG compilation)
2. Learned Preference Model (Bayesian regression, Shannon entropy, active learning query generation)
3. Provable Autonomy via Conformal Risk Control (CRC guarantee E[L] <= alpha, CUSUM drift detection)
4. Self-Extension & Tool Synthesizer (safe sandbox exec, inverse rollback handlers, TOOL_MANIFESTS injection)
5. Lifelong Causal World Model (Rubin ATE potential outcomes, 7-day forward horizon rehearsal, provenance cascade)
"""

import time
import math
from datetime import datetime, timezone
from backend.app.apprenticeship import (
    get_native_foreground_window,
    start_trace_recording,
    record_event,
    stop_trace_recording,
    synthesize_workflow_from_trace,
    TraceStartRequest,
    TraceEventRequest,
    StopTraceRequest,
    SynthesizeRequest,
)
from backend.app.preference_model import (
    extract_features,
    predict_approval,
    get_preference_weights,
    save_preference_weights,
    update_preference_model,
    get_active_learning_queries,
    FeedbackRequest,
)
from backend.app.conformal import (
    compute_conformal_threshold,
    evaluate_conformal_gate,
    record_conformal_feedback,
    DEFAULT_ALPHA,
)
from backend.app.synthesizer import (
    _safe_sandbox_exec,
    synthesize_tool,
    verify_synthesized_tool,
    SynthesizeToolRequest,
    VerifyToolRequest,
    TOOL_MANIFESTS,
)
from backend.app.world_model import (
    add_knowledge_triple,
    query_knowledge_triples,
    evaluate_causal_trial,
    simulate_forward_horizon,
    TripleRequest,
    CausalTrialRequest,
)
from backend.app.db import connect, now_iso


def run_test(name: str, fn):
    t0 = time.perf_counter()
    try:
        fn()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        print(f"[PASS] {name:<50} ({elapsed_ms:5.1f}ms)")
        return True
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        print(f"[FAIL] {name:<50} ({elapsed_ms:5.1f}ms) - {exc}")
        return False


def test_01_win32_os_perception():
    win = get_native_foreground_window()
    assert "window_title" in win
    assert "process_name" in win or "platform" in win


def test_02_apprenticeship_recording_and_pii_masking():
    t_start = start_trace_recording(TraceStartRequest(
        title="Benchmark Test Demonstration",
        process_name="test_app.exe",
        window_title="Test Application Window"
    ))
    trace_id = t_start["trace_id"]
    assert t_start["recording"] is True

    # Record regular step
    ev1 = record_event(TraceEventRequest(
        trace_id=trace_id,
        event_type="click",
        target_name="Save Document Button"
    ))
    assert ev1["recorded"] is True

    # Record sensitive credential -> verifies automated masking
    ev2 = record_event(TraceEventRequest(
        trace_id=trace_id,
        event_type="type",
        target_role="password",
        target_name="Account Password",
        value="TopSecretPassword123"
    ))
    assert ev2["recorded"] is True

    with connect() as db:
        row = db.execute("SELECT events FROM apprenticeship_traces WHERE id=?", (trace_id,)).fetchone()
    import json
    events = json.loads(row["events"])
    assert events[1]["value"] == "[MASKED_CREDENTIAL]"

    # Stop recording
    stopped = stop_trace_recording(StopTraceRequest(trace_id=trace_id))
    assert stopped["stopped"] is True
    assert stopped["total_events"] == 2


def test_03_parameter_lifting_and_dag_synthesis():
    t_start = start_trace_recording(TraceStartRequest(
        title="Invoice Pipeline Demonstration",
        process_name="excel.exe",
        window_title="Financial Statement"
    ))
    trace_id = t_start["trace_id"]

    # Record events with dates and emails
    record_event(TraceEventRequest(
        trace_id=trace_id,
        event_type="type",
        target_name="Due Date Field",
        value="2026-11-20"
    ))
    record_event(TraceEventRequest(
        trace_id=trace_id,
        event_type="type",
        target_name="Recipient Email",
        value="cfo@company.org"
    ))
    stop_trace_recording(StopTraceRequest(trace_id=trace_id))

    # Synthesize DAG
    res = synthesize_workflow_from_trace(SynthesizeRequest(trace_id=trace_id))
    assert res["synthesized"] is True
    assert "target_date" in res["lifted_inputs"]
    assert "contact_email" in res["lifted_inputs"]
    assert res["total_nodes"] >= 3
    # Verifies independent verifier node is automatically appended
    last_node = res["spec"]["nodes"][-1]
    assert last_node["type"] == "verify"


def test_04_bayesian_preference_feature_extraction():
    feats = extract_features("draft_reply", {"source_id": "src_123"}, life_area="work", daily_count=4)
    assert len(feats) == 8
    # Risk score for draft_reply is 0.8, is_work is 1.0, bias is 1.0
    assert feats[0] == 0.8
    assert feats[2] == 1.0
    assert feats[7] == 1.0


def test_05_shannon_epistemic_entropy_calculation():
    # Maximum entropy at p = 0.5 is 1.0 bit
    pred_mid = predict_approval([0, 0, 0, 0, 0, 0, 0, 0])
    assert abs(pred_mid["uncertainty_entropy"] - 1.0) < 0.05
    assert pred_mid["is_confident"] is False


def test_06_online_bayesian_feedback_gradient_update():
    prev_weights = get_preference_weights()
    res = update_preference_model(FeedbackRequest(
        action_type="create_reminder",
        approved=True,
        learning_rate=0.20
    ))
    assert res["updated"] is True
    assert len(res["new_weights"]) == 8
    # Weights should adapt
    assert res["new_weights"] != prev_weights


def test_07_active_learning_uncertainty_queries():
    res = get_active_learning_queries()
    assert "active_queries" in res
    for q in res["active_queries"]:
        assert q["entropy"] > 0.70


def test_08_conformal_risk_finite_sample_guarantee():
    # Insert 50 calibration points with 0 losses to satisfy n/(n+1)*R + 1/(n+1) <= alpha
    with connect() as db:
        db.execute("DELETE FROM crc_calibration_points WHERE action_type='benchmark_action'")
        for i in range(50):
            db.execute(
                """INSERT INTO crc_calibration_points(id, action_type, feature_vector, predicted_prob, non_conformity_score, user_decision, loss, created_at)
                   VALUES(?, 'benchmark_action', '{}', 0.95, 0.05, 1, 0.0, ?)""",
                (f"bench_pt_{i}", now_iso())
            )
    cal = compute_conformal_threshold("benchmark_action", alpha=0.03)
    assert cal["status"] == "calibrated"
    assert cal["can_auto_execute"] is True
    assert cal["calibrated_tau"] is not None


def test_09_conformal_gate_evaluation():
    # If score <= tau -> approved_by_crc
    gate_pass = evaluate_conformal_gate("benchmark_action", predicted_prob=0.98)
    assert gate_pass["auto_execute"] is True
    assert gate_pass["status"] == "approved_by_crc"

    # If score > tau -> abstain_uncertain
    gate_fail = evaluate_conformal_gate("benchmark_action", predicted_prob=0.60)
    assert gate_fail["auto_execute"] is False
    assert gate_fail["status"] == "abstain_uncertain"


def test_10_cusum_martingale_sequential_drift_detection():
    # Trigger repeated unapproved losses on benchmark action to drive martingale statistic
    for i in range(10):
        rec = record_conformal_feedback("benchmark_action", predicted_prob=0.98, user_approved=False)
    with connect() as db:
        row = db.execute("SELECT martingale_drift_statistic, status FROM crc_policy_thresholds WHERE action_type='benchmark_action'").fetchone()
    # Martingale should accumulate
    assert row["martingale_drift_statistic"] > 0.0


def test_11_safe_sandbox_code_execution():
    code = """
def handler(args):
    data = args.get('items', [])
    return {'count': len(data), 'doubled': [x * 2 for x in data]}
"""
    res = _safe_sandbox_exec(code, {"items": [1, 2, 3, 4]})
    assert res["success"] is True
    assert res["output"]["count"] == 4
    assert res["output"]["doubled"] == [2, 4, 6, 8]


def test_12_sandbox_security_isolation_blocks_unsafe_ops():
    unsafe_code = """
def handler(args):
    import os
    os.system('echo dangerous')
    return {'done': True}
"""
    res = _safe_sandbox_exec(unsafe_code, {})
    # exec must fail because import/os is not in safe_globals
    assert res["success"] is False


def test_13_autonomous_tool_synthesis_and_injection():
    req = SynthesizeToolRequest(
        name="crypto.token_hash",
        description="Hashes and formats input payload safely",
        operation_type="formatting"
    )
    synth = synthesize_tool(req)
    assert synth["synthesized"] is True
    assert synth["verified"] is True
    assert "crypto.token_hash" in TOOL_MANIFESTS
    manifest = TOOL_MANIFESTS["crypto.token_hash"]
    assert manifest["inverse"] == "crypto.token_hash.rollback"
    assert manifest["risk"] == "low"


def test_14_synthesized_tool_verification():
    with connect() as db:
        row = db.execute("SELECT id FROM synthesized_tools WHERE name='crypto.token_hash'").fetchone()
    assert row is not None
    ver = verify_synthesized_tool(VerifyToolRequest(tool_id=row["id"], sample_inputs={"text": "benchmark"}))
    assert ver["verified"] is True


def test_15_knowledge_graph_provenance_triples():
    with connect() as db:
        db.execute(
            "INSERT OR IGNORE INTO sources(id, filename, kind, title, content, digest, created_at, origin, scanned) "
            "VALUES('src_doc_benchmark', 'bench.txt', 'note', 'Benchmark Guidelines', 'Guidelines', 'dig123', ?, 'manual', 1)",
            (now_iso(),)
        )
    trip = add_knowledge_triple(TripleRequest(
        subject="Project Alpha",
        predicate="requires_encryption",
        object="AES-256",
        confidence=0.99,
        source_id="src_doc_benchmark",
        evidence="Per company security guidelines section 4"
    ))
    assert trip["created"] is True

    results = query_knowledge_triples(subject="Project Alpha")
    assert len(results) >= 1
    assert results[0]["object"] == "AES-256"
    assert results[0]["source_id"] == "src_doc_benchmark"


def test_16_rubin_potential_outcomes_causal_trial():
    trial = evaluate_causal_trial(CausalTrialRequest(
        name="Benchmark Delay vs Immediate Dispatch",
        intervention="2-Hour Review Buffer",
        outcome_metric="User Satisfaction Score",
        treatment_samples=[5.8, 6.2, 5.9, 6.1, 6.0],
        control_samples=[2.1, 2.3, 2.0, 2.2, 1.9]
    ))
    # ATE should be positive and statistically significant
    assert trial["causal_effect_ate"] > 3.0
    assert trial["statistically_significant"] is True
    assert "causes an average change" in trial["conclusion"]


def test_17_forward_7day_horizon_workload_rehearsal():
    horizon = simulate_forward_horizon()
    assert horizon["horizon_days"] == 7
    assert len(horizon["forecast"]) == 7
    assert "morning_recommendation" in horizon
    for day in horizon["forecast"]:
        assert "workload_score" in day
        assert "risk_level" in day
        assert day["risk_level"] in {"calm", "medium", "high"}


def main():
    print("=" * 60)
    print("SOVEREIGN DELEGATE (AGI CORE) - 5-PILLAR BENCHMARK SUITE")
    print("=" * 60)

    tests = [
        ("Task 01: Win32 OS Introspection (Any Native App)", test_01_win32_os_perception),
        ("Task 02: Ambient Apprenticeship & PII Masking", test_02_apprenticeship_recording_and_pii_masking),
        ("Task 03: Parameter Lifting & Typed DAG Synthesis", test_03_parameter_lifting_and_dag_synthesis),
        ("Task 04: Bayesian Preference Feature Extraction", test_04_bayesian_preference_feature_extraction),
        ("Task 05: Shannon Epistemic Entropy Quantification", test_05_shannon_epistemic_entropy_calculation),
        ("Task 06: Online Bayesian Feedback Gradient Update", test_06_online_bayesian_feedback_gradient_update),
        ("Task 07: Active Learning Query Synthesis", test_07_active_learning_uncertainty_queries),
        ("Task 08: Finite-Sample Conformal Risk Guarantee", test_08_conformal_risk_finite_sample_guarantee),
        ("Task 09: Conformal Gate Evaluator (Abstain vs Auto)", test_09_conformal_gate_evaluation),
        ("Task 10: Sequential CUSUM Martingale Drift Detector", test_10_cusum_martingale_sequential_drift_detection),
        ("Task 11: Sandboxed Code Execution Engine", test_11_safe_sandbox_code_execution),
        ("Task 12: Sandbox Security Boundary Enforcement", test_12_sandbox_security_isolation_blocks_unsafe_ops),
        ("Task 13: Autonomous Tool Synthesis & Injection", test_13_autonomous_tool_synthesis_and_injection),
        ("Task 14: Synthesized Tool Sandbox Verification", test_14_synthesized_tool_verification),
        ("Task 15: Auditable Knowledge Provenance Triples", test_15_knowledge_graph_provenance_triples),
        ("Task 16: Rubin Potential Outcomes Causal ATE Trial", test_16_rubin_potential_outcomes_causal_trial),
        ("Task 17: Forward 7-Day Horizon Workload Rehearsal", test_17_forward_7day_horizon_workload_rehearsal),
    ]

    passed = 0
    t_start = time.perf_counter()
    for name, fn in tests:
        if run_test(name, fn):
            passed += 1

    total_time = (time.perf_counter() - t_start) * 1000
    print("=" * 60)
    print(f"SOVEREIGN BENCHMARK SUMMARY: {passed}/{len(tests)} PASSED ({(passed/len(tests))*100:.1f}%) in {total_time:.1f}ms")
    print("=" * 60)

    if passed < len(tests):
        exit(1)


if __name__ == "__main__":
    main()
