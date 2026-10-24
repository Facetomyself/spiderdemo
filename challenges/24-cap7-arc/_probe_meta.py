"""Summarize cap7 captcha metadata without printing image bytes."""

from __future__ import annotations

import json
from pathlib import Path

from modules.runtime import SpiderSession

REFERER = "https://www.spiderdemo.cn/captcha/cap7_challenge?challenge_type=cap7_challenge"
OUT = Path(__file__).with_name("captcha_meta.json")


def main() -> None:
    session = SpiderSession()
    with session.client(headers={"Referer": REFERER, "Accept": "application/json"}) as client:
        init = client.get("/captcha/api/cap7_challenge/init/?challenge_type=cap7_challenge").json()
        page_data = init.get("page_data")
        print("init_keys", sorted(init.keys()))
        print("page_data_type", type(page_data).__name__)
        if isinstance(page_data, list):
            print("page_data_len", len(page_data))
            print("page_data_sample", page_data[:3])
        elif isinstance(page_data, dict):
            print("page_data_keys", sorted(page_data.keys())[:40])
        cap = client.get("/captcha/api/cap7_challenge/captcha_image/").json()
        info = cap.get("image_info")
        arc = cap.get("arc_path") or {}
        points = arc.get("points") if isinstance(arc, dict) else None
        summary = {
            "keys": sorted(cap.keys()),
            "slider_y": cap.get("slider_y"),
            "image_info": info,
            "arc_keys": sorted(arc.keys()) if isinstance(arc, dict) else type(arc).__name__,
            "arc_non_points": {k: v for k, v in arc.items() if k != "points"} if isinstance(arc, dict) else None,
            "point_count": len(points) if isinstance(points, list) else None,
            "point_first": points[0] if isinstance(points, list) and points else None,
            "point_mid": points[len(points) // 2] if isinstance(points, list) and points else None,
            "point_last": points[-1] if isinstance(points, list) and points else None,
            "masked_len": len(cap.get("masked") or ""),
            "overlay_len": len(cap.get("overlay") or ""),
        }
        OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2)[:4000])


if __name__ == "__main__":
    main()
