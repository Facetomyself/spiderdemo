"""Print status codes for possible page endpoints. No bodies."""

from modules.runtime import SpiderSession

PATHS = [
    "/authentication/api/jsvmp2_challenge/page/?challenge_type=jsvmp2_challenge&page=2",
    "/authentication/api/jsvmp2_challenge/page/2/?challenge_type=jsvmp2_challenge",
    "/authentication/api/jsvmp2_challenge/data/?challenge_type=jsvmp2_challenge&page=2",
    "/authentication/api/jsvmp2_challenge/?challenge_type=jsvmp2_challenge&page=2",
    "/ws/",
    "/authentication/api/jsvmp2_challenge/submit/",
]
REFERER = "https://www.spiderdemo.cn/authentication/jsvmp2_challenge/?challenge_type=jsvmp2_challenge"


def main() -> None:
    session = SpiderSession()
    with session.client({"Referer": REFERER, "Accept": "application/json"}) as client:
        for path in PATHS:
            response = client.get(path)
            print(response.status_code, path, response.headers.get("content-type", ""), len(response.content))


if __name__ == "__main__":
    main()
