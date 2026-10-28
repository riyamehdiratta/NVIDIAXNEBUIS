import re


TIME_RANGE = re.compile(r"\b(\d{1,2}:\d{2})\s*(?:to|until|[-–])\s*(\d{1,2}:\d{2})\b", re.I)
SCOPES = {"all_auto", "create_reminder", "draft_reply", "calendar_export"}


def _minutes(value: str) -> int:
    hour, minute = (int(part) for part in value.split(":"))
    if hour > 23 or minute > 59:
        raise ValueError("Use 24-hour times from 00:00 to 23:59")
    return hour * 60 + minute


def is_quiet(start: str, end: str, minute_of_day: int) -> bool:
    first, last = _minutes(start), _minutes(end)
    if first < last:
        return first <= minute_of_day < last
    return minute_of_day >= first or minute_of_day < last


def compile_quiet_hours(statement: str, scope: str) -> dict:
    if scope not in SCOPES:
        raise ValueError("Choose a supported action scope")
    if not re.search(r"\b(?:no|never|block|avoid|don't|do not)\b", statement, re.I):
        raise ValueError("State the boundary plainly, for example: 'No automatic actions from 22:00 to 07:00.'")
    if not re.search(r"\b(?:automatic|auto|actions?|reminders?|drafts?|calendar)\b", statement, re.I):
        raise ValueError("The statement must identify which automatic actions it limits")
    hit = TIME_RANGE.search(statement)
    if not hit:
        raise ValueError("Include a time range such as 22:00 to 07:00")
    start, end = hit.groups()
    first, last = _minutes(start), _minutes(end)
    if first == last:
        raise ValueError("Start and end cannot be the same time")
    span = (last - first) % 1440
    samples = {"at_start": first, "inside": (first + max(1, span // 2)) % 1440,
               "before_end": (last - 1) % 1440, "at_end": last, "after_end": (last + 60) % 1440}
    red_team = {name: {"time": f"{minute // 60:02d}:{minute % 60:02d}", "blocked": is_quiet(start, end, minute)} for name, minute in samples.items()}
    expected = {"at_start": True, "inside": True, "before_end": True, "at_end": False, "after_end": False}
    red_team_passed = all(red_team[name]["blocked"] == value for name, value in expected.items())
    if not red_team_passed:
        raise ValueError("The rule failed its boundary checks. Change the time range and try again.")
    return {"start": start, "end": end, "scope": scope, "red_team": red_team, "red_team_passed": red_team_passed}
