"""Reproduce the fsymmetry page signature and submit the 100-page sum."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import time
from pathlib import Path
from urllib.parse import quote

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "fsymmetry_challenge"
HMAC_KEY = b"dsa_secret_key_2025"
OUT = Path(__file__).with_name("result.json")
REFERER = (
    "https://www.spiderdemo.cn/authentication/fsymmetry_challenge/"
    "?challenge_type=fsymmetry_challenge"
)

# PKCS#1 keys embedded in the webpack bundle (JSEncrypt).
PUBLIC_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC1vKwZUIv7pgpJUXXPpDlD4+VE
on3a0ANOrNmqAESrcGfkmYzDCo2JeuYezhBGjBNjwVmSct/Y3BBOCRGT2bvtCJGd
S12RMvHbFcdbwS/Adh48+rhLiMNYXLm+7pI3e2k6TlScxKa7EeeZpVtew/Cv5z6o
l0llNPp6BdqAlOa8DwIDAQAB
-----END PUBLIC KEY-----""".encode()

PRIVATE_PEM = """-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQC1vKwZUIv7pgpJUXXPpDlD4+VEon3a0ANOrNmqAESrcGfkmYzD
Co2JeuYezhBGjBNjwVmSct/Y3BBOCRGT2bvtCJGdS12RMvHbFcdbwS/Adh48+rhL
iMNYXLm+7pI3e2k6TlScxKa7EeeZpVtew/Cv5z6ol0llNPp6BdqAlOa8DwIDAQAB
AoGAS0GaWI9AsFAFEXBgoz/jkMf14DKTgEFEJVexeNLMnNuawhCNuBSOIMCaO2Zk
WfpWaygdUeYs6M3UGKRruXhf92g/BRmJK5FzR0kWW4qw6WwlYob3TPc3c9MFOjmp
VtWQ0VSeEPrnBNoQRccKl0dGBnToHGuV+KEuKx8oWZc/JM0CQQDH/cvlx0BKz2zN
6PM8FidAvc+Wgon8YW81KJgC7iJIrK9FOpctOE3L1pdF7guOQNVGRqN4HCIgLfHE
cqxWJKJtAkEA6KIkwHe/Q23uWH5GP8DHtVkLVfohTumYkpb0rk05EYQ0dsWSNzWH
XDH/kD6ayNq+fscnS8g+59onzvfhJ0bq6wJBAKNFkDEHenWY4js481sauvEgBVnb
OMvSv/emLHQ39cVfNbhPHRzN2rWPe/CbZtO8GmJFSS/FyBZ9a+P1uryZLAECQAaw
ApZ12s25b0yj9KkIhbU05hqGokZ+eKBeLpKELcvPHSL88wMbStTfqxUed5ymjStf
1kVbcFOB9fsBLTvP0hkCQFCON0l1VjFli+vqfN0lypgIqCf85V6FZFN19creGCCd
76pX/X2FIBbUSDN1z48SM5I/RKdCkTx7FY+509q2Mek=
-----END RSA PRIVATE KEY-----""".encode()

_PRIVATE = serialization.load_pem_private_key(PRIVATE_PEM, password=None)
_PUBLIC = serialization.load_pem_public_key(PUBLIC_PEM)


def rsa_encrypt(text: str) -> str:
    cipher = _PUBLIC.encrypt(text.encode("ascii"), padding.PKCS1v15())
    return base64.b64encode(cipher).decode("ascii")


def rsa_sign(text: str) -> str:
    signature = _PRIVATE.sign(text.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode("ascii")


def page_proof(page: int, stamp: int) -> dict[str, str]:
    material = f"{page}_{CHALLENGE}_{stamp}"
    return {
        "material": material,
        "auth_key": rsa_encrypt(material),
        "signature": rsa_sign(material),
        "data": rsa_encrypt(material + "_param"),
        "verify": hmac.new(HMAC_KEY, material.encode("ascii"), hashlib.sha256).hexdigest(),
        "t": str(stamp),
    }


async def get_with_backoff(client, path: str, headers: dict[str, str] | None = None):
    delay = 0.5
    last = None
    for _ in range(8):
        last = await client.get(path, headers=headers)
        if last.status_code != 429:
            return last
        await asyncio.sleep(delay)
        delay = min(delay * 2, 8.0)
    return last


def _numbers(payload: dict, label: str) -> list[int]:
    numbers = payload.get("page_data")
    if not isinstance(numbers, list) or len(numbers) != 10:
        detail = payload.get("error") or payload.get("message") or "unexpected page_data"
        raise RuntimeError(f"{label}: {detail}")
    return [int(item) for item in numbers]


async def main() -> None:
    session = SpiderSession()
    async with session.async_client({"Referer": REFERER}) as client:
        init_response = await get_with_backoff(
            client,
            f"/authentication/api/fsymmetry_challenge/init/?challenge_type={CHALLENGE}",
        )
        init_payload = init_response.json()
        if init_response.status_code != 200 or init_payload.get("success") is not True:
            detail = init_payload.get("error") or init_payload.get("message") or init_response.status_code
            raise SystemExit(f"init failed: {detail}")
        total_pages = int(init_payload.get("total_pages") or 100)
        page_one = _numbers(init_payload, "init")

        async def fetch_page(page: int) -> list[int]:
            stamp = int(time.time() * 1000)
            proof = page_proof(page, stamp)
            path = (
                f"/authentication/api/fsymmetry_challenge/page/{page}/"
                f"?challenge_type={CHALLENGE}"
                f"&data={quote(proof['data'], safe='')}"
                f"&verify={proof['verify']}&t={proof['t']}"
            )
            response = await get_with_backoff(
                client,
                path,
                {
                    "X-Auth-Key": proof["auth_key"],
                    "X-Signature": proof["signature"],
                },
            )
            payload = response.json()
            if response.status_code != 200 or payload.get("success") is not True:
                detail = payload.get("error") or payload.get("message") or response.status_code
                raise RuntimeError(f"page {page}: {detail}")
            if payload.get("encryption_verified") is False:
                raise RuntimeError(f"page {page}: encryption not verified")
            return _numbers(payload, f"page {page}")

        # Page 1 is the init payload. Pages 2..N use the signed axios call.
        # A signed page-1 read is only a consistency check and is not summed twice.
        signed_page_one = await fetch_page(1)
        rest = await collect_pages(fetch_page, range(2, total_pages + 1), concurrency=4)
        pages = {1: page_one, **rest}
        if len(pages) != total_pages:
            raise RuntimeError(f"expected {total_pages} pages, got {len(pages)}")
        total = sum(sum(pages[page]) for page in range(1, total_pages + 1))
        submit = await client.post(
            "/authentication/api/fsymmetry_challenge/submit/",
            json={"challenge_type": CHALLENGE, "answer": total},
        )
        body = submit.json()
        result = public_result(body if isinstance(body, dict) else {})
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        accepted = body.get("is_correct") is True or "答案正确" in str(body.get("message") or "")
        print(
            "pages",
            len(pages),
            "page1_match",
            signed_page_one == page_one,
            "http",
            submit.status_code,
            "accepted",
            accepted,
        )
        print("message", body.get("message"))
        if not accepted:
            raise SystemExit("submit was not accepted")


if __name__ == "__main__":
    asyncio.run(main())
