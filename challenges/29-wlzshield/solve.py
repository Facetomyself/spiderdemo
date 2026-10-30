"""无感验证码：同一 RuyiDOM 进程签发 token、校验分页并提交总和。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from modules.runtime import SpiderSession, public_result

OUT = Path(__file__).with_name("result.json")
ROOT = Path(__file__).resolve().parent
NODE = Path(r"D:\reverse_ENV\tools\node\node.exe")


def _accepted(result: dict) -> bool:
    if result.get("is_correct") is True:
        return True
    text = str(result.get("message") or result.get("msg") or "")
    return "答案正确" in text


def _wipe(path: Path) -> None:
    if not path.exists():
        return
    path.write_bytes(b"")
    path.unlink()


def main() -> int:
    session = SpiderSession()
    mint = ROOT / "evidence" / "mint"
    mint.mkdir(parents=True, exist_ok=True)
    cookie_path = mint / "cookies.txt"
    token_path = mint / "token.txt"
    result_path = mint / "public.json"
    log_path = mint / "run.log"
    lines = [f"{cookie.name}\t{cookie.value}" for cookie in session.cookies.jar]
    cookie_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(cookie_path, 0o600)
    except OSError:
        pass
    token_path.write_bytes(b"")
    if result_path.exists():
        result_path.unlink()
    env = os.environ.copy()
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env.pop(key, None)
    env["RUYIDOM_COOKIE_FILE"] = str(cookie_path)
    env["RUYIDOM_TOKEN_OUT"] = str(token_path)
    env["RUYIDOM_RESULT_OUT"] = str(result_path)
    env["RUYIDOM_SCRIPT"] = str(ROOT / "runtime" / "ruyidom-mint.js")
    env["RUYIDOM_PROJECT_ROOT"] = str(ROOT)
    try:
        completed = subprocess.run(
            [str(NODE), str(ROOT / "runtime" / "long-run.mjs")],
            env=env,
            check=False,
            capture_output=True,
            timeout=7300,
        )
        log_path.write_bytes(completed.stdout + b"\n" + completed.stderr)
    finally:
        _wipe(cookie_path)
        _wipe(token_path)
    raw = result_path.read_text(encoding="utf-8") if result_path.exists() else ""
    try:
        payload = json.loads(raw) if raw.strip() else {"success": False, "error": "no result"}
    except json.JSONDecodeError:
        payload = {"success": False, "error": "bad result"}
    if not isinstance(payload, dict):
        payload = {"success": False, "error": "bad result"}
    result = public_result(payload)
    if not result:
        result = {"success": False, "error": str(payload.get("error") or "no public fields")[:80]}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if _accepted(result) else 1


if __name__ == "__main__":
    sys.exit(main())
