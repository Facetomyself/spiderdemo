"""Print a coarse foreground histogram for restored captcha images."""

from pathlib import Path

from PIL import Image


def main() -> None:
    folder = Path(__file__).parent
    for path in sorted(folder.glob("_look_*.jpg")):
        image = Image.open(path).convert("RGB")
        pixels = image.load()
        width, height = image.size
        bg = pixels[width // 2, 2]
        bins = 34
        print(path.name, "bg", bg, "size", image.size)
        line = []
        for index in range(bins):
            x0 = index * width // bins
            x1 = (index + 1) * width // bins
            count = 0
            total = 0
            for x in range(x0, x1):
                for y in range(0, height, 2):
                    red, green, blue = pixels[x, y]
                    total += 1
                    if abs(red - bg[0]) + abs(green - bg[1]) + abs(blue - bg[2]) > 40:
                        count += 1
            level = min(9, count * 10 // max(total, 1))
            line.append(str(level))
        print("".join(line))


if __name__ == "__main__":
    main()
