"""Show how the VM reads bytecode and how the first argument begins."""

from pathlib import Path

js = Path(__file__).with_name("static__js__check_devtools_jsvmp.js").read_text(encoding="utf-8")
pos = js.find("function Dg")
print(js[pos : pos + 1800])
print("---ARG0 HEAD 2500---")
call = js.find("})(function(em,eB")
print("call", call)
print(js[call : call + 2500])
