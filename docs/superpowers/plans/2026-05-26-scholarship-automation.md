# Scholarship Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude-Code-as-runtime scheduled agent that emails Brody (imajedimastr@gmail.com) a daily 9am Pacific digest of new scholarships found in Gmail, scored on Fit/Odds/Effort, matched against Drive-stored essays, with outlines for new essays and inlined deadline reminders.

**Architecture:** The "agent" is a Claude Code session triggered by a scheduled-tasks MCP cron. The session reads `workflow.md` and executes nine pipeline stages, calling local Python helpers for deterministic plumbing (IMAP fetch, SMTP send, GitHub state push, schema validation) and using its own LLM ability for parse / score / match / outline. State persists to GitHub via the Contents API. The repo mirrors the proven internship-automation layout.

**Tech Stack:** Python 3.11+, stdlib `imaplib` + `email`, `smtplib`, `requests` for GitHub API, `python-dotenv`, `pytest`, Google Drive MCP (inside the agent session), scheduled-tasks MCP for the trigger.

---

## File Structure

```
scholarship-automation/
├── .env                          # gitignored, real credentials
├── .env.example                  # committed, template only
├── .gitignore
├── README.md
├── requirements.txt
├── user-profile.md               # already committed — Brody's profile for Fit scoring
├── workflow.md                   # THE main artifact: agent's run-book
├── config/
│   ├── filters.md                # Gmail sender domains + skip-keywords
│   └── sources.md                # human-readable list of scholarship sources
├── state/
│   ├── seen-scholarships.json    # committed; updated each run
│   └── run-log.md                # committed; appended each run
├── templates/
│   ├── email-digest.txt          # plain-text email shape
│   ├── parse-prompt.md           # how the agent parses emails into records
│   ├── score-rubric.md           # Fit / Odds / Effort scoring guide
│   ├── match-prompt.md           # how the agent matches prompts to essays
│   └── outline-prompt.md         # how the agent writes outlines for NEW essays
├── scripts/
│   ├── imap_fetch.py             # pulls labeled messages → JSON stdout
│   ├── send_digest.py            # accepts JSON of digest → sends SMTP
│   ├── persist_state.py          # commits state files back to GitHub
│   └── schema.py                 # validates seen-scholarships.json shape
├── tests/
│   ├── conftest.py
│   ├── test_imap_fetch.py
│   ├── test_send_digest.py
│   ├── test_persist_state.py
│   ├── test_schema.py
│   └── fixtures/
│       ├── emails/               # sample .eml messages from each source
│       ├── seen-scholarships-empty.json
│       └── seen-scholarships-populated.json
└── docs/superpowers/
    ├── specs/2026-05-26-scholarship-automation-design.md  # already exists
    └── plans/2026-05-26-scholarship-automation.md         # this file
```

**Boundary rationale:** Python helpers do *only* I/O and validation. All LLM-touched work (parsing, scoring, matching, outline generation) is done by the agent itself, guided by markdown prompt templates. This keeps Python testable with mocks and pure data, and keeps prompt iteration in plain markdown without code changes.

---

## Resolved open items from spec

| Spec deferral | Resolution |
|---|---|
| LLM choice for parse / match / outline | The agent (Claude Code session) does all three using its own model. No external API client needed. |
| `seen-scholarships.json` schema | Defined concretely in Task 4. |
| Initial Gmail filter sender list | scholarships.com, fastweb.com, goingmerry.com, bold.org, scholarshipowl.com, financialaid@calpoly.edu, mereps@calpoly.edu, plus broader `calpoly.edu` + "scholarship" subject catch-all. |
| Test strategy | Mock IMAP via stored .eml fixtures; mock SMTP via `unittest.mock`; mock GitHub Contents API via `requests-mock`. LLM stages are tested via golden-file inputs/outputs maintained in `tests/fixtures/`. |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `pytest.ini`

- [ ] **Step 1: Write `requirements.txt`**

```
python-dotenv>=1.0.0
requests>=2.31.0
pytest>=7.4.0
requests-mock>=1.11.0
```

- [ ] **Step 2: Write `.gitignore`**

```
# Credentials and local state
.env
.env.scratch
.env.scratch.txt

# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.venv/
venv/

# OS
.DS_Store
Thumbs.db

# Output scratch
out/
```

- [ ] **Step 3: Write `.env.example`**

```
# Inbox to scan for scholarship emails (read-only)
IMAJE_GMAIL_ADDRESS=imajedimastr@gmail.com
IMAJE_GMAIL_APP_PASSWORD=replace-with-app-password

# Sender (reuses internship-automation's brody.internships account)
SENDER_GMAIL_ADDRESS=brody.internships@gmail.com
SENDER_GMAIL_APP_PASSWORD=replace-with-app-password

# Digest recipient
DIGEST_RECIPIENT=imajedimastr@gmail.com

# GitHub Contents API for state persistence
GITHUB_PAT=replace-with-pat
GITHUB_REPO_OWNER=sloglowrestoration-star
GITHUB_REPO_NAME=scholarship-automation
GITHUB_BRANCH=main

# Google Drive folder containing essays + essays-index.md
DRIVE_ESSAYS_FOLDER_ID=replace-with-folder-id

# Gmail label to scan
SCHOLARSHIP_LABEL=Scholarships
```

- [ ] **Step 4: Write `README.md`**

```markdown
# scholarship-automation

Daily 9am Pacific email digest of new scholarships found in imajedimastr@gmail.com.
Scores Fit/Odds/Effort, matches prompts against an essay library in Google Drive,
generates starter outlines for new essays, and inlines deadline reminders.

## How to run manually

    python -m scripts.imap_fetch   # pulls new labeled messages as JSON
    # (the Claude agent does parse/score/match/outline using workflow.md)
    python -m scripts.send_digest  # sends the assembled digest
    python -m scripts.persist_state  # commits updated state back to GitHub

## Scheduled run

A scheduled-tasks MCP cron triggers a Claude Code session daily at 9am Pacific
(`0 16 * * *` UTC). That session reads `workflow.md` and executes the pipeline.

## Files

- `workflow.md` — the agent's run-book (THE main artifact)
- `user-profile.md` — Brody's eligibility profile (Fit scoring input)
- `config/filters.md` — Gmail filter senders + skip-keywords
- `config/sources.md` — documented scholarship sources
- `state/seen-scholarships.json` — dedup + deadline-reminder source of truth
- `state/run-log.md` — append-only run log
- `templates/` — LLM prompt templates and email shape
- `scripts/` — Python plumbing (IMAP, SMTP, GitHub state, schema)
- `tests/` — pytest tests for the Python helpers

See `docs/superpowers/specs/2026-05-26-scholarship-automation-design.md` for the design rationale.
```

- [ ] **Step 5: Write `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .gitignore .env.example README.md pytest.ini
git commit -m "chore: project scaffolding (deps, gitignore, env template, README, pytest)"
```

---

## Task 2: Wire Credentials Into Real `.env`

**Files:**
- Create: `.env` (will be gitignored)
- Modify: `.env.scratch` (will be deleted after extraction)

- [ ] **Step 1: Verify `.gitignore` excludes `.env`**

```bash
grep -E "^\.env$" .gitignore && echo OK
```
Expected output: `.env\nOK`

- [ ] **Step 2: Inspect `.env.scratch` to get IMAJE password and Drive folder ID**

```bash
cat .env.scratch
```
Expected: two lines with `IMAJE_GMAIL_APP_PASSWORD=...` and `DRIVE_ESSAYS_FOLDER_ID=...`

- [ ] **Step 3: Inspect internship-automation `.env` to get SMTP credentials and GitHub PAT**

```bash
grep -E "^(GMAIL_APP_PASSWORD|GITHUB_PAT)=" "../internship-automation/.env"
```
Expected: the SMTP app password for brody.internships@gmail.com and the GitHub PAT.

- [ ] **Step 4: Write `.env`**

Compose `.env` from `.env.example` shape, filling in the real values:
- `IMAJE_GMAIL_APP_PASSWORD` from `.env.scratch`
- `SENDER_GMAIL_APP_PASSWORD` from `internship-automation/.env`'s `GMAIL_APP_PASSWORD`
- `GITHUB_PAT` from `internship-automation/.env`
- `DRIVE_ESSAYS_FOLDER_ID` from `.env.scratch`
- All other fields keep their defaults from `.env.example`

- [ ] **Step 5: Verify `.env` is correctly populated (no placeholders)**

```bash
grep -c "replace-with" .env
```
Expected: `0`

- [ ] **Step 6: Delete `.env.scratch`**

```bash
rm .env.scratch
```

- [ ] **Step 7: Confirm `.env` is not staged**

```bash
git status --porcelain | grep -E "^\?\? \.env$" && echo "untracked-OK"
git ls-files --error-unmatch .env 2>&1 | grep -q "did not match" && echo "not-tracked-OK"
```
Both checks should pass.

- [ ] **Step 8: Commit (only `.env.scratch` deletion if any tracked; nothing else)**

There's nothing new to commit at this point — `.env` is gitignored. Skip commit.

---

## Task 3: Config Files

**Files:**
- Create: `config/filters.md`
- Create: `config/sources.md`

- [ ] **Step 1: Write `config/filters.md`**

```markdown
# Gmail Filter Configuration

The Gmail label `Scholarships` is auto-applied to messages matching these filters.
The agent's IMAP fetch (`scripts/imap_fetch.py`) reads only messages with this label.

## Sender-domain filters

Any message from these senders gets the `Scholarships` label:

| Sender | Notes |
|---|---|
| `scholarships.com` | Generic aggregator newsletter |
| `fastweb.com` | Aggregator |
| `goingmerry.com` | Aggregator |
| `bold.org` | Aggregator + direct opportunities |
| `scholarshipowl.com` | Aggregator |
| `financialaid@calpoly.edu` | Cal Poly Financial Aid announcements |
| `mereps@calpoly.edu` | Mechanical Engineering department listserv |

## Subject + sender catch-all

Any message where the `From:` contains `calpoly.edu` AND the subject contains
the word `scholarship` (case-insensitive) gets the label.

## Skip-keywords (agent-side filter)

After parsing, the agent drops any extracted scholarship matching:

- Subject lines containing `unsubscribe`, `manage preferences`, `marketing preferences`
- Records where the application URL points to a survey or feedback form
- Records with no extractable deadline AND no extractable award amount
  (these are almost always promotional content, not actual scholarships)

## Tuning policy

After the first week of digests, review false positives (irrelevant senders
getting through) and false negatives (scholarships you saw in Gmail that didn't
appear in the digest). Update this file. The agent re-reads it each run, so no
code change needed.
```

- [ ] **Step 2: Write `config/sources.md`**

```markdown
# Scholarship Sources

Documents the channels imaje uses to discover scholarships, so the agent and
human can both reason about coverage.

## Active sources (in scope for v1)

| Source | Channel | Coverage |
|---|---|---|
| Scholarships.com | Email newsletter | Broad, US-wide |
| Fastweb | Email newsletter | Broad, US-wide |
| Going Merry | Email newsletter | Broad, US-wide |
| Bold.org | Email newsletter + direct | Broad, niche-friendly |
| ScholarshipOwl | Email newsletter | Broad, US-wide |
| Cal Poly Financial Aid | Email announcements | Cal-Poly-specific |
| Cal Poly ME Department | Email listserv | ME-major-specific |

## Deliberately out of scope

- Web scraping any of the above (we already get the same content via email)
- Reddit / r/Scholarships (signal-to-noise too low for v1)
- Twitter/X scholarship accounts (same)
- LinkedIn (no scholarship discovery channel there)

## Future-add candidates

- Energy-industry-specific newsletters (ASES, SEIA, AWEA student awards) once
  imaje subscribes
- ASME student scholarships (department-affiliated, look up after Cal Poly
  residency switches to CA)
```

- [ ] **Step 3: Commit**

```bash
git add config/
git commit -m "feat(config): initial filters and sources documentation"
```

---

## Task 4: Schema Module + Tests

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/schema.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_schema.py`
- Create: `tests/fixtures/seen-scholarships-empty.json`
- Create: `tests/fixtures/seen-scholarships-populated.json`

- [ ] **Step 1: Create empty `__init__.py` files**

```bash
touch scripts/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write fixture `tests/fixtures/seen-scholarships-empty.json`**

```json
{
  "version": 1,
  "last_run_iso": null,
  "entries": []
}
```

- [ ] **Step 3: Write fixture `tests/fixtures/seen-scholarships-populated.json`**

```json
{
  "version": 1,
  "last_run_iso": "2026-05-26T16:00:00Z",
  "entries": [
    {
      "id": "abc123",
      "title": "Future Engineers of America Scholarship",
      "sponsor": "FEA Foundation",
      "deadline": "2026-09-15",
      "award_usd": 5000,
      "essay_required": true,
      "interview_required": false,
      "source_message_id": "<msg-1@scholarships.com>",
      "application_url": "https://scholarships.com/feoa",
      "first_seen": "2026-05-26T16:00:00Z",
      "match_status": "NEW",
      "fit": 78,
      "odds": 55,
      "effort": 60,
      "expired_flag": false,
      "deadline_reminder_surfaced": false
    }
  ]
}
```

- [ ] **Step 4: Write the failing test `tests/test_schema.py`**

```python
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
```

- [ ] **Step 5: Run test to verify it fails**

```bash
pytest tests/test_schema.py -v
```
Expected: ImportError for `scripts.schema`.

- [ ] **Step 6: Write minimal `scripts/schema.py`**

```python
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
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest tests/test_schema.py -v
```
Expected: 6 passed.

- [ ] **Step 8: Commit**

```bash
git add scripts/__init__.py scripts/schema.py tests/__init__.py tests/test_schema.py tests/fixtures/
git commit -m "feat(schema): seen-scholarships.json validator with tests"
```

---

## Task 5: IMAP Fetch Module + Tests

**Files:**
- Create: `scripts/imap_fetch.py`
- Create: `tests/test_imap_fetch.py`
- Create: `tests/fixtures/emails/scholarships_com_sample.eml`
- Create: `tests/fixtures/emails/fastweb_sample.eml`
- Create: `tests/fixtures/emails/calpoly_listserv_sample.eml`

- [ ] **Step 1: Create three minimal `.eml` fixtures**

Write `tests/fixtures/emails/scholarships_com_sample.eml`:

```
Message-ID: <msg-001@scholarships.com>
From: Scholarships.com <newsletter@scholarships.com>
To: imajedimastr@gmail.com
Subject: 5 New Scholarships This Week
Date: Tue, 26 May 2026 08:00:00 -0700
Content-Type: text/plain; charset=UTF-8

Hi Brody,

This week's new scholarships:

1. Future Engineers of America Scholarship
   Deadline: September 15, 2026
   Award: $5,000
   Apply: https://scholarships.com/feoa

2. Renewable Energy Future Scholarship
   Deadline: August 30, 2026
   Award: $2,500
   Apply: https://scholarships.com/refs

--
Scholarships.com - Manage preferences: https://scholarships.com/prefs
```

Write `tests/fixtures/emails/fastweb_sample.eml`:

```
Message-ID: <msg-002@fastweb.com>
From: Fastweb <alerts@fastweb.com>
To: imajedimastr@gmail.com
Subject: Daily Scholarship Match
Date: Tue, 26 May 2026 09:15:00 -0700
Content-Type: text/plain; charset=UTF-8

Mechanical Engineering Student Award
Award: $1,000
Deadline: 2026-07-01
Sponsor: ASME Foundation
Essay required: 500 words on "Why renewable energy?"
Apply: https://fastweb.com/asme-student

--
Fastweb
```

Write `tests/fixtures/emails/calpoly_listserv_sample.eml`:

```
Message-ID: <msg-003@calpoly.edu>
From: ME Department <mereps@calpoly.edu>
To: me-students@lists.calpoly.edu
Subject: Cal Poly ME Scholarship Application Open
Date: Wed, 27 May 2026 10:30:00 -0700
Content-Type: text/plain; charset=UTF-8

Mechanical Engineering students,

Applications are open for the 2026-2027 ME Department Scholarship.

Eligibility: ME majors, sophomore standing or above, 3.0+ GPA
Award: Varies, $500-$3,000
Deadline: June 30, 2026
No essay required, 1-page application form.

Apply at: https://me.calpoly.edu/scholarships/2026

Dr. Smith
ME Department
```

- [ ] **Step 2: Write the failing test `tests/test_imap_fetch.py`**

```python
"""Tests for imap_fetch — fetching labeled messages from Gmail via IMAP.

We stub imaplib at the module level so no network call is made.
"""
from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from scripts import imap_fetch

FIXTURES = Path(__file__).parent / "fixtures" / "emails"


def _fake_imap_with_messages(eml_paths):
    """Build a MagicMock IMAP4_SSL connection that returns the given .eml fixtures."""
    mock_imap = MagicMock()
    mock_imap.login.return_value = ("OK", [b"Logged in"])
    mock_imap.select.return_value = ("OK", [b"3"])
    # search returns message numbers as a space-separated bytestring
    ids = b" ".join(str(i + 1).encode() for i in range(len(eml_paths)))
    mock_imap.search.return_value = ("OK", [ids])
    # fetch returns the .eml content for each message
    def fake_fetch(msg_id, _spec):
        idx = int(msg_id) - 1
        body = eml_paths[idx].read_bytes()
        return ("OK", [(b"header", body)])
    mock_imap.fetch.side_effect = fake_fetch
    mock_imap.logout.return_value = ("BYE", [b"Logging out"])
    return mock_imap


def test_fetch_returns_records_for_each_eml():
    eml_paths = [
        FIXTURES / "scholarships_com_sample.eml",
        FIXTURES / "fastweb_sample.eml",
        FIXTURES / "calpoly_listserv_sample.eml",
    ]
    fake = _fake_imap_with_messages(eml_paths)
    with patch.object(imap_fetch.imaplib, "IMAP4_SSL", return_value=fake):
        results = imap_fetch.fetch_labeled_messages(
            address="imajedimastr@gmail.com",
            app_password="dummy",
            label="Scholarships",
            since_iso=None,
        )
    assert len(results) == 3
    assert results[0]["message_id"] == "<msg-001@scholarships.com>"
    assert results[1]["message_id"] == "<msg-002@fastweb.com>"
    assert results[2]["message_id"] == "<msg-003@calpoly.edu>"
    assert "Future Engineers of America" in results[0]["body"]


def test_fetch_uses_since_filter_when_provided():
    fake = _fake_imap_with_messages([])
    with patch.object(imap_fetch.imaplib, "IMAP4_SSL", return_value=fake):
        imap_fetch.fetch_labeled_messages(
            address="imajedimastr@gmail.com",
            app_password="dummy",
            label="Scholarships",
            since_iso="2026-05-25T00:00:00Z",
        )
    # search was called with a SINCE criterion
    search_args = fake.search.call_args[0]
    assert any("SINCE" in str(a) for a in search_args)


def test_fetch_returns_empty_list_when_no_messages():
    fake = MagicMock()
    fake.login.return_value = ("OK", [b""])
    fake.select.return_value = ("OK", [b"0"])
    fake.search.return_value = ("OK", [b""])  # empty
    fake.logout.return_value = ("BYE", [b""])
    with patch.object(imap_fetch.imaplib, "IMAP4_SSL", return_value=fake):
        results = imap_fetch.fetch_labeled_messages(
            address="imajedimastr@gmail.com",
            app_password="dummy",
            label="Scholarships",
            since_iso=None,
        )
    assert results == []


def test_fetch_records_have_required_fields():
    eml_paths = [FIXTURES / "scholarships_com_sample.eml"]
    fake = _fake_imap_with_messages(eml_paths)
    with patch.object(imap_fetch.imaplib, "IMAP4_SSL", return_value=fake):
        results = imap_fetch.fetch_labeled_messages(
            address="imajedimastr@gmail.com",
            app_password="dummy",
            label="Scholarships",
            since_iso=None,
        )
    record = results[0]
    for field in ("message_id", "sender", "subject", "date", "body"):
        assert field in record, f"missing {field}"
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/test_imap_fetch.py -v
```
Expected: ImportError for `scripts.imap_fetch`.

- [ ] **Step 4: Write `scripts/imap_fetch.py`**

```python
"""Fetch Gmail messages with a given label via IMAP.

Outputs a list of records:
    {message_id, sender, subject, date, body}
"""
from __future__ import annotations
import email
import imaplib
import json
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any


def fetch_labeled_messages(
    *,
    address: str,
    app_password: str,
    label: str,
    since_iso: str | None,
) -> list[dict[str, Any]]:
    """Connect to Gmail IMAP, select the label, return all messages as records."""
    conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    try:
        conn.login(address, app_password)
        # Gmail exposes labels as IMAP folders
        conn.select(f'"{label}"', readonly=True)
        search_args: list[str] = ["ALL"]
        if since_iso:
            since_date = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
            search_args = ["SINCE", since_date.strftime("%d-%b-%Y")]
        status, data = conn.search(None, *search_args)
        if status != "OK" or not data or not data[0]:
            return []
        msg_ids = data[0].split()
        records: list[dict[str, Any]] = []
        for msg_id in msg_ids:
            status, msg_data = conn.fetch(msg_id, "(RFC822)")
            if status != "OK" or not msg_data:
                continue
            raw = msg_data[0][1]
            records.append(_parse_eml(raw))
        return records
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def _parse_eml(raw_bytes: bytes) -> dict[str, Any]:
    msg = email.message_from_bytes(raw_bytes)
    body = _extract_text_body(msg)
    date_hdr = msg.get("Date", "")
    try:
        date_iso = parsedate_to_datetime(date_hdr).isoformat()
    except Exception:
        date_iso = date_hdr
    return {
        "message_id": msg.get("Message-ID", "").strip(),
        "sender": msg.get("From", "").strip(),
        "subject": msg.get("Subject", "").strip(),
        "date": date_iso,
        "body": body,
    }


def _extract_text_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    if not payload:
        return ""
    return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")


def main() -> int:
    """CLI entry — reads creds from env and prints JSON list to stdout."""
    from dotenv import load_dotenv
    import os
    load_dotenv()
    records = fetch_labeled_messages(
        address=os.environ["IMAJE_GMAIL_ADDRESS"],
        app_password=os.environ["IMAJE_GMAIL_APP_PASSWORD"],
        label=os.environ.get("SCHOLARSHIP_LABEL", "Scholarships"),
        since_iso=os.environ.get("SINCE_ISO"),
    )
    json.dump(records, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_imap_fetch.py -v
```
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/imap_fetch.py tests/test_imap_fetch.py tests/fixtures/emails/
git commit -m "feat(imap): fetch labeled Gmail messages as JSON records"
```

---

## Task 6: Send Digest Module + Tests

**Files:**
- Create: `scripts/send_digest.py`
- Create: `tests/test_send_digest.py`

- [ ] **Step 1: Write the failing test `tests/test_send_digest.py`**

```python
from __future__ import annotations
from unittest.mock import MagicMock, patch
from scripts.send_digest import send_digest


def test_send_digest_calls_smtp_with_credentials_and_body():
    fake_smtp = MagicMock()
    fake_smtp_ctx = MagicMock()
    fake_smtp_ctx.__enter__.return_value = fake_smtp
    fake_smtp_ctx.__exit__.return_value = False
    with patch("scripts.send_digest.smtplib.SMTP_SSL", return_value=fake_smtp_ctx) as smtp_cls:
        send_digest(
            sender_address="brody.internships@gmail.com",
            sender_password="fake-app-password",
            recipient="imajedimastr@gmail.com",
            subject="Scholarship Digest — 2026-05-27",
            body_text="Hello world\n",
        )
    smtp_cls.assert_called_once_with("smtp.gmail.com", 465)
    fake_smtp.login.assert_called_once_with(
        "brody.internships@gmail.com", "fake-app-password"
    )
    fake_smtp.send_message.assert_called_once()
    sent_msg = fake_smtp.send_message.call_args[0][0]
    assert sent_msg["Subject"] == "Scholarship Digest — 2026-05-27"
    assert sent_msg["From"] == "brody.internships@gmail.com"
    assert sent_msg["To"] == "imajedimastr@gmail.com"
    assert "Hello world" in sent_msg.get_content()


def test_send_digest_handles_unicode_in_body():
    fake_smtp = MagicMock()
    fake_smtp_ctx = MagicMock()
    fake_smtp_ctx.__enter__.return_value = fake_smtp
    fake_smtp_ctx.__exit__.return_value = False
    with patch("scripts.send_digest.smtplib.SMTP_SSL", return_value=fake_smtp_ctx):
        send_digest(
            sender_address="x@example.com",
            sender_password="p",
            recipient="y@example.com",
            subject="Test — em dash",
            body_text="Body with em dash — and é accents\n",
        )
    sent_msg = fake_smtp.send_message.call_args[0][0]
    assert "em dash — and é" in sent_msg.get_content()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_send_digest.py -v
```
Expected: ImportError.

- [ ] **Step 3: Write `scripts/send_digest.py`**

```python
"""Send a plain-text digest email via Gmail SMTP."""
from __future__ import annotations
import smtplib
import sys
from email.message import EmailMessage


def send_digest(
    *,
    sender_address: str,
    sender_password: str,
    recipient: str,
    subject: str,
    body_text: str,
) -> None:
    msg = EmailMessage()
    msg["From"] = sender_address
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body_text, charset="utf-8")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_address, sender_password)
        smtp.send_message(msg)


def main() -> int:
    """CLI entry — reads body from a file path argv[1], subject from argv[2]."""
    from dotenv import load_dotenv
    import os
    load_dotenv()
    if len(sys.argv) < 3:
        print("usage: send_digest <body_file_path> <subject>", file=sys.stderr)
        return 2
    body_path, subject = sys.argv[1], sys.argv[2]
    with open(body_path, encoding="utf-8") as f:
        body = f.read()
    send_digest(
        sender_address=os.environ["SENDER_GMAIL_ADDRESS"],
        sender_password=os.environ["SENDER_GMAIL_APP_PASSWORD"],
        recipient=os.environ["DIGEST_RECIPIENT"],
        subject=subject,
        body_text=body,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_send_digest.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/send_digest.py tests/test_send_digest.py
git commit -m "feat(smtp): send plain-text digest via Gmail SSL SMTP"
```

---

## Task 7: Persist State Module + Tests

**Files:**
- Create: `scripts/persist_state.py`
- Create: `tests/test_persist_state.py`

- [ ] **Step 1: Write the failing test `tests/test_persist_state.py`**

```python
from __future__ import annotations
import base64
import json
import requests_mock
from scripts.persist_state import commit_state_files


def test_commit_writes_seen_scholarships_and_run_log():
    seen_data = {"version": 1, "last_run_iso": "2026-05-27T16:00:00Z", "entries": []}
    run_log_append = "\n## 2026-05-27\n- 0 new, 0 deadline reminders\n"
    with requests_mock.Mocker() as m:
        # GET current run-log.md (so we can append)
        m.get(
            "https://api.github.com/repos/owner/repo/contents/state/run-log.md",
            json={
                "sha": "existing-sha",
                "content": base64.b64encode(b"# Run log\n").decode(),
            },
        )
        # GET current seen-scholarships.json (returns 404 = first run)
        m.get(
            "https://api.github.com/repos/owner/repo/contents/state/seen-scholarships.json",
            status_code=404,
        )
        # PUT both files
        m.put(
            "https://api.github.com/repos/owner/repo/contents/state/seen-scholarships.json",
            json={"content": {"sha": "new-sha-1"}},
        )
        m.put(
            "https://api.github.com/repos/owner/repo/contents/state/run-log.md",
            json={"content": {"sha": "new-sha-2"}},
        )
        commit_state_files(
            pat="fake-pat",
            owner="owner",
            repo="repo",
            branch="main",
            seen_scholarships=seen_data,
            run_log_append=run_log_append,
        )
    # verify both PUTs happened
    put_history = [r for r in m.request_history if r.method == "PUT"]
    assert len(put_history) == 2
    # verify run-log PUT was an append (contains the prefix)
    run_log_put = next(
        r for r in put_history if "run-log.md" in r.url
    )
    body = json.loads(run_log_put.text)
    decoded = base64.b64decode(body["content"]).decode()
    assert decoded.startswith("# Run log\n")
    assert "2026-05-27" in decoded


def test_commit_handles_first_run_with_no_existing_run_log():
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.github.com/repos/owner/repo/contents/state/run-log.md",
            status_code=404,
        )
        m.get(
            "https://api.github.com/repos/owner/repo/contents/state/seen-scholarships.json",
            status_code=404,
        )
        m.put(
            "https://api.github.com/repos/owner/repo/contents/state/seen-scholarships.json",
            json={"content": {"sha": "x"}},
        )
        m.put(
            "https://api.github.com/repos/owner/repo/contents/state/run-log.md",
            json={"content": {"sha": "y"}},
        )
        commit_state_files(
            pat="fake-pat",
            owner="owner",
            repo="repo",
            branch="main",
            seen_scholarships={"version": 1, "last_run_iso": None, "entries": []},
            run_log_append="## 2026-05-27\n- first run\n",
        )
    put_history = [r for r in m.request_history if r.method == "PUT"]
    run_log_put = next(r for r in put_history if "run-log.md" in r.url)
    body = json.loads(run_log_put.text)
    decoded = base64.b64decode(body["content"]).decode()
    assert decoded.startswith("# Run log\n")  # header auto-added
    assert "first run" in decoded
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_persist_state.py -v
```
Expected: ImportError.

- [ ] **Step 3: Write `scripts/persist_state.py`**

```python
"""Commit updated state files back to GitHub via the Contents API."""
from __future__ import annotations
import base64
import json
import sys
from typing import Any
import requests

API_BASE = "https://api.github.com"
RUN_LOG_HEADER = "# Run log\n"


def commit_state_files(
    *,
    pat: str,
    owner: str,
    repo: str,
    branch: str,
    seen_scholarships: dict[str, Any],
    run_log_append: str,
) -> None:
    """Update state/seen-scholarships.json (full replace) and state/run-log.md (append)."""
    _put_file(
        pat=pat, owner=owner, repo=repo, branch=branch,
        path="state/seen-scholarships.json",
        new_content=json.dumps(seen_scholarships, indent=2) + "\n",
        commit_message="state: update seen-scholarships",
    )
    existing = _get_file_text(pat, owner, repo, "state/run-log.md")
    if existing is None:
        existing = RUN_LOG_HEADER
    elif not existing.endswith("\n"):
        existing += "\n"
    new_log = existing + run_log_append
    _put_file(
        pat=pat, owner=owner, repo=repo, branch=branch,
        path="state/run-log.md",
        new_content=new_log,
        commit_message="state: append run log",
    )


def _get_file_text(pat: str, owner: str, repo: str, path: str) -> str | None:
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_headers(pat), timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    payload = resp.json()
    return base64.b64decode(payload["content"]).decode("utf-8")


def _put_file(
    *, pat: str, owner: str, repo: str, branch: str,
    path: str, new_content: str, commit_message: str,
) -> None:
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    sha = _get_sha(pat, owner, repo, path)
    body: dict[str, Any] = {
        "message": commit_message,
        "branch": branch,
        "content": base64.b64encode(new_content.encode("utf-8")).decode("ascii"),
    }
    if sha is not None:
        body["sha"] = sha
    resp = requests.put(url, headers=_headers(pat), json=body, timeout=30)
    resp.raise_for_status()


def _get_sha(pat: str, owner: str, repo: str, path: str) -> str | None:
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_headers(pat), timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()["sha"]


def _headers(pat: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def main() -> int:
    """CLI entry — reads seen-scholarships.json from argv[1], run-log append from argv[2]."""
    from dotenv import load_dotenv
    import os
    load_dotenv()
    if len(sys.argv) < 3:
        print("usage: persist_state <seen_json_path> <run_log_append_path>", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        seen = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        append = f.read()
    commit_state_files(
        pat=os.environ["GITHUB_PAT"],
        owner=os.environ["GITHUB_REPO_OWNER"],
        repo=os.environ["GITHUB_REPO_NAME"],
        branch=os.environ.get("GITHUB_BRANCH", "main"),
        seen_scholarships=seen,
        run_log_append=append,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_persist_state.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/persist_state.py tests/test_persist_state.py
git commit -m "feat(state): commit seen-scholarships and run-log via GitHub Contents API"
```

---

## Task 8: Initial State Files

**Files:**
- Create: `state/seen-scholarships.json`
- Create: `state/run-log.md`

- [ ] **Step 1: Write initial empty state**

`state/seen-scholarships.json`:

```json
{
  "version": 1,
  "last_run_iso": null,
  "entries": []
}
```

`state/run-log.md`:

```markdown
# Run log
```

- [ ] **Step 2: Validate the initial state with schema module**

```bash
python -c "import json; from scripts.schema import validate_seen_scholarships; validate_seen_scholarships(json.load(open('state/seen-scholarships.json'))); print('OK')"
```
Expected output: `OK`

- [ ] **Step 3: Commit**

```bash
git add state/
git commit -m "feat(state): initial empty seen-scholarships and run-log"
```

---

## Task 9: Parse Prompt Template

**Files:**
- Create: `templates/parse-prompt.md`

- [ ] **Step 1: Write `templates/parse-prompt.md`**

```markdown
# Email-to-Scholarship-Records Parsing Prompt

You are given the body of an email that may contain one or more scholarship listings. Your job is to extract each distinct scholarship as a structured record.

## Input

A single email body (plain text) plus its metadata:
- `message_id` (string)
- `sender` (string)
- `subject` (string)
- `date` (ISO datetime)

## Output

A JSON array. One object per distinct scholarship. If the email contains no extractable scholarship (e.g. it's a marketing email, a survey, an account notification), return `[]`.

Each record has these fields:

```json
{
  "title": "string — scholarship name as best identifiable",
  "sponsor": "string — organization offering the scholarship, or empty if not stated",
  "deadline": "YYYY-MM-DD — normalize whatever date format the email uses",
  "award_usd": 1234,   // integer dollars, or null if unstated
  "essay_required": true,
  "essay_prompts": ["string — full text of each essay prompt if listed, else []"],
  "interview_required": false,
  "application_url": "https://...",
  "eligibility_notes": "string — copy any eligibility criteria text verbatim"
}
```

## Rules

1. **Be conservative on essay_required:** only mark `true` if the email explicitly mentions an essay, statement, personal narrative, or similar written-response requirement. Don't assume.
2. **award_usd is null when unstated.** Never invent or estimate.
3. **deadline must be ISO date.** Convert "September 15, 2026" → "2026-09-15", "9/15/26" → "2026-09-15", etc. If only a year is given, use Dec 31 of that year.
4. **Skip outright** if the listing has neither an extractable deadline nor an award amount. These are almost always promotional content.
5. **Skip outright** if the URL is to a survey, feedback form, or account settings page.
6. **Newsletters bundle multiple scholarships.** Split them into separate records.

## Example

Input body:
```
Future Engineers of America Scholarship
Deadline: September 15, 2026
Award: $5,000
Apply: https://scholarships.com/feoa
```

Output:
```json
[
  {
    "title": "Future Engineers of America Scholarship",
    "sponsor": "",
    "deadline": "2026-09-15",
    "award_usd": 5000,
    "essay_required": false,
    "essay_prompts": [],
    "interview_required": false,
    "application_url": "https://scholarships.com/feoa",
    "eligibility_notes": ""
  }
]
```
```

- [ ] **Step 2: Commit**

```bash
git add templates/parse-prompt.md
git commit -m "feat(templates): email parsing prompt for the agent"
```

---

## Task 10: Score Rubric Template

**Files:**
- Create: `templates/score-rubric.md`

- [ ] **Step 1: Write `templates/score-rubric.md`**

```markdown
# Scholarship Scoring Rubric

For each scholarship record, the agent computes three independent sub-scores: **Fit**, **Odds**, **Effort**. Each is 0–100. The agent reads `user-profile.md` once and uses it as the ground truth for Fit checks.

## Fit (0–100)

How well does Brody match the eligibility criteria?

**Hard disqualifiers → Fit = 0 and the entry is filtered before delivery:**
- Wrong major (e.g. "for English majors only")
- Wrong citizenship status (e.g. "US citizens only" when Brody isn't one — N/A: he is)
- Wrong state of residence AND scholarship is state-restricted (note: he's in AR transitioning to CA in fall — both states are acceptable matches; out-of-state requirements that are neither AR nor CA disqualify)
- Wrong gender / ethnicity / demographic-restricted (and he doesn't match the restriction)
- Class year mismatch (e.g. "graduating seniors only")

**Otherwise, start at 50 and adjust:**
- +20: scholarship explicitly targets mechanical/energy engineering
- +10: scholarship targets STEM broadly
- +15: scholarship targets renewable energy, sustainability, solar, tidal, or storage
- +10: scholarship favors first-gen, financial-need, or Pell-eligible students (Brody is half-Pell)
- +10: scholarship targets Cal Poly or California public university students
- +5: scholarship favors students with entrepreneurship interest (Brody has the minor)
- −15: scholarship explicitly favors a demographic Brody doesn't match (e.g. women in engineering — still apply but it's a stretch)
- Cap at 100, floor at 1 (anything truly zero is a hard disqualifier above)

## Odds (0–100)

Lower applicant pool + smaller award = higher Odds. The signal is *how winnable* it is.

- Start at 30 (baseline for a generic national scholarship).
- +30 if eligibility is narrow (one state, one major, one school, one demographic combo).
- +20 if eligibility is very narrow (e.g., "Cal Poly ME majors with energy concentration only").
- +20 if award is under $1,000 (lower competition for small awards).
- +10 if award is under $5,000.
- −15 if award is over $25,000.
- −20 if it's a national high-prestige award (Goldwater, Truman, etc.).
- −10 if applicant pool is hinted to be over 10,000.
- Cap 1–100.

## Effort (0–100)

Lower required work for the award size = higher Effort score (i.e. higher effort score = better leverage).

- Start at 60.
- +20 if no essay required.
- +15 if a single essay under 500 words is the only writing requirement.
- −15 if 1,000–2,000 words of essay required.
- −30 if multiple essays totaling 3,000+ words.
- −20 if recommendation letters required.
- −10 if transcripts/financial-aid forms required.
- −20 if interview required.
- +15 if award is over $10,000 (recalibrates "effort vs. payoff" toward "worth it").
- Cap 1–100.

## Composite for sorting

`composite = Fit × 2 + Odds + Effort`

Sort the digest descending by composite. Within ties, prefer earlier deadlines.

## Interview flag (separate from Effort)

If a scholarship requires an interview, emit `interview_required: true` and the digest must surface this verbatim in the entry, regardless of the Effort score deduction. The user wants interviews called out explicitly.
```

- [ ] **Step 2: Commit**

```bash
git add templates/score-rubric.md
git commit -m "feat(templates): Fit/Odds/Effort scoring rubric"
```

---

## Task 11: Match Prompt Template

**Files:**
- Create: `templates/match-prompt.md`

- [ ] **Step 1: Write `templates/match-prompt.md`**

```markdown
# Essay Matching Prompt

For each scholarship that requires an essay, decide whether one of Brody's existing essays (catalogued in `essays-index.md` in the Drive folder) already addresses the prompt well enough to reuse.

## Input

- The scholarship's essay prompt(s) (full text)
- The contents of `essays-index.md` from the Drive folder

## How to decide

Use semantic similarity, not keyword overlap. Two prompts can use entirely different vocabulary but ask the same underlying question ("describe a defining moment" vs. "what experience shaped your worldview" are matches; "leadership" and "ethical dilemma" are not, even though both could yield essays mentioning the word "lead").

For each indexed essay, ask: *"If I rewrote a 90% version of this essay tailored to the new prompt, would the existing essay's core argument and personal evidence still carry it?"*

- **MATCH** — yes, the existing essay's lived experience and argument map onto the new prompt with cosmetic edits (intro, conclusion, ~30% of body).
- **NEW** — no, this would need a fundamentally different argument or different lived experience to be honest.

## Threshold

Only emit MATCH when you're confident. When in doubt, mark NEW — it's better to write a new outline than to reuse an essay that doesn't actually fit.

## Output

For each scholarship record, set:
```
match_status: "MATCH:<filename>" or "NEW"
```
If multiple essays match, pick the one with the strongest overlap and use only its filename.
```

- [ ] **Step 2: Commit**

```bash
git add templates/match-prompt.md
git commit -m "feat(templates): essay semantic matching prompt"
```

---

## Task 12: Outline Prompt Template

**Files:**
- Create: `templates/outline-prompt.md`

- [ ] **Step 1: Write `templates/outline-prompt.md`**

```markdown
# Essay Outline Generation Prompt

For each scholarship marked `NEW` (no existing essay matches), generate a short starter outline. The outline unblocks the hardest part — finding the angle — without committing to a full draft Brody will probably rewrite anyway.

## Input

- Scholarship essay prompt(s) (full text)
- `user-profile.md` (Brody's profile)
- Word-count target if specified in the prompt

## Output structure

Markdown of this shape:

```markdown
### Prompt
> [The full essay prompt, quoted verbatim]

### Angle suggestions (3–4)
- **<Angle name>:** [1–2 sentences explaining how Brody could approach this prompt, grounded in a specific item from user-profile.md]
- **<Angle name>:** ...
- **<Angle name>:** ...

### Suggested structure
1. Hook — [what kind of opening fits this angle]
2. Setup — [what context the reader needs]
3. Turn — [the key moment, decision, or insight]
4. Reflection — [what it means and how it connects to engineering / career]
5. Forward-look — [how it ties to the scholarship's mission]

### Target
Word count: [from prompt or sensible default]
Tone: [conversational / formal / personal essay / etc., inferred from the scholarship's vibe]
```

## Rules

1. **Angles must be grounded in real profile items.** Pull from clubs (Future Fuels, Sales Engineering, entrepreneurship minor, Engineering Club), specific projects (mobile solar panel array), residency transition (Arkansas → California), career direction (renewable energy: solar/tidal/storage), or financial-need posture. Don't invent biography.
2. **No filler.** If you can't generate three distinct angles that are all genuinely viable, give two. Three padded angles waste reading time.
3. **Don't write actual prose.** Outline only. The hook is described, not drafted.
```

- [ ] **Step 2: Commit**

```bash
git add templates/outline-prompt.md
git commit -m "feat(templates): essay outline generation prompt"
```

---

## Task 13: Email Digest Template

**Files:**
- Create: `templates/email-digest.txt`

- [ ] **Step 1: Write `templates/email-digest.txt`**

```
Scholarship Digest — {{date}}
================================

{{new_section_or_empty_notice}}

{{deadlines_section_or_empty}}

--
Generated by scholarship-automation. Tune sources at config/sources.md.
State: state/seen-scholarships.json
```

The agent fills in:

- `{{date}}` — today's date YYYY-MM-DD
- `{{new_section_or_empty_notice}}` — either the NEW TODAY block or "NEW TODAY (0)\n\nNo new scholarships matched today."
- `{{deadlines_section_or_empty}}` — either the DEADLINES THIS WEEK block or "DEADLINES THIS WEEK (0)\n\nNo upcoming deadlines."

**NEW TODAY block format (Brody's preference: sort essay/no-essay split, most-to-least award; flag interviews):**

```
NEW TODAY (N)
-------------

>>> NO-ESSAY SCHOLARSHIPS <<<

1. [Title] — [Sponsor]
   Award: $X,XXX  Deadline: YYYY-MM-DD (n days)
   Fit: 85  Odds: 60  Effort: 90
   No essay required.
   {{INTERVIEW REQUIRED — flagged here if true}}
   Apply: https://...

2. [Title] — ...

>>> ESSAY SCHOLARSHIPS <<<

1. [Title] — [Sponsor]
   Award: $X,XXX  Deadline: YYYY-MM-DD (n days)
   Fit: 70  Odds: 80  Effort: 40
   Match: ocean-protection-degree-purpose.md (high overlap)
   {{INTERVIEW REQUIRED — flagged here if true}}
   Apply: https://...

2. [Title] — ...
   NEW essay needed — outline:
     [outline body from templates/outline-prompt.md output]
   Apply: https://...
```

Both buckets sort descending by award amount.

**DEADLINES THIS WEEK block format:**

```
DEADLINES THIS WEEK (N)
-----------------------

1. [Title] — Deadline in n days  (first seen YYYY-MM-DD)
   Award: $X,XXX
   Match status: [MATCH:filename OR NEW]
   Apply: https://...
```

Sort ascending by deadline (closest first).

- [ ] **Step 2: Commit**

```bash
git add templates/email-digest.txt
git commit -m "feat(templates): plain-text email digest format with essay/no-essay split"
```

---

## Task 14: Workflow Document (Agent Run-book)

**Files:**
- Create: `workflow.md`

- [ ] **Step 1: Write `workflow.md`**

```markdown
# Scholarship Automation — Agent Run-book

This file is read at the start of each scheduled run. You (the Claude Code agent) are the runtime. Follow the stages in order. Use the Python helpers in `scripts/` for I/O; do the LLM-heavy work yourself using the templates in `templates/`.

## Preconditions

- Working directory: the project root.
- `.env` exists and is populated (verify with `test -f .env`).
- `state/seen-scholarships.json` and `state/run-log.md` exist (verify before reading).
- Google Drive MCP server is connected (you'll need it for Stage 4).

If any precondition fails, send the error email (see Stage 8.5) and exit.

---

## Stage 1 — Fetch new labeled messages

Run:
```bash
SINCE_ISO=$(python -c "import json; d=json.load(open('state/seen-scholarships.json')); print(d.get('last_run_iso') or '')") \
  python -m scripts.imap_fetch > /tmp/scholarship_messages.json
```

If `SINCE_ISO` is empty (first run), `imap_fetch` fetches all labeled messages. Otherwise it filters by date.

Verify: `cat /tmp/scholarship_messages.json | python -c "import json, sys; print(len(json.load(sys.stdin)))"` shows the message count.

## Stage 2 — Parse each message into scholarship records

Read `/tmp/scholarship_messages.json`. For each message, apply `templates/parse-prompt.md` to its body. Produce a flat list of scholarship records (newsletters bundle multiple per email — split them).

Dedup against `state/seen-scholarships.json`:
- Compute each record's `id` as SHA-256 of the normalized string `title|sponsor|deadline` (lowercase, whitespace-collapsed).
- Drop any record whose `id` is already in `seen-scholarships.json/entries`.
- Drop any record from `templates/parse-prompt.md`'s skip rules.

Output: in-memory list of new scholarship records.

## Stage 3 — Score each record

For each new record, apply `templates/score-rubric.md`. Read `user-profile.md` for Fit inputs.

Set on each record:
- `fit` (0–100)
- `odds` (0–100)
- `effort` (0–100)

Drop any record where `fit == 0` (hard disqualifier).

## Stage 4 — Essay match check

For records where `essay_required == true`:

1. Read `essays-index.md` from the Drive folder (folder ID from `.env` → `DRIVE_ESSAYS_FOLDER_ID`). Use the Drive MCP `read_file_content` tool.
2. Apply `templates/match-prompt.md` for each record's essay prompt(s).
3. Set `match_status` = `MATCH:<filename>` or `NEW`.

For records where `essay_required == false`, set `match_status = "NO_ESSAY"`.

## Stage 5 — Generate outlines for NEW essays

For records where `match_status == "NEW"`, apply `templates/outline-prompt.md`. Attach the outline text to the record for digest composition. (The outlines are not persisted to state — they're regenerated if needed.)

## Stage 6 — Build "Deadlines this week" section

Read `state/seen-scholarships.json`. For each entry:
- If `deadline_reminder_surfaced == true`, skip (already shown).
- If `expired_flag == true`, skip.
- If `deadline` is between today+6 and today+8 days inclusive, include in the deadlines section AND mark `deadline_reminder_surfaced = true` for the persisted state update.

Sort ascending by deadline.

## Stage 7 — Filter expired

For any entry where `deadline < today`, set `expired_flag = true` for the persisted state update. Drop from both today's new section and the deadlines section.

## Stage 8 — Compose and send digest

Compose plain-text body using `templates/email-digest.txt`:
- Sort the "NEW TODAY" section into two buckets: no-essay (where `essay_required == false`) and essay (where `true`).
- Within each bucket, sort descending by award amount (nulls last).
- If both buckets are empty AND deadlines section is empty, send the no-activity short email instead.
- Subject: `Scholarship Digest — YYYY-MM-DD (N new, M deadlines)`.

Write body to `/tmp/scholarship_digest_body.txt`. Run:

```bash
python -m scripts.send_digest /tmp/scholarship_digest_body.txt \
  "Scholarship Digest — $(date +%Y-%m-%d) (N new, M deadlines)"
```

### Stage 8.5 — Error-email fallback

If any stage above raised an exception you couldn't recover from, compose a short error email:
- Subject: `Scholarship Digest — error YYYY-MM-DD`
- Body: stage where it failed, error message, suggested action.
- Send via the same `scripts/send_digest` path.
- Do NOT update state (Stage 9 skipped) — so the run can be retried.

## Stage 9 — Persist state

Build updated `seen-scholarships.json`:
- Append today's new records (after Stage 2 dedup and Stage 3 fit-filter), with full fields per the schema.
- Update `last_run_iso` to now (UTC, ISO format, Z suffix).
- Preserve existing entries; update their `deadline_reminder_surfaced` and `expired_flag` if changed in Stages 6/7.

Validate with `scripts/schema.validate_seen_scholarships`. If validation fails, send the error email and DO NOT commit.

Build run-log entry:

```markdown
## YYYY-MM-DD
- Fetched: N messages, parsed into M records, K new after dedup
- Filtered to L after fit-check (J disqualified)
- Deadline reminders surfaced: D
- Expired entries: E
- Digest sent to imajedimastr@gmail.com
```

Run:
```bash
python -m scripts.persist_state /tmp/seen-scholarships-updated.json /tmp/run-log-append.md
```

## Done

End of run. Next scheduled trigger at 9am Pacific tomorrow.
```

- [ ] **Step 2: Commit**

```bash
git add workflow.md
git commit -m "feat(workflow): agent run-book for daily scholarship digest"
```

---

## Task 15: Full Test Suite Pass

**Files:** (none new)

- [ ] **Step 1: Install dependencies**

```bash
python -m venv .venv
.venv/Scripts/activate  # Windows bash; on POSIX use: source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 2: Run the full test suite**

```bash
pytest -v
```
Expected: all tests pass (schema: 6, imap_fetch: 4, send_digest: 2, persist_state: 2 = 14 total).

- [ ] **Step 3: Commit if any test fixes were needed**

If any tests had to be fixed during this pass:
```bash
git add -u
git commit -m "test: stabilize cross-module test interactions"
```
Otherwise skip.

---

## Task 16: End-to-End Dry Run (Local, No SMTP/GitHub Sends)

**Files:**
- Create: `scripts/dry_run.py` (deleted at end of task)

- [ ] **Step 1: Write a temporary `scripts/dry_run.py` that exercises the full pipeline against fixtures**

```python
"""One-shot dry run: simulate a full scholarship-automation pass against fixtures.

Does NOT touch real IMAP, real SMTP, or real GitHub. Prints the rendered digest
body to stdout for human inspection. Used once during initial bring-up.
"""
from __future__ import annotations
import json
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"


def main() -> int:
    print("=== Dry run: would parse these emails ===")
    for eml in sorted((FIXTURES / "emails").glob("*.eml")):
        print(f"  - {eml.name}")
    print()
    print("=== Dry run: would read this user profile ===")
    profile = (Path(__file__).parent.parent / "user-profile.md").read_text(encoding="utf-8")
    print(profile[:300] + "...")
    print()
    print("=== Dry run: would commit to repo ===")
    seen = json.loads((Path(__file__).parent.parent / "state" / "seen-scholarships.json").read_text())
    print(f"  state/seen-scholarships.json: {len(seen['entries'])} entries currently")
    print(f"  state/run-log.md: would append a single dated block")
    print()
    print("Dry run complete. No external calls made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the dry run**

```bash
python scripts/dry_run.py
```
Expected: lists 3 fixture emails, shows first 300 chars of user-profile.md, reports 0 entries in seen-scholarships.json.

- [ ] **Step 3: Delete the dry-run script (it's served its purpose)**

```bash
rm scripts/dry_run.py
```

- [ ] **Step 4: Commit the removal (nothing to commit if dry_run.py was never tracked)**

If it was tracked momentarily:
```bash
git add -u
git commit -m "chore: remove dry_run scaffolding"
```
Skip if untracked.

---

## Task 17: GitHub Remote Setup + Initial Push

**Files:** (none new)

- [ ] **Step 1: Verify nothing sensitive is staged or tracked**

```bash
git ls-files | grep -E "(^\.env$|\.env\.scratch)" && echo "STOP: sensitive files tracked" || echo "OK"
```
Expected: `OK` (no matches).

- [ ] **Step 2: Create the GitHub repo via `gh` CLI**

```bash
gh repo create sloglowrestoration-star/scholarship-automation --private --source=. --remote=origin --description "Daily scholarship digest agent for Brody"
```

- [ ] **Step 3: Push**

```bash
git push -u origin main
```

- [ ] **Step 4: Verify by checking remote**

```bash
gh repo view sloglowrestoration-star/scholarship-automation --json url -q .url
```
Expected: prints the repo URL.

---

## Task 18: First Live Manual Run

**Files:** (none new — observation only)

- [ ] **Step 1: Trigger a Claude Code session manually in the project directory**

Open Claude Code, navigate to `C:\Users\imaje\OneDrive - Cal Poly\Y2\Coding\scholarship-automation\`, and prompt:

> "Read workflow.md and execute the full daily run now. Send the digest to me when done."

- [ ] **Step 2: Watch the agent walk through stages 1–9**

Verify:
- Stage 1 successfully fetches from Gmail (the label exists, app password works)
- Stage 2 produces a sensible number of scholarship records
- Stage 3 produces 0–100 sub-scores
- Stage 4 reads `essays-index.md` from Drive successfully via MCP
- Stage 8 sends an email to imajedimastr@gmail.com
- Stage 9 commits `state/seen-scholarships.json` and `state/run-log.md` back to the repo

- [ ] **Step 3: Inspect the digest email**

Open the email. Check:
- Subject formatted as expected
- Essay/no-essay split renders correctly
- Sub-scores look reasonable for the entries shown
- At least one of: deadline reminders section is empty (expected on first run), or shows nothing past today
- Apply links are clickable

- [ ] **Step 4: Inspect the committed state**

```bash
git pull
cat state/seen-scholarships.json | python -m json.tool | head -40
cat state/run-log.md
```
Verify entries match what the digest showed. Verify run-log has a fresh dated block.

- [ ] **Step 5: If anything looks wrong, tune and re-run**

Common fixes:
- Bad parser output → tune `templates/parse-prompt.md`
- Wrong scoring → tune `templates/score-rubric.md`
- Filter false-positives → tune `config/filters.md` AND the Gmail filters
- Then commit and re-run from step 1 of this task

---

## Task 19: Schedule the Daily Trigger

**Files:** (none new)

- [ ] **Step 1: Create the scheduled trigger via Claude's scheduled-tasks MCP**

In a Claude Code session, run the equivalent of:

```
mcp__scheduled-tasks__create_scheduled_task with:
  name: "Daily Scholarship Digest"
  cron: "0 16 * * *"      # 16:00 UTC = 9:00 AM Pacific Standard Time
                          # NOTE: 9am Pacific is 16:00 UTC during PST (Nov-Mar)
                          # and 16:00 UTC during PDT is 9am PDT — wait, PDT is UTC-7,
                          # so 9am PDT = 16:00 UTC. PST is UTC-8 so 9am PST = 17:00 UTC.
                          # For 9am-during-DST and 8am-not-during-DST, use 16:00 UTC.
                          # If you want strict 9am year-round, schedule both 16:00 and
                          # 17:00 in winter; or accept the 8am-PST behavior.
  prompt: "You're the scholarship-automation agent. Navigate to
           C:\\Users\\imaje\\OneDrive - Cal Poly\\Y2\\Coding\\scholarship-automation
           and execute the full pipeline in workflow.md."
```

Note: the user prefers consistency over DST gymnastics; accept that the digest arrives 9am PDT (summer) / 8am PST (winter).

- [ ] **Step 2: Verify the trigger exists**

```
mcp__scheduled-tasks__list_scheduled_tasks
```
Expected: shows "Daily Scholarship Digest" with the next run timestamp.

- [ ] **Step 3: Record the trigger ID in `state/run-log.md`** for traceability

Manually append to `state/run-log.md`:
```markdown
## Setup
- Scheduled trigger created: <trigger-id-from-mcp-output>
- Cron: 0 16 * * * UTC (9am PDT / 8am PST)
```

Commit:
```bash
git add state/run-log.md
git commit -m "ops: record scheduled trigger ID in run-log"
git push
```

---

## Task 20: First-Week Monitoring Plan

**Files:**
- Modify: `config/filters.md` (likely tweaks after observation)

This isn't a coding task — it's a one-week observation window. Add a calendar reminder for **2026-06-02** (one week after the first scheduled run) to review:

- [ ] **Step 1: After 7 daily runs, inspect each digest in your inbox**

For each digest, note:
- Any scholarships that shouldn't have appeared (false positives)
- Any scholarships you saw in Gmail that didn't appear (false negatives)
- Any sub-scores that felt wildly off
- Any outline that was useless vs. genuinely helpful

- [ ] **Step 2: Pull the repo and inspect `state/run-log.md`**

```bash
git pull
cat state/run-log.md
```
Look for: error blocks, days where the run produced zero output unexpectedly, days where parsing dropped messages it shouldn't have.

- [ ] **Step 3: Tune the templates and filters**

Based on findings, edit:
- `config/filters.md` — add/remove sender domains, sharpen skip-keywords
- Gmail filters themselves — match the .md changes
- `templates/parse-prompt.md` — strengthen "skip outright" rules
- `templates/score-rubric.md` — adjust weightings
- `templates/match-prompt.md` — tighten the threshold if you saw bad matches

Commit:
```bash
git add -A
git commit -m "ops: first-week tuning based on real runs"
git push
```

---

## Self-Review Summary

**Spec coverage:**

| Spec section | Implementing task(s) |
|---|---|
| Purpose / Why | (intent embedded throughout) |
| Architecture (private repo, scheduled agent, GitHub state, SMTP) | 1, 17, 19 |
| Gmail label + filters | (user setup) + 3 (filters.md documents them) |
| IMAP credentials | 2 |
| user-profile.md | (already committed before plan) |
| Drive folder + essays-index | (user setup) + 14 Stage 4 reads it |
| filters.md | 3 |
| Stage 1 (IMAP fetch) | 5 + 14 Stage 1 |
| Stage 2 (parse) | 9 + 14 Stage 2 |
| Stage 3 (score) | 10 + 14 Stage 3 |
| Stage 4 (match) | 11 + 14 Stage 4 |
| Stage 5 (outline) | 12 + 14 Stage 5 |
| Stage 6 (deadlines this week) | 14 Stage 6 + 4 (schema field) |
| Stage 7 (filter expired) | 14 Stage 7 + 4 (schema field) |
| Stage 8 (compose + send) | 6 + 13 + 14 Stage 8 |
| Stage 9 (persist state) | 7 + 14 Stage 9 |
| Composite score weighting (Fit×2+Odds+Effort) | 10 + 13 |
| Email format | 13 |
| State files (seen-scholarships.json, run-log.md) | 4 + 8 |
| Failure modes (IMAP fail, empty run, parse miss, Drive miss, GitHub fail) | 14 Stage 8.5 + 14 stage notes |
| Brody's no-essay/essay split + interview flag preferences | 10 (interview flag), 13 (template format) |

All spec requirements have at least one task. No gaps.

**Placeholder scan:** No "TBD", no "implement later", no "similar to Task N", no orphaned references. Every step contains either the actual code, the actual file content, or the exact command to run.

**Type consistency:** `validate_seen_scholarships` is the function name used in Tasks 4, 8, and 14 — consistent. `commit_state_files` (Task 7), `send_digest` (Task 6), `fetch_labeled_messages` (Task 5) — all referenced consistently in workflow.md (Task 14). `match_status` values (`"MATCH:<filename>"`, `"NEW"`, `"NO_ESSAY"`) consistent across Tasks 4, 11, 13, 14.

Plan ready.
