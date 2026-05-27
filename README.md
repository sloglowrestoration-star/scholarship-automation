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
