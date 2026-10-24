"""See how the public verify endpoint answers a dummy token."""

from __future__ import annotations

import httpx


def main() -> None:
    body = {
        "siteKey": "9d4295076aaef0b4c16e18e4f53b5120",
        "wsToken": "probe",
    }
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        response = client.post("https://captcha.wangluozhe.com/api/verify", json=body)
        print("verify", response.status_code, response.headers.get("content-type"), response.text[:300])
        response = client.get("https://captcha.wangluozhe.com/api/verify")
        print("get", response.status_code, response.text[:180])


if __name__ == "__main__":
    main()
