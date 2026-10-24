"""Download challenge script and WlzShield SDK. No cookies printed."""

from __future__ import annotations

from pathlib import Path

import httpx

from modules.runtime import SpiderSession

OUT = Path(__file__).resolve().parent


def save(name: str, text: str) -> None:
    path = OUT / name
    path.write_text(text, encoding="utf-8")
    print(name, len(text))


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        page_js = client.get("/static/js/captcha/wlzshield_captcha_challenge.js")
        print("page_js", page_js.status_code, page_js.headers.get("content-type"))
        save("wlzshield_captcha_challenge.js", page_js.text)
        css = client.get("/static/css/captcha/wlzshield_captcha_challenge.css")
        print("css", css.status_code)
        save("wlzshield_captcha_challenge.css", css.text)
        anti = client.get("/static/js/anti_automation.js")
        print("anti", anti.status_code)
        save("anti_automation.js", anti.text)
    with httpx.Client(timeout=30.0, follow_redirects=True) as public:
        for url, name in (
            ("https://captcha.wangluozhe.com/wlzshield.min.js", "wlzshield.min.js"),
            ("https://captcha.wangluozhe.com/vendors.min.js", "vendors.min.js"),
        ):
            response = public.get(url)
            print(name, response.status_code, response.headers.get("content-type"), len(response.content))
            (OUT / name).write_bytes(response.content)


if __name__ == "__main__":
    main()
