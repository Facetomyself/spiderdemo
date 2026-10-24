"""Authenticated HTTP helpers for spiderdemo challenge solvers.

Cookie and password values stay in the client. Callers must not log them.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, TypeVar

import httpx

from .login.client import ORIGIN, login_from_env

T = TypeVar("T")

DEFAULT_HEADERS = {
    "Accept": "application/json, text/html, */*",
    "Origin": ORIGIN,
    "Referer": ORIGIN + "/",
}


class SessionError(RuntimeError):
    """Login was not accepted, so no challenge request was sent."""


class SpiderSession:
    """One logged-in cookie jar shared by sync and async clients."""

    def __init__(self) -> None:
        login_client, payload = login_from_env()
        if payload.get("success") is not True or not payload.get("session_cookie_set"):
            raise SessionError("login was not accepted")
        self.cookies = httpx.Cookies()
        for cookie in login_client.jar:
            self.cookies.set(
                cookie.name,
                cookie.value,
                domain=cookie.domain or "www.spiderdemo.cn",
                path=cookie.path or "/",
            )

    def client(self, headers: dict[str, str] | None = None) -> httpx.Client:
        merged = dict(DEFAULT_HEADERS)
        if headers:
            merged.update(headers)
        return httpx.Client(
            base_url=ORIGIN,
            cookies=self.cookies,
            headers=merged,
            timeout=30.0,
            follow_redirects=True,
        )

    def async_client(self, headers: dict[str, str] | None = None) -> httpx.AsyncClient:
        merged = dict(DEFAULT_HEADERS)
        if headers:
            merged.update(headers)
        return httpx.AsyncClient(
            base_url=ORIGIN,
            cookies=self.cookies,
            headers=merged,
            timeout=30.0,
            follow_redirects=True,
        )


async def collect_pages(
    fetch_page: Callable[[int], Awaitable[T]],
    pages: Iterable[int],
    concurrency: int = 8,
) -> dict[int, T]:
    """Fetch many pages concurrently. Results are keyed by page number."""
    if concurrency < 1:
        raise ValueError("concurrency must be at least 1")
    gate = asyncio.Semaphore(concurrency)

    async def run(page: int) -> tuple[int, T]:
        async with gate:
            return page, await fetch_page(page)

    pairs = await asyncio.gather(*(run(page) for page in pages))
    return {page: value for page, value in pairs}


def public_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep only fields that show whether the site accepted the answer."""
    kept: dict[str, Any] = {}
    for key in ("success", "message", "msg", "error", "score", "correct", "is_correct", "completed"):
        if key in payload:
            kept[key] = payload[key]
    return kept
