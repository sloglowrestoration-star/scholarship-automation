# Essay Outline Generation Prompt

For each scholarship marked `NEW` (no existing essay matches), generate a short starter outline. The outline unblocks the hardest part -- finding the angle -- without committing to a full draft Brody will probably rewrite anyway.

## Input

- Scholarship essay prompt(s) (full text)
- `user-profile.md` (Brody's profile)
- Word-count target if specified in the prompt

## Output structure

Markdown of this shape:

```
### Prompt
> [The full essay prompt, quoted verbatim]

### Angle suggestions (3-4)
- **<Angle name>:** [1-2 sentences explaining how Brody could approach this prompt, grounded in a specific item from user-profile.md]
- **<Angle name>:** ...
- **<Angle name>:** ...

### Suggested structure
1. Hook -- [what kind of opening fits this angle]
2. Setup -- [what context the reader needs]
3. Turn -- [the key moment, decision, or insight]
4. Reflection -- [what it means and how it connects to engineering / career]
5. Forward-look -- [how it ties to the scholarship's mission]

### Target
Word count: [from prompt or sensible default]
Tone: [conversational / formal / personal essay / etc., inferred from the scholarship's vibe]
```

## Rules

1. **Angles must be grounded in real profile items.** Pull from clubs (Future Fuels, Sales Engineering, entrepreneurship minor, Engineering Club), specific projects (mobile solar panel array), residency transition (Arkansas to California), career direction (renewable energy: solar/tidal/storage), or financial-need posture. Do not invent biography.
2. **No filler.** If you cannot generate three distinct angles that are all genuinely viable, give two. Three padded angles waste reading time.
3. **Do not write actual prose.** Outline only. The hook is described, not drafted.
