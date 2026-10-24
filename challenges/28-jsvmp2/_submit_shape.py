"""Show the submit endpoint's validation shape. Sends an empty object, not an answer."""

import json

from modules.runtime import SpiderSession

URL = "/authentication/api/jsvmp2_challenge/submit/"
REFERER = "https://www.spiderdemo.cn/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge"


def main() -> None:
    session = SpiderSession()
    with session.client({"Referer": REFERER, "Accept": "application/json"}) as client:
        response = client.post(URL, json={})
        print("status", response.status_code)
        try:
            payload = response.json()
        except json.JSONDecodeError:
            print("text", len(response.content))
            return
        if isinstance(payload, dict):
            print("keys", ",".join(payload.keys()))
            message = payload.get("message") or payload.get("detail") or payload.get("error")
            if isinstance(message, str):
                print("message", message[:160])
        else:
            print("type", type(payload).__name__)


if __name__ == "__main__":
    main()
