"""Solve the press-rotate number challenge and submit the 30-page sum.

Page fetches share one asyncio gather with concurrency 4. Captcha bytes,
proofs, and tokens stay in memory and are not printed.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import math
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

from modules.runtime import SpiderSession, collect_pages, public_result

HERE = Path(__file__).resolve().parent
NODE = r"D:\reverse_ENV\tools\node\node.exe"
ENGINE = HERE / "engine.cjs"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
PAGE = "https://www.spiderdemo.cn/captcha/press_rotate_challenge?challenge_type=press_rotate_challenge"
CHALLENGE = "press_rotate_challenge"
ORIENTATION_MODEL = Path(
    r"D:\reverse_ENV\workspace\cv-cat\JdApis\static\jcap\run\models\orientation_model_v2_0.9882.onnx"
)
_ORT_LOCK = threading.Lock()
_ORT: ort.InferenceSession | None = None
INIT = f"/captcha/api/{CHALLENGE}/init/?challenge_type={CHALLENGE}"
CAPTCHA = f"/captcha/api/{CHALLENGE}/captcha"
VERIFY = f"/captcha/api/{CHALLENGE}/verify"
SUBMIT = f"/captcha/api/{CHALLENGE}/submit/"


def _orientation_session() -> ort.InferenceSession:
    global _ORT
    if _ORT is None:
        _ORT = ort.InferenceSession(str(ORIENTATION_MODEL), providers=["CPUExecutionProvider"])
    return _ORT


def _class_probabilities(rgb: np.ndarray) -> np.ndarray:
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    resized = cv2.resize(bgr, (416, 416), interpolation=cv2.INTER_AREA)
    crop = cv2.cvtColor(resized[16:400, 16:400], cv2.COLOR_BGR2RGB).astype(np.float32)
    crop /= 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    tensor = ((crop - mean) / std).transpose(2, 0, 1)[None].astype(np.float32)
    session = _orientation_session()
    with _ORT_LOCK:
        logits = np.asarray(session.run(None, {session.get_inputs()[0].name: tensor})[0][0], dtype=np.float32)
    logits -= float(logits.max())
    probabilities = np.exp(logits)
    probabilities /= max(float(probabilities.sum()), 1e-6)
    return probabilities


def _circular_distance(first: float, second: float) -> float:
    delta = abs((first - second) % 360.0)
    return min(delta, 360.0 - delta)


def _line_correction(rgb: np.ndarray, probabilities: np.ndarray) -> tuple[float, float]:
    """Clockwise degrees that align long inner edges, snapped to the classifier quadrant."""
    orientation_class = int(np.argmax(probabilities))
    coarse_ccw = {0: 0.0, 1: 270.0, 2: 180.0, 3: 90.0}[orientation_class]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    height, width = gray.shape
    radius = min(height, width) * 0.42
    lines = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(gray)[0]
    weighted = 0j
    total = 0.0
    if lines is not None:
        for x1, y1, x2, y2 in lines.reshape(-1, 4):
            midpoint_x = float(x1 + x2) / 2.0
            midpoint_y = float(y1 + y2) / 2.0
            if (midpoint_x - width / 2.0) ** 2 + (midpoint_y - height / 2.0) ** 2 > radius ** 2:
                continue
            dx = float(x2 - x1)
            dy = float(y2 - y1)
            length = math.hypot(dx, dy)
            if length < 12.0:
                continue
            theta = math.atan2(dy, dx)
            weight = length * length
            weighted += weight * complex(math.cos(4.0 * theta), math.sin(4.0 * theta))
            total += weight
    if total <= 0.0:
        return (360.0 - coarse_ccw) % 360.0, 0.0
    axis = (math.degrees(math.atan2(weighted.imag, weighted.real)) / 4.0) % 90.0
    candidates = [(axis + 90.0 * index) % 360.0 for index in range(4)]
    ccw = min(candidates, key=lambda candidate: _circular_distance(candidate, coarse_ccw))
    return (360.0 - ccw) % 360.0, abs(weighted) / total


def _circular_mean(angles: list[float]) -> float:
    radians = np.deg2rad(np.asarray(angles, dtype=np.float64))
    return float(math.degrees(math.atan2(np.sin(radians).mean(), np.cos(radians).mean())) % 360.0)


def _cluster_span(angles: list[float]) -> float:
    if len(angles) <= 1:
        return 0.0
    ordered = sorted(angle % 360.0 for angle in angles)
    gaps = [ordered[index + 1] - ordered[index] for index in range(len(ordered) - 1)]
    gaps.append(ordered[0] + 360.0 - ordered[-1])
    return 360.0 - max(gaps)


def _semantic_correction(image: Image.Image) -> float:
    """Center of the rotation band the classifier calls upright, for pictures without a horizon."""
    samples: list[tuple[int, float]] = []
    for angle in range(0, 360, 10):
        rotated = np.asarray(image.rotate(-angle, resample=Image.Resampling.BILINEAR, fillcolor=(0, 0, 0)))
        samples.append((angle, float(_class_probabilities(rotated)[0])))
    peak = max(score for _, score in samples)
    threshold = max(0.55, peak * 0.97)
    chosen = [float(angle) for angle, score in samples if score >= threshold]
    if not chosen:
        chosen = [float(max(samples, key=lambda item: item[1])[0])]
    center = _circular_mean(chosen)
    refined: list[tuple[float, float]] = []
    for delta in range(-12, 13, 3):
        angle = (center + delta) % 360.0
        rotated = np.asarray(image.rotate(-angle, resample=Image.Resampling.BILINEAR, fillcolor=(0, 0, 0)))
        refined.append((angle, float(_class_probabilities(rotated)[0])))
    refined_peak = max(score for _, score in refined)
    band = [angle for angle, score in refined if score >= max(0.55, refined_peak * 0.97)]
    if _cluster_span(band) <= 18.0:
        return max(refined, key=lambda item: item[1])[0]
    return _circular_mean(band)


def best_angle(image: Image.Image) -> float:
    rgb_image = image.convert("RGB")
    rgb = np.asarray(rgb_image)
    probabilities = _class_probabilities(rgb)
    line_angle, strength = _line_correction(rgb, probabilities)
    if strength >= 0.45:
        return float(line_angle)
    semantic = _semantic_correction(rgb_image)
    if strength >= 0.25 and _circular_distance(semantic, line_angle) <= 12.0:
        return float(line_angle)
    return float(semantic)


def build_proof(blob: str, target_angle: float) -> dict[str, Any]:
    job_file = tempfile.NamedTemporaryFile(prefix="pr-job-", suffix=".json", dir=HERE, delete=False)
    out_file = tempfile.NamedTemporaryFile(prefix="pr-out-", suffix=".json", dir=HERE, delete=False)
    job_path = Path(job_file.name)
    out_path = Path(out_file.name)
    job_file.close()
    out_file.close()
    try:
        job_path.write_text(
            json.dumps({"blob": blob, "ua": UA, "target_angle": target_angle}),
            encoding="utf-8",
        )
        subprocess.run(
            [NODE, str(ENGINE), str(job_path), str(out_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(out_path.read_text(encoding="utf-8"))
    finally:
        job_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)


async def request_json(client: Any, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    delay = 0.8
    last_status = 0
    for _ in range(6):
        response = await client.request(method, url, **kwargs)
        last_status = response.status_code
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay *= 2
            continue
        payload = response.json()
        if isinstance(payload, dict):
            return payload
        break
    raise RuntimeError(f"request failed status={last_status}")


async def load_page(client: Any, page: int, token: str | None) -> list[int]:
    params = {"challenge_type": CHALLENGE}
    if token:
        params["token"] = token
    payload = await request_json(
        client,
        "GET",
        f"/captcha/api/{CHALLENGE}/page/{page}/",
        params=params,
    )
    numbers = payload.get("page_data")
    if payload.get("success") is not True or not isinstance(numbers, list) or len(numbers) != 10:
        raise RuntimeError(f"page {page} was not accepted")
    return [int(item) for item in numbers]


async def unlock_page(client: Any, page: int) -> list[int]:
    last_error = "verify failed"
    for _ in range(8):
        captcha = await request_json(client, "GET", CAPTCHA)
        data = captcha.get("data") if isinstance(captcha.get("data"), dict) else None
        if captcha.get("success") is not True or not data:
            last_error = "captcha was not issued"
            await asyncio.sleep(0.4)
            continue
        raw = base64.b64decode(str(data["bg"]).split(",", 1)[1])
        image = Image.open(io.BytesIO(raw)).convert("RGBA")
        angle = await asyncio.to_thread(best_angle, image)
        proof = await asyncio.to_thread(build_proof, str(data["data"]), angle)
        verified = await request_json(
            client,
            "POST",
            VERIFY,
            json={
                "timestamp": proof["timestamp"],
                "angle": proof["angle"],
                "captchaId": data["captchaId"],
                "data": proof["proof"],
            },
        )
        token = (verified.get("data") or {}).get("token") if isinstance(verified.get("data"), dict) else None
        if verified.get("success") is True and isinstance(token, str) and token:
            try:
                return await load_page(client, page, token)
            except RuntimeError:
                last_error = "page rejected the token"
                continue
        message = verified.get("message") or verified.get("error") or "verify failed"
        last_error = message if isinstance(message, str) else "verify failed"
    raise RuntimeError(f"page {page} captcha failed: {last_error[:40]}")


async def fetch_page(client: Any, page: int) -> list[int]:
    if page == 1:
        return await load_page(client, page, None)
    return await unlock_page(client, page)


async def solve_async(pages: range) -> dict[str, Any]:
    session = SpiderSession()
    headers = {"Referer": PAGE, "User-Agent": UA, "Accept": "application/json, text/plain, */*"}
    async with session.async_client(headers) as client:
        init = await request_json(client, "GET", INIT)
        if init.get("success") is not True:
            raise RuntimeError("init was not accepted")
        loaded = await collect_pages(lambda page: fetch_page(client, page), pages, concurrency=4)
        ordered = [loaded[page] for page in pages]
        answer = sum(sum(numbers) for numbers in ordered)
        if pages != range(1, 31):
            return {"partial_pages": len(ordered), "partial_sum": answer}
        submitted = await request_json(
            client,
            "POST",
            SUBMIT,
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        return public_result(submitted)


def main() -> None:
    result = asyncio.run(solve_async(range(1, 31)))
    (HERE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
