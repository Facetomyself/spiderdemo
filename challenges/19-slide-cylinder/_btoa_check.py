"""Round-trip the page btoa/atob, including out-of-range char codes."""

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890+/="
LOOKUP = {char: index for index, char in enumerate(ALPHABET[:64])}


def code_at(text: str, index: int) -> int:
    if index < 0 or index >= len(text):
        return 0
    return ord(text[index])


def btoa(text: str) -> str:
    out: list[str] = []
    pad = (0, 2, 1)[len(text) % 3]
    index = 0
    while index < len(text) - pad:
        chunk = (
            (code_at(text, index) << 16)
            | (code_at(text, index + 1) << 8)
            | code_at(text, index + 2)
        )
        out.append(ALPHABET[(chunk >> 18) & 63])
        out.append(ALPHABET[(chunk >> 12) & 63])
        out.append(ALPHABET[(chunk >> 6) & 63])
        out.append(ALPHABET[chunk & 63])
        index += 3
    if pad == 2:
        chunk = code_at(text, index)
        out.append(ALPHABET[(chunk >> 2) & 63])
        out.append(ALPHABET[(chunk << 4) & 63])
        out.append("==")
    elif pad == 1:
        chunk = (code_at(text, index) << 8) | code_at(text, index + 1)
        out.append(ALPHABET[(chunk >> 10) & 63])
        out.append(ALPHABET[(chunk >> 4) & 63])
        out.append(ALPHABET[(chunk << 2) & 63])
        out.append("=")
    return "".join(out)


def atob(text: str) -> str:
    cleaned = "".join(char for char in text if char in LOOKUP or char == "=")
    out: list[str] = []
    index = 0
    while index < len(cleaned):
        chunk = (
            (LOOKUP.get(cleaned[index], 0) << 18)
            | (LOOKUP.get(cleaned[index + 1], 0) << 12)
            | (LOOKUP.get(cleaned[index + 2], 0) << 6)
            | LOOKUP.get(cleaned[index + 3], 0)
        )
        out.append(chr((chunk >> 16) & 255))
        if cleaned[index + 2] != "=":
            out.append(chr((chunk >> 8) & 255))
        if cleaned[index + 3] != "=":
            out.append(chr(chunk & 255))
        index += 4
    return "".join(out)


def main() -> None:
    samples = ["a", "ab", "abc", "abcd", "abcde", '{"x":1,"y":2,"timestamp":3}']
    for sample in samples:
        encoded = btoa(sample)
        decoded = atob(encoded)
        print(len(sample) % 3, len(sample), decoded == sample, repr(decoded[:40]), "enc", encoded[:24])


if __name__ == "__main__":
    main()
