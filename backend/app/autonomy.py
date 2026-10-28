import math


Z_95 = 1.96
MIN_SHADOW_SAMPLES = 40
TARGET_WILSON_LOWER_BOUND = 0.80


def wilson_lower_bound(successes: int, samples: int, z: float = Z_95) -> float | None:
    """Return the 95% Wilson lower confidence bound for a Bernoulli rate."""
    if samples <= 0:
        return None
    rate = successes / samples
    z2 = z * z
    denominator = 1 + z2 / samples
    center = rate + z2 / (2 * samples)
    margin = z * math.sqrt((rate * (1 - rate) + z2 / (4 * samples)) / samples)
    return max(0.0, (center - margin) / denominator)


def shadow_summary(successes: int, samples: int) -> dict:
    bound = wilson_lower_bound(successes, samples)
    accuracy = successes / samples if samples else None
    remaining = max(0, MIN_SHADOW_SAMPLES - samples)
    promoted = samples >= MIN_SHADOW_SAMPLES and bound is not None and bound >= TARGET_WILSON_LOWER_BOUND
    return {
        "shadow_samples": samples,
        "shadow_agreements": successes,
        "shadow_accuracy": accuracy,
        "wilson_lower_95": bound,
        "samples_to_minimum": remaining,
        "promotion_suggested": promoted,
        "promotion_target": TARGET_WILSON_LOWER_BOUND,
    }


def shadow_prediction(approved: int, rejected: int, minimum_history: int = 5) -> bool | None:
    """Abstain until this action type has enough decisions to form a baseline."""
    if approved + rejected < minimum_history:
        return None
    return approved >= rejected
