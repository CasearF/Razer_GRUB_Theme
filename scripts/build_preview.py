"""Render a preview that mimics how GRUB will draw the Razer theme."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "Razer"
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


def composite_highlight(canvas, x, y, w, h):
    """Composite the 9-slice highlight pieces (_w / _c / _e) onto canvas at
    the given menu-item rect, the same way GRUB stretches them."""
    hl_w = Image.open(THEME / "highlight_w.png").convert("RGBA")
    hl_c = Image.open(THEME / "highlight_c.png").convert("RGBA")
    hl_e = Image.open(THEME / "highlight_e.png").convert("RGBA")

    # _w on the left (fixed width, vertically centered to h)
    w_piece = hl_w
    canvas.paste(w_piece, (x - w_piece.width, y + (h - w_piece.height) // 2), w_piece)

    # _e on the right (fixed width, stretched vertically to h)
    e_piece = hl_e.resize((hl_e.width, h))
    canvas.paste(e_piece, (x + w - e_piece.width, y), e_piece)

    # _c stretched to fill the middle (between _w right edge anchored to x,
    # up to _e left edge)
    c_w = max(1, w - e_piece.width)
    c_piece = hl_c.resize((c_w, h))
    canvas.paste(c_piece, (x, y), c_piece)


def main():
    img = Image.open(THEME / "background.png").convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Match GRUB boot_menu: left=28%, top=22%, width=50%, height=45% of 1920x1080
    box_left = int(0.28 * 1920) + 30
    box_top = int(0.22 * 1080) + 35
    item_h = 33 + 5
    items = ["Ubuntu", "Windows Boot Manager", "macOS", "SteamOS", "Firmware"]
    font = find_font(20)

    selected = 1
    for i, name in enumerate(items):
        y = box_top + i * item_h
        if i == selected:
            # measure text and size the highlight rect to match
            tb = draw.textbbox((0, 0), name, font=font)
            text_w = tb[2] - tb[0]
            pad_x = 14
            box_w = text_w + pad_x * 2
            composite_highlight(img, box_left, y, box_w, 33)
            draw.text((box_left + pad_x, y + 4), name, font=font, fill=WHITE)
        else:
            draw.text((box_left + 14, y + 4), name, font=font, fill=RAZER_GREEN)

    img.save(DST)
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
