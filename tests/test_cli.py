import pytest
from pytest_httpx import HTTPXMock

from substack_url_tool import cli

_ARTICLE_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Post Title — Some Blog</title>
  <link rel="canonical" href="https://foo.substack.com/p/post-slug">
</head>
<body>
  <article>
    <h1>Post Title</h1>
    <p>This is the article body. It is long enough that trafilatura accepts it
       as a real article. We add a couple more sentences to be sure precision
       mode does not reject the short page heuristic.</p>
    <p>Subscribe</p>
    <p>Share</p>
    <p>A second real paragraph, also of reasonable length so the extractor
       is comfortable with this fixture HTML.</p>
    <p>Thanks for reading!</p>
  </article>
</body>
</html>
"""


def test_cli_invalid_url(capsys):
    rc = cli.main(["not-a-url"])
    assert rc == 3
    assert "invalid URL" in capsys.readouterr().err


def test_cli_fetch_failure(httpx_mock: HTTPXMock, capsys, monkeypatch):
    monkeypatch.setattr(
        "substack_url_tool.fetch.time.sleep", lambda _: None
    )
    for _ in range(3):
        httpx_mock.add_response(url="https://foo.substack.com/p/x", status_code=503)
    rc = cli.main(["https://foo.substack.com/p/x"])
    assert rc == 1
    assert "503" in capsys.readouterr().err


def test_cli_extraction_failure(httpx_mock: HTTPXMock, capsys):
    httpx_mock.add_response(
        url="https://foo.substack.com/p/x",
        text="<html><body></body></html>",
    )
    rc = cli.main(["https://foo.substack.com/p/x"])
    assert rc == 2


def test_cli_happy_path_emits_cleantext(httpx_mock: HTTPXMock, capsys):
    httpx_mock.add_response(
        url="https://foo.substack.com/p/post-slug",
        text=_ARTICLE_HTML,
    )
    rc = cli.main(["https://foo.substack.com/p/post-slug"])
    assert rc == 0
    out = capsys.readouterr().out
    lines = out.split("\n")
    assert lines[0].strip() != ""
    assert lines[1] == ""
    assert "Subscribe" not in out
    assert "Share" not in out
    assert "Thanks for reading" not in out
    assert "article body" in out
    assert "second real paragraph" in out.lower()


def test_cli_paywall_warning(httpx_mock: HTTPXMock, capsys, monkeypatch):
    html = _ARTICLE_HTML.replace("<article>", '<article><div class="paywall">x</div>')
    httpx_mock.add_response(
        url="https://foo.substack.com/p/post-slug",
        text=html,
    )
    cli.main(["https://foo.substack.com/p/post-slug"])
    assert "paywall detected" in capsys.readouterr().err


def test_cli_markdown_format_prepends_h1(httpx_mock: HTTPXMock, capsys):
    httpx_mock.add_response(
        url="https://foo.substack.com/p/post-slug",
        text=_ARTICLE_HTML,
    )
    rc = cli.main(["--format", "markdown", "https://foo.substack.com/p/post-slug"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("# ")
    assert out.split("\n")[1] == ""


def test_cli_default_format_is_txt(httpx_mock: HTTPXMock, capsys):
    httpx_mock.add_response(
        url="https://foo.substack.com/p/post-slug",
        text=_ARTICLE_HTML,
    )
    rc = cli.main(["https://foo.substack.com/p/post-slug"])
    assert rc == 0
    out = capsys.readouterr().out
    assert not out.startswith("# ")


def test_cli_does_not_duplicate_title_in_markdown(httpx_mock: HTTPXMock, capsys):
    """trafilatura's markdown body includes the article's H1; the CLI
    must not also prepend the metadata title on top of it. Past bug:
    TTS read the title twice."""
    httpx_mock.add_response(
        url="https://foo.substack.com/p/post-slug",
        text=_ARTICLE_HTML,
    )
    rc = cli.main(["--format", "markdown", "https://foo.substack.com/p/post-slug"])
    assert rc == 0
    out = capsys.readouterr().out
    title_h1_lines = [line for line in out.split("\n") if line.startswith("# ")]
    assert len(title_h1_lines) == 1, f"expected 1 H1 title, got: {title_h1_lines}"


def test_cli_txt_default_does_not_duplicate_title(httpx_mock: HTTPXMock, capsys):
    httpx_mock.add_response(
        url="https://foo.substack.com/p/post-slug",
        text=_ARTICLE_HTML,
    )
    rc = cli.main(["https://foo.substack.com/p/post-slug"])
    assert rc == 0
    out = capsys.readouterr().out
    # The title text appears at most twice across the output (line 1
    # = title; sometimes title also occurs naturally inside body
    # references). What we're guarding against is the
    # title-as-line-1-AND-title-as-line-3 pattern.
    lines = [ln for ln in out.split("\n") if ln.strip()]
    if len(lines) >= 2:
        # First line is the title, second non-blank line must NOT also
        # be just the title (i.e., the article body has real content)
        assert lines[0].strip() != lines[1].strip(), (
            f"title duplicated on consecutive non-blank lines: {lines[:3]}"
        )
