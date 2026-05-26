# Scholarship Automation — Design Spec

**Date:** 2026-05-26
**Owner:** imaje (imajedimastr@gmail.com)
**Status:** Approved by user, pre-implementation
**Companion project:** internship-automation (proven pattern this design reuses)

## Purpose

A scheduled remote agent that emails imaje a daily 9:00am Pacific digest of new scholarship opportunities found in their Gmail inbox. Each scholarship is scored on Fit, Odds, and Effort, matched against an existing essay library when possible, and given a starter outline when a new essay is needed. Deadline reminders for already-seen scholarships are inlined into the same digest.

## Why

Scholarship discovery is currently passive — relevant emails arrive but get buried, deadlines slip, and essay reuse opportunities are missed. A daily morning briefing surfaces what's new, tells imaje whether they realistically qualify and whether existing work can be repurposed, and unblocks the hardest part of essay writing (finding the angle) with starter outlines.

## High-level architecture

Mirrors the internship-automation pattern closely:

- **New private GitHub repo:** `scholarship-automation`
- **Scheduled remote agent:** runs daily at 9:00am Pacific (cron `0 16 * * *` UTC)
- **State persistence:** GitHub Contents API writes `seen-scholarships.json` and `run-log.md` to the repo after each successful run
- **Email send:** Python `smtplib` SMTP from `brody.internships@gmail.com` (reusing the existing app password and SMTP setup from internship-automation), plain-text body, delivered to `imajedimastr@gmail.com`
- **Credentials:** `.env` committed to the private repo (mirrors the internship-automation convention; GitHub PAT + Gmail app passwords)

### New components specific to scholarships

| Component | Where it lives | Purpose |
|---|---|---|
| Gmail label `Scholarships` + filters | imajedimastr@gmail.com | Input gate. Filters auto-apply the label to known sender domains (Scholarships.com, Fastweb, Going Merry, BoldOrg, Cal Poly financial aid listservs, ME department listservs). |
| IMAP read credentials | `.env` as `IMAJE_GMAIL_APP_PASSWORD` | Lets the agent read labeled messages from imaje's primary inbox. |
| `user-profile.md` | Committed in repo | Eligibility data for Fit scoring. Major, year, GPA, Cal Poly affiliation, residency, citizenship, demographics (only fields imaje is comfortable using), financial-need, career interests, extracurriculars summary. |
| Google Drive folder "Scholarship Essays" | imaje's Google Drive | Stores past scholarship essays. Folder ID stored in `.env`. |
| `essays-index.md` | Inside the Drive folder, human-curated | Lightweight index of essays: one section per essay with tags + one-line summary. The agent reads this each run to match prompts to existing essays without re-reading every essay's full content. |
| `config/filters.md` | Committed in repo | Tunable inclusion/exclusion rules (which sender domains, which keywords to skip, etc.). Tuned after the first week. |

## Daily pipeline

Nine stages, run in order. State mutations are deferred to the final stage so partial failures cannot corrupt the seen-list.

### Stage 1 — Pull new scholarship emails (IMAP)
Connect to `imajedimastr@gmail.com` via IMAP. Fetch messages with label `Scholarships` received since the last successful run timestamp (stored in `run-log.md`). Skip messages already represented in `seen-scholarships.json` (dedup key: message-id + extracted scholarship URL).

### Stage 2 — Parse each email into scholarship records
For each new message, extract: scholarship title, sponsor, award amount, deadline (normalized to ISO date), eligibility criteria, essay prompt(s) and word counts, application URL. Newsletters frequently bundle multiple scholarships per email — Stage 2 splits these into individual records. LLM-assisted parsing since formats vary widely across sources.

### Stage 3 — Score each scholarship (three sub-scores, 0–100)
- **Fit** — Compare scholarship eligibility against `user-profile.md`. Hard disqualifiers (wrong major, wrong state, citizenship requirement imaje does not meet, gender/ethnicity restrictions imaje does not meet) drop Fit to 0 and the entry is filtered out before delivery. Otherwise, partial matches lower the Fit score proportionally.
- **Odds** — Heuristic from award size and selectivity signals (national vs. local, applicant pool hints in the description, niche eligibility narrowing the field). Smaller award and narrower eligibility raise Odds.
- **Effort** — Essay count, total word-count required, recommendation letters required, transcripts required. Lower required output for the award size raises the Effort score (i.e. "easier to apply relative to payoff" = higher score).

### Stage 4 — Essay match check
For each scholarship's essay prompt(s), compare against `essays-index.md` from the Drive folder using LLM semantic similarity (not keyword overlap). Threshold for MATCH = high-confidence semantic overlap with at least one indexed essay. Otherwise NEW.

### Stage 5 — Generate outline (NEW essays only)
For each NEW essay, produce a short outline: prompt restatement, 3–4 angle suggestions grounded in `user-profile.md`, suggested structure, word-count target. No full draft.

### Stage 6 — Build "Deadlines this week" section
Scan `seen-scholarships.json` for entries where deadline is 6–8 days out, not marked expired, and not already in today's new-scholarships list. Include these in the digest as a separate inlined section (same email, no separate notification).

### Stage 7 — Filter expired
Drop any scholarship where deadline < today from both the new section and the deadlines section.

### Stage 8 — Compose and send digest
Plain-text email to `imajedimastr@gmail.com`, sent from `brody.internships@gmail.com`. Sort by composite score: `Fit × 2 + Odds + Effort` (Fit-dominant since unqualified entries are wasted reading and are already filtered at Fit=0). Each entry shows: title, sponsor, deadline, award, the three sub-scores, match status (`MATCH: <essay-filename>` or `NEW — outline below`), application URL, and the outline body if NEW.

### Stage 9 — Persist state
Append today's run summary to `run-log.md`. Update `seen-scholarships.json` with new entries (including their deadlines for later use in Stage 6). Commit both back to the repo via GitHub Contents API.

## Composite score weighting

```
composite = Fit × 2 + Odds + Effort
```

Fit-dominant by design. Outputs sort descending. A scholarship with Fit=0 never reaches the digest.

## Email format (plain text)

```
Scholarship Digest — YYYY-MM-DD
================================

NEW TODAY (n)
-------------

1. [Title] — [Sponsor]
   Award: $X,XXX  Deadline: YYYY-MM-DD (n days)
   Fit: 85  Odds: 60  Effort: 70
   Match: leadership-overcoming-2025.docx (high overlap)
   Apply: https://...

2. [Title] — [Sponsor]
   Award: $X,XXX  Deadline: YYYY-MM-DD (n days)
   Fit: 70  Odds: 80  Effort: 40
   NEW essay needed — outline:
     Prompt: "Describe a time you led through adversity..."
     Angles:
       - Club budget crisis (matches profile: ME Council treasurer)
       - ...
     Structure: hook → setback → action → outcome → reflection
     Target: 500 words
   Apply: https://...

DEADLINES THIS WEEK (n)
-----------------------

1. [Title] — Deadline in n days  (originally seen YYYY-MM-DD)
   Apply: https://...
```

## State files

- **`seen-scholarships.json`** — array of objects, each: `{id, title, sponsor, deadline, award, source_message_id, first_seen, match_status}`. Used for dedup, deadline-reminder lookup, and expired filtering.
- **`run-log.md`** — append-only, one block per run: timestamp, count of new scholarships found, count of deadline reminders surfaced, errors encountered, last successful run timestamp.

## Failure modes and error handling

- **IMAP connection fails:** retry once, then send a short error email to imaje and exit. Do not update state.
- **No new emails since last run:** send a minimal digest with only the "Deadlines this week" section. If that section is also empty, send a one-line "no activity today" email so imaje knows the agent ran.
- **Parsing produces no extractable scholarship from a message:** log it to `run-log.md`, skip silently, do not mark the message as seen (so it can be retried after parser tuning).
- **Drive folder unreadable:** treat all essays as NEW for the day, note the issue in `run-log.md`.
- **GitHub Contents API write fails:** send the digest anyway, log the state-write failure prominently in the next run's first email (so a missed commit doesn't go unnoticed).

## What's deliberately out of scope (YAGNI)

- Full essay drafting (only outlines, per the brainstorming decision)
- HTML digest format (plain text is faster to scan on mobile and bypasses Gmail clipping)
- Application-submission tracking (low payoff at imaje's expected volume; can be added later if needed)
- Auto-updating `essays-index.md` from new essay files (kept human-curated to keep matching honest)
- Web scraping for scholarships outside imaje's inbox (the email channel covers the explicitly chosen sources)

## User-side setup prerequisites

These must be completed before the implementation plan can be executed end-to-end:

1. Gmail label `Scholarships` created in `imajedimastr@gmail.com` with filters auto-applying it to chosen sender domains.
2. Gmail app password generated for `imajedimastr@gmail.com` and stored as `IMAJE_GMAIL_APP_PASSWORD` in `.env`.
3. Google Drive folder `Scholarship Essays` created; folder ID captured for `.env`.
4. `essays-index.md` seeded inside the Drive folder (can start empty/near-empty; grows over time).
5. `user-profile.md` filled in and committed to the repo.
6. Confirmation that `brody.internships@gmail.com`'s SMTP app password from internship-automation's `.env` is reused here.

## Open items deferred to implementation planning

- Exact LLM choice for Stages 2, 4, 5 (parsing, semantic matching, outline generation)
- Exact prompt templates for each LLM-touched stage
- Concrete schema for `seen-scholarships.json`
- Initial seed list of Gmail filter sender-domains
- Test strategy (mock IMAP fixtures? first-week monitoring plan?)
