"""Print the VM body edges and the debugger occurrence."""

from pathlib import Path

js = Path(__file__).with_name("static__js__check_devtools_jsvmp.js").read_text(encoding="utf-8")
print("BODY_TAIL")
print(js[10200:10780])
print("---DEBUG---")
pos = js.find("debugger")
print(js[pos - 200 : pos + 200])
print("---ARG0 TAIL---")
# reuse previous offsets: call starts 10764
print(js[10764 + 17500 : 10764 + 18200])
