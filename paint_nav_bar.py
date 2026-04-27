"""
paint_nav_bar.py
────────────────
Run this script in the same folder as 425image.jpeg and transparent logo.png.
It paints the Conception nav bar directly onto the laptop screen in the photo,
so the HTML intro zoom shows it baked in — no overlay, no alignment drift.

Usage:  python3 paint_nav_bar.py
Output: 425image.jpeg  (overwritten in-place)
"""

from PIL import Image, ImageDraw, ImageFont
import os, sys

# ── File paths ──────────────────────────────────────────────────────────────
PHOTO_PATH = "425image.jpeg"
LOGO_PATH  = "transparent logo.png"
OUT_PATH   = "425image.jpeg"   # overwrite in-place

if not os.path.exists(PHOTO_PATH):
    sys.exit(f"ERROR: {PHOTO_PATH} not found. Run this script in the same folder.")

# ── Load photo ───────────────────────────────────────────────────────────────
photo = Image.open(PHOTO_PATH).convert("RGBA")
W, H  = photo.size
print(f"Photo size: {W}×{H}")

# ── Laptop screen nav bar geometry (measured on 1456×816 source) ─────────────
#
#  The laptop screen is perspective-tilted: left side is closer (lower in frame),
#  right side is further (higher in frame). The top edge of the screen is a
#  very slight diagonal — almost flat but tilted ~4px over 600px of width.
#
#  Nav bar corners in image pixels (top-left, top-right, bottom-right, bottom-left):
#
#    TL ──────────────────────────────── TR
#    │   LOGO   HOME   LEARNING RES ≡   │
#    BL ──────────────────────────────── BR
#
#  Measured from the photo (adjust these if your image differs):
NAV_TL = (487,  154)   # top-left  corner of nav bar
NAV_TR = (1101, 148)   # top-right corner (slightly higher — perspective tilt)
NAV_BR = (1101, 192)   # bottom-right
NAV_BL = (487,  198)   # bottom-left  (slightly lower — matches tilt)

NAV_COLOR = (26, 43, 69)   # #1A2B45 — exact navy from CSS variable --navy

# ── Draw layer ───────────────────────────────────────────────────────────────
overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw    = ImageDraw.Draw(overlay)

# Fill the perspective-correct trapezoid with navy
nav_poly = [NAV_TL, NAV_TR, NAV_BR, NAV_BL]
draw.polygon(nav_poly, fill=(*NAV_COLOR, 255))

# ── Helper: get nav bar bounding box ─────────────────────────────────────────
nav_x     = min(NAV_TL[0], NAV_BL[0])
nav_y     = min(NAV_TL[1], NAV_TR[1])
nav_w     = max(NAV_TR[0], NAV_BR[0]) - nav_x
nav_h     = max(NAV_BL[1], NAV_BR[1]) - nav_y
nav_mid_y = (NAV_TL[1] + NAV_BL[1]) // 2   # vertical centre on left edge

# ── Logo ─────────────────────────────────────────────────────────────────────
logo_h_px = int(nav_h * 0.68)

if os.path.exists(LOGO_PATH):
    logo_raw = Image.open(LOGO_PATH).convert("RGBA")
    # Scale keeping aspect ratio
    lw, lh   = logo_raw.size
    logo_w_px = int(logo_h_px * lw / lh)
    logo_img  = logo_raw.resize((logo_w_px, logo_h_px), Image.LANCZOS)

    # Tint to white: replace every pixel's RGB with white, keep alpha
    r, g, b, a = logo_img.split()
    white_logo  = Image.merge("RGBA", (
        Image.new("L", logo_img.size, 255),
        Image.new("L", logo_img.size, 255),
        Image.new("L", logo_img.size, 255),
        a
    ))

    logo_x = NAV_TL[0] + int(nav_w * 0.015)
    logo_y = nav_mid_y - logo_h_px // 2
    overlay.paste(white_logo, (logo_x, logo_y), white_logo)
    logo_right = logo_x + logo_w_px
    print(f"Logo drawn at ({logo_x}, {logo_y}) size {logo_w_px}×{logo_h_px}")
else:
    # No logo file — skip silently (text fallback below)
    logo_right = NAV_TL[0] + int(nav_w * 0.16)
    print("WARNING: transparent logo.png not found — logo skipped")

# ── Nav link text ─────────────────────────────────────────────────────────────
# Font: use a system bold sans-serif, or fall back to Pillow default
FONT_SIZE = max(8, int(nav_h * 0.30))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE)
except:
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", FONT_SIZE)
    except:
        font = ImageFont.load_default()

WHITE = (255, 255, 255, 255)

# Position links: start after the logo with a gap
link_gap   = int(nav_w * 0.035)
text_y     = nav_mid_y   # will be vertically centred via anchor

links = ["HOME", "LEARNING RESOURCES  ▾"]

# Start text after logo
cursor_x = logo_right + link_gap

for i, txt in enumerate(links):
    bbox = draw.textbbox((0, 0), txt, font=font)
    tw   = bbox[2] - bbox[0]
    th   = bbox[3] - bbox[1]
    draw.text(
        (cursor_x, nav_mid_y - th // 2),
        txt,
        font=font,
        fill=WHITE
    )
    cursor_x += tw + link_gap * (2.2 if i == 0 else 1)

# ── Hamburger icon (3 white lines, right side) ───────────────────────────────
hbg_w     = int(nav_h * 0.38)
hbg_x     = NAV_TR[0] - int(nav_w * 0.022) - hbg_w
line_h    = max(1, int(nav_h * 0.07))
line_gap  = int(nav_h * 0.14)
total_bar = line_h * 3 + line_gap * 2
hbg_y     = nav_mid_y - total_bar // 2

for i in range(3):
    y0 = hbg_y + i * (line_h + line_gap)
    draw.rectangle(
        [(hbg_x, y0), (hbg_x + hbg_w, y0 + line_h)],
        fill=WHITE
    )

print(f"Hamburger drawn at x={hbg_x}, nav_mid_y={nav_mid_y}")

# ── Composite and save ────────────────────────────────────────────────────────
result = Image.alpha_composite(photo, overlay).convert("RGB")
result.save(OUT_PATH, "JPEG", quality=95)
print(f"Saved → {OUT_PATH}")
print("Done. Reload your browser to see the updated intro photo.")
