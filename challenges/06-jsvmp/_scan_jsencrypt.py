from pathlib import Path

text = Path(r"D:\reverse_ENV\workspace\spiderdemo\challenges\06-jsvmp\assets\jsencrypt1.js").read_text(encoding="utf-8")
needles = ["pkcs1pad2", "prototype.encrypt", "encrypt:function", ".encrypt=function", "hex2b64", "doPublic"]
for needle in needles:
    index = 0
    count = 0
    while count < 3:
        found = text.find(needle, index)
        if found < 0:
            break
        print("\n==", needle, found)
        print(text[max(0, found - 80) : found + 220].replace("\n", " "))
        index = found + len(needle)
        count += 1
    if count == 0:
        print("missing", needle)
