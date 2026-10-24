"""Look for a public writeup phrase without saving the page."""

from curl_cffi import requests as curl

URLS = [
    "https://www.52pojie.cn/thread-2076005-1-1.html",
    "https://blog.csdn.net/qq_53444631/article/details/153781127",
]
NEEDLES = ["jsvmp_secret_key", "authToken", "X-Protobuf-Request", "getCssEncryptedData", "鉴权"]


def main() -> None:
    for url in URLS:
        response = curl.get(url, impersonate="chrome120", timeout=30)
        text = response.text
        print("url", response.status_code, len(text), "title", text[text.find("<title>"):text.find("</title>") + 8][:80] if "<title>" in text else "")
        for needle in NEEDLES:
            print(" ", needle, text.find(needle))


if __name__ == "__main__":
    main()
