"""Save one captcha sample and print only sizes and arc summary."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from modules.runtime import SpiderSession

REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"
OUT = Path(__file__).parent


def main() -> None:
    session = SpiderSession()
    with session.client(headers={"Referer": REFERER, "Accept": "application/json"}) as client:
        cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
    masked = base64.b64decode(cap["masked"])
    overlay = base64.b64decode(cap["overlay"])
    (OUT / "sample_masked.png").write_bytes(masked)
    suffix = "webp" if overlay[:4] == b"RIFF" else "bin"
    (OUT / f"sample_overlay.{suffix}").write_bytes(overlay)
    meta = {
        "slider_y": cap.get("slider_y"),
        "image_info": cap.get("image_info"),
        "points": cap.get("arc_path", {}).get("points"),
        "masked_bytes": len(masked),
        "overlay_bytes": len(overlay),
        "overlay_kind": suffix,
    }
    (OUT / "sample_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    print("masked", len(masked), "overlay", len(overlay), suffix, "points", len(meta["points"]))


if __name__ == "__main__":
    main()
