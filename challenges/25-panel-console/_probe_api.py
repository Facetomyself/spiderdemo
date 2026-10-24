"""Probe panel init and page endpoints. Print only status and public keys."""

from __future__ import annotations

import json

from modules.runtime import SpiderSession

PAGE = "/authentication/panel_challenge/?challenge_type=panel_challenge"


def brief(payload: object) -> str:
    if not isinstance(payload, dict):
        return type(payload).__name__
    keys = sorted(payload.keys())
    parts = [f"keys={keys}"]
    for key in ("success", "message", "msg", "error", "code", "need_init"):
        if key in payload:
            parts.append(f"{key}={payload[key]!r}")
    data = payload.get("page_data")
    if isinstance(data, list):
        parts.append(f"page_data_len={len(data)}")
    return " ".join(parts)


def main() -> None:
    session = SpiderSession()
    with session.client({"Referer": "https://www.spiderdemo.cn" + PAGE}) as client:
        for path in (
            "/authentication/api/panel_challenge/init/?challenge_type=panel_challenge",
            "/authentication/api/panel_challenge/page/1/?challenge_type=panel_challenge",
            "/authentication/api/panel_challenge/page/2/?challenge_type=panel_challenge",
        ):
            response = client.get(path)
            try:
                payload = response.json()
            except json.JSONDecodeError:
                payload = {"error": "non-json", "len": len(response.content)}
            print(response.status_code, path.split("?")[0], brief(payload))


if __name__ == "__main__":
    main()
