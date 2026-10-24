from pathlib import Path

text = (Path(__file__).resolve().parent / "static__js__anti_automation.js").read_text(encoding="utf-8")
for token in ("AntiAutomation", "validatePageNavigation", "clickCounters", "MAX_CLICKS"):
    index = 0
    seen = 0
    while seen < 3:
        found = text.find(token, index)
        if found < 0:
            break
        print("\n==", token, found)
        print(text[max(0, found - 80): found + 160])
        index = found + len(token)
        seen += 1
