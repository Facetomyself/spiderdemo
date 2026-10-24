"""Login client for the spiderdemo practice site.

The request shape comes from RuyiTrace run rt_20261010083653_880526e2a7.
The login POST body is JSON with username and password. It has no captcha field.
A rejected attempt returns success=false and does not set a session cookie.
An accepted attempt returns success=true and Set-Cookie sessionid.
"""

from __future__ import annotations

import json
from http.cookiejar import Cookie, CookieJar
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener

from .env import credentials

ORIGIN = "https://www.spiderdemo.cn"
LOGIN_URL = ORIGIN + "/admin_I/api/auth/login"
USER_STATS_URL = ORIGIN + "/admin_I/api/user/stats"
SESSION_COOKIE = "sessionid"
GATE_COOKIE = "cs_stable_gate"


class LoginError(Exception):
    """The login endpoint did not return a JSON object."""


def build_login_request(username: str, password: str) -> Request:
    """Build the observed login request. The body has only the two credential fields."""
    if not isinstance(username, str) or not username:
        raise ValueError("username is required")
    if not isinstance(password, str) or not password:
        raise ValueError("password is required")
    body = json.dumps(
        {"username": username, "password": password},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return Request(
        LOGIN_URL,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": ORIGIN,
            "Referer": ORIGIN + "/",
        },
    )


def session_cookie_set(jar: CookieJar) -> bool:
    return any(cookie.name == SESSION_COOKIE and cookie.value for cookie in jar)


class LoginClient:
    """Keeps the cookie jar created by one login."""

    def __init__(self, opener: Any | None = None, gate_cookie: str | None = None) -> None:
        self.jar = CookieJar()
        self.opener = opener if opener is not None else build_opener(HTTPCookieProcessor(self.jar))
        if gate_cookie:
            self.jar.set_cookie(_gate_cookie(gate_cookie))

    def login(self, username: str, password: str, timeout: float = 30) -> dict[str, Any]:
        request = build_login_request(username, password)
        try:
            with self.opener.open(request, timeout=timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            raw = exc.read()
        except URLError as exc:
            raise LoginError("login request failed") from exc
        payload = _json_object(raw)
        payload["session_cookie_set"] = session_cookie_set(self.jar)
        return payload

    def user_stats(self, timeout: float = 30) -> dict[str, Any]:
        """Read back the account after a login that stored sessionid."""
        request = Request(
            USER_STATS_URL,
            method="GET",
            headers={"Accept": "application/json", "Referer": ORIGIN + "/"},
        )
        try:
            with self.opener.open(request, timeout=timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            raw = exc.read()
        except URLError as exc:
            raise LoginError("user stats request failed") from exc
        return _json_object(raw)


def login_from_env(path: Path | None = None, timeout: float = 30) -> tuple[LoginClient, dict[str, Any]]:
    """Log in with SPIDERDEMO_USERNAME and SPIDERDEMO_PASSWORD from the project .env."""
    username, password = credentials(path)
    client = LoginClient()
    return client, client.login(username, password, timeout=timeout)


def _json_object(raw: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LoginError("login response was not JSON") from exc
    if not isinstance(payload, dict):
        raise LoginError("login response was not a JSON object")
    return payload


def _gate_cookie(value: str) -> Cookie:
    return Cookie(
        version=0,
        name=GATE_COOKIE,
        value=value,
        port=None,
        port_specified=False,
        domain="www.spiderdemo.cn",
        domain_specified=True,
        domain_initial_dot=False,
        path="/",
        path_specified=True,
        secure=False,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={"HttpOnly": None},
        rfc2109=False,
    )
