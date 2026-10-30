"""Personalized Preference & Decision Model with Active Learning.

Maintains an online Bayesian decision model over user action choices,
quantifies epistemic uncertainty, and triggers active learning queries
to minimize user interruption while learning personal decision boundaries.
"""

import json
import math
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .db import connect, json_value, now_iso

router = APIRouter(prefix="/api/preferences", tags=["preferences"])

# Prior feature weights for risk assessment:
# [risk_level, reversible, is_work_area, late_hour, external_write, daily_volume_ratio, entity_familiar, base_bias]
DEFAULT_WEIGHTS = [-1.8, 1.4, -0.4, -0.8, -2.2, -0.6, 1.2, 0.5]


def extract_features(action_type: str, payload: dict, life_area: str = "personal", daily_count: int = 0) -> list[float]:
    """Transform contextual action request into normalized mathematical feature vector x."""
    risk_score = 0.8 if action_type == "draft_reply" else 0.2 if action_type == "create_reminder" else 0.5
    reversible = 1.0 if action_type in {"create_reminder", "draft_reply"} else 0.0
    is_work = 1.0 if life_area == "work" else 0.0

    hour = datetime_now_hour()
    late_hour = 1.0 if (hour >= 21 or hour < 7) else 0.0
    external_write = 1.0 if action_type == "calendar_export" else 0.0
    daily_volume_ratio = min(1.0, daily_count / 10.0)
    entity_familiar = 1.0 if payload.get("source_id") else 0.5

    return [risk_score, reversible, is_work, late_hour, external_write, daily_volume_ratio, entity_familiar, 1.0]


def datetime_now_hour() -> int:
    from datetime import datetime
    return datetime.now().hour


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


def get_preference_weights() -> list[float]:
    """Load or initialize online Bayesian weights."""
    with connect() as db:
        row = db.execute("SELECT value FROM app_settings WHERE key='bayesian_preference_weights'").fetchone()
    if row:
        return json_value(row["value"], DEFAULT_WEIGHTS)
    return list(DEFAULT_WEIGHTS)


def save_preference_weights(weights: list[float]):
    with connect() as db:
        db.execute(
            """INSERT INTO app_settings(key, value, updated_at) VALUES('bayesian_preference_weights', ?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (json.dumps(weights), now_iso())
        )


def predict_approval(features: list[float]) -> dict[str, Any]:
    """Compute predicted approval probability and epistemic uncertainty."""
    weights = get_preference_weights()
    logit = sum(w * f for w, f in zip(weights, features))
    prob = sigmoid(logit)
    entropy = -prob * math.log2(max(1e-9, prob)) - (1 - prob) * math.log2(max(1e-9, 1 - prob))
    # Epistemic variance approximation
    uncertainty = round(entropy, 4)
    return {
        "predicted_prob": round(prob, 4),
        "logit": round(logit, 3),
        "uncertainty_entropy": uncertainty,
        "is_confident": (uncertainty < 0.65 and (prob >= 0.80 or prob <= 0.20))
    }


class PredictRequest(BaseModel):
    action_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    life_area: str = "personal"
    daily_count: int = 0


class FeedbackRequest(BaseModel):
    action_type: str
    approved: bool
    features: list[float] | None = None
    learning_rate: float = 0.15


@router.post("/predict")
def predict_action_approval(body: PredictRequest):
    """Predict whether the user will approve a proposed action in the given context."""
    features = extract_features(body.action_type, body.payload, body.life_area, body.daily_count)
    pred = predict_approval(features)
    return {**pred, "features": features, "action_type": body.action_type}


@router.post("/feedback")
def update_preference_model(body: FeedbackRequest):
    """Online Bayesian gradient update on user approval feedback."""
    features = body.features or extract_features(body.action_type, {})
    weights = get_preference_weights()
    logit = sum(w * f for w, f in zip(weights, features))
    pred = sigmoid(logit)
    target = 1.0 if body.approved else 0.0
    error = target - pred

    # Gradient update with L2 regularization
    l2_reg = 0.01
    updated_weights = [
        round(w + body.learning_rate * (error * f - l2_reg * w), 5)
        for w, f in zip(weights, features)
    ]
    save_preference_weights(updated_weights)

    return {
        "updated": True,
        "prediction_error": round(error, 4),
        "previous_weights": weights,
        "new_weights": updated_weights
    }


FEATURE_NAMES = [
    "Risk Score",
    "Reversible",
    "Work Life Area",
    "Late Hour (21:00-07:00)",
    "External Write",
    "Daily Volume Ratio",
    "Entity Familiarity",
    "Base Bias",
]


@router.get("/status")
def get_preference_model_status():
    """Return model parameters, Bayesian weights, feature names, and uncertainty stats."""
    weights = get_preference_weights()
    queries = get_active_learning_queries()["active_queries"]
    with connect() as db:
        decisions_count = db.execute("SELECT COUNT(*) as c FROM actions WHERE status IN ('completed', 'rejected')").fetchone()["c"]
    return {
        "model_type": "Online Bayesian Logistic Regression",
        "weights": weights,
        "feature_names": FEATURE_NAMES,
        "active_queries_count": len(queries),
        "total_decisions_observed": decisions_count,
        "entropy_threshold": 0.70,
    }


@router.get("/active_queries")
def get_active_learning_queries():
    """Identify actions with maximal epistemic uncertainty to query the user strategically."""
    actions = ["create_reminder", "draft_reply", "calendar_export"]
    queries = []
    for act in actions:
        feats = extract_features(act, {}, life_area="work")
        pred = predict_approval(feats)
        if pred["uncertainty_entropy"] > 0.70:
            queries.append({
                "action_type": act,
                "question": f"When receiving requests in your work area, would you prefer Threadline to automatically prepare a {act.replace('_', ' ')}?",
                "entropy": pred["uncertainty_entropy"],
                "predicted_prob": pred["predicted_prob"]
            })
    return {"active_queries": queries, "count": len(queries)}
