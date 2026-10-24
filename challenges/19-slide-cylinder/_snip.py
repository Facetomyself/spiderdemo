from pathlib import Path

text = Path(__file__).with_name("restore.js").read_text(encoding="utf-8")
index = text.find("IGdYUQ")
Path(__file__).with_name("_snip_out.txt").write_text(
    f"index={index}\n" + repr(text[index - 120 : index + 500]),
    encoding="utf-8",
)
