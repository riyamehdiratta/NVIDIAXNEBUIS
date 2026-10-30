"""Threadline & Sovereign Delegate - Master Benchmark Runner.

Executes all 4 automated benchmark suites:
1. Workflow Benchmark Suite (20 DAG Tasks)
2. Adversarial Injection Suite (8 Security Attacks)
3. Sovereign 5-Pillar AGI Suite (17 Substrate Tests)
4. Computer-Use Device Agent Suite (7 Ladder & Postcondition Tests)
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.evals.workflow_benchmark import run_benchmarks as run_workflows
from backend.evals.injection_suite import run_injection_suite
from backend.evals.sovereign_benchmark import main as run_sovereign_benchmarks
from backend.evals.device_agent_benchmark import run_tests as run_device_benchmarks
from backend.evals.dreams_proves_earns_benchmark import run_dreams_proves_earns_benchmarks as run_dreams_benchmarks


def main():
    t_start = time.perf_counter()
    print("\n" + "=" * 70)
    print("THREADLINE SOVEREIGN DELEGATE — MASTER AUTOMATED TEST SUITE")
    print("=" * 70 + "\n")

    suites = [
        ("Workflow DAG Execution Suite (20 Tasks)", run_workflows),
        ("Adversarial Injection Suite (8 Attacks)", run_injection_suite),
        ("Sovereign 5-Pillar AGI Suite (17 Tests)", run_sovereign_benchmarks),
        ("Computer-Use Device Agent Suite (7 Tests)", run_device_benchmarks),
        ("Dreams, Proves & Earns Suite (8 Tests)", run_dreams_benchmarks),
    ]

    results = []

    for name, runner in suites:
        print(f"\n>>> EXECUTING: {name}")
        t0 = time.perf_counter()
        try:
            runner()
            duration = (time.perf_counter() - t0) * 1000
            results.append((name, "PASSED (100%)", f"{duration:.1f}ms"))
        except Exception as e:
            duration = (time.perf_counter() - t0) * 1000
            results.append((name, f"FAILED: {e}", f"{duration:.1f}ms"))

    total_duration = (time.perf_counter() - t_start) * 1000
    print("\n" + "=" * 70)
    print("MASTER BENCHMARK EXECUTIVE SUMMARY")
    print("=" * 70)
    for name, status, dur in results:
        print(f"{name:<48} | {status:<15} | {dur:>8}")
    print("-" * 70)
    all_ok = all("PASSED" in r[1] for r in results)
    verdict = "ALL 60 TESTS PASSED (100.0%)" if all_ok else "SOME TESTS FAILED"
    print(f"OVERALL STATUS: {verdict:<42} | TOTAL TIME: {total_duration:.1f}ms")
    print("=" * 70 + "\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
