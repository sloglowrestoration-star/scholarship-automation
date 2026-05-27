# Scholarship Automation -- Agent Run-book

This file is read at the start of each scheduled run. You (the Claude Code agent) are the runtime. Follow the stages in order. Use the Python helpers in `scripts/` for I/O; do the LLM-heavy work yourself using the templates in `templates/`.

## Preconditions

Before starting, verify:
1. Working directory is the project root (contains `workflow.md`, `user-profile.md`, `.env`)
2. `.env` exists: `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ.get('IMAJE_GMAIL_ADDRESS', 'MISSING'))"`
3. `state/seen-scholarships.json` and `state/run-log.md` exist
4. Google Drive MCP server is connected (you will need it for Stage 4)

If any precondition fails, skip to Stage 8.5 (error email) and exit.

---

## Stage 1 -- Fetch new labeled messages

Get the last_run_iso from state:

```bash
python -c "import json; d=json.load(open('state/seen-scholarships.json')); print(d.get('last_run_iso') or '')"
```

Then fetch messages (set SINCE_ISO to the value above, or leave unset for first run):

```bash
SINCE_ISO="<last_run_iso>" python -m scripts.imap_fetch > /tmp/scholarship_messages.json
```

Verify message count:

```bash
python -c "import json, sys; msgs=json.load(open('/tmp/scholarship_messages.json')); print(f'Fetched {len(msgs)} messages')"
```

If 0 messages and this is not the first run, that is fine -- proceed to Stage 6 to check deadlines.

---

## Stage 2 -- Parse each message into scholarship records

Read `/tmp/scholarship_messages.json`. For each message, apply the instructions in `templates/parse-prompt.md` to the message body. You are the LLM doing the parsing.

Produce a flat list of scholarship records. Newsletters may contain multiple scholarships per email -- split them into individual records.

Then deduplicate against `state/seen-scholarships.json`:
- Compute each record's `id` as the SHA-256 hex digest of the normalized string `f"{title.lower().strip()}|{sponsor.lower().strip()}|{deadline}"` (use Python's `hashlib.sha256(...).hexdigest()`)
- Drop any record whose `id` is already in `seen-scholarships.json/entries`
- Drop any record matching the skip rules in `templates/parse-prompt.md` (no deadline + no award, URL is a settings/survey page)

Hold the surviving records in memory as `new_records`.

---

## Stage 3 -- Score each record

For each record in `new_records`, apply `templates/score-rubric.md`. Read `user-profile.md` once at the start of this stage.

Set on each record:
- `fit` (0-100)
- `odds` (0-100)
- `effort` (0-100)

Drop any record where `fit == 0` (hard disqualifier per the rubric). Log the count of dropped records.

---

## Stage 4 -- Essay match check

For records where `essay_required == true`:

1. Use the Drive MCP `search_files` tool to find `essays-index.md` in the folder with ID from `.env` DRIVE_ESSAYS_FOLDER_ID.
2. Use the Drive MCP `read_file_content` tool to fetch its content.
3. Apply `templates/match-prompt.md` for each record's essay prompts against the index.
4. Set `match_status = "MATCH:<filename>"` or `"NEW"`.

For records where `essay_required == false`, set `match_status = "NO_ESSAY"`.

If the Drive MCP is unavailable or the folder is unreadable, set all essay records to `match_status = "NEW"` and note the issue in the run-log append (Stage 9).

---

## Stage 5 -- Generate outlines for NEW essays

For each record where `match_status == "NEW"`:
- Apply `templates/outline-prompt.md`, using the record's essay prompts and `user-profile.md`.
- Attach the outline text to the record as `outline_text` (in-memory only, not persisted to state).

---

## Stage 6 -- Build "Deadlines this week" section

Read `state/seen-scholarships.json/entries`. For each entry:
- Skip if `deadline_reminder_surfaced == true`
- Skip if `expired_flag == true`
- Skip if this entry's `id` is already in `new_records` (already appearing in today's new section)
- Compute days until deadline: `(deadline_date - today).days`
- If 6 <= days <= 8: include in `deadline_reminders` list AND mark `deadline_reminder_surfaced = true` in the updated state

Sort `deadline_reminders` ascending by deadline (closest first).

---

## Stage 7 -- Filter expired

For any entry in `seen-scholarships.json/entries` where `deadline < today`:
- Set `expired_flag = true` in the updated state
- Remove from `deadline_reminders` if present

Also drop any `new_records` entry where `deadline < today` (shouldn't happen, but sanity check).

---

## Stage 8 -- Compose and send digest

Compute today's date: `python -c "from datetime import date; print(date.today())"`

Compose the email body following the format in `templates/email-digest.txt`:

1. Split `new_records` into two buckets: `no_essay` (essay_required == false) and `essay` (essay_required == true or None)
2. Sort each bucket descending by `award_usd` (nulls last)
3. For the essay bucket, include `Match: <filename>` or the full outline block
4. Mark any entry with `interview_required == true` with "INTERVIEW REQUIRED" on its own line
5. Append the Deadlines This Week section from `deadline_reminders`
6. If both sections are empty, use the no-activity variant from `templates/email-digest.txt`

Count N = len(new_records), M = len(deadline_reminders).
Subject: `Scholarship Digest -- YYYY-MM-DD (N new, M deadlines)`

Write body to `/tmp/scholarship_digest_body.txt`.

Send:
```bash
python -m scripts.send_digest /tmp/scholarship_digest_body.txt "Scholarship Digest -- $(python -c 'from datetime import date; print(date.today())') (N new, M deadlines)"
```

### Stage 8.5 -- Error-email fallback

If any stage above raised an unrecoverable exception:
- Compose a short error email body: stage name where it failed, error message, suggested action (check run-log, retry manually)
- Subject: `Scholarship Digest -- ERROR YYYY-MM-DD`
- Write to `/tmp/scholarship_error_body.txt`
- Send: `python -m scripts.send_digest /tmp/scholarship_error_body.txt "Scholarship Digest -- ERROR <date>"`
- Exit without running Stage 9 (do not update state on error)

---

## Stage 9 -- Persist state

Build the updated `seen-scholarships.json`:
- Keep all existing entries
- For entries modified in Stages 6/7: update `deadline_reminder_surfaced` and `expired_flag`
- Append `new_records` (after Stage 3 filtering) as new entries, each with:
  - `id`: computed SHA-256 from Stage 2
  - `title`, `sponsor`, `deadline`, `award_usd`, `essay_required`, `interview_required`
  - `source_message_id`: from the original email record
  - `application_url`
  - `first_seen`: now (UTC ISO datetime with Z suffix)
  - `match_status`: from Stage 4
  - `fit`, `odds`, `effort`: from Stage 3
  - `expired_flag`: false
  - `deadline_reminder_surfaced`: false
- Update `last_run_iso` to now (UTC ISO datetime, Z suffix)

Validate with:
```bash
python -c "import json; from scripts.schema import validate_seen_scholarships; validate_seen_scholarships(json.load(open('/tmp/seen-scholarships-updated.json'))); print('schema OK')"
```

If validation fails: send the error email (Stage 8.5) and do NOT commit.

Build run-log append block:
```
## YYYY-MM-DD
- Fetched: N messages, parsed into M records, K new after dedup
- Filtered to L after fit-check (J disqualified)
- Deadline reminders surfaced: D
- Expired entries: E
- Digest sent to imajedimastr@gmail.com
```

Write both to temp files and persist:
```bash
python -m scripts.persist_state /tmp/seen-scholarships-updated.json /tmp/run-log-append.md
```

---

## Done

End of run. Next scheduled trigger at 9am Pacific tomorrow (0 16 * * * UTC).
