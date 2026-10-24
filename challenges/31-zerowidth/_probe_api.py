"""Probe spiderking endpoints. Print status, keys, and shapes only."""

from __future__ import annotations

import json

from modules.runtime import SpiderSession

PATHS = [
    "/authentication/api/spiderking_challenge/init/?challenge_type=spiderking_challenge",
    "/authentication/api/spiderking_challenge/page/1/?challenge_type=spiderking_challenge",
    "/authentication/api/spiderking_challenge/worker/",
    "/static/js/spiderking_worker.js",
    "/authentication/spiderking_challenge/worker.js",
]

ZW = "\u200b\u200c\u200d\ufeff\u2060\u180e"


def zw_count(text: str) -> int:
    return sum(text.count(char) for char in ZW)


def summarize(value: object) -> object:
    if isinstance(value, str):
        return {"t": "str", "n": len(value), "zw": zw_count(value)}
    if isinstance(value, list):
        sample = type(value[0]).__name__ if value else None
        return {"t": "list", "n": len(value), "sample_t": sample}
    if isinstance(value, dict):
        return {"t": "dict", "keys": list(value.keys())[:30]}
    if isinstance(value, (int, float, bool)) or value is None:
        return {"t": type(value).__name__, "v": value}
    return {"t": type(value).__name__}


def main() -> None:
    session = SpiderSession()
    headers = {"Referer": "https://www.spiderdemo.cn/authentication/spiderking_challenge/"}
    with session.client(headers) as client:
        for path in PATHS:
            response = client.get(path)
            text = response.text
            print("PATH", path)
            print(" status", response.status_code, "len", len(response.content), "zw", zw_count(text))
            if text[:1] in "{[":
                try:
                    payload = response.json()
                except json.JSONDecodeError:
                    print(" head", repr(text[:160]))
                    continue
                if isinstance(payload, dict):
                    print(" keys", list(payload.keys()))
                    print(" summary", json.dumps({key: summarize(value) for key, value in payload.items()}, ensure_ascii=False))
                else:
                    print(" json_t", type(payload).__name__, "n", len(payload) if hasattr(payload, "__len__") else None)
            else:
                print(" head", repr(text[:180]))


if __name__ == "__main__":
    main()
