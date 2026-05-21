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
