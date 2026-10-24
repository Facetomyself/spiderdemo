from pathlib import Path

from modules.runtime import SpiderSession

target = Path(r"D:\reverse_ENV\workspace\spiderdemo\challenges\06-jsvmp\assets\challenge.proto")
session = SpiderSession()
with session.client() as client:
    response = client.get("/static/protos/challenge.proto")
    target.write_bytes(response.content)
print("bytes", len(response.content))
print(response.content.decode("utf-8", "replace"))
