from datetime import date, timedelta

from .autonomy import can_execute_automatically, shadow_prediction, shadow_summary


def simulate_week(today: date | None = None) -> dict:
    """Replay clearly synthetic decisions without changing workspace state."""
    anchor = today or date.today()
    approved = rejected = agreements = samples = 0
    day_rows = []
    events = []
    rejection_indexes = {18, 39}

    for index in range(49):
        day_index = index // 7
        decision = "reject" if index in ({2, *rejection_indexes}) else "approve"
        prediction = shadow_prediction(approved, rejected)
        agreement = None if prediction is None else (prediction == (decision == "approve"))
        if prediction is not None:
            samples += 1
            agreements += int(agreement)
        if decision == "approve":
            approved += 1
        else:
            rejected += 1
        events.append({
            "day": (anchor - timedelta(days=6 - day_index)).isoformat(),
            "action_type": "create_reminder",
            "synthetic_source": f"Synthetic email {index + 1:02d}: Please send the project reminder by Friday.",
            "decision": decision,
            "shadow_prediction": None if prediction is None else ("approve" if prediction else "reject"),
            "agreement": agreement,
        })
        if index % 7 == 6:
            summary = shadow_summary(agreements, samples)
            day_rows.append({
                "day": events[-1]["day"], "decisions": index + 1,
                "shadow_samples": samples, "agreements": agreements,
                "agreement_rate": summary["shadow_accuracy"],
                "wilson_lower_95": summary["wilson_lower_95"],
                "promotion_suggested": summary["promotion_suggested"],
            })

    thin_evidence = shadow_summary(2, 3)
    unearned_allowed = can_execute_automatically(
        enabled=True, shadow_mode=False, reversible=True,
        autonomy_level=1, daily_count=0, daily_cap=10,
    )
    return {
        "simulation_only": True,
        "persisted": False,
        "notice": "All seven days and decisions are synthetic. This replay does not modify your real policies or action history.",
        "daily": day_rows,
        "events": events,
        "earned_example": {
            "action_type": "create_reminder",
            "shadow_samples": samples,
            "agreements": agreements,
            **shadow_summary(agreements, samples),
            "configured_level": 1,
            "configured_level_changed_automatically": False,
        },
        "unearned_example": {
            "action_type": "draft_reply",
            "shadow_samples": thin_evidence["shadow_samples"],
            "wilson_lower_95": thin_evidence["wilson_lower_95"],
            "promotion_suggested": thin_evidence["promotion_suggested"],
            "configured_level": 1,
            "automatic_execution_allowed": unearned_allowed,
            "blocked_reason": "Only three decisions are available; shadow mode abstains below five, and the action remains at L1 until the user changes it.",
        },
    }
