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
  "award_usd": 1234,
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
3. **deadline must be ISO date.** Convert "September 15, 2026" to "2026-09-15", "9/15/26" to "2026-09-15", etc. If only a year is given, use Dec 31 of that year.
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
