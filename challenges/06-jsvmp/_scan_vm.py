from pathlib import Path

text = Path(r"D:\reverse_ENV\workspace\spiderdemo\challenges\06-jsvmp\assets\jsvmp_patched.js").read_text(encoding="utf-8")
head = text.split("\u2028", 1)[0]
print(head[:2500])
