import hashlib
import re


SIGNALS = [
    ("authority_threat", 24, re.compile(r"\b(?:digital arrest|arrest warrant|police|cbi|customs officer|court case|law enforcement)\b", re.I), "Claims of police, legal, or government authority"),
    ("urgent_deadline", 16, re.compile(r"\b(?:immediately|right now|within \d+ minutes|last warning|account (?:will be )?(?:blocked|suspended)|act now|urgent)\b", re.I), "Pressure to act before you can verify"),
    ("credential_request", 30, re.compile(r"\b(?:otp|one[- ]time password|password|pin|cvv|verification code|login code)\b", re.I), "Requests or references to authentication secrets"),
    ("money_transfer", 26, re.compile(r"\b(?:transfer|wire|upi|gift card|crypto(?:currency)?|pay a fee|send money|bank account|wallet)\b", re.I), "Money movement or payment instrument mentioned"),
    ("remote_access", 25, re.compile(r"\b(?:install|download|screen share|remote access|anydesk|teamviewer|apk|allow access)\b", re.I), "Requests to install software or grant device access"),
    ("secrecy_pressure", 14, re.compile(r"\b(?:do not tell|don't tell|keep this secret|stay on the line|don't hang up|do not contact your bank)\b", re.I), "Attempts to isolate you from independent advice"),
    ("shortened_link", 18, re.compile(r"\b(?:https?://)?(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|cutt\.ly)/\S+", re.I), "A shortened link obscures its final destination"),
]


def inspect_message(message: str) -> dict:
    hits = []
    raw_score = 0
    for signal_id, weight, pattern, label in SIGNALS:
        if pattern.search(message):
            hits.append({"id": signal_id, "label": label, "weight": weight})
            raw_score += weight
    score = min(100, raw_score)
    band = "high concern" if score >= 50 else "caution" if score >= 20 else "few signals found"
    advice = ["Pause before replying, clicking, installing anything, or sending money.",
              "Contact the organization or person through a number or app you already trust.",
              "Never share an OTP, password, PIN, or remote-control access with an unsolicited caller."]
    return {"score": score, "band": band, "signals": hits, "advice": advice,
            "message_digest": hashlib.sha256(message.encode("utf-8", errors="replace")).hexdigest(),
            "message_length": len(message)}
