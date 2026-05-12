from substack_url_tool.substack import (
    clean_substack,
    detect_paywall,
    is_substack,
)


def test_is_substack_by_host():
    assert is_substack("https://foo.substack.com/p/x")
    assert is_substack("https://substack.com/p/x")
    assert not is_substack("https://example.com/post")


def test_is_substack_by_canonical_link():
    html = (
        '<html><head><link rel="canonical" href="https://foo.substack.com/p/x">'
        "</head></html>"
    )
    assert is_substack("https://custom-domain.com/post", html)
    assert not is_substack("https://custom-domain.com/post")


def test_detect_paywall_marker_present():
    html = '<html><body><div class="paywall">...</div></body></html>'
    assert detect_paywall(html)


def test_detect_paywall_absent():
    assert not detect_paywall("<html><body><p>free content</p></body></html>")


def test_clean_substack_strips_cta_lines():
    text = (
        "First paragraph.\n\n"
        "Subscribe\n\n"
        "Share\n\n"
        "Real second paragraph.\n\n"
        "Leave a comment\n\n"
        "Thanks for reading my newsletter!\n"
    )
    cleaned = clean_substack(text)
    assert "Subscribe" not in cleaned
    assert "Share" not in cleaned
    assert "Leave a comment" not in cleaned
    assert "Thanks for reading" not in cleaned
    assert "First paragraph." in cleaned
    assert "Real second paragraph." in cleaned


def test_clean_substack_strips_footnote_markers():
    text = "Body line one.\n\n[1]\n\nBody line two.\n\n1.\n\nBody line three."
    cleaned = clean_substack(text)
    assert "[1]" not in cleaned
    assert cleaned.count("Body line") == 3


def test_clean_substack_collapses_multiple_blank_runs():
    text = "A\n\n\n\n\nB"
    assert clean_substack(text) == "A\n\nB"


def test_clean_substack_preserves_paragraph_breaks():
    text = "Para one.\n\nPara two."
    assert clean_substack(text) == "Para one.\n\nPara two."


def test_clean_substack_is_case_insensitive_on_cta():
    text = "Header.\n\nSUBSCRIBE\n\nshare this post\n\nBody."
    cleaned = clean_substack(text)
    assert "SUBSCRIBE" not in cleaned
    assert "share this post" not in cleaned


def test_clean_substack_trims_leading_and_trailing_blanks():
    text = "\n\n\nReal content.\n\n\n"
    assert clean_substack(text) == "Real content."
