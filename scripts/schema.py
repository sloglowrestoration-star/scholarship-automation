"""Schema validator for state/seen-scholarships.json."""
from __future__ import annotations
import re
from typing import Any

SCHEMA_VERSION = 1
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISO_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

REQUIRED_ENTRY_FIELDS = {
    "id": str,
    "title": str,
    "sponsor": str,
    "deadline": str,
    "award_usd": (int, type(None)),
    "essay_required": bool,
    "interview_required": bool,
    "source_message_id": str,
    "application_url": str,
    "first_seen": str,
    "match_status": str,
    "fit": int,
    "odds": int,
    "effort": int,
    "expired_flag": bool,
    "deadline_reminder_surfaced": bool,
}


class ValidationError(ValueError):
    pass


def validate_seen_scholarships(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValidationError("root must be an object")
    if data.get("version") != SCHEMA_VERSION:
        raise ValidationError(f"version must be {SCHEMA_VERSION}")
    if "entries" not in data or not isinstance(data["entries"], list):
        raise ValidationError("entries must be a list")
    last_run = data.get("last_run_iso")
    if last_run is not None and not _ISO_DATETIME.match(last_run):
        raise ValidationError("last_run_iso must be ISO datetime or null")
    for i, entry in enumerate(data["entries"]):
        _validate_entry(entry, i)


def _validate_entry(entry: Any, idx: int) -> None:
    if not isinstance(entry, dict):
        raise ValidationError(f"entry[{idx}] must be an object")
    for field, expected_type in REQUIRED_ENTRY_FIELDS.items():
        if field not in entry:
            raise ValidationError(f"entry[{idx}] missing field: {field}")
        if not isinstance(entry[field], expected_type):
            raise ValidationError(
                f"entry[{idx}].{field} wrong type: "
                f"expected {expected_type}, got {type(entry[field])}"
            )
    if not _ISO_DATE.match(entry["deadline"]):
        raise ValidationError(
            f"entry[{idx}].deadline must be YYYY-MM-DD, got {entry['deadline']}"
        )
    if not _ISO_DATETIME.match(entry["first_seen"]):
        raise ValidationError(
            f"entry[{idx}].first_seen must be ISO datetime"
        )
