"""Probe init and one signed page. Prints status and public fields only."""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from urllib.parse import quote

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from modules.runtime import SpiderSession

CHALLENGE = "fsymmetry_challenge"
HMAC_KEY = b"dsa_secret_key_2025"
REFERER = (
    "https://www.spiderdemo.cn/authentication/fsymmetry_challenge/"
    "?challenge_type=fsymmetry_challenge"
)

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

private_key = serialization.load_pem_private_key(PRIVATE_PEM, password=None)
public_key = serialization.load_pem_public_key(PUBLIC_PEM)


def rsa_encrypt(text: str) -> str:
    cipher = public_key.encrypt(text.encode("ascii"), padding.PKCS1v15())
    return base64.b64encode(cipher).decode("ascii")


def rsa_sign(text: str) -> str:
    signature = private_key.sign(text.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode("ascii")


def main() -> None:
    pub_n = public_key.public_numbers().n
    prv_n = private_key.public_key().public_numbers().n
    print("moduli_match", pub_n == prv_n, "bits", pub_n.bit_length())
    sample = "2_fsymmetry_challenge_1"
    signature = rsa_sign(sample)
    public_key.verify(base64.b64decode(signature), sample.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    print("local_verify_ok", True)

    session = SpiderSession()
    with session.client({"Referer": REFERER}) as client:
        init = client.get(
            f"/authentication/api/fsymmetry_challenge/init/?challenge_type={CHALLENGE}"
        )
        body = init.json()
        print("init", init.status_code, "keys", sorted(body.keys()) if isinstance(body, dict) else type(body))
        if isinstance(body, dict):
            safe = {k: body.get(k) for k in ("success", "message", "error", "msg") if k in body}
            print("init_public", safe)
            data = body.get("page_data")
            print("init_page_data_len", len(data) if isinstance(data, list) else type(data).__name__)

        page = 2
        stamp = int(time.time() * 1000)
        material = f"{page}_{CHALLENGE}_{stamp}"
        path = (
            f"/authentication/api/fsymmetry_challenge/page/{page}/"
            f"?challenge_type={CHALLENGE}"
            f"&data={quote(rsa_encrypt(material + '_param'), safe='')}"
            f"&verify={hmac.new(HMAC_KEY, material.encode(), hashlib.sha256).hexdigest()}"
            f"&t={stamp}"
        )
        response = client.get(
            path,
            headers={
                "X-Auth-Key": rsa_encrypt(material),
                "X-Signature": rsa_sign(material),
            },
        )
        payload = response.json()
        print("page", response.status_code, "keys", sorted(payload.keys()) if isinstance(payload, dict) else type(payload))
        if isinstance(payload, dict):
            safe = {k: payload.get(k) for k in ("success", "message", "error", "msg") if k in payload}
            print("page_public", safe)
            data = payload.get("page_data")
            print("page_data_len", len(data) if isinstance(data, list) else type(data).__name__)


if __name__ == "__main__":
    main()
