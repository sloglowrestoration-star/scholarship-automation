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
