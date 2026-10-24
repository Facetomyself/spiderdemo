from modules.runtime import SpiderSession

def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        response = client.get(
            "/captcha/api/wlzshield_captcha_challenge/init/?challenge_type=wlzshield_captcha_challenge"
        )
        payload = response.json()
        page = payload.get("page_data") or []
        print(
            "status", response.status_code,
            "success", payload.get("success"),
            "passed", payload.get("has_passed_before"),
            "pages", payload.get("total_pages"),
            "count", len(page),
            "message", payload.get("message"),
        )

if __name__ == "__main__":
    main()
