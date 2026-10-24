"""jsvmp_challenge page collector.

Page bodies are CSS-mixed HTML. Each number is split by an empty span.
The span's encrypted value is a two-digit int; the hidden digit is
value - 50 when the value is even, and value - 52 when it is odd.
"""

from __future__ import annotations

import asyncio
import base64
import json
import re
import time
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "jsvmp_challenge"
PAGE_URL = "/authentication/api/jsvmp_challenge/page/{page}/?challenge_type=" + CHALLENGE
INIT_URL = "/authentication/api/jsvmp_challenge/init/?challenge_type=" + CHALLENGE
SUBMIT_URL = "/authentication/api/jsvmp_challenge/submit/?challenge_type=" + CHALLENGE
REFERER = "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=" + CHALLENGE
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) "
    "Gecko/20100101 Firefox/155.0"
)
PLUGINS = (
    "PDF Viewer, Chrome PDF Viewer, Chromium PDF Viewer, "
    "Microsoft Edge PDF Viewer, WebKit built-in PDF"
)
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCHshK1NixnImx08tq3V6Vjvfwk
ARCOJbnPMZr4Ogh16ORkC45CFUB+2gu+IN2vjH3oJaY2e/6y0shD2fURMB3urxKE
3gewRZMm5/T7noAXs4DJTOxJGwAJFHFfd9Zp73vXEcac4DKrvItOkjLx9P5JkA39
47brgsMObYGdG3HOdwIDAQAB
-----END PUBLIC KEY-----"""
KEY = serialization.load_pem_public_key(PUBLIC_KEY.encode())
HERE = Path(__file__).resolve().parent


def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        piece = value & 0x7F
        value >>= 7
        if value:
            out.append(piece | 0x80)
        else:
            out.append(piece)
            return bytes(out)


def _field_varint(field: int, value: int) -> bytes:
    return _varint((field << 3) | 0) + _varint(value)


def _field_bytes(field: int, payload: bytes) -> bytes:
    return _varint((field << 3) | 2) + _varint(len(payload)) + payload


def _rsa_b64(text: str) -> str:
    cipher = KEY.encrypt(text.encode("utf-8"), padding.PKCS1v15())
    return base64.b64encode(cipher).decode("ascii")


def page_body(page: int, stamp: int) -> bytes:
    secret = f"{stamp}_jsvmp_secret_key_2024"
    token = _rsa_b64(base64.b64encode(secret.encode()).decode())
    fingerprint = b"".join(
        [
            _field_bytes(1, _rsa_b64(UA[:80]).encode()),
            _field_bytes(2, b"zh-CN"),
            _field_bytes(3, b"1920x1080"),
            _field_bytes(4, b"24"),
            _field_varint(5, 32),
            _field_varint(6, 1),
            _field_bytes(7, PLUGINS.encode()),
            _field_varint(8, 1),
            _field_varint(9, 0),
        ]
    )
    message = b"".join(
        [
            _field_varint(1, page),
            _field_bytes(2, CHALLENGE.encode()),
            _field_bytes(3, token.encode()),
            _field_varint(4, stamp),
            _field_bytes(5, fingerprint),
        ]
    )
    return b"\x00" + len(message).to_bytes(4, "big") + message


def _read_varint(buf: bytes, index: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        byte = buf[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index
        shift += 7


def _chunks(buf: bytes) -> list[tuple[int, bytes]]:
    index = 0
    found: list[tuple[int, bytes]] = []
    while index < len(buf):
        key, index = _read_varint(buf, index)
        field, wire = key >> 3, key & 7
        if wire == 0:
            _, index = _read_varint(buf, index)
        elif wire == 2:
            length, index = _read_varint(buf, index)
            found.append((field, buf[index : index + length]))
            index += length
        else:
            break
    return found


def decode_numbers(body: bytes) -> list[int]:
    """Rebuild the ten page numbers from the grpc-web CSS payload."""
    payload = body
    if body[:1] == b"\x00" and len(body) >= 5:
        size = int.from_bytes(body[1:5], "big")
        payload = body[5 : 5 + size]
    html = ""
    hidden: list[int] = []
    for _field, chunk in _chunks(payload):
        if b"context_kw" in chunk:
            html = chunk.decode("utf-8")
            continue
        try:
            plain = base64.b64decode(chunk, validate=True).decode("ascii")
        except (ValueError, UnicodeError):
            continue
        parts = [part for part in plain.split(",") if part]
        if len(parts) == 10 and all(part.isdigit() for part in parts):
            hidden = [int(part) for part in parts]
    if not html or len(hidden) != 10:
        raise RuntimeError("css fields missing")
    digits = [item - 50 - 2 * (item % 2) for item in hidden]
    if len(digits) != 10 or any(item < 0 or item > 9 for item in digits):
        raise RuntimeError("css digit transform rejected")
    pieces: list[str] = []
    hole = 0
    for span, text in re.findall(r"(<span class='context_kw\d+'></span>)|([^<]+)", html):
        if span:
            pieces.append(str(digits[hole]))
            hole += 1
        else:
            pieces.append(text)
    if hole != 10:
        raise RuntimeError("css hole count rejected")
    numbers = [int(item) for item in "".join(pieces).split() if item.strip()]
    if len(numbers) != 10:
        raise RuntimeError("css number count rejected")
    return numbers


async def fetch_page(client, page: int) -> list[int]:
    delay = 0.4
    last = ""
    for _ in range(6):
        stamp = int(time.time())
        response = await client.post(
            PAGE_URL.format(page=page),
            content=page_body(page, stamp),
            headers={
                "Content-Type": "application/grpc-web+proto",
                "X-Protobuf-Request": "1",
                "Accept": "application/grpc-web+proto, application/json, */*",
                "User-Agent": UA,
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            continue
        if response.status_code != 200:
            last = response.content[:180].decode("utf-8", "replace")
            raise RuntimeError(f"page {page} status {response.status_code} {last}")
        return decode_numbers(response.content)
    raise RuntimeError(f"page {page} rate limited {last}")


async def solve() -> dict:
    session = SpiderSession()
    headers = {"Referer": REFERER, "Origin": "https://www.spiderdemo.cn"}
    async with session.async_client(headers) as client:
        opened = await client.get(INIT_URL, headers={"Accept": "application/json, */*"})
        init_body = opened.json()
        if opened.status_code != 200 or not isinstance(init_body, dict) or init_body.get("success") is not True:
            detail = ""
            if isinstance(init_body, dict):
                detail = str(init_body.get("error") or init_body.get("message") or "")
            raise RuntimeError(f"init status {opened.status_code} {detail[:80]}")
        expected = init_body.get("page_data")

        async def one(page: int) -> list[int]:
            return await fetch_page(client, page)

        pages = await collect_pages(one, range(1, 101), concurrency=4)
        if len(pages) != 100 or any(len(pages[page]) != 10 for page in range(1, 101)):
            raise RuntimeError(f"collected {len(pages)} pages")
        if isinstance(expected, list) and len(expected) == 10 and pages[1] != [int(item) for item in expected]:
            raise RuntimeError("page 1 did not match the init numbers")
        total = sum(sum(pages[page]) for page in range(1, 101))
        response = await client.post(
            SUBMIT_URL,
            json={"challenge_type": CHALLENGE, "answer": total},
            headers={"Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest"},
        )
        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError(f"submit status {response.status_code}")
        return public_result(body)


def main() -> None:
    try:
        verdict = asyncio.run(solve())
    except RuntimeError as error:
        print(str(error)[:300])
        raise SystemExit(1) from error
    (HERE / "result.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verdict, ensure_ascii=False))


if __name__ == "__main__":
    main()
