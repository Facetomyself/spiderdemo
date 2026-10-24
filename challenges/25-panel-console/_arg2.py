"""Print the global-object argument with unicode escapes decoded."""

from pathlib import Path

js = Path(__file__).with_name("static__js__check_devtools_jsvmp.js").read_text(encoding="utf-8")
start = js.find("})(function(em,eB")
# third argument begins after the bytecode string's closing paren
# Find the string table end by the known tail of arg1: ,function(eB){try{return eB=typeof
marker = ",function(eB){try{return eB=typeof"
pos = js.find(marker)
print("pos", pos)
fn = js.find("function(eB){try{return eB=typeof", pos)
depth = 0
end = None
for index, char in enumerate(js[fn:], fn):
    if char == "{":
        depth += 1
    elif char == "}":
        depth -= 1
        if depth == 0:
            end = index
            break
chunk = js[fn : end + 1]
print("len", len(chunk))
print(chunk.encode("ascii").decode("unicode_escape"))
