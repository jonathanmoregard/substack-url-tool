"""trafilatura wrapper. HTML -> (title, body_text)."""
from __future__ import annotations

import trafilatura


class ExtractionError(RuntimeError):
    pass


def extract_article(html: str) -> tuple[str, str]:
    body = trafilatura.extract(
        html,
        output_format="txt",
        include_comments=False,
        include_tables=False,
        include_images=False,
        include_links=False,
        favor_precision=True,
    )
    if not body or not body.strip():
        raise ExtractionError("no article body extracted")

    title = ""
    meta = trafilatura.extract_metadata(html)
    if meta is not None:
        title = (meta.title or "").strip()

    return title, body.strip()
