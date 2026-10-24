"""Probe one cylinder slide against the page API. No secrets in output."""

from __future__ import annotations

import base64
import hashlib
import io
import itertools
import json
import random
from pathlib import Path

from PIL import Image

from modules.runtime import SpiderSession

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890+/="
PAGE = "/captcha/slide_cylinder_challenge?challenge_type=slide_cylinder_challenge"
REFERER = "https://www.spiderdemo.cn" + PAGE
CHALLENGE = "slide_cylinder_challenge"
TILE_W = 255
TILE_H = 185
CONTAINER_W = 400
CONTAINER_H = 240


def custom_btoa(text: str) -> str:
    out: list[str] = []
    pad = (0, 2, 1)[len(text) % 3]
    index = 0
    limit = len(text) - pad
    while index < limit:
        chunk = (
            (ord(text[index]) << 16)
            | (ord(text[index + 1]) << 8)
            | ord(text[index + 2])
        )
        out.append(ALPHABET[(chunk >> 18) & 63])
        out.append(ALPHABET[(chunk >> 12) & 63])
        out.append(ALPHABET[(chunk >> 6) & 63])
        out.append(ALPHABET[chunk & 63])
        index += 3
    if pad == 2:
        chunk = ord(text[index])
        out.append(ALPHABET[(chunk >> 2) & 63])
        out.append(ALPHABET[(chunk << 4) & 63])
        out.append("==")
    elif pad == 1:
        chunk = (ord(text[index]) << 8) | ord(text[index + 1])
        out.append(ALPHABET[(chunk >> 10) & 63])
        out.append(ALPHABET[(chunk >> 4) & 63])
        out.append(ALPHABET[(chunk << 2) & 63])
        out.append("=")
    return "".join(out)


def js_number(value: float) -> str:
    nearest = round(value)
    if abs(value - nearest) < 1e-9:
        return str(int(nearest))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def track_for(fraction: float) -> str:
    final_x = (fraction % 1.0) * 350.0
    if final_x < 1:
        final_x = 350.0
    points = []
    y_base = 486
    for step in range(1, 29):
        progress = step / 28
        eased = 1 - (1 - progress) ** 2
        points.append(
            {
                "x": final_x * eased,
                "y": y_base + random.choice((-1, 0, 0, 1)),
                "timestamp": random.randint(14, 26),
            }
        )
    points[-1]["x"] = final_x
    body = ",".join(
        '{"x":%s,"y":%s,"timestamp":%s}'
        % (js_number(item["x"]), js_number(item["y"]), js_number(item["timestamp"]))
        for item in points
    )
    return custom_btoa("[" + body + "]")


def permutation(order: str, server_time: str) -> list[int]:
    for perm in itertools.permutations(range(8)):
        text = json.dumps(list(perm), separators=(",", ":")) + server_time
        if hashlib.md5(text.encode()).hexdigest() == order:
            return list(perm)
    raise RuntimeError("permutation not found")


def restore(image: Image.Image, perm: list[int]) -> Image.Image:
    canvas = Image.new("RGB", image.size)
    for source, dest in enumerate(perm):
        sx = (source % 4) * TILE_W
        sy = (source // 4) * TILE_H
        dx = (dest % 4) * TILE_W
        dy = (dest // 4) * TILE_H
        canvas.paste(image.crop((sx, sy, sx + TILE_W, sy + TILE_H)), (dx, dy))
    return canvas


def centers(image: Image.Image) -> tuple[float, float]:
    pixels = image.load()
    width, height = image.size
    bg = pixels[width - 1, height // 2]
    total_x = 0
    count = 0
    min_x, max_x = width, 0
    for y in range(height):
        for x in range(width):
            red, green, blue = pixels[x, y]
            if abs(red - bg[0]) + abs(green - bg[1]) + abs(blue - bg[2]) > 36:
                total_x += x
                count += 1
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
    if count == 0:
        return 0.5, 0.5
    bbox = ((min_x + max_x) / 2) / width
    com = (total_x / count) / width
    return bbox, com


def wrap(value: float) -> float:
    return value % 1.0


def candidates(offset: float, bbox: float, com: float) -> list[tuple[str, float]]:
    found: list[tuple[str, float]] = []
    for label, center in (("bbox", bbox), ("com", com)):
        found.append((f"{label}:off-c", wrap(offset - center)))
        found.append((f"{label}:c-off", wrap(center - offset)))
        found.append((f"{label}:off-mirror", wrap(offset - (1 - center))))
        found.append((f"{label}:mirror-off", wrap((1 - center) - offset)))
    return found


def public_body(payload: dict) -> dict:
    kept = {}
    for key in ("success", "error", "message", "msg", "is_correct"):
        if key in payload:
            kept[key] = payload[key]
    page = payload.get("page_data")
    if isinstance(page, list):
        kept["page_len"] = len(page)
        if page and all(isinstance(item, (int, float)) for item in page):
            kept["page_sum"] = sum(page)
    return kept


def three_hint(text: str) -> None:
    revision = text.find("REVISION")
    print("three_bytes", len(text), "revision_at", revision)
    if revision >= 0:
        print("revision_snip", text[revision : revision + 40].replace("\n", " "))
    marker = text.find("CylinderGeometry")
    print("cylinder_at", marker)
    if marker >= 0:
        print("cylinder_snip", text[marker : marker + 180].replace("\n", " "))
    for needle in ("thetaLength", "uvs.push", "faceVertexUvs"):
        print(needle, text.find(needle))


def main() -> None:
    random.seed(19)
    session = SpiderSession()
    folder = Path(__file__).parent
    with session.client(headers={"Referer": REFERER}) as client:
        three = client.get("/static/js/three.min.js")
        three.raise_for_status()
        (folder / "three.min.js").write_bytes(three.content)
        three_hint(three.text)
        init = client.get(
            "/captcha/api/slide_cylinder_challenge/init/",
            params={"challenge_type": CHALLENGE},
        )
        print("init", init.status_code, public_body(init.json()))
        for attempt in range(8):
            image = client.get(
                "/captcha/api/slide_cylinder_challenge/captcha_image/",
                params={"t": attempt + 1},
            )
            if image.status_code == 429:
                print("captcha_429")
                break
            payload = image.json()
            server_time = image.cookies.get("server_time", "")
            if not server_time:
                print("missing_time", attempt)
                break
            raw = base64.b64decode(payload["bg"])
            picture = Image.open(io.BytesIO(raw)).convert("RGB")
            perm = permutation(payload["order"], server_time)
            restored = restore(picture, perm)
            bbox, com = centers(restored)
            offset = float(payload["offset"])
            name, fraction = candidates(offset, bbox, com)[attempt]
            response = client.post(
                "/captcha/api/slide_cylinder_challenge/page/",
                json={
                    "captcha_id": payload["captchaId"],
                    "page_num": 2,
                    "challenge_type": CHALLENGE,
                    "track": track_for(fraction),
                    "container_width": CONTAINER_W,
                    "container_height": CONTAINER_H,
                },
            )
            body = {}
            try:
                body = response.json()
            except json.JSONDecodeError:
                body = {"error": f"nonjson {response.status_code}"}
            print(
                "try",
                attempt,
                name,
                "off",
                round(offset, 4),
                "bbox",
                round(bbox, 4),
                "com",
                round(com, 4),
                "frac",
                round(fraction % 1, 4),
                "http",
                response.status_code,
                public_body(body if isinstance(body, dict) else {"error": str(type(body))}),
            )
            if isinstance(body, dict) and body.get("success") is True:
                break


if __name__ == "__main__":
    main()
