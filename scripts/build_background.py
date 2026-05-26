"""Recolor ROG background to Razer theme and replace bottom-left logo."""
import colorsys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SRC = Path(__file__).resolve().parents[1] / "ROG_GRUB_Theme" / "ROG" / "background.png"
DST = Path(__file__).resolve().parents[1] / "Razer" / "background.png"

# Razer signature green (#44D62C) - HSV hue ~= 114 deg
RAZER_GREEN = (0x44, 0xD6, 0x2C)


def red_to_green(rgb):
    r, g, b = [c / 255.0 for c in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    # near-red hues (around 0 / 1.0) -> shift to ~114 deg (0.317)
    # Also catch pink/coral hues
    if s < 0.18:
        return rgb  # grey/white/black untouched
    # Treat hues 0.90..1.0 and 0.0..0.05 as "red-ish"
    if h <= 0.06 or h >= 0.90:
        new_h = 0.317  # ~114 deg
        nr, ng, nb = colorsys.hsv_to_rgb(new_h, s, v)
        return (int(nr * 255), int(ng * 255), int(nb * 255))
    return rgb


def main():
    img = Image.open(SRC).convert("RGBA")
    pixels = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            nr, ng, nb = red_to_green((r, g, b))
            pixels[x, y] = (nr, ng, nb, a)

    draw = ImageDraw.Draw(img)

    # ---- Rewrite the title bar text: "TIME TO BOOT" -> "READY TO STRIKE" ----
    # Bar fill (post-shift) is approximately #43FB30. Paint over the original
    # text area, then redraw the new title in black.
    BAR_FILL = (0x43, 0xFB, 0x30, 255)
    # Cover only the inner rectangular text region (avoid the slanted right
    # edge of the parallelogram, which is around x>=1000).
    draw.rectangle([(545, 168), (1000, 228)], fill=BAR_FILL)

    title_font = None
    for fp in [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/bahnschrift.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]:
        if Path(fp).exists():
            title_font = ImageFont.truetype(fp, 44)
            break
    if title_font is None:
        title_font = ImageFont.load_default()

    title_text = "READY TO STRIKE"
    # Center the title within the rectangular portion of the bar.
    tb = draw.textbbox((0, 0), title_text, font=title_font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx = 545 + ((1000 - 545) - tw) // 2 - tb[0]
    ty = 168 + ((228 - 168) - th) // 2 - tb[1]
    draw.text((tx, ty), title_text, font=title_font, fill=(0, 0, 0, 255))

    # ---- Replace ROG logo at bottom-left with Razer wordmark ----
    # Original logo area roughly: x=60..290, y=955..1025
    draw.rectangle([(40, 940), (340, 1040)], fill=(0, 0, 0, 255))

    # Try to load a system font for the wordmark
    font_path_candidates = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    big_font = small_font = None
    for fp in font_path_candidates:
        if Path(fp).exists():
            big_font = ImageFont.truetype(fp, 34)
            small_font = ImageFont.truetype(fp, 14)
            break
    if big_font is None:
        big_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw a stylized Razer mark: three vertical bars (snake-head abstraction)
    # then "RAZER" wordmark and "FOR GAMERS. BY GAMERS." tagline
    bar_x = 60
    bar_y = 970
    # three angled "fang"/snake-head bars
    for i, (dx, dy, ang_w) in enumerate([(0, 0, 6), (14, 0, 6), (28, 0, 6)]):
        draw.polygon([
            (bar_x + dx, bar_y),
            (bar_x + dx + ang_w, bar_y),
            (bar_x + dx + ang_w - 6, bar_y + 36),
            (bar_x + dx - 6, bar_y + 36),
        ], fill=RAZER_GREEN)

    # vertical separator
    sep_x = bar_x + 50
    draw.line([(sep_x, bar_y - 2), (sep_x, bar_y + 40)], fill=RAZER_GREEN, width=2)

    # "RAZER" wordmark
    draw.text((sep_x + 12, bar_y - 4), "RAZER", font=big_font, fill=RAZER_GREEN)
    # tagline below
    draw.text((sep_x + 12, bar_y + 28), "FOR GAMERS. BY GAMERS.", font=small_font, fill=RAZER_GREEN)

    DST.parent.mkdir(parents=True, exist_ok=True)
    img.save(DST)
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
