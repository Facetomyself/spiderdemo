"""Launch the browser stub with the session cookie kept in the child environment."""

import os
import subprocess
from pathlib import Path

from modules.runtime import SpiderSession

NODE = r"D:\reverse_ENV\tools\node\node.exe"
SCRIPT = Path(__file__).with_name("_sandbox.js")


def cookie_header(session: SpiderSession) -> str:
    pairs = []
    for cookie in session.cookies.jar:
        pairs.append(f"{cookie.name}={cookie.value}")
    return "; ".join(pairs)


def main() -> None:
    session = SpiderSession()
    env = os.environ.copy()
    env["SPIDER_COOKIE"] = cookie_header(session)
    completed = subprocess.run([NODE, str(SCRIPT)], env=env, cwd=str(SCRIPT.parent))
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
