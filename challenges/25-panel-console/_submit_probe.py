"""Submit console-key candidates. Print only public judgment fields."""

from __future__ import annotations

import json

from modules.runtime import SpiderSession, public_result

CANDIDATES = [
    "wlzshield-check-devtools-v8-spiderdemo-2026-02-09",
    "SecretKey: wlzshield-check-devtools-v8-spiderdemo-2026-02-09",
]
REFERER = "https://www.spiderdemo.cn/authentication/panel_challenge/?challenge_type=panel_challenge"


def main() -> None:
    session = SpiderSession()
    with session.client({"Referer": REFERER}) as client:
        init = client.get("/authentication/api/panel_challenge/init/?challenge_type=panel_challenge")
        body = init.json()
        print("init", init.status_code, public_result(body if isinstance(body, dict) else {}))
        for answer in CANDIDATES:
            response = client.post(
                "/authentication/api/panel_challenge/submit/",
                json={"challenge_type": "panel_challenge", "answer": answer},
            )
            payload = response.json()
            print("submit", response.status_code, "len", len(answer), public_result(payload if isinstance(payload, dict) else {}))
            if isinstance(payload, dict) and (payload.get("is_correct") is True or "答案正确" in str(payload.get("message") or "")):
                break


if __name__ == "__main__":
    main()
