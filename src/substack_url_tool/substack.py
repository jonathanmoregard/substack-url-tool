"""Substack-specific post-processing of trafilatura output."""
from __future__ import annotations

import re
from urllib.parse import urlparse

_NOISE = re.compile(
    r"^(?:"
    r"subscribe"
    r"|share"
    r"|share this post"
    r"|leave a comment"
    r"|thanks for reading.*"
    r"|if you (?:liked|enjoyed) this.*"
    r")$",
    re.IGNORECASE,
)

_FOOTNOTE_REF = re.compile(r"^(?:\[\d+\]|\d+\.)$")

_PAYWALL_MARKERS = (
    'class="paywall"',
    'class="single-post-paywall"',
    'data-paywalled="true"',
    "subscriber-only-content",
)


def is_substack(url: str, html: str | None = None) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if host == "substack.com" or host.endswith(".substack.com"):
        return True
    if html and "substack.com" in html.lower():
        low = html.lower()
        return (
            '<link rel="canonical"' in low and "substack.com" in low
        ) or 'property="og:site_name" content="substack"' in low
    return False


def detect_paywall(html: str) -> bool:
    low = html.lower()
    return any(m in low for m in _PAYWALL_MARKERS)


def clean_substack(text: str) -> str:
    """Strip CTAs, footnote markers, collapse 3+ blank lines."""
    out: list[str] = []
    prev_blank = False
    for raw in text.split("\n"):
        line = raw.rstrip()
        stripped = line.strip()
        if _NOISE.match(stripped) or _FOOTNOTE_REF.match(stripped):
            continue
        if stripped == "":
            if prev_blank:
                continue
            prev_blank = True
            out.append("")
        else:
            prev_blank = False
            out.append(line)

    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)
