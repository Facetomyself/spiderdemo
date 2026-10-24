import json
import os
import subprocess
from pathlib import Path

from modules.runtime import SpiderSession, public_result

ROOT = Path(__file__).resolve().parent
session = SpiderSession()
pairs = [f"{cookie.name}={cookie.value}" for cookie in session.cookies.jar]
env = dict(os.environ)
env["SPIDER_COOKIE"] = "; ".join(pairs)
env["WIRE_LOG"] = "1"
env.pop("ALIGN_ONLY", None)
env.pop("COOKIE_SYNC", None)
env.pop("PLAIN_SHAPE", None)
env.pop("INIT_CHECK", None)
env["PYTHONIOENCODING"] = "utf-8"
proc = subprocess.run(
    [r"D:\reverse_ENV\tools\node\node.exe", str(ROOT / "_run_vm.js")],
    env=env,
    check=False,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
error = ""
status = None
sent = False
for line in (proc.stdout or "").splitlines():
    if line.startswith(("WRITE", "WRITER_", "FIELD ", "FRAME_LEN ", "FP ", "CANVAS_", "NAV ", "PLUGIN_GET ", "SEND ", "PAGE1 ")):
        print(line[:240])
    if line.startswith("SEND ") and " 0 " in line:
        sent = False
    if line.startswith("PAGE1 ") and "error=" in line:
        sent = True
        error = line.split("error=", 1)[1].strip()
        piece = line.split("status=", 1)[1].split(" ", 1)[0]
        status = int(piece)
if proc.returncode != 0:
    print("EXIT", proc.returncode)
    raise SystemExit(proc.returncode)
if status == 200:
    print("PAGE1_STATUS", 200)
    raise SystemExit(0)
if not sent:
    print("RESULT_HELD")
    raise SystemExit(0)
if not error:
    raise SystemExit(1)
payload = {"success": False, "error": error}
kept = public_result(payload)
kept["success"] = False
(ROOT / "result.json").write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("RESULT_KEYS", ",".join(kept.keys()))
