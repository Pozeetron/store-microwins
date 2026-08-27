#!/usr/bin/env python3
"""Build Google Play marketing screenshots from store/screenshots-clean."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "screenshots-clean"
OUT = ROOT / "screenshots-gp"

FONT_DISPLAY = (
    ROOT.parent
    / "node_modules/@expo-google-fonts/fraunces/600SemiBold/Fraunces_600SemiBold.ttf"
)
FONT_BODY = (
    ROOT.parent
    / "node_modules/@expo-google-fonts/nunito/500Medium/Nunito_500Medium.ttf"
)

CANVAS_W = 1080
CANVAS_H = 1920
HEADER_H = 360
PHONE_PAD_BOTTOM = 48
PHONE_MAX_W = 900
CORNER_R = 36

COLORS = {
    "mist": (234, 243, 240),
    "mist_deep": (213, 232, 225),
    "foam": (247, 251, 250),
    "ink": (31, 58, 52),
    "ink_soft": (74, 99, 92),
    "teal": (61, 139, 122),
    "teal_soft": (184, 217, 207),
    "glow": (168, 213, 196),
    "shadow": (47, 107, 94, 90),
}

SHOTS = [
    (
        "01-home.png",
        "Soft warmth,\nnot harsh streaks",
        "A gentle diary of tiny wins",
    ),
    (
        "02-today-wins.png",
        "Log tiny crumbs",
        "No giant tasks — only what feels possible",
    ),
    (
        "03-add.png",
        "One tap is enough",
        "Presets for the smallest wins",
    ),
    (
        "04-calendar.png",
        "Gentle goals only",
        "Calendar & progress without pressure",
    ),
    (
        "05-settings.png",
        "Private on your phone",
        "No account · no cloud · no ads",
    ),
    (
        "06-badges.png",
        "Quiet milestones",
        "Soft reminders that you showed up",
    ),
]


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def make_background() -> Image.Image:
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), COLORS["mist"])
    px = img.load()
    for y in range(CANVAS_H):
        t = y / (CANVAS_H - 1)
        r = lerp(COLORS["mist"][0], COLORS["foam"][0], t * 0.55)
        g = lerp(COLORS["mist"][1], COLORS["foam"][1], t * 0.55)
        b = lerp(COLORS["mist"][2], COLORS["foam"][2], t * 0.55)
        for x in range(CANVAS_W):
            px[x, y] = (r, g, b)

    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((620, -120, 1120, 380), fill=(184, 217, 207, 70))
    draw.ellipse((-180, 120, 260, 560), fill=(168, 213, 196, 55))
    draw.ellipse((760, 1500, 1180, 1920), fill=(213, 232, 225, 80))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.replace("\n", " \n ").split()
    lines: list[str] = []
    current = ""
    for word in words:
        if word == "\n":
            if current:
                lines.append(current)
                current = ""
            lines.append("")
            continue
        trial = word if not current else f"{current} {word}"
        if font.getlength(trial) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return [line for line in lines if line != ""]


def draw_header(
    canvas: Image.Image,
    title: str,
    subtitle: str,
    title_font: ImageFont.FreeTypeFont,
    subtitle_font: ImageFont.FreeTypeFont,
) -> None:
    draw = ImageDraw.Draw(canvas)
    title_lines = title.split("\n")
    subtitle_lines = wrap_text(subtitle, subtitle_font, CANVAS_W - 120)

    y = 72
    for line in title_lines:
        width = title_font.getlength(line)
        draw.text(
            ((CANVAS_W - width) / 2, y),
            line,
            font=title_font,
            fill=COLORS["ink"],
        )
        y += title_font.size + 8

    y += 18
    for line in subtitle_lines:
        width = subtitle_font.getlength(line)
        draw.text(
            ((CANVAS_W - width) / 2, y),
            line,
            font=subtitle_font,
            fill=COLORS["ink_soft"],
        )
        y += subtitle_font.size + 10


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def fit_phone(screenshot: Image.Image) -> Image.Image:
    max_h = CANVAS_H - HEADER_H - PHONE_PAD_BOTTOM
    scale = min(PHONE_MAX_W / screenshot.width, max_h / screenshot.height)
    size = (
        max(1, int(screenshot.width * scale)),
        max(1, int(screenshot.height * scale)),
    )
    return screenshot.resize(size, Image.Resampling.LANCZOS)


def paste_phone(canvas: Image.Image, phone: Image.Image) -> None:
    shadow = Image.new("RGBA", (phone.width + 80, phone.height + 80), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (28, 28, phone.width + 52, phone.height + 52),
        radius=CORNER_R + 8,
        fill=COLORS["shadow"],
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))

    mask = rounded_mask(phone.size, CORNER_R)
    framed = Image.new("RGBA", phone.size, (0, 0, 0, 0))
    framed.paste(phone.convert("RGBA"), (0, 0), mask)

    x = (CANVAS_W - phone.width) // 2
    y = HEADER_H + 8
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(shadow, (x - 40, y - 16), shadow)
    canvas_rgba.paste(framed, (x, y), framed)
    canvas.paste(canvas_rgba.convert("RGB"))


def build_one(
    src_name: str,
    title: str,
    subtitle: str,
    title_font: ImageFont.FreeTypeFont,
    subtitle_font: ImageFont.FreeTypeFont,
) -> Image.Image:
    screenshot = Image.open(SRC / src_name).convert("RGB")
    canvas = make_background()
    draw_header(canvas, title, subtitle, title_font, subtitle_font)
    phone = fit_phone(screenshot)
    paste_phone(canvas, phone)
    return canvas


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Missing source folder: {SRC}")

    OUT.mkdir(parents=True, exist_ok=True)
    title_font = ImageFont.truetype(str(FONT_DISPLAY), 58)
    subtitle_font = ImageFont.truetype(str(FONT_BODY), 34)

    for src_name, title, subtitle in SHOTS:
        out_name = src_name.replace(".png", "-gp.png")
        image = build_one(src_name, title, subtitle, title_font, subtitle_font)
        out_path = OUT / out_name
        image.save(out_path, format="PNG", optimize=True)
        ratio = image.width / image.height
        print(f"{out_path.name}  {image.size}  ratio={ratio:.3f}")


if __name__ == "__main__":
    main()
