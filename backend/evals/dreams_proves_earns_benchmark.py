"""Automated Benchmark Suite for:
1. Autonomy Backtesting Engine (90-day counterfactual replay, Wilson UCB, counterexample discovery)
2. Overnight Dreaming Pipeline (Memory consolidation, Hermes skill distillation, sandbox rollback, conflict catching)
3. Proof-of-Privacy Merkle Chain & Personal Chaos Monkey (Tamper detection, zero-raw-record audit, 10-vector stress test)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from backend.app.db import connect, initialize
from backend.app.backtest import (
    compute_wilson_error_ucb,
    generate_90day_decision_history,
    run_autonomy_backtest,
    BacktestRequest
)
from backend.app.dreaming import execute_nightly_dream_cycle
from backend.app.privacy_proof import (
    ensure_merkle_genesis,
    append_privacy_block,
    verify_privacy_merkle_chain,
    run_personal_chaos_monkey,
    compute_block_hash
)

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def test_01_wilson_ucb_statistics():
    """Verify Wilson Score Upper Confidence Bound conforms to statistical invariants."""
    # 0 failures out of 100 trials: UCB should be small (approx 3.7%)
    ucb_0 = compute_wilson_error_ucb(0, 100, confidence=0.95)
    assert 0.02 < ucb_0 < 0.05, f"Unexpected UCB for 0/100: {ucb_0}"

    # 10 failures out of 100 trials: UCB should be approx 17%
    ucb_10 = compute_wilson_error_ucb(10, 100, confidence=0.95)
    assert 0.14 < ucb_10 < 0.19, f"Unexpected UCB for 10/100: {ucb_10}"

    # Monotonicity: more failures -> higher UCB
    assert ucb_10 > ucb_0, "Wilson UCB must be strictly monotonic with respect to failures"


def test_02_90day_replay_dataset():
    """Verify 90-day counterfactual decision dataset generation."""
    history = generate_90day_decision_history("decline_spam_invites")
    assert len(history) >= 40, f"Expected at least 40 events over 90 days, got {len(history)}"
    
    # Check required fields
    first = history[0]
    for key in ["id", "day_index", "timestamp", "sender", "subject", "user_ground_truth"]:
        assert key in first, f"Missing key {key} in historical trace"


def test_03_backtest_promotion_granted():
    """Verify candidate policy achieves L3 promotion when error rate is within alpha."""
    req = BacktestRequest(
        policy_name="decline_spam_invites",
        target_autonomy_level=3,
        time_window_days=90,
        alpha_threshold=0.10, # Realistic alpha tolerance
        inject_adversarial_counterexample=False
    )
    res = run_autonomy_backtest(req)
    assert res.status == "promoted", f"Expected promotion, got {res.status}: {res.verdict_explanation}"
    assert res.ucb_error_rate <= req.alpha_threshold
    assert res.total_samples >= 40
    assert len(res.counterexamples) <= 5


def test_04_backtest_refused_on_invariant_breach():
    """Verify backtest REFUSES promotion when a hard safety invariant is violated."""
    req = BacktestRequest(
        policy_name="decline_spam_invites",
        target_autonomy_level=3,
        time_window_days=90,
        alpha_threshold=0.20,
        inject_adversarial_counterexample=True # Injects VIP calendar decline
    )
    res = run_autonomy_backtest(req)
    assert res.status == "refused_invariant", f"Expected refused_invariant, got {res.status}"
    assert res.worst_case_trace is not None
    assert "VIP" in res.worst_case_trace or "financial" in res.worst_case_trace.lower()


def test_05_overnight_dream_cycle():
    """Verify 4-phase overnight dream cycle executes and stores report."""
    report = execute_nightly_dream_cycle()
    assert report.report_id.startswith("dream_rep_")
    assert len(report.memories_consolidated) >= 2
    assert len(report.draft_skills_synthesized) >= 1
    
    # Check quarantine invariant: all dream skills must be draft_unapproved
    for s in report.draft_skills_synthesized:
        assert s.status == "draft_unapproved", f"Quarantine breach! Skill {s.name} was not draft_unapproved"
        assert s.inverse_rollback_verified is True, f"Inverse rollback handler failed for {s.name}"

    assert len(report.conflicts_caught_for_tomorrow) >= 1


def test_06_privacy_merkle_chain_integrity():
    """Verify Merkle log cryptographic linking and tamper detection."""
    ensure_merkle_genesis()
    
    # Append two valid blocks
    b1 = append_privacy_block("model_inference", "nebius_token_factory", 1420, 0, "Redacted workflow query")
    b2 = append_privacy_block("tool_execution", "local_sandbox", 0, 0, "Filesystem workspace verified")
    
    # Verify clean chain
    receipt = verify_privacy_merkle_chain()
    assert receipt.chain_valid is True, "Expected valid Merkle chain"
    assert receipt.raw_records_leaked == 0, f"Expected 0 raw records leaked, got {receipt.raw_records_leaked}"
    assert receipt.openshell_signatures_valid is True


def test_07_privacy_tamper_detection():
    """Verify Merkle chain detects if a block in SQLite has been maliciously modified."""
    ensure_merkle_genesis()
    
    # Append block
    b = append_privacy_block("test_event", "local_device", 100, 0, "Original data")
    
    # Maliciously mutate block payload in DB
    with connect() as db:
        db.execute(
            "UPDATE privacy_proof_chain SET payload_summary = 'Tampered text' WHERE block_index = ?",
            (b["block_index"],)
        )
        
    receipt = verify_privacy_merkle_chain()
    assert receipt.chain_valid is False, "Merkle verifier failed to detect tampered payload!"

    # Restore block to valid state
    with connect() as db:
        db.execute(
            "UPDATE privacy_proof_chain SET payload_summary = 'Original data' WHERE block_index = ?",
            (b["block_index"],)
        )


def test_08_personal_chaos_monkey_stress():
    """Verify Personal Chaos Monkey attacks all 10 vectors and confirms 100% neutralization."""
    res = run_personal_chaos_monkey()
    assert res["total_probes"] == 10
    assert res["blocked_count"] == 10
    assert res["bypassed_count"] == 0
    assert res["resilience_score"] == 100.0
    assert len(res["suggested_patches"]) >= 1


BENCHMARKS = [
    ("Task 01: Wilson Score Upper Confidence Bound Invariants", test_01_wilson_ucb_statistics),
    ("Task 02: 90-Day Historical Replay Dataset Generation", test_02_90day_replay_dataset),
    ("Task 03: Autonomy Backtest Promotion Granted (UCB <= alpha)", test_03_backtest_promotion_granted),
    ("Task 04: Autonomy Backtest Invariant Veto (Counterexample Discovery)", test_04_backtest_refused_on_invariant_breach),
    ("Task 05: Overnight Dream Cycle (Memory, Skills, Sandbox, Rehearsal)", test_05_overnight_dream_cycle),
    ("Task 06: Proof-of-Privacy Merkle Chain Linkage & Zero-Leak Audit", test_06_privacy_merkle_chain_integrity),
    ("Task 07: Merkle Chain Cryptographic Tamper Detection", test_07_privacy_tamper_detection),
    ("Task 08: Personal Chaos Monkey 10-Vector Adversarial Stress Test", test_08_personal_chaos_monkey_stress),
]


def run_dreams_proves_earns_benchmarks():
    print("=" * 60)
    print("DREAMS, PROVES & EARNS (AUTONOMY SUBSTRATE) BENCHMARK SUITE")
    print("=" * 60)
    initialize()
    passed = 0
    total = len(BENCHMARKS)

    for name, fn in BENCHMARKS:
        t0 = time.perf_counter()
        try:
            fn()
            dt = (time.perf_counter() - t0) * 1000.0
            print(f"[{GREEN}PASS{RESET}] {name:<54} ({dt:5.1f}ms)")
            passed += 1
        except Exception as e:
            dt = (time.perf_counter() - t0) * 1000.0
            print(f"[{RED}FAIL{RESET}] {name:<54} ({dt:5.1f}ms) - {e}")

    print("=" * 60)
    pct = (passed / total) * 100.0
    print(f"DREAMS, PROVES & EARNS SUMMARY: {passed}/{total} PASSED ({pct:.1f}%)")
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    import sys
    success = run_dreams_proves_earns_benchmarks()
    sys.exit(0 if success else 1)

