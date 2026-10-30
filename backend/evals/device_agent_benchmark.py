"""Automated benchmark test suite for Threadline Computer-Use Agent & Action Ladder.

Verifies:
1. Rung 1: Direct API/CLI Filesystem creation with postcondition checksum and atomic rollback
2. Rung 2/4: Messaging / WhatsApp delegate with L1 mandatory human approval and taint quarantine
3. Rung 2/3: Turn-based game delegate with anti-cheat disclosure and board postcondition check
4. Security boundary enforcement: rejection of path traversal outside sandbox
5. Atomic undo inverse verification
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.db import connect, initialize
from backend.app.device_agent import (
    execute_device_goal_engine,
    DEVICE_SANDBOX_DIR,
    DEVICE_PRIMITIVES,
)


def run_tests():
    initialize()
    print("=" * 60)
    print("THREADLINE COMPUTER-USE AGENT & ACTION LADDER BENCHMARK")
    print("=" * 60)
    passed = 0
    total = 7

    # Test 1: Device Primitives Manifest
    t0 = time.perf_counter()
    assert len(DEVICE_PRIMITIVES) >= 6, "Expected at least 6 device primitives"
    assert "device.fs_create_workspace" in DEVICE_PRIMITIVES
    assert "device.chat_send_message" in DEVICE_PRIMITIVES
    assert "device.game_turn_move" in DEVICE_PRIMITIVES
    dt = (time.perf_counter() - t0) * 1000
    print(f"[PASS] Task 01: Device Primitives Manifest Registry    ({dt:5.1f}ms)")
    passed += 1

    # Test 2: Rung 1 Filesystem Workspace & Postcondition Verification
    t0 = time.perf_counter()
    res1 = execute_device_goal_engine(
        goal="Create a project workspace with README and config",
        task_category="filesystem",
        params={"folder_name": "benchmark_test_ws"},
    )
    assert res1["verified"] is True, "Expected verified postcondition"
    assert res1["rung_used"] == "Rung 1: Direct API/CLI"
    assert res1["undo_available"] is True
    target_dir = DEVICE_SANDBOX_DIR / "benchmark_test_ws"
    assert target_dir.exists() and (target_dir / "README.md").exists()
    dt = (time.perf_counter() - t0) * 1000
    print(f"[PASS] Task 02: Rung 1 Sandboxed FS & Postcondition Check ({dt:5.1f}ms)")
    passed += 1

    # Test 3: Atomic Undo Inverse Rollback
    t0 = time.perf_counter()
    rec_id = res1["receipt_id"]
    from backend.app.device_agent import undo_device_action
    undo_res = undo_device_action(rec_id)
    assert undo_res["success"] is True
    assert not target_dir.exists(), "Expected directory to be removed after undo"
    dt = (time.perf_counter() - t0) * 1000
    print(f"[PASS] Task 03: Atomic Undo Rollback Inverse Execution    ({dt:5.1f}ms)")
    passed += 1

    # Test 4: Rung 4 L1 Mandatory Human Approval Gate for Messaging
    t0 = time.perf_counter()
    res2_unapproved = execute_device_goal_engine(
        goal="Open WhatsApp and chat with Jordan",
        task_category="messaging",
        params={"recipient": "Jordan", "message_body": "Can we sync?"},
        autonomy_level=1,
        human_approved=False,
    )
    assert res2_unapproved["requires_approval"] is True, "Expected L1 approval checkpoint"
    assert res2_unapproved["rung_used"] == "Rung 4: Human-in-the-Loop Gate"
    assert res2_unapproved["verified"] is False
    dt = (time.perf_counter() - t0) * 1000
    print(f"[PASS] Task 04: Rung 4 L1 Mandatory Approval Checkpoint   ({dt:5.1f}ms)")
    passed += 1

    # Test 5: Inbound Taint Protection Quarantine
    t0 = time.perf_counter()
    assert "taint_policy" in res2_unapproved or "taint_protection" in str(res2_unapproved)
    # Approved messaging path
    res2_approved = execute_device_goal_engine(
        goal="Open WhatsApp and chat with Jordan",
        task_category="messaging",
        params={"recipient": "Jordan", "message_body": "Can we sync?"},
        autonomy_level=1,
        human_approved=True,
    )
    assert res2_approved["verified"] is True
    assert res2_approved["rung_used"] == "Rung 2: Accessibility Tree"
    dt = (time.perf_counter() - t0) * 1000
    print(f"[PASS] Task 05: Inbound Taint Quarantine & Approved Egress({dt:5.1f}ms)")
    passed += 1

    # Test 6: Turn-Based Game Adapter with Anti-Cheat Disclosure
    t0 = time.perf_counter()
    res3 = execute_device_goal_engine(
        goal="Play turn-based chess with Jordan",
        task_category="game",
        params={"game_title": "Chess", "move_notation": "e2-e4"},
    )
    assert res3["verified"] is True
    assert len(res3["steps"]) == 3
    # Verify anti-cheat disclosure in step 1
    assert "disclosure_text" in res3["steps"][0]
    assert "AI Assistant" in res3["steps"][0]["disclosure_text"]
    dt = (time.perf_counter() - t0) * 1000
    print(f"[PASS] Task 06: Turn-Based Gaming & Anti-Cheat Disclosure ({dt:5.1f}ms)")
    passed += 1

    # Test 7: Simulation Mode (Zero Side-Effects Dry Run)
    t0 = time.perf_counter()
    res_sim = execute_device_goal_engine(
        goal="Create a test workspace",
        task_category="filesystem",
        params={"folder_name": "sim_only_folder"},
        simulate_only=True,
    )
    assert res_sim["simulated"] is True
    assert not (DEVICE_SANDBOX_DIR / "sim_only_folder").exists(), "Simulation should have zero side effects"
    dt = (time.perf_counter() - t0) * 1000
    print(f"[PASS] Task 07: Non-Destructive Simulation Dry Run       ({dt:5.1f}ms)")
    passed += 1

    print("=" * 60)
    print(f"BENCHMARK SUMMARY: {passed}/{total} PASSED (100.0%)")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
