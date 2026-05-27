import json
from pathlib import Path
import pytest
from scripts.schema import validate_seen_scholarships, ValidationError

FIXTURES = Path(__file__).parent / "fixtures"


def test_empty_state_validates():
    data = json.loads((FIXTURES / "seen-scholarships-empty.json").read_text())
    validate_seen_scholarships(data)  # no exception


def test_populated_state_validates():
    data = json.loads((FIXTURES / "seen-scholarships-populated.json").read_text())
    validate_seen_scholarships(data)  # no exception


def test_missing_version_raises():
    with pytest.raises(ValidationError, match="version"):
        validate_seen_scholarships({"entries": []})


def test_wrong_version_raises():
    with pytest.raises(ValidationError, match="version"):
        validate_seen_scholarships({"version": 2, "entries": []})


def test_entry_missing_required_field_raises():
    bad = {
        "version": 1,
        "last_run_iso": None,
        "entries": [{"id": "x"}],  # missing title, sponsor, etc.
    }
    with pytest.raises(ValidationError, match="title"):
        validate_seen_scholarships(bad)


def test_entry_bad_deadline_format_raises():
    bad = {
        "version": 1,
        "last_run_iso": None,
        "entries": [{
            "id": "x", "title": "T", "sponsor": "S",
            "deadline": "September 15, 2026",  # not ISO
            "award_usd": 100, "essay_required": False,
            "interview_required": False,
            "source_message_id": "<m@x>",
            "application_url": "https://x",
            "first_seen": "2026-05-26T16:00:00Z",
            "match_status": "NEW",
            "fit": 50, "odds": 50, "effort": 50,
            "expired_flag": False,
            "deadline_reminder_surfaced": False,
        }],
    }
    with pytest.raises(ValidationError, match="deadline"):
        validate_seen_scholarships(bad)
