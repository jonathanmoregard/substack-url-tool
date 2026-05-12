# substack-url-tool

Substack article URL -> CleanText (UTF-8) on stdout. Composes with `tts-tool`.

```
substack-url-tool https://example.substack.com/p/some-post > article.txt
substack-url-tool "$URL" | tts-tool -o article.mp3
```

## CleanText shape

```
Article title

First paragraph...

Second paragraph...
```

- Line 1: title. Line 2: blank. Lines 3+: body.
- Paragraphs separated by `\n\n`.
- No markdown, no HTML, no image captions, no Subscribe/Share CTAs, no
  footnote markers. Footnote bodies are dropped in v0.1.
- Code blocks become `[code omitted]` on their own line.

## Install (dev)

```sh
nix develop
uv sync --all-extras
uv run pytest
uv run substack-url-tool --help
```

## Install (Nix flake)

```sh
nix run github:jonathanmoregard/substack-url-tool -- "$URL"
nix profile install github:jonathanmoregard/substack-url-tool
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Fetch error (network, 4xx, 5xx) |
| 2 | Extraction error (no article body) |
| 3 | Invalid input (bad URL) |

## Known limits (v0.1)

- No paywall handling. Paywalled posts emit only the public preview; a
  warning is printed to stderr.
- Tuned for `*.substack.com` and equivalent. Other hosts may work via
  trafilatura fallback but aren't guaranteed.
- English only (sentence boundary detection downstream is English-tuned).
