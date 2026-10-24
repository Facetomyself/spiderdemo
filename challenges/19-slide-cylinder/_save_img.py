"""Decode the sample background and print its size."""

import base64
import json
from pathlib import Path

from PIL import Image

folder = Path(__file__).parent
payload = json.loads((folder / "_sample.json").read_text(encoding="utf-8"))
raw = base64.b64decode(payload["bg"])
path = folder / "_bg.jpg"
path.write_bytes(raw)
image = Image.open(path)
print(image.size, image.mode)
