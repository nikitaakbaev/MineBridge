from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "resources" / "icons"


def lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def gradient(size: int, start: tuple[int, int, int], end: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            pixels[x, y] = (
                lerp(start[0], end[0], t),
                lerp(start[1], end[1], t),
                lerp(start[2], end[2], t),
                255,
            )
    return img


def draw_icon(size: int) -> Image.Image:
    scale = size / 256
    img = Image.new("RGBA", (size, size), (23, 34, 49, 0))
    draw = ImageDraw.Draw(img)

    def p(value: float) -> int:
        return round(value * scale)

    draw.rounded_rectangle([0, 0, size, size], radius=p(56), fill=(23, 34, 49, 255))

    bg = gradient(size, (79, 140, 255), (25, 179, 125))
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.arc([p(52), p(76), p(204), p(228)], 196, 318, fill=255, width=p(18))
    md.line([p(204), p(105), p(202), p(159)], fill=255, width=p(18))
    md.arc([p(126), p(122), p(202), p(198)], 0, 92, fill=255, width=p(18))
    md.line([p(179), p(82), p(200), p(106), p(169), p(114)], fill=255, width=p(18), joint="curve")
    img.alpha_composite(Image.composite(bg, Image.new("RGBA", (size, size), (0, 0, 0, 0)), mask))

    cube = [
        (p(67), p(93)),
        (p(128), p(58)),
        (p(189), p(93)),
        (p(189), p(163)),
        (p(128), p(198)),
        (p(67), p(163)),
    ]
    draw.polygon(cube, fill=(232, 241, 249, 255))
    draw.line(
        [(p(67), p(93)), (p(128), p(128)), (p(189), p(93))],
        fill=(23, 34, 49, 80),
        width=p(8),
        joint="curve",
    )
    draw.line([(p(128), p(128)), (p(128), p(198))], fill=(23, 34, 49, 80), width=p(8))
    draw.polygon(
        [(p(91), p(113)), (p(128), p(92)), (p(165), p(113)), (p(128), p(134))],
        fill=(49, 196, 141, 255),
    )
    draw.line([(p(98), p(151)), (p(158), p(151))], fill=(23, 34, 49, 255), width=p(14))
    draw.line([(p(110), p(170)), (p(146), p(170))], fill=(23, 34, 49, 255), width=p(14))

    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    icon = draw_icon(512)
    icon.save(OUT_DIR / "icon.png")
    icon.save(
        OUT_DIR / "icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()
