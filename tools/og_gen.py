# -*- coding: utf-8 -*-
"""og.png 1200x630 — 'The Settling Line': horizon, ticks, AFTER THE FALL."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os

SCRATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "og.png")
W, H = 1200, 630
BG = (12, 15, 20)
INK = (242, 239, 236)
EMBER_HI = (224, 90, 65)
STEEL = (154, 168, 186)
DIMC = (128, 147, 168)
UP = (110, 200, 136)
DOWN = (242, 118, 107)
HY = 448  # horizon y

img = Image.new("RGB", (W, H), BG).convert("RGBA")

# 2. warm ground below the line (alpha ramp 0@448 -> 150@630)
ground = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gp = ground.load()
for y in range(HY, H):
    a = int(150 * (y - HY) / (H - HY))
    for x in range(W):
        gp[x, y] = (22, 10, 10, a)
img = Image.alpha_composite(img, ground)

# 3. horizon glow: blurred ellipse mask, max alpha 70
mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
md.ellipse([140, 318, 1060, 578], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(55)).point(lambda v: v * 70 // 255)
glow = Image.new("RGBA", (W, H), EMBER_HI + (0,))
glow.putalpha(mask)
img = Image.alpha_composite(img, glow)

d = ImageDraw.Draw(img)

# 4. embers
for cx, cy, r, a in [(150, 330, 2, 110), (240, 300, 2, 70), (330, 370, 2, 130), (430, 270, 1, 60),
                     (560, 395, 2, 140), (660, 340, 1, 70), (760, 385, 2, 120), (850, 320, 2, 90),
                     (950, 370, 2, 140), (1040, 310, 1, 70), (1105, 395, 2, 110)]:
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=EMBER_HI + (a,))

# fonts
def load(path, size, axes=None):
    f = ImageFont.truetype(path, size)
    if axes:
        f.set_variation_by_axes(axes)
    return f

oswald = os.path.join(SCRATCH, "oswald.ttf")
inter = os.path.join(SCRATCH, "inter.ttf")
f_top = load(oswald, 66, [600])
f_fall = load(oswald, 220, [600])
f_stats = load(inter, 27, [27, 700])
f_sub = load(inter, 31, [31, 500])

def tracked_w(font, text, tr):
    return sum(font.getlength(c) for c in text) + tr * (len(text) - 1)

def draw_tracked(dr, x, y, text, font, fill, tr):
    for c in text:
        dr.text((x, y), c, font=font, fill=fill, anchor="lm")
        x += font.getlength(c) + tr

# 7. AFTER THE
t1 = "AFTER THE"
draw_tracked(d, 600 - tracked_w(f_top, t1, 10) / 2, 148, t1, f_top, INK, 10)

# 8. FALL with glow
t2 = "FALL"
fx = 600 - tracked_w(f_fall, t2, 26) / 2
layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ld = ImageDraw.Draw(layer)
draw_tracked(ld, fx, 298, t2, f_fall, EMBER_HI + (255,), 26)
layer = layer.filter(ImageFilter.GaussianBlur(28))
layer.putalpha(layer.getchannel("A").point(lambda v: v * 55 // 100))
img = Image.alpha_composite(img, layer)
d = ImageDraw.Draw(img)
draw_tracked(d, fx, 298, t2, f_fall, EMBER_HI, 26)

# 5. horizon line 2px, alpha fades from center
for x in range(W):
    a = max(0, round(255 * (1 - abs(x - 600) / 560)))
    if a:
        d.point([(x, HY), (x, HY + 1)], fill=EMBER_HI + (a,))

# 6. ticks crossing the line
for x, h in [(120, 26), (205, 42), (258, 16), (395, 32), (500, 20),
             (688, 38), (752, 18), (900, 28), (1002, 44), (1088, 22)]:
    d.rectangle([x, HY - h, x + 2, HY - 1], fill=UP + (200,))
for x, h in [(162, 34), (300, 18), (348, 44), (452, 24), (580, 16),
             (640, 36), (806, 42), (858, 20), (948, 32), (1118, 38)]:
    d.rectangle([x, HY + 2, x + 2, HY + 2 + h], fill=DOWN + (200,))

# 10. subtitle
d.text((600, 534), "Лидерборд Европы после вайпа рейтинга · 31 июля",
       font=f_sub, fill=STEEL, anchor="mm")

# 9. stats row at y=586
up_txt, dn_txt, sep = "+3303", "−3311", "·"
tri_w, gap, pad = 18, 8, 22
total = (tri_w + gap + d.textlength(up_txt, font=f_stats) + pad +
         d.textlength(sep, font=f_stats) + pad + tri_w + gap +
         d.textlength(dn_txt, font=f_stats))
x = 600 - total / 2
d.polygon([(x, 592), (x + 18, 592), (x + 9, 578)], fill=UP)
x += tri_w + gap
d.text((x, 585), up_txt, font=f_stats, fill=UP, anchor="lm")
x += d.textlength(up_txt, font=f_stats) + pad
d.text((x, 585), sep, font=f_stats, fill=DIMC, anchor="lm")
x += d.textlength(sep, font=f_stats) + pad
d.polygon([(x, 578), (x + 18, 578), (x + 9, 592)], fill=DOWN)
x += tri_w + gap
d.text((x, 585), dn_txt, font=f_stats, fill=DOWN, anchor="lm")

img.convert("RGB").save(OUT, "PNG", optimize=True)
print("saved", OUT, os.path.getsize(OUT), "bytes")
