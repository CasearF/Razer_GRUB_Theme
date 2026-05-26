"""Render a preview that mimics how GRUB will draw the Razer theme."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BG = ROOT / "Razer" / "background.png"
HL_W = ROOT / "Razer" / "highlight_w.png"
DST = ROOT / "preview.png"

RAZER_GREEN = (0x44, 0xD6, 0x2C)
WHITE = (0xFF, 0xFF, 0xFF)


def find_font(size):
    for path in [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main():
    img = Image.open(BG).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Match GRUB boot_menu: left=28%, top=22%, width=50%, height=45% of 1920x1080
    box_left = int(0.28 * 1920) + 30
    box_top = int(0.22 * 1080) + 35
    item_h = 33 + 5
    items = ["Ubuntu", "Windows", "macOS", "SteamOS", "Firmware"]
    font = find_font(20)

    # highlight on the first item
    hl = Image.open(HL_W).convert("RGBA")
    img.paste(hl, (box_left - hl.width - 4, box_top), hl)
    # white pill behind selected text
    sel_w, sel_h = 240, 30
    draw.rectangle(
        [(box_left, box_top), (box_left + sel_w, box_top + sel_h)],
        outline=WHITE,
        width=2,
    )

    for i, name in enumerate(items):
        y = box_top + i * item_h
        color = WHITE if i == 0 else RAZER_GREEN
        draw.text((box_left + 10, y), name, font=font, fill=color)

    img.save(DST)
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
