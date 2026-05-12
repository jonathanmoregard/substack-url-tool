"""HTTP fetch with retries on transient errors."""
from __future__ import annotations

import time
from typing import Callable

import httpx

USER_AGENT = (
    "substack-url-tool/0.1 (+github.com/jonathanmoregard/substack-url-tool)"
)


class FetchError(RuntimeError):
    pass


def fetch_html(
    url: str,
    *,
    timeout: float = 30.0,
    retries: int = 2,
    sleep: Callable[[float], None] = time.sleep,
    client_factory: Callable[..., httpx.Client] | None = None,
) -> str:
    """Fetch a URL and return decoded text. Retries 5xx + transport errors."""
    backoffs = [1.0, 2.0][:retries]
    last_err: Exception | None = None

    def _new_client() -> httpx.Client:
        if client_factory is not None:
            return client_factory(
                follow_redirects=True,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT},
            )
        return httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )

    for delay in [0.0, *backoffs]:
        if delay:
            sleep(delay)
        try:
            with _new_client() as client:
                resp = client.get(url)
        except (httpx.TransportError, httpx.TimeoutException) as e:
            last_err = e
            continue
        if resp.status_code >= 500:
            last_err = FetchError(
                f"HTTP {resp.status_code} {resp.reason_phrase}".strip()
            )
            continue
        if resp.status_code >= 400:
            raise FetchError(
                f"HTTP {resp.status_code} {resp.reason_phrase}".strip()
            )
        return resp.text

    raise FetchError(f"fetch failed after retries: {last_err}")
