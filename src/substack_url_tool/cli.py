"""substack-url-tool entrypoint."""
from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

from . import extract, fetch, substack

EXIT_OK = 0
EXIT_FETCH = 1
EXIT_EXTRACT = 2
EXIT_INVALID = 3


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="substack-url-tool",
        description=(
            "Substack article URL -> CleanText (UTF-8) on stdout. "
            "Use --format markdown to preserve bold/italic/headers/blockquotes "
            "for downstream prose-decorate / SSML pipelines."
        ),
    )
    p.add_argument("url", help="Article URL (http:// or https://).")
    p.add_argument(
        "-f", "--format",
        choices=["txt", "markdown"],
        default="txt",
        help="Output format. 'txt' (default) is back-compat plain text; "
             "'markdown' preserves inline formatting for prose-decorate.",
    )
    return p


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
    except ValueError:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc)


def _fallback_title(url: str) -> str:
    p = urlparse(url)
    segments = [s for s in p.path.split("/") if s]
    last = segments[-1] if segments else (p.hostname or "untitled")
    return last.replace("-", " ").replace("_", " ").strip()


def _format_output(title: str, body: str, fmt: str) -> str:
    if fmt == "markdown":
        return f"# {title}\n\n{body.rstrip()}\n"
    return f"{title}\n\n{body.rstrip()}\n"


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    url = args.url

    if not _valid_url(url):
        _log(f"error: invalid URL: {url}")
        return EXIT_INVALID

    try:
        html = fetch.fetch_html(url)
    except fetch.FetchError as e:
        _log(f"error: {e}")
        return EXIT_FETCH

    is_sub = substack.is_substack(url, html)
    if is_sub and substack.detect_paywall(html):
        _log("warning: paywall detected, output may be truncated")

    try:
        title, body = extract.extract_article(html, output_format=args.format)
    except extract.ExtractionError as e:
        _log(f"error: {e}")
        return EXIT_EXTRACT

    if is_sub:
        body = substack.clean_substack(body)

    if not body.strip():
        _log("error: empty body after Substack cleanup")
        return EXIT_EXTRACT

    title = title.strip() or _fallback_title(url)
    sys.stdout.write(_format_output(title, body, args.format))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
