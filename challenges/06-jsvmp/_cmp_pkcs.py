"""Compare page JSEncrypt output with Python PKCS#1 v1.5.

Stdin is one JSON object. Stdout is lengths and booleans only.
"""

from __future__ import annotations

import base64
import json
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding


def main() -> None:
    data = json.load(sys.stdin)
    plain = data["plain"].encode("utf-8")
    page_pub = serialization.load_pem_public_key(data["page_pub"].encode("utf-8"))
    private_key = serialization.load_pem_private_key(data["priv"].encode("utf-8"), password=None)
    python_page = base64.b64encode(page_pub.encrypt(plain, padding.PKCS1v15())).decode("ascii")
    js_raw = base64.b64decode(data["js_temp"])
    size = private_key.key_size // 8
    if len(js_raw) < size:
        js_raw = b"\x00" * (size - len(js_raw)) + js_raw
    js_roundtrip = False
    try:
        js_roundtrip = private_key.decrypt(js_raw, padding.PKCS1v15()) == plain
    except Exception:
        js_roundtrip = False
    py_roundtrip = False
    try:
        blob = private_key.public_key().encrypt(plain, padding.PKCS1v15())
        py_roundtrip = private_key.decrypt(blob, padding.PKCS1v15()) == plain
    except Exception:
        py_roundtrip = False
    sys.stdout.write(
        json.dumps(
            {
                "py_b64_len": len(python_page),
                "py_raw_len": len(base64.b64decode(python_page)),
                "js_temp_b64_len": len(data["js_temp"]),
                "js_temp_raw_len": len(base64.b64decode(data["js_temp"])),
                "js_roundtrip": js_roundtrip,
                "py_roundtrip": py_roundtrip,
            }
        )
    )


if __name__ == "__main__":
    main()
