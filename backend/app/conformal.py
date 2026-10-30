"""Provable Autonomy via Conformal Risk Control (CRC) & Sequential Drift Detection.

Guarantees finite-sample error control under user-specified safety budgets alpha.
Replaces arbitrary model confidence scores with mathematically provable error ceilings.
"""

import math
from typing import Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .db import connect, json_value, now_iso

router = APIRouter(prefix="/api/conformal", tags=["conformal"])

DEFAULT_ALPHA = 0.02  # Maximum 2% error budget
MIN_CALIBRATION_SAMPLES = 20
DRIFT_THRESHOLD_H = 3.5


class CalibrateRequest(BaseModel):
    action_type: str
    risk_budget_alpha: float = Field(default=DEFAULT_ALPHA, ge=0.001, le=0.20)


class EvaluateRequest(BaseModel):
    action_type: str
    predicted_prob: float = Field(ge=0.0, le=1.0)


class DecisionRecordRequest(BaseModel):
    action_type: str
    predicted_prob: float = Field(ge=0.0, le=1.0)
    user_approved: bool
    source_id: str | None = None


def compute_conformal_threshold(action_type: str, alpha: float = DEFAULT_ALPHA) -> dict[str, Any]:
    """Calculate the calibrated non-conformity threshold tau_hat for an action type."""
    with connect() as db:
        rows = db.execute(
            "SELECT non_conformity_score, user_decision FROM crc_calibration_points WHERE action_type=? ORDER BY non_conformity_score ASC",
            (action_type,)
        ).fetchall()

    n = len(rows)
    if n < MIN_CALIBRATION_SAMPLES:
        return {
            "action_type": action_type,
            "status": "collecting_data",
            "sample_size": n,
            "min_required": MIN_CALIBRATION_SAMPLES,
            "calibrated_tau": None,
            "risk_budget_alpha": alpha,
            "can_auto_execute": False
        }

    tau_hat = None
    best_empirical_risk = 0.0
    for row in rows:
        candidate_tau = row["non_conformity_score"]
        # False auto-executions: score <= candidate_tau AND user rejected (decision == 0)
        unapproved = sum(1 for r in rows if r["non_conformity_score"] <= candidate_tau and r["user_decision"] == 0)
        r_hat = unapproved / n
        upper_bound = (n / (n + 1)) * r_hat + (1.0 / (n + 1))

        if upper_bound <= alpha:
            tau_hat = candidate_tau
            best_empirical_risk = r_hat
        else:
            break

    status = "calibrated" if tau_hat is not None else "risk_exceeded"
    t_now = now_iso()
    with connect() as db:
        db.execute(
            """INSERT INTO crc_policy_thresholds(action_type, risk_budget_alpha, calibrated_tau, sample_size, empirical_risk, status, last_calibrated_at, updated_at)
               VALUES(?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(action_type) DO UPDATE SET
                   risk_budget_alpha=excluded.risk_budget_alpha,
                   calibrated_tau=excluded.calibrated_tau,
                   sample_size=excluded.sample_size,
                   empirical_risk=excluded.empirical_risk,
                   status=excluded.status,
                   last_calibrated_at=excluded.last_calibrated_at,
                   updated_at=excluded.updated_at""",
            (action_type, alpha, tau_hat, n, best_empirical_risk, status, t_now, t_now)
        )

    return {
        "action_type": action_type,
        "status": status,
        "sample_size": n,
        "calibrated_tau": round(tau_hat, 4) if tau_hat is not None else None,
        "empirical_risk": round(best_empirical_risk, 4),
        "risk_budget_alpha": alpha,
        "can_auto_execute": (tau_hat is not None)
    }


def evaluate_conformal_gate(action_type: str, predicted_prob: float) -> dict[str, Any]:
    """Test whether predicted approval probability meets the calibrated conformal bound."""
    with connect() as db:
        row = db.execute("SELECT * FROM crc_policy_thresholds WHERE action_type=?", (action_type,)).fetchone()

    score = round(1.0 - predicted_prob, 4)
    if not row or row["status"] != "calibrated" or row["calibrated_tau"] is None:
        return {
            "auto_execute": False,
            "status": "abstain_uncalibrated",
            "score": score,
            "threshold": None,
            "reason": "Insufficient calibration data to mathematically guarantee error bound"
        }

    tau_hat = row["calibrated_tau"]
    if score <= tau_hat:
        return {
            "auto_execute": True,
            "status": "approved_by_crc",
            "score": score,
            "threshold": round(tau_hat, 4),
            "guaranteed_max_error": row["risk_budget_alpha"],
            "reason": f"Non-conformity score {score:.3f} <= calibrated threshold {tau_hat:.3f}"
        }
    return {
        "auto_execute": False,
        "status": "abstain_uncertain",
        "score": score,
        "threshold": round(tau_hat, 4),
        "reason": f"Non-conformity score {score:.3f} exceeds safe threshold {tau_hat:.3f}"
    }


def record_conformal_feedback(action_type: str, predicted_prob: float, user_approved: bool, source_id: str | None = None) -> dict[str, Any]:
    """Log calibration decision and update sequential CUSUM martingale drift detection."""
    t_now = now_iso()
    score = round(1.0 - predicted_prob, 4)
    decision_int = 1 if user_approved else 0
    pt_id = "crc_" + uuid4().hex[:10]

    with connect() as db:
        db.execute(
            """INSERT INTO crc_calibration_points(id, action_type, feature_vector, predicted_prob, non_conformity_score, user_decision, loss, context_source_id, created_at)
               VALUES(?, ?, '{}', ?, ?, ?, ?, ?, ?)""",
            (pt_id, action_type, predicted_prob, score, decision_int, 1.0 if not user_approved else 0.0, source_id, t_now)
        )
        threshold_row = db.execute("SELECT * FROM crc_policy_thresholds WHERE action_type=?", (action_type,)).fetchone()

    drift_detected = False
    if threshold_row and threshold_row["calibrated_tau"] is not None:
        alpha = threshold_row["risk_budget_alpha"]
        tau_hat = threshold_row["calibrated_tau"]
        loss = 1.0 if (score <= tau_hat and not user_approved) else 0.0
        kappa = alpha / 2.0
        new_drift = max(0.0, threshold_row["martingale_drift_statistic"] + (loss - alpha) - kappa)
        drift_detected = new_drift > DRIFT_THRESHOLD_H
        new_status = "drift_detected" if drift_detected else threshold_row["status"]

        with connect() as db:
            db.execute(
                "UPDATE crc_policy_thresholds SET martingale_drift_statistic=?, status=?, updated_at=? WHERE action_type=?",
                (round(new_drift, 3), new_status, t_now, action_type)
            )

    return {
        "recorded": True,
        "calibration_point_id": pt_id,
        "score": score,
        "drift_detected": drift_detected
    }


@router.post("/calibrate")
def calibrate_action(body: CalibrateRequest):
    """Calibrate non-conformity threshold for a specific action type under safety budget alpha."""
    return compute_conformal_threshold(body.action_type, body.risk_budget_alpha)


@router.post("/evaluate")
def evaluate_action(body: EvaluateRequest):
    """Query whether an action can auto-execute under conformal guarantees."""
    return evaluate_conformal_gate(body.action_type, body.predicted_prob)


@router.post("/record_decision")
def record_decision(body: DecisionRecordRequest):
    """Record an empirical decision to calibrate the model and update drift detectors."""
    return record_conformal_feedback(body.action_type, body.predicted_prob, body.user_approved, body.source_id)


@router.get("/status")
def list_conformal_status():
    """List calibration status and active drift monitors across all action types."""
    with connect() as db:
        rows = db.execute("SELECT * FROM crc_policy_thresholds ORDER BY action_type").fetchall()
        pts_counts = db.execute("SELECT action_type, COUNT(*) as cnt FROM crc_calibration_points GROUP BY action_type").fetchall()

    counts = {r["action_type"]: r["cnt"] for r in pts_counts}
    result = []
    for r in rows:
        result.append({
            "action_type": r["action_type"],
            "risk_budget_alpha": r["risk_budget_alpha"],
            "calibrated_tau": r["calibrated_tau"],
            "sample_size": counts.get(r["action_type"], r["sample_size"]),
            "empirical_risk": r["empirical_risk"],
            "martingale_drift_statistic": r["martingale_drift_statistic"],
            "status": r["status"],
            "last_calibrated_at": r["last_calibrated_at"]
        })
    return {"policies": result}


@router.get("/points")
def list_calibration_points(action_type: str | None = None, limit: int = 50):
    """List empirical calibration points and observed losses."""
    with connect() as db:
        if action_type:
            rows = db.execute(
                "SELECT * FROM crc_calibration_points WHERE action_type=? ORDER BY created_at DESC LIMIT ?",
                (action_type, limit)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM crc_calibration_points ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
    return [{
        "id": r["id"],
        "action_type": r["action_type"],
        "predicted_prob": r["predicted_prob"],
        "non_conformity_score": r["non_conformity_score"],
        "user_decision": r["user_decision"],
        "loss": r["loss"],
        "created_at": r["created_at"]
    } for r in rows]
