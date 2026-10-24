"""Show page payload shape and whether key-<digits> passes format checks."""

from __future__ import annotations

from modules.runtime import SpiderSession, public_result

REFERER = "https://www.spiderdemo.cn/authentication/panel_challenge/?challenge_type=panel_challenge"


def shape(value, depth=0):
    if isinstance(value, dict):
        return {key: shape(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        return [shape(item, depth + 1) for item in value[:3]] + (["..."] if len(value) > 3 else [])
    return type(value).__name__


def main() -> None:
    session = SpiderSession()
    with session.client({"Referer": REFERER}) as client:
        init = client.get("/authentication/api/panel_challenge/init/?challenge_type=panel_challenge")
        body = init.json()
        print("init_shape", shape(body))
        page = client.get("/authentication/api/panel_challenge/page/2/?challenge_type=panel_challenge")
        payload = page.json()
        print("page_shape", shape(payload))
        data = payload.get("page_data")
        if isinstance(data, list):
            print("sample_types", [type(item).__name__ for item in data])
            print("sample", data)
        response = client.post(
            "/authentication/api/panel_challenge/submit/",
            json={"challenge_type": "panel_challenge", "answer": "key-1"},
        )
        print("format", response.status_code, public_result(response.json()))


if __name__ == "__main__":
    main()
