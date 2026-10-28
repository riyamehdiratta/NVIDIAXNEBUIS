from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
import re


def _decode(v):
    if not v:
        return ""
    try:
        return str(v)
    except Exception:
        return ""


def parse_source(filename: str, raw: bytes) -> tuple[str, str, str]:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"
    if suffix == "eml":
        msg = BytesParser(policy=policy.default).parsebytes(raw)
        chunks = [f"Subject: {_decode(msg.get('subject'))}", f"From: {_decode(msg.get('from'))}", f"Date: {_decode(msg.get('date'))}"]
        body = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and not part.get_filename():
                    try:
                        body.append(part.get_content())
                    except Exception:
                        pass
        elif msg.get_content_type() == "text/plain":
            try:
                body.append(msg.get_content())
            except Exception:
                pass
        chunks.extend(body or ["(No plain-text body found.)"])
        title = _decode(msg.get("subject")) or filename
        return "email", title, "\n".join(x for x in chunks if x)
    if suffix == "ics":
        text = raw.decode("utf-8", errors="replace").replace("\r\n ", "").replace("\n ", "")
        events = []
        for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, flags=re.S | re.I):
            fields = {}
            for line in block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fields[k.split(";", 1)[0].upper()] = v.replace("\\n", " ").replace("\\,", ",")
            start = fields.get("DTSTART", "")
            if re.fullmatch(r"\d{8}", start):
                start = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
            elif re.fullmatch(r"\d{8}T\d{6}Z?", start):
                start = f"{start[:4]}-{start[4:6]}-{start[6:8]} {start[9:11]}:{start[11:13]}"
            events.append(" | ".join(filter(None, [fields.get("SUMMARY", "Calendar event"), f"When: {start}" if start else "", f"Where: {fields.get('LOCATION', '')}" if fields.get("LOCATION") else "", fields.get("DESCRIPTION", "")])))
        title = f"Calendar import · {len(events)} event{'s' if len(events) != 1 else ''}"
        return "calendar", title, "\n".join(events) if events else text
    if suffix not in {"txt", "md", "csv", "log"}:
        raise ValueError("Supported input types are .txt, .md, .csv, .log, .eml, and .ics")
    text = raw.decode("utf-8-sig", errors="replace")
    return "note", filename, text
