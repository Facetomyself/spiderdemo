import json
from pathlib import Path

from modules.runtime import SpiderSession

OUT = Path(__file__).resolve().parent / "init.json"


def main() -> None:
    session = SpiderSession()
    with session.client() as client:
        response = client.get("/authentication/api/jsvmp_challenge/init/?challenge_type=jsvmp_challenge")
        response.raise_for_status()
        payload = response.json()
    OUT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print("saved", payload.get("success"), payload.get("current_page"), payload.get("total_pages"), len(payload.get("page_data") or []))


if __name__ == "__main__":
    main()
