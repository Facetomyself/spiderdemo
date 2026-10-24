from pathlib import Path

text = Path(__file__).parent.joinpath("_fns", "recordTrajectoryPoint.js").read_text(encoding="utf-8")
at = text.rfind("userTrajec")
print(text[at: at + 2500])
