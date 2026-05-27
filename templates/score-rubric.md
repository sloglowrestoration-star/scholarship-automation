# Scholarship Scoring Rubric

For each scholarship record, compute three independent sub-scores: **Fit**, **Odds**, **Effort**. Each is 0-100. Read `user-profile.md` once and use it as the ground truth for Fit checks.

## Fit (0-100)

How well does Brody match the eligibility criteria?

**Hard disqualifiers — Fit = 0, entry filtered before delivery:**
- Wrong major (e.g. "for English majors only")
- Wrong citizenship (Brody is a US Citizen, so non-citizen-only scholarships disqualify)
- Wrong state of residence AND scholarship is state-restricted (AR or CA are both valid per profile; all other state-restricted scholarships disqualify)
- Class year mismatch (e.g. "graduating seniors only" — Brody is a sophomore)

These are facts in `user-profile.md` that Brody has declared. A mismatch means he cannot apply.

**Demographic restrictions — do NOT disqualify, flag instead:**

If the scholarship's title, sponsor, or eligibility text indicates a demographic group Brody has not claimed in `user-profile.md` (ethnicity, religion, gender, sexual orientation, military/veteran family, first-gen, disability, unique hardship), set `demographic_flag` on the record to a short tag like `"Native American"`, `"Latino/a"`, `"Hindu"`, `"Women in STEM"`, `"Veteran family"`. These records are routed to a separate "DEMOGRAPHIC-RESTRICTED — REVIEW MANUALLY" section of the digest so Brody can opt in by editing his profile if any apply.

Apply -15 to Fit (it is a stretch as-scored) but continue scoring normally. Do not set Fit = 0.

For non-flagged records, leave `demographic_flag` as an empty string `""`.

**Otherwise, start at 50 and adjust:**
- +20: scholarship explicitly targets mechanical or energy engineering
- +10: scholarship targets STEM broadly
- +15: scholarship targets renewable energy, sustainability, solar, tidal, or storage
- +10: scholarship favors first-gen, financial-need, or Pell-eligible students (Brody is half-Pell)
- +10: scholarship targets Cal Poly or California public university students
- +5: scholarship favors students with entrepreneurship interest (Brody has the minor)
- -15: scholarship explicitly favors a demographic Brody doesn't match (the demographic_flag case above)
- Cap at 100, floor at 1

## Odds (0-100)

How winnable is this? Lower applicant pool + smaller award = higher Odds.

- Start at 30 (baseline for a generic national scholarship)
- +30 if eligibility is narrow (one state, one major, one school, one demographic combo)
- +20 if eligibility is very narrow (e.g. "Cal Poly ME juniors with energy concentration only")
- +20 if award is under $1,000
- +10 if award is under $5,000
- -15 if award is over $25,000
- -20 if it's a national high-prestige award (Goldwater, Truman, etc.)
- -10 if applicant pool is hinted to be over 10,000
- Cap 1-100

## Effort (0-100)

Lower required work for the award size = higher Effort score (higher = better leverage).

- Start at 60
- +20 if no essay required
- +15 if a single essay under 500 words is the only writing requirement
- -15 if 1,000-2,000 words of essay required
- -30 if multiple essays totaling 3,000+ words
- -20 if recommendation letters required
- -10 if transcripts or financial-aid forms required
- -20 if interview required
- +15 if award is over $10,000
- Cap 1-100

## Composite for sorting

`composite = Fit x 2 + Odds + Effort`

Sort the digest descending by composite. Within ties, prefer earlier deadlines.

## Interview flag

If a scholarship requires an interview, the digest MUST surface "INTERVIEW REQUIRED" inline on that entry, regardless of the Effort score. Brody wants interviews called out explicitly at a glance.
