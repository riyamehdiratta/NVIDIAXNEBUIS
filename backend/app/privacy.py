import re


PATTERNS = [
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("phone", re.compile(r"(?<!\w)(?:\+?\d[\d .()/-]{7,}\d)(?!\w)")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("long-number", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
]


def redact(text: str):
    counts = {}
    result = text
    for label, pattern in PATTERNS:
        def replace(match):
            counts[label] = counts.get(label, 0) + 1
            return f"[{label.upper()}_{counts[label]}]"
        result = pattern.sub(replace, result)
    return result, sum(counts.values()), counts
