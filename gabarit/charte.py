"""Charte Flash IA (helpers repris de gabarit/render_carrousel_001.py)."""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BG = (11, 11, 15); YEL = (255, 225, 77); WHITE = (255, 255, 255); GREY = (150, 150, 160); DARK = (24, 24, 30)
F_TITLE = "/home/claude/flash-ia-reels/gabarit/fonts/ArchivoBlack.ttf"
F_BOLD = "/home/claude/flash-ia-reels/gabarit/fonts/Inter-ExtraBold.otf"
F_SEMI = "/home/claude/flash-ia-reels/gabarit/fonts/Inter-SemiBold.otf"
f = lambda p, s: ImageFont.truetype(p, s)

def background(W, H, glow=(0.75, 0.12)):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=(18, 18, 24))
    for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=(18, 18, 24))
    g = Image.new("L", (W, H), 0)
    cx, cy = W * glow[0], H * glow[1]
    ImageDraw.Draw(g).ellipse([cx - 420, cy - 420, cx + 420, cy + 420], fill=80)
    g = g.filter(ImageFilter.GaussianBlur(190))
    im = Image.composite(Image.new("RGB", (W, H), YEL), im, g)
    random.seed(3)
    n = Image.effect_noise((W // 2, H // 2), 40).resize((W, H))
    return Image.blend(im, Image.merge("RGB", (n, n, n)), 0.03)

def bolt(d, cx, cy, s, fill):
    pts = [(0.15, -0.5), (-0.25, 0.08), (0.02, 0.08), (-0.12, 0.5), (0.3, -0.12), (0.03, -0.12), (0.2, -0.5)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in pts], fill=fill)

def badge(d, W, y=70):
    ft = f(F_TITLE, 40); txt = "FLASH IA"
    w = d.textlength(txt, font=ft); bw = w + 110; x0 = (W - bw) / 2
    d.rounded_rectangle([x0, y, x0 + bw, y + 76], radius=38, fill=YEL)
    bolt(d, x0 + 48, y + 38, 48, BG)
    d.text((x0 + 82, y + 12), txt, font=ft, fill=BG)

def rich_lines(d, x, y, lines, font, lh, W=None, center=False):
    """lines: list of list of (text, color). returns y after."""
    for segs in lines:
        tw = sum(d.textlength(t, font=font) for t, _ in segs)
        cx = (W - tw) / 2 if center else x
        for t, c in segs:
            d.text((cx, y), t, font=font, fill=c); cx += d.textlength(t, font=font)
        y += lh
    return y

def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def footer(d, W, H, n, total, src=None):
    fs = f(F_SEMI, 30)
    d.text((70, H - 90), "@flash.ia_actu", font=fs, fill=GREY)
    t = f"{n}/{total}"
    d.text((W - 70 - d.textlength(t, font=fs), H - 90), t, font=fs, fill=GREY)
    if src:
        w = d.textlength(src, font=fs); d.text(((W - w) / 2, H - 90), src, font=fs, fill=GREY)

