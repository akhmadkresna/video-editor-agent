"""Compose a locked odoo-studio-agentic-ai thumbnail from a text-free plate.

Image generators drift on alignment, type scale and safe margins, so the copy
stack is drawn here instead. Metrics come from ``refs/part1-canonical.png``
(same four-block stack: badge, two title lines, payoff, chips).

    uv run python styles/series/odoo-studio-agentic-ai/build_thumbnail.py \
        --plate plate.png --out edit/thumbnails/yt-thumb-odoo-studio-part3.png \
        --part 3 --line-a "AI BUILDS" --line-b "ODOO SALES" \
        --chip cart=Sales --chip basket=Cart --chip box=Stock

The plate must be text-free artwork: host right (beige tee, whole head with
headroom), his studio room behind him, darkened Odoo UI panels left. Any aspect
is accepted; it is top-cropped to 16:9 so generated 3:2 output keeps the hair.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720

# Canonical copy metrics, sampled from refs/part1-canonical.png
MARGIN_X = 49
BADGE_Y, BADGE_W, BADGE_H, BADGE_CAP = 88, 161, 57, 27
LINE_A_Y, LINE_A_CAP = 173, 134
LINE_B_Y, LINE_B_CAP = 321, 125
PAYOFF_Y, PAYOFF_CAP = 479, 39
RULE_Y0, RULE_Y1 = 538, 544
CHIPS_Y0, CHIPS_Y1 = 570, 628
TITLE_TRACK = 8

ACCENT = (61, 191, 243)
ACCENT_TITLE = (71, 201, 244)
INK = (255, 255, 255)
CHIP_FILL = (26, 34, 44)

FONT_DIR = Path(__file__).parent / "fonts"
ANTON = FONT_DIR / "Anton-Regular.ttf"
INTER = FONT_DIR / "Inter.ttf"
FONT_HINT = (
    "Missing fonts. Download into "
    f"{FONT_DIR}:\n"
    "  Anton-Regular.ttf  https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf\n"
    "  Inter.ttf          https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
)


def inter(size: int, weight: int = 700) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(INTER), size)
    for axes in ([14.0, float(weight)], [float(weight)]):
        try:
            f.set_variation_by_axes(axes)
            break
        except Exception:
            continue
    return f


def fit_cap(text: str, target_cap: int, *, condensed: bool, weight: int = 700):
    """Return a font whose uppercase cap height matches ``target_cap``."""
    size = 200
    for _ in range(6):
        f = ImageFont.truetype(str(ANTON), size) if condensed else inter(size, weight)
        box = f.getbbox(text)
        cap = box[3] - box[1]
        if not cap:
            break
        size = max(8, round(size * target_cap / cap))
    return ImageFont.truetype(str(ANTON), size) if condensed else inter(size, weight)


def draw_text_at(draw, xy, text, font, fill, *, shadow=None, track=0):
    """Place text so its glyph bbox top-left lands exactly on ``xy``."""
    x, y = xy
    box = font.getbbox(text)
    py = y - box[1]
    if not track:
        px = x - box[0]
        if shadow:
            off, col = shadow
            draw.text((px + off, py + off), text, font=font, fill=col)
        draw.text((px, py), text, font=font, fill=fill)
        return box[2] - box[0], box[3] - box[1]

    cx = x - box[0]
    for ch in text:
        if shadow:
            off, col = shadow
            draw.text((cx + off, py + off), ch, font=font, fill=col)
        draw.text((cx, py), ch, font=font, fill=fill)
        cx += font.getlength(ch) + track
    return int(cx - track - x), box[3] - box[1]


def icon(draw, kind: str, x: int, y: int, s: int, col, wd: int = 3) -> None:
    """Cyan outline icon inside an ``s`` x ``s`` box at (x, y)."""
    if kind == "cart":
        draw.line([(x, y + 4), (x + 6, y + 4)], fill=col, width=wd)
        draw.line([(x + 6, y + 4), (x + 11, y + s - 12)], fill=col, width=wd)
        draw.line(
            [(x + 8, y + 9), (x + s, y + 9), (x + s - 5, y + s - 12), (x + 11, y + s - 12)],
            fill=col,
            width=wd,
        )
        for cx in (x + 14, x + s - 8):
            draw.ellipse([cx - 3, y + s - 11, cx + 3, y + s - 5], outline=col, width=wd)
    elif kind == "basket":
        draw.arc([x + 8, y + 2, x + s - 8, y + 22], start=180, end=360, fill=col, width=wd)
        draw.line([(x, y + 12), (x + s, y + 12)], fill=col, width=wd)
        draw.line(
            [(x + 4, y + 14), (x + 9, y + s - 3), (x + s - 9, y + s - 3), (x + s - 4, y + 14)],
            fill=col,
            width=wd,
        )
    elif kind == "box":
        mid = s // 2
        top = y + mid // 2 + 2
        bot = y + s - mid // 2 - 2
        pts = [(x + mid, y), (x + s, top), (x + s, bot), (x + mid, y + s), (x, bot), (x, top)]
        draw.line(pts + [pts[0]], fill=col, width=wd, joint="curve")
        draw.line([(x, top), (x + mid, y + mid), (x + s, top)], fill=col, width=wd)
        draw.line([(x + mid, y + mid), (x + mid, y + s)], fill=col, width=wd)
    elif kind == "menu":
        for i in range(3):
            gy = y + 6 + i * 10
            draw.line([(x + 2, gy), (x + s - 2, gy)], fill=col, width=wd)
    elif kind == "chart":
        draw.line([(x + 2, y + 2), (x + 2, y + s - 3), (x + s - 1, y + s - 3)], fill=col, width=wd)
        for i, bh in enumerate((10, 18, 26)):
            bx = x + 9 + i * 8
            draw.line([(bx, y + s - 5), (bx, y + s - 5 - bh)], fill=col, width=5)
    elif kind == "receipt":
        draw.rounded_rectangle(
            [x + 4, y + 1, x + s - 4, y + s - 1], radius=3, outline=col, width=wd
        )
        for i in range(3):
            gy = y + 9 + i * 7
            draw.line([(x + 10, gy), (x + s - 10, gy)], fill=col, width=2)
    elif kind == "pie":
        draw.ellipse([x + 2, y + 2, x + s - 2, y + s - 2], outline=col, width=wd)
        mid = s // 2
        draw.line([(x + mid, y + mid), (x + mid, y + 2)], fill=col, width=wd)
        draw.line([(x + mid, y + mid), (x + s - 2, y + mid)], fill=col, width=wd)
    else:
        draw.rounded_rectangle([x, y + 4, x + s, y + s - 4], radius=4, outline=col, width=wd)


def build(args: argparse.Namespace) -> Path:
    if not ANTON.is_file() or not INTER.is_file():
        sys.exit(FONT_HINT)

    plate = Image.open(args.plate).convert("RGB")
    pw, ph = plate.size
    # Top-crop, never centre-crop: generators put the head near the top edge.
    plate = plate.crop((0, 0, pw, min(round(pw * 9 / 16), ph))).resize((W, H), Image.LANCZOS)

    scrim = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scrim)
    for x in range(W):
        t = max(0.0, 1.0 - x / (W * 0.62))
        sd.line([(x, 0), (x, H)], fill=int(args.scrim * t))
    plate = Image.composite(Image.new("RGB", (W, H), (6, 10, 16)), plate, scrim)

    img = plate.convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    badge = f"PART {args.part}"
    bf = fit_cap(badge, BADGE_CAP, condensed=False, weight=800)
    d.rounded_rectangle(
        [MARGIN_X, BADGE_Y, MARGIN_X + BADGE_W, BADGE_Y + BADGE_H], radius=12, fill=ACCENT
    )
    box = bf.getbbox(badge)
    draw_text_at(
        d,
        (
            MARGIN_X + (BADGE_W - (box[2] - box[0])) // 2,
            BADGE_Y + (BADGE_H - (box[3] - box[1])) // 2,
        ),
        badge,
        bf,
        INK,
    )

    shadow = (6, (0, 0, 0, 190))
    draw_text_at(
        d,
        (MARGIN_X, LINE_A_Y),
        args.line_a,
        fit_cap(args.line_a, LINE_A_CAP, condensed=True),
        INK,
        shadow=shadow,
        track=TITLE_TRACK,
    )
    draw_text_at(
        d,
        (MARGIN_X, LINE_B_Y),
        args.line_b,
        fit_cap(args.line_b, LINE_B_CAP, condensed=True),
        ACCENT_TITLE,
        shadow=shadow,
        track=TITLE_TRACK,
    )

    # Payoff is a wide grotesque in the refs, not the condensed title face.
    payoff_w, _ = draw_text_at(
        d,
        (MARGIN_X + 3, PAYOFF_Y),
        args.payoff,
        fit_cap(args.payoff, PAYOFF_CAP, condensed=False, weight=900),
        INK,
        shadow=(4, (0, 0, 0, 170)),
        track=2,
    )
    d.rounded_rectangle(
        [MARGIN_X, RULE_Y0, MARGIN_X + payoff_w + 6, RULE_Y1], radius=3, fill=ACCENT
    )

    ch = CHIPS_Y1 - CHIPS_Y0
    chip_font = inter(34, 600)
    isz, pad_l, gap_icon, pad_r, gap = 34, 22, 14, 24, 20
    x = MARGIN_X
    for spec in args.chip:
        kind, _, label = spec.partition("=")
        lb = chip_font.getbbox(label)
        lw, lh = lb[2] - lb[0], lb[3] - lb[1]
        cw = pad_l + isz + gap_icon + lw + pad_r
        d.rounded_rectangle(
            [x, CHIPS_Y0, x + cw, CHIPS_Y1],
            radius=ch // 2,
            fill=CHIP_FILL + (235,),
            outline=ACCENT,
            width=3,
        )
        icon(d, kind, x + pad_l, CHIPS_Y0 + (ch - isz) // 2, isz, ACCENT)
        draw_text_at(
            d, (x + pad_l + isz + gap_icon, CHIPS_Y0 + (ch - lh) // 2), label, chip_font, INK
        )
        x += cw + gap

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(img, layer).convert("RGB").save(out)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plate", required=True, help="Text-free background plate")
    p.add_argument("--out", required=True, help="Output png (exactly 1280x720)")
    p.add_argument("--part", required=True)
    p.add_argument("--line-a", required=True, help="Title line 1 (white, upper)")
    p.add_argument("--line-b", required=True, help="Title line 2 (accent, upper)")
    p.add_argument("--payoff", default="1 FREE APP")
    p.add_argument(
        "--chip",
        action="append",
        default=[],
        metavar="ICON=LABEL",
        help="Repeat exactly 3 times. ICON: cart, basket, box, menu, chart, receipt, pie",
    )
    p.add_argument("--scrim", type=int, default=95, help="Left darkening strength (0-255)")
    args = p.parse_args()
    if len(args.chip) != 3:
        p.error("pass exactly 3 --chip values (the series locks 3 chips)")
    out = build(args)
    print(f"wrote {out} 1280x720")


if __name__ == "__main__":
    main()
