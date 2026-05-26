"""Recolor highlight and progress-bar accents for the Razer theme."""
import colorsys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "ROG_GRUB_Theme" / "ROG"
DST_DIR = ROOT / "Razer"

# Razer green. Selected accent (replacement for teal #74d6cf) -> bright white-green
RAZER_GREEN = (0x44, 0xD6, 0x2C)
RAZER_BRIGHT = (0xC8, 0xFF, 0xB0)  # pale highlight tint for selected-item arrow


def shift_pixel(rgb, mode):
    r, g, b = [c / 255.0 for c in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < 0.15:
        return rgb
    if mode == "red_to_green":
        # red-ish hues -> Razer green hue
        if h <= 0.06 or h >= 0.90:
            nr, ng, nb = colorsys.hsv_to_rgb(0.311, s, v)
            return (int(nr * 255), int(ng * 255), int(nb * 255))
    elif mode == "teal_to_pale_green":
        # cyan/teal hues (~0.45..0.55) -> pale green
        if 0.40 <= h <= 0.60:
            # use a pale, slightly desaturated green
            nr, ng, nb = colorsys.hsv_to_rgb(0.311, s * 0.65, min(1.0, v * 1.05))
            return (int(nr * 255), int(ng * 255), int(nb * 255))
    return rgb


def recolor(src_name, mode):
    src = SRC_DIR / src_name
    dst = DST_DIR / src_name
    img = Image.open(src).convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            nr, ng, nb = shift_pixel((r, g, b), mode)
            px[x, y] = (nr, ng, nb, a)
    img.save(dst)
    print(f"wrote {dst}")


def build_clean_highlight():
    """Replace the upstream highlight_c with a proper stretchable middle piece,
    and add highlight_e so the box has a real right edge.

    The upstream highlight_c.png baked a fixed-width white "L" frame into the
    center tile, so GRUB stretching it for longer menu items distorted the
    decoration. A clean 9-slice keeps borders in dedicated edge tiles.
    """
    item_h = 33  # must match theme.txt item_height
    border = (0xBC, 0xF7, 0xB2, 255)  # match the pale green of highlight_w

    # highlight_c: top + bottom row colored, middle transparent
    c_w = 4
    c = Image.new("RGBA", (c_w, item_h), (0, 0, 0, 0))
    cpx = c.load()
    for x in range(c_w):
        cpx[x, 0] = border
        cpx[x, item_h - 1] = border
    c.save(DST_DIR / "highlight_c.png")
    print(f"wrote {DST_DIR / 'highlight_c.png'}")

    # highlight_e: 2px-wide vertical line as the right edge
    e_w = 2
    e = Image.new("RGBA", (e_w, item_h), (0, 0, 0, 0))
    epx = e.load()
    for y in range(item_h):
        for x in range(e_w):
            epx[x, y] = border
    e.save(DST_DIR / "highlight_e.png")
    print(f"wrote {DST_DIR / 'highlight_e.png'}")


def main():
    recolor("highlight_w.png", "teal_to_pale_green")
    recolor("progress_highlight_c.png", "red_to_green")
    build_clean_highlight()


if __name__ == "__main__":
    main()
