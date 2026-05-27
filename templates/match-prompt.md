# Essay Matching Prompt

For each scholarship that requires an essay, decide whether one of Brody's existing essays (catalogued in `essays-index.md` in the Drive folder) already addresses the prompt well enough to reuse.

## Input

- The scholarship's essay prompt(s) (full text)
- The contents of `essays-index.md` from the Drive folder

## How to decide

Use semantic similarity, not keyword overlap. Two prompts can use entirely different vocabulary but ask the same underlying question ("describe a defining moment" vs. "what experience shaped your worldview" are matches; "leadership" and "ethical dilemma" are not, even though both could yield essays mentioning the word "lead").

For each indexed essay, ask: "If I rewrote a 90% version of this essay tailored to the new prompt, would the existing essay's core argument and personal evidence still carry it?"

- **MATCH** -- yes, the existing essay's lived experience and argument map onto the new prompt with cosmetic edits (intro, conclusion, ~30% of body).
- **NEW** -- no, this would need a fundamentally different argument or different lived experience to be honest.

## Threshold

Only emit MATCH when confident. When in doubt, mark NEW -- it is better to write a new outline than to reuse an essay that does not actually fit.

## Output

For each scholarship record, set:

```
match_status: "MATCH:<filename>" or "NEW"
```

If multiple essays match, pick the one with the strongest overlap and use only its filename.
