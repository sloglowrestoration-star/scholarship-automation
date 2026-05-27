"""Scan a scholarship's application/detail page for essay-requirement markers.

Used by workflow Stage 2.5 when the source email is silent on whether an essay
is required. Fetches the URL, strips HTML, looks for explicit signals.

Returns one of three verdicts:
    - "essay"    -- found explicit essay-requirement language
    - "no-essay" -- found explicit "no essay" / "no writing required" language
    - "unknown"  -- inconclusive (page unreachable, JS-rendered, no markers)
"""
from __future__ import annotations
import re
from html.parser import HTMLParser
from typing import Literal
import requests

Verdict = Literal["essay", "no-essay", "unknown"]

# Phrases that strongly imply an essay-style written response is required.
# Markers are intentionally specific to avoid false positives from sidebar
# category lists ("essay scholarships, no essay scholarships, ...") and "you
# may also like" panels that name other scholarships with "essay" in them.
# Each marker must imply an action or structural requirement, not just be a
# bare topic-tag.
ESSAY_MARKERS = (
    # Action verbs paired with essay (singular and plural)
    "submit an essay",
    "submit the essay",
    "submit your essay",
    "submit essays",
    "submit a personal statement",
    "write an essay",
    "write the essay",
    "write essays",
    "write a personal statement",
    "complete an essay",
    "complete the essay",
    "complete essays",
    "compose an essay",
    "upload your essay",
    "essay submission",
    "required essay",
    "required essays",
    "essays demonstrating",
    "essays showing",
    "essays explaining",
    # Structural phrases that name an essay requirement
    "essay prompt",
    "essay topic",
    "essay question",
    "essay requirement",
    "essay required",
    "essay must",
    "essay should",
    "essay describing",
    "essay explaining",
    "essay about",
    "essay on the topic",
    "essay response",
    "in essay form",
    # Statement / narrative variants
    "personal statement",
    "personal narrative",
    "written response",
    "writing sample",
    "short-answer",
    # Word-count constraints (rare in sidebars)
    "word count",
    "word limit",
    "word minimum",
    "word maximum",
    "minimum word",
    "maximum word",
    "words minimum",
    "words maximum",
    "word essay",
    # Research-paper variants (functionally an essay for effort scoring)
    "submit a research paper",
    "provide a research paper",
    "submit an original research paper",
    "provide an original research paper",
    "original research paper",
    "research paper required",
    "an original research paper",
    "research paper or abstract",
)

# Regex patterns covering numeric word-count requirements that vary in form,
# e.g. "minimum 1,500 words", "500-word essay", "750 word personal statement".
import re as _re
ESSAY_REGEX = (
    _re.compile(r"\bminimum\s+\d[\d,]*\s+words?\b", _re.IGNORECASE),
    _re.compile(r"\bmaximum\s+\d[\d,]*\s+words?\b", _re.IGNORECASE),
    _re.compile(r"\b\d[\d,]*[-\s]+word\s+(?:essay|statement|response|paper|narrative|answer)\b", _re.IGNORECASE),
    _re.compile(r"\bessay\s+of\s+\d[\d,]*\s+words?\b", _re.IGNORECASE),
    _re.compile(r"\bin\s+\d[\d,]*\s+words?\b", _re.IGNORECASE),
)

# Phrases that explicitly disclaim an essay requirement. Bare "no essay" is
# excluded because scholarships.com's "you may also like" sidebar lists rival
# scholarships with "no essay" in their titles.
NO_ESSAY_MARKERS = (
    "no essay required",
    "no essay needed",
    "no essay is required",
    "no essay is needed",
    "no writing required",
    "no written response required",
    "without writing an essay",
    "essay not required",
    "application form only",
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class _TextStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "noscript"):
            self.skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip and data.strip():
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def scan_url(url: str, *, timeout: float = 12.0) -> tuple[Verdict, str]:
    """Fetch URL and classify essay requirement. Returns (verdict, evidence)."""
    try:
        resp = requests.get(
            url, timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"},
            allow_redirects=True,
        )
    except requests.RequestException as e:
        return "unknown", f"fetch failed: {type(e).__name__}: {e}"
    if not resp.ok:
        return "unknown", f"http {resp.status_code}"
    if "text/html" not in resp.headers.get("Content-Type", "").lower():
        return "unknown", f"non-html content-type"
    stripper = _TextStripper()
    try:
        stripper.feed(resp.text)
    except Exception as e:
        return "unknown", f"parse failed: {type(e).__name__}"
    text = stripper.text().lower()
    if not text:
        return "unknown", "page text empty (likely JS-rendered)"
    essay_hit = _first_match(text, ESSAY_MARKERS)
    if not essay_hit:
        essay_hit = _first_regex(text, ESSAY_REGEX)
    no_essay_hit = _first_match(text, NO_ESSAY_MARKERS)
    if essay_hit:
        return "essay", f"matched: {essay_hit!r}"
    if no_essay_hit:
        return "no-essay", f"matched: {no_essay_hit!r}"
    return "unknown", "no markers found"


def _first_regex(text: str, patterns: tuple) -> str | None:
    for p in patterns:
        m = p.search(text)
        if m:
            return m.group(0)
    return None


def _first_match(text: str, markers: tuple[str, ...]) -> str | None:
    for m in markers:
        if m in text:
            return m
    return None


def main() -> int:
    """CLI: scripts.page_scan <url>  -> prints verdict and evidence."""
    import sys
    if len(sys.argv) < 2:
        print("usage: page_scan <url>", file=sys.stderr)
        return 2
    verdict, evidence = scan_url(sys.argv[1])
    print(f"{verdict}\t{evidence}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
