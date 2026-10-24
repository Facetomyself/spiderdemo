from pathlib import Path

root = Path(__file__).with_name("_fns")
text = (root / "updateSliderPosition.js").read_text(encoding="utf-8")
at = text.find("rotate")
print("UPDATE LEN", len(text), "rotate at", at)
print(text[at - 1800: at + 400])
print("\n\n===== VERIFY TAIL =====")
ver = (root / "verifyCaptchaAndGetData.js").read_text(encoding="utf-8")
at = ver.find("apiGetPageData")
print(ver[at - 2200: at + 200])
