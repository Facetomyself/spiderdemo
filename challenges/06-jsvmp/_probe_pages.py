"""Search for a JSON page feed. Prints page index and a short hash, not the numbers."""

import hashlib
import json

from modules.runtime import SpiderSession

BASE = "/authentication/api/jsvmp_challenge"


def mark(payload: object) -> str:
    if not isinstance(payload, dict):
        return type(payload).__name__
    data = payload.get("page_data", payload.get("numbers"))
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:8]
    return "page=" + str(payload.get("current_page")) + " n=" + str(len(data) if isinstance(data, list) else data) + " h=" + digest


def show(label: str, response) -> None:
    text = response.content[:140].decode("utf-8", "replace").replace("\n", " ")
    try:
        payload = response.json()
    except Exception:
        payload = None
    print(label, response.status_code, mark(payload) if payload is not None else "", text)


def main() -> None:
    session = SpiderSession()
    headers = {
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
        "Origin": "https://www.spiderdemo.cn",
        "Accept": "application/json, */*",
    }
    urls = [
        BASE + "/init/?challenge_type=jsvmp_challenge&page=2",
        BASE + "/init/?challenge_type=jsvmp_challenge&current_page=2",
        BASE + "/init/?challenge_type=jsvmp_challenge&page_num=2",
        BASE + "/page/2/?challenge_type=jsvmp_challenge",
        BASE + "/page/?challenge_type=jsvmp_challenge&page=2",
    ]
    with session.client(headers) as client:
        for url in urls:
            show("GET " + url.split("jsvmp_challenge", 1)[1], client.get(url))
        show("POST json", client.post(
            BASE + "/page/2/?challenge_type=jsvmp_challenge",
            json={"challenge_type": "jsvmp_challenge", "page": 2},
        ))
        show("POST form", client.post(
            BASE + "/page/2/?challenge_type=jsvmp_challenge",
            data={"challenge_type": "jsvmp_challenge", "page": 2},
        ))


if __name__ == "__main__":
    main()
