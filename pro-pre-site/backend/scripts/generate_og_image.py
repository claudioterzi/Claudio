"""Generate a professional 1200x630 social share image for Pro-pre.
Renders directly to /app/frontend/public/og-image.png so it's served statically.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap

W, H = 1200, 630
OUT = Path("/app/frontend/public/og-image.png")

NAVY = (27, 40, 69)          # #1B2845
NAVY_DEEP = (11, 20, 41)      # darker
BLUE = (91, 164, 212)         # #5BA4D4
YELLOW = (250, 204, 21)       # #FACC15
WHITE = (255, 255, 255)
SOFT_WHITE = (241, 245, 249)
MUTED = (148, 163, 184)


def _load_font(sizes, prefer_bold=True):
    """Try a list of common serif/sans fonts; return first match at given size."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if prefer_bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if prefer_bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, sizes)
        except Exception:
            continue
    return ImageFont.load_default()


def _text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _gradient_bg():
    """Create a vertical navy→deeper-navy gradient background."""
    img = Image.new("RGB", (W, H), NAVY_DEEP)
    top = NAVY
    bottom = NAVY_DEEP
    for y in range(H):
        ratio = y / H
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        for x in range(W):
            pass
    # For performance, use ImageDraw approach
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        ratio = y / H
        r = int(NAVY[0] + (NAVY_DEEP[0] - NAVY[0]) * ratio)
        g = int(NAVY[1] + (NAVY_DEEP[1] - NAVY[1]) * ratio)
        b = int(NAVY[2] + (NAVY_DEEP[2] - NAVY[2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return img


def _decorative_circles(img):
    """Add subtle blurred blue circles on the right for visual interest."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # Big soft blue circle top-right
    od.ellipse((W - 380, -180, W + 100, 300), fill=(91, 164, 212, 60))
    # Smaller circle bottom-right
    od.ellipse((W - 260, H - 220, W - 20, H + 20), fill=(91, 164, 212, 40))
    # Tiny yellow accent circle
    od.ellipse((W - 550, H - 460, W - 460, H - 370), fill=(250, 204, 21, 80))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=40))
    img.paste(overlay, (0, 0), overlay)
    return img


def _draw_logo(img, x, y):
    """Draw a text-based Pro-pre logotype badge (self-contained, no image URL fetch)."""
    draw = ImageDraw.Draw(img)
    logo_font = _load_font(38)
    # Rounded rectangle background
    box_w, box_h = 220, 60
    draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=30, fill=WHITE)
    label = "PRO-PRE"
    lw, lh = _text_size(draw, label, logo_font)
    draw.text((x + (box_w - lw) / 2, y + (box_h - lh) / 2 - 4), label, font=logo_font, fill=NAVY)


def build():
    img = _gradient_bg()
    img = _decorative_circles(img)
    draw = ImageDraw.Draw(img)

    # Left content padding
    pad_left = 80
    y_cursor = 70

    # Logo badge
    _draw_logo(img, pad_left, y_cursor)
    y_cursor += 90

    # Kicker
    kicker_font = _load_font(24)
    kicker = "NETTOYAGE TEXTILE PROFESSIONNEL"
    draw.text((pad_left, y_cursor), kicker, font=kicker_font, fill=BLUE)
    y_cursor += 55

    # Main headline (large, wraps automatically)
    title_font = _load_font(72)
    title_lines = ["Vraiment propre.", "Vraiment simple."]
    for line in title_lines:
        draw.text((pad_left, y_cursor), line, font=title_font, fill=WHITE)
        y_cursor += 76

    y_cursor += 20

    # Subtitle
    sub_font = _load_font(30, prefer_bold=False)
    sub_lines = [
        "Canapés · Matelas · Tapis · Auto",
        "Bruxelles · Paris · Bergamo",
    ]
    for line in sub_lines:
        draw.text((pad_left, y_cursor), line, font=sub_font, fill=SOFT_WHITE)
        y_cursor += 40

    y_cursor += 30

    # CTA badge
    cta_font = _load_font(26)
    cta_text = "Réservation en ligne en 2 minutes"
    cta_w, cta_h = _text_size(draw, cta_text, cta_font)
    box_x, box_y = pad_left, y_cursor
    box_w = cta_w + 60
    box_h = cta_h + 28
    draw.rounded_rectangle((box_x, box_y, box_x + box_w, box_y + box_h), radius=32, fill=YELLOW)
    draw.text((box_x + 30, box_y + 12), cta_text, font=cta_font, fill=NAVY)
    y_cursor += box_h + 30

    # Bottom domain
    domain_font = _load_font(22, prefer_bold=False)
    draw.text((pad_left, H - 60), "www.pro-pre.com", font=domain_font, fill=BLUE)

    # Right column: Free test badge — solid yellow card for max readability
    badge_font_kicker = _load_font(22)
    badge_font_big = _load_font(96)
    badge_font_sm = _load_font(20, prefer_bold=False)
    badge_x = W - 400
    badge_y = 180
    badge_w = 320
    badge_h = 280
    # Solid yellow rounded card
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
        radius=28, fill=YELLOW,
    )
    # Content
    draw.text((badge_x + 24, badge_y + 24), "DÉFI DE LA BANDE", font=badge_font_kicker, fill=NAVY)
    # Big "GRATUIT"
    big_txt = "GRATUIT"
    bw, bh = _text_size(draw, big_txt, badge_font_big)
    draw.text((badge_x + (badge_w - bw) / 2, badge_y + 62), big_txt, font=badge_font_big, fill=NAVY)
    # Divider line
    draw.line((badge_x + 40, badge_y + 190, badge_x + badge_w - 40, badge_y + 190), fill=NAVY, width=2)
    # Details
    draw.text((badge_x + 24, badge_y + 205), "Test 30 × 30 cm", font=badge_font_sm, fill=NAVY_DEEP)
    draw.text((badge_x + 24, badge_y + 235), "Sans engagement", font=badge_font_sm, fill=NAVY_DEEP)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"OK: written {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
