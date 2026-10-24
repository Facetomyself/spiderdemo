"""See which key-number shapes pass the format check. No secrets stored."""

from __future__ import annotations

from modules.runtime import SpiderSession, public_result

SECRET = "wlzshield-check-devtools-v8-spiderdemo-2026-02-09"
REFERER = "https://www.spiderdemo.cn/authentication/panel_challenge/?challenge_type=panel_challenge"
CANDIDATES = [
    SECRET + "-1",
    "key-" + SECRET,
    "SecretKey-" + "1",
    SECRET + "-20260209",
    "key-20260209",
]


def main() -> None:
    session = SpiderSession()
    with session.client({"Referer": REFERER}) as client:
        client.get("/authentication/api/panel_challenge/init/?challenge_type=panel_challenge")
        for answer in CANDIDATES:
            response = client.post(
                "/authentication/api/panel_challenge/submit/",
                json={"challenge_type": "panel_challenge", "answer": answer},
            )
            payload = response.json()
            print(response.status_code, answer[:24], "...", answer[-12:], public_result(payload))


if __name__ == "__main__":
    main()
