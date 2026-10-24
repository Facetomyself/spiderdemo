"""Solve the protobuf challenge with a local modified MD4 and protobuf body."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "protobuf_challenge"
PAGE_URL = "/authentication/api/protobuf_challenge/page/{page}/"
INIT_URL = "/authentication/api/protobuf_challenge/init/?challenge_type=" + CHALLENGE
SUBMIT_URL = "/authentication/api/protobuf_challenge/submit/"
HERE = Path(__file__).resolve().parent


def _rot(value: int, bits: int) -> int:
    value &= 0xFFFFFFFF
    return ((value << bits) | (value >> (32 - bits))) & 0xFFFFFFFF


def _f(x: int, y: int, z: int) -> int:
    return ((~x & z) | (y & x)) & 0xFFFFFFFF


def _g(x: int, y: int, z: int) -> int:
    return ((x & y) | (x & z) | (y & z)) & 0xFFFFFFFF


def _h(x: int, y: int, z: int) -> int:
    return (x ^ y ^ z) & 0xFFFFFFFF


def _js_byte(char: str) -> int:
    # Bitwise ops coerce with ToNumber, so a digit character is its value, not its code point.
    return int(char) if char.isdigit() else 0


def modified_md4(text: str) -> str:
    """MD4 variant: numeric character bytes, and a 32-bit length repeated into both length words."""
    raw = [_js_byte(char) for char in text]
    bit_len = len(raw) * 8
    padded = bytearray(raw)
    padded.append(0x80)
    while (len(padded) * 8 + 64) % 512 != 0:
        padded.append(0)
    low = bit_len & 0xFFFFFFFF
    for index in range(8):
        padded.append((low >> ((index * 8) & 31)) & 0xFF)

    a, b, c, d = 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476
    for offset in range(0, len(padded), 64):
        words = [
            int.from_bytes(padded[offset + i * 4 : offset + i * 4 + 4], "little")
            for i in range(16)
        ]
        aa, bb, cc, dd = a, b, c, d
        for i in range(16):
            shift = (3, 7, 11, 19)[i & 3]
            if i & 3 == 0:
                aa = _rot(aa + _f(bb, cc, dd) + words[i], shift)
            elif i & 3 == 1:
                dd = _rot(dd + _f(aa, bb, cc) + words[i], shift)
            elif i & 3 == 2:
                cc = _rot(cc + _f(dd, aa, bb) + words[i], shift)
            else:
                bb = _rot(bb + _f(cc, dd, aa) + words[i], shift)
        order = (0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15)
        for i, word in enumerate(order):
            shift = (3, 5, 9, 13)[i & 3]
            mixed = words[word] + 0x5A827999
            if i & 3 == 0:
                aa = _rot(aa + _g(bb, cc, dd) + mixed, shift)
            elif i & 3 == 1:
                dd = _rot(dd + _g(aa, bb, cc) + mixed, shift)
            elif i & 3 == 2:
                cc = _rot(cc + _g(dd, aa, bb) + mixed, shift)
            else:
                bb = _rot(bb + _g(cc, dd, aa) + mixed, shift)
        order = (0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15)
        for i, word in enumerate(order):
            shift = (3, 9, 11, 15)[i & 3]
            mixed = words[word] + 0x6ED9EBA1
            if i & 3 == 0:
                aa = _rot(aa + _h(bb, cc, dd) + mixed, shift)
            elif i & 3 == 1:
                dd = _rot(dd + _h(aa, bb, cc) + mixed, shift)
            elif i & 3 == 2:
                cc = _rot(cc + _h(dd, aa, bb) + mixed, shift)
            else:
                bb = _rot(bb + _h(cc, dd, aa) + mixed, shift)
        a = (a + aa) & 0xFFFFFFFF
        b = (b + bb) & 0xFFFFFFFF
        c = (c + cc) & 0xFFFFFFFF
        d = (d + dd) & 0xFFFFFFFF
    digest = b"".join(part.to_bytes(4, "little") for part in (a, b, c, d))
    return digest.hex()


def encrypt_type(value: str) -> str:
    return "".join(chr(ord(char) + 3) for char in value)


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


def _signed(value: int) -> int:
    if value >= 2**63:
        return value - 2**64
    return value


def encode_page_request(page: int, challenge: str, timestamp: int) -> bytes:
    signature = modified_md4(str(timestamp))
    encoded_type = encrypt_type(challenge).encode()
    signature_bytes = signature.encode()
    return b"".join(
        (
            _varint(1 << 3) + _varint(page),
            _varint((2 << 3) | 2) + _varint(len(encoded_type)) + encoded_type,
            _varint(3 << 3) + _varint(timestamp),
            _varint((4 << 3) | 2) + _varint(len(signature_bytes)) + signature_bytes,
        )
    )


def decode_numbers(payload: bytes) -> list[int]:
    index = 0
    numbers: list[int] = []
    while index < len(payload):
        key, index = _read_varint(payload, index)
        field, wire = key >> 3, key & 7
        if wire == 0:
            _, index = _read_varint(payload, index)
        elif wire == 2:
            length, index = _read_varint(payload, index)
            chunk = payload[index : index + length]
            index += length
            if field == 1:
                numbers.append(_number_value(chunk))
        elif wire == 5:
            index += 4
        elif wire == 1:
            index += 8
        else:
            raise ValueError("unsupported protobuf wire type")
    return numbers


def _number_value(payload: bytes) -> int:
    index = 0
    value = 0
    while index < len(payload):
        key, index = _read_varint(payload, index)
        field, wire = key >> 3, key & 7
        if wire == 0:
            number, index = _read_varint(payload, index)
            if field == 2:
                value = _signed(number)
        elif wire == 2:
            length, index = _read_varint(payload, index)
            index += length
        elif wire == 5:
            index += 4
        elif wire == 1:
            index += 8
        else:
            raise ValueError("unsupported protobuf wire type")
    return value


async def _request_page(client, page: int) -> list[int]:
    delay = 0.5
    last_status = 0
    for _ in range(8):
        timestamp = int(time.time() * 1000)
        response = await client.post(
            PAGE_URL.format(page=page),
            content=encode_page_request(page, CHALLENGE, timestamp),
            headers={"Content-Type": "application/x-protobuf"},
        )
        last_status = response.status_code
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            continue
        if response.status_code != 200:
            raise RuntimeError(f"page {page} status {response.status_code}")
        numbers = decode_numbers(response.content)
        if len(numbers) != 10:
            raise RuntimeError(f"page {page} returned {len(numbers)} numbers")
        return numbers
    raise RuntimeError(f"page {page} stayed at status {last_status}")


async def solve() -> dict:
    session = SpiderSession()
    headers = {"Referer": "https://www.spiderdemo.cn/authentication/protobuf_challenge/?challenge_type=protobuf_challenge"}
    async with session.async_client(headers=headers) as client:
        init = await client.get(INIT_URL)
        if init.status_code == 429:
            await asyncio.sleep(1.0)
            init = await client.get(INIT_URL)
        if init.status_code != 200:
            raise RuntimeError(f"init status {init.status_code}")
        init_payload = init.json()
        if init_payload.get("success") is not True:
            raise RuntimeError("init was not accepted")
        async def fetch_page(page: int) -> list[int]:
            return await _request_page(client, page)

        pages = await collect_pages(fetch_page, range(1, 101), concurrency=4)
        missing = [page for page in range(1, 101) if page not in pages]
        if missing:
            raise RuntimeError(f"missing pages {missing[:5]}")
        total = sum(sum(pages[page]) for page in range(1, 101))
        submitted = await client.post(
            SUBMIT_URL,
            json={"challenge_type": CHALLENGE, "answer": total},
        )
        if submitted.status_code == 429:
            await asyncio.sleep(1.0)
            submitted = await client.post(
                SUBMIT_URL,
                json={"challenge_type": CHALLENGE, "answer": total},
            )
        if submitted.status_code != 200:
            raise RuntimeError(f"submit status {submitted.status_code}")
        payload = submitted.json()
    result = public_result(payload)
    if not result:
        result = {
            key: value
            for key, value in payload.items()
            if key in ("success", "message", "msg", "error", "score", "correct", "is_correct", "completed")
        }
    (HERE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    result = asyncio.run(solve())
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
