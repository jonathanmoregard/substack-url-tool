"""trafilatura wrapper. HTML -> (title, body_text)."""
from __future__ import annotations

from typing import Literal

import trafilatura

Format = Literal["txt", "markdown"]


class ExtractionError(RuntimeError):
    pass


def extract_article(html: str, output_format: Format = "txt") -> tuple[str, str]:
    """Returns (title, body). `output_format` selects 'txt' or 'markdown'.

    Markdown preserves bold/italic/headers/lists/blockquotes — needed downstream
    when a prose-decorate stage maps those structural cues to TTS prosody tags.
    """
    body = trafilatura.extract(
        html,
        output_format=output_format,
        include_comments=False,
        include_tables=False,
        include_images=False,
        include_links=False,
        include_formatting=output_format == "markdown",
        favor_precision=True,
    )
    if not body or not body.strip():
        raise ExtractionError("no article body extracted")

    title = ""
    meta = trafilatura.extract_metadata(html)
    if meta is not None:
        title = (meta.title or "").strip()

    return title, body.strip()
