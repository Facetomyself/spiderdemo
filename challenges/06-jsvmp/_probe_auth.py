"""Post protobuf auth variants. Prints status and public error text only."""

import base64
import json
import time
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from modules.runtime import SpiderSession

ROOT = Path(__file__).resolve().parent
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
PLUGINS = "PDF Viewer, Chrome PDF Viewer, Chromium PDF Viewer"
URL = "/authentication/api/jsvmp_challenge/page/1/?challenge_type=jsvmp_challenge"


def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        piece = value & 0x7F
        value >>= 7
        if value:
            out.append(piece | 0x80)
        else:
            out.append(piece)
            return bytes(out)


def field_varint(field: int, value: int) -> bytes:
    return varint((field << 3) | 0) + varint(value)


def field_bytes(field: int, payload: bytes) -> bytes:
    return varint((field << 3) | 2) + varint(len(payload)) + payload


def field_str(field: int, text: str) -> bytes:
    return field_bytes(field, text.encode("utf-8"))


def signed64(value: int) -> bytes:
    if value < 0:
        value += 1 << 64
    return varint(value)


def load_keys():
    unique = json.loads((ROOT / "vm-strings.json").read_text(encoding="utf-8"))["unique"]
    pems = []
    for item in unique:
        if not str(item).startswith("-----BEGIN PUBLIC KEY-----"):
            continue
        lines = [line.strip() for line in str(item).splitlines() if line.strip()]
        pems.append("\n".join(lines) + "\n")
    keys = []
    for pem in pems:
        key = serialization.load_pem_public_key(pem.encode("utf-8"))
        numbers = key.public_numbers()
        hex_n = f"{numbers.n:x}"
        keys.append(key)
        print(f"key bits={numbers.n.bit_length()} e={numbers.e} head={hex_n[:8]} tail={hex_n[-8:]}")
    return keys[0]


def rsa_b64(key, text: str) -> str:
    cipher = key.encrypt(text.encode("utf-8"), padding.PKCS1v15())
    return base64.b64encode(cipher).decode("ascii")


def fingerprint(ua_field: str, timezone: int, signed: bool) -> bytes:
    zone = signed64(timezone) if signed else varint(timezone)
    nested = b"".join(
        [
            field_str(1, ua_field),
            field_str(2, "zh-CN"),
            field_str(3, "1920x1080"),
            field_str(4, "24"),
            varint((5 << 3) | 0) + zone,
            field_varint(6, 1),
            field_str(7, PLUGINS),
            field_varint(8, 1),
            field_varint(9, 0),
        ]
    )
    return field_bytes(5, nested)


def frame(page: int, token: str, timestamp: int, fp: bytes) -> bytes:
    message = b"".join(
        [
            field_varint(1, page),
            field_str(2, "jsvmp_challenge"),
            field_str(3, token),
            field_varint(4, timestamp),
            fp,
        ]
    )
    return b"\x00" + len(message).to_bytes(4, "big") + message


def main() -> None:
    print("plugins", len(PLUGINS), "ua", len(CHROME_UA), "ua80", len(CHROME_UA[:80]))
    key = load_keys()
    ua_token = rsa_b64(key, CHROME_UA[:80])
    now = int(time.time())
    samples = []
    for year in (2025, 2024, 2022, 2026, 2023):
        plain = base64.b64encode(f"{now}_jsvmp_secret_key_{year}".encode()).decode()
        samples.append((f"b64-{year}-tz32", rsa_b64(key, plain), fingerprint(ua_token, 32, False)))
    raw = f"{now}_jsvmp_secret_key_2025"
    samples.append(("raw-2025-tz32", rsa_b64(key, raw), fingerprint(ua_token, 32, False)))
    plain = base64.b64encode(f"{now}_jsvmp_secret_key_2025".encode()).decode()
    token = rsa_b64(key, plain)
    samples.append(("b64-2025-tz-480", token, fingerprint(ua_token, -480, True)))
    samples.append(("b64-2025-ua-raw", token, fingerprint(CHROME_UA[:80], 32, False)))
    session = SpiderSession()
    headers = {
        "Content-Type": "application/grpc-web+proto",
        "X-Protobuf-Request": "1",
        "Accept": "application/grpc-web+proto, application/json, */*",
        "User-Agent": CHROME_UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.spiderdemo.cn/authentication/jsvmp_challenge?challenge_type=jsvmp_challenge",
        "Origin": "https://www.spiderdemo.cn",
    }
    with session.client(headers) as client:
        for name, auth, fp in samples:
            response = client.post(URL, content=frame(1, auth, now, fp))
            text = response.content[:180].decode("utf-8", "replace").replace("\n", " ")
            safe_headers = {
                key: value
                for key, value in response.headers.items()
                if key.lower() not in {"set-cookie", "cookie"}
            }
            print(name, response.status_code, len(response.content), text)
            print(" headers", safe_headers)
            if response.status_code == 429:
                time.sleep(2)
            else:
                time.sleep(0.4)


if __name__ == "__main__":
    main()
