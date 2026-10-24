from modules.runtime import SpiderSession

session = SpiderSession()
with session.client(
    headers={
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
        "X-Protobuf-Request": "1",
    }
) as client:
    response = client.get("/authentication/api/jsvmp_challenge/init/?challenge_type=jsvmp_challenge")
    for key, value in response.headers.items():
        if "cookie" in key.lower() or "session" in key.lower():
            print(key, "len", len(value))
        else:
            print(key, value[:120])
    body = response.json()
    print("page_count", len(body.get("page_data") or []), "total", body.get("total_pages"))
