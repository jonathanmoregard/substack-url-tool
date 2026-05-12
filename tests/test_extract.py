import pytest

from substack_url_tool.extract import ExtractionError, extract_article

_BASE_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>How Cats Sleep — Tabby Times</title>
  <meta property="og:title" content="How Cats Sleep">
  <meta property="article:author" content="Author Name">
</head>
<body>
  <article>
    <h1>How Cats Sleep</h1>
    <p>Cats sleep up to sixteen hours a day. The exact number depends on age,
       diet, and the quality of available sunbeams.</p>
    <p>Older cats sleep more. Kittens, surprisingly, also sleep a lot.</p>
    <p>This is enough text to satisfy trafilatura's minimum threshold for what
       counts as a real article body. We add another sentence here for safety,
       because precision-mode trafilatura is fussy about short pages.</p>
  </article>
</body>
</html>
"""


def test_extract_pulls_body_and_title():
    title, body = extract_article(_BASE_HTML)
    assert "Cats sleep" in body
    assert "Kittens" in body
    assert "How Cats Sleep" in title


def test_extract_empty_html_raises():
    with pytest.raises(ExtractionError):
        extract_article("<html><body></body></html>")


def test_extract_strips_subscribe_cta_via_substack_postprocess():
    """trafilatura keeps the text; substack post-process is separate."""
    html = _BASE_HTML.replace(
        "<article>", '<article><p>Subscribe</p>'
    )
    title, body = extract_article(html)
    assert "Cats sleep" in body
