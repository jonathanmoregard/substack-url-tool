import httpx
import pytest
from pytest_httpx import HTTPXMock

from substack_url_tool.fetch import FetchError, fetch_html


def test_fetch_returns_text(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url="https://example.com/post", text="<html>hi</html>")
    assert fetch_html("https://example.com/post") == "<html>hi</html>"


def test_fetch_follows_redirects(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://example.com/old",
        status_code=301,
        headers={"location": "https://example.com/new"},
    )
    httpx_mock.add_response(url="https://example.com/new", text="<html>redirected</html>")
    assert fetch_html("https://example.com/old") == "<html>redirected</html>"


def test_fetch_retries_on_500_then_succeeds(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url="https://example.com/p", status_code=500)
    httpx_mock.add_response(url="https://example.com/p", text="<html>ok</html>")
    sleeps: list[float] = []
    assert (
        fetch_html("https://example.com/p", retries=2, sleep=sleeps.append)
        == "<html>ok</html>"
    )
    assert sleeps == [1.0]


def test_fetch_raises_after_all_5xx(httpx_mock: HTTPXMock):
    for _ in range(3):
        httpx_mock.add_response(url="https://example.com/p", status_code=503)
    with pytest.raises(FetchError, match="503"):
        fetch_html("https://example.com/p", retries=2, sleep=lambda _: None)


def test_fetch_raises_immediately_on_4xx(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url="https://example.com/p", status_code=404)
    with pytest.raises(FetchError, match="404"):
        fetch_html("https://example.com/p", sleep=lambda _: None)


def test_fetch_retries_on_transport_error(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(httpx.ConnectError("boom"))
    httpx_mock.add_response(url="https://example.com/p", text="ok")
    assert (
        fetch_html("https://example.com/p", retries=2, sleep=lambda _: None)
        == "ok"
    )


def test_fetch_sets_user_agent(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url="https://example.com/p", text="ok")
    fetch_html("https://example.com/p")
    req = httpx_mock.get_request()
    assert req is not None
    assert "substack-url-tool" in req.headers["user-agent"]
