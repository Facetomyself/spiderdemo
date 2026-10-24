"""Launch the stubbed VMP with the session cookie kept in the child environment."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from modules.runtime import SpiderSession

NODE = Path(r"D:\reverse_ENV\tools\node\node.exe")
HERE = Path(__file__).resolve().parent


def main() -> None:
    session = SpiderSession()
    pairs: list[str] = []
    for cookie in session.cookies.jar:
        pairs.append(f"{cookie.name}={cookie.value}")
    env = os.environ.copy()
    env["SPIDER_COOKIE"] = "; ".join(pairs)
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [str(NODE), str(HERE / "_run_vm.js")],
        cwd=str(HERE),
        env=env,
        check=False,
        timeout=70,
    )
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
