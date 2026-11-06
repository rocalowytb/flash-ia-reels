"""Rendu du Reel Flash IA n°004 (Instagram Edits sur Mac) — 1080x1920, 30 fps, charte noir/jaune."""
import json, math, os, random, subprocess, sys
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BG = (11, 11, 15)
YEL = (255, 225, 77)
WHITE = (255, 255, 255)
GREY = (150, 150, 160)
DARK = (24, 24, 30)

F_TITLE = os.path.join(FONTS, "ArchivoBlack.ttf")
F_BOLD = os.path.join(FONTS, "Inter-ExtraBold.otf")
F_SEMI = os.path.join(FONTS, "Inter-SemiBold.otf")

_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3

def ease_back(x):
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def appear(t, t0, dur=0.3):
    return ease_out((t - t0) / dur)

# ---------- audio / timings ----------
OFF = 0.3  # la voix démarre à 0,3 s (mixage aligné)
words = [dict(w, start=w["start"] + OFF, end=w["end"] + OFF) for w in json.load(open("words.json"))["words"]
         if w["type"] == "word" and not w["text"].startswith("[") and w["text"] != ":"]
VOICE_END = 31.76 + OFF
DUR = VOICE_END + 1.2
NFRAMES = int(DUR * FPS)

# captions: groups of up to 3 words, break on punctuation
groups, cur = [], []
for w in words:
    if w["text"] == "?":
        if cur:
            cur[-1] = dict(cur[-1], text=cur[-1]["text"] + " ?", end=w["end"])
            groups.append(cur); cur = []
        continue
    cur.append(w)
    if len(cur) == 3 or w["text"][-1] in ".,…?":
        groups.append(cur); cur = []
if cur:
    groups.append(cur)

# ---------- static layers ----------
def make_bg():
    bg = Image.new("RGB", (W, H), BG)
    # subtle grid
    d = ImageDraw.Draw(bg)
    for x in range(0, W, 90):
        d.line([(x, 0), (x, H)], fill=(18, 18, 24), width=1)
    for y in range(0, H, 90):
        d.line([(0, y), (W, y)], fill=(18, 18, 24), width=1)
    # vignette
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-300, -200, W + 300, H + 200], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", (W, H), (4, 4, 6))
    return Image.composite(bg, dark, vig)

def make_glow(size=1400):
    g = Image.new("L", (size, size), 0)
    ImageDraw.Draw(g).ellipse([size * 0.25, size * 0.25, size * 0.75, size * 0.75], fill=70)
    return g.filter(ImageFilter.GaussianBlur(170))

random.seed(7)
def make_grain():
    g = Image.effect_noise((W // 2, H // 2), 40).resize((W, H))
    return g

BG_IMG = make_bg()
GLOW = make_glow()
GRAINS = [make_grain() for _ in range(4)]
YEL_LAYER = Image.new("RGB", (W, H), YEL)

def bolt(d, cx, cy, s, fill):
    pts = [(0.15, -0.5), (-0.25, 0.08), (0.02, 0.08), (-0.12, 0.5), (0.3, -0.12), (0.03, -0.12), (0.2, -0.5)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in pts], fill=fill)

# ---------- drawing helpers on RGBA overlay ----------
def text_center(d, y, txt, f, fill, alpha=255):
    w = d.textlength(txt, font=f)
    d.text(((W - w) / 2, y), txt, font=f, fill=fill + (alpha,))
    return w

def pill(d, cx, cy, txt, f, bg, fg, alpha=255, padx=34, pady=18, r=None):
    w = d.textlength(txt, font=f)
    asc, desc = f.getmetrics()
    h = asc + desc
    box = [cx - w / 2 - padx, cy - h / 2 - pady, cx + w / 2 + padx, cy + h / 2 + pady]
    d.rounded_rectangle(box, radius=r if r is not None else (h / 2 + pady), fill=bg + (alpha,))
    d.text((cx - w / 2, cy - h / 2), txt, font=f, fill=fg + (alpha,))
    return box

def check(d, x, y, s, fill):
    d.line([(x, y + s * 0.5), (x + s * 0.38, y + s * 0.85), (x + s, y + s * 0.1)], fill=fill, width=int(s * 0.18), joint="curve")

def cross(d, x, y, s, fill):
    wd = int(s * 0.18)
    d.line([(x, y), (x + s, y + s)], fill=fill, width=wd)
    d.line([(x + s, y), (x, y + s)], fill=fill, width=wd)

def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def paste_anim(base, lay, a, dy=0, scale=1.0, angle=0):
    """compose overlay `lay` with global alpha a, vertical offset dy, scale around center"""
    if a <= 0:
        return
    if scale != 1.0 or angle:
        lay = lay.rotate(angle, resample=Image.BICUBIC, center=(W / 2, H / 2)) if angle else lay
        if scale != 1.0:
            sw, sh = int(W * scale), int(H * scale)
            lay = lay.resize((sw, sh), Image.BICUBIC)
            canvas = layer()
            canvas.paste(lay, ((W - sw) // 2, (H - sh) // 2))
            lay = canvas
    if a < 1:
        r, g, b, al = lay.split()
        al = al.point(lambda v: int(v * a))
        lay = Image.merge("RGBA", (r, g, b, al))
    base.alpha_composite(lay, (0, int(dy)))

# ---------- scenes ----------
TOP = 430  # top of the content zone (rien sous y 1130)

def stamp(txt, size, cy, t, t0, rot=-4, cx=W / 2):
    S = layer(); sd = ImageDraw.Draw(S)
    fs = font(F_TITLE, size)
    w = sd.textlength(txt, font=fs)
    asc, desc = fs.getmetrics()
    x0 = cx - w / 2 - 40
    sd.rounded_rectangle([x0, cy, x0 + w + 80, cy + asc + desc + 30], radius=18, fill=YEL + (255,))
    sd.text((cx - w / 2, cy + 12), txt, font=fs, fill=BG + (255,))
    if t < t0:
        return None
    return (S, min(1, (t - t0) / 0.12), 0, 1.6 - 0.6 * ease_back((t - t0) / 0.35), rot)

def laptop(d, x0, y0, x1, y1):
    """un Mac stylisé : écran + base"""
    d.rounded_rectangle([x0, y0, x1, y1], radius=26, fill=(20, 20, 26, 255), outline=(70, 70, 82, 255), width=4)
    d.rounded_rectangle([x0 - 50, y1 + 6, x1 + 50, y1 + 30], radius=12, fill=(55, 55, 66, 255))

def timeline(d, x0, y0, x1, t, t_tracks):
    """timeline multi-pistes ; pistes qui apparaissent à t_tracks"""
    cols = [YEL, (120, 170, 255), (255, 140, 120)]
    for i in range(3):
        k = ease_out((t - t_tracks - i * 0.18) / 0.35)
        if k <= 0: continue
        yy = y0 + i * 52
        d.rounded_rectangle([x0, yy, x1, yy + 40], radius=8, fill=(30, 30, 38, 255))
        segs = [(0.0, 0.32), (0.36, 0.7), (0.74, 1.0)] if i == 0 else ([(0.1, 0.55), (0.6, 0.9)] if i == 1 else [(0.0, 0.95)])
        for a, b in segs:
            bx = x0 + (x1 - x0) * a; ex = x0 + (x1 - x0) * min(b, a + (b - a) * k)
            if ex - bx > 6:
                d.rounded_rectangle([bx + 3, yy + 5, ex - 3, yy + 35], radius=6, fill=cols[i] + (255,))
        if i == 2:  # forme d'onde audio
            for j in range(0, int((x1 - x0) * 0.95 * k), 9):
                h = 6 + 11 * abs(math.sin(j * 0.13) * math.cos(j * 0.041))
                d.line([(x0 + j + 6, yy + 20 - h), (x0 + j + 6, yy + 20 + h)], fill=(120, 60, 50, 255), width=4)
    # tête de lecture
    if t > t_tracks:
        px = x0 + (x1 - x0) * (((t - t_tracks) * 0.18) % 1)
        d.line([(px, y0 - 14), (px, y0 + 150)], fill=WHITE + (255,), width=3)

def scene_hook(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    f = font(F_TITLE, 94)
    text_center(d, TOP + 40, "INSTAGRAM SORT", f, WHITE)
    w1 = d.textlength("EDITS ", font=f); w2 = d.textlength("SUR MAC", font=f)
    x = (W - w1 - w2) / 2
    d.text((x, TOP + 160), "EDITS ", font=f, fill=YEL + (255,))
    d.text((x + w1, TOP + 160), "SUR MAC", font=f, fill=WHITE + (255,))
    out.append((L, 1.0, 0, 1.0, 0))  # titre visible dès la 1re image (couverture)
    s = stamp("GRATUIT", 150, TOP + 335, t, 2.75)
    if s: out.append(s)
    C = layer(); cd = ImageDraw.Draw(C)
    pill(cd, W / 2, TOP + 640, "LE RIVAL DE CAPCUT · 5 NOVEMBRE", font(F_BOLD, 40), DARK, YEL)
    out.append((C, appear(t, 4.3, 0.3), (1 - appear(t, 4.3, 0.3)) * 30, 1.0, 0))
    return out

def scene_pro(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "UN VRAI LOGICIEL", font(F_TITLE, 80), WHITE)
    text_center(d, TOP + 105, "DE MONTAGE", font(F_TITLE, 80), YEL)
    out.append((L, appear(t, 5.9, 0.3), (1 - appear(t, 5.9, 0.3)) * 50, 1.0, 0))
    M = layer(); md = ImageDraw.Draw(M)
    x0, y0, x1, y1 = 150, TOP + 205, W - 150, TOP + 560
    laptop(md, x0, y0, x1, y1)
    # aperçu vidéo + roue chromatique
    md.rounded_rectangle([x0 + 30, y0 + 25, x0 + 420, y0 + 165], radius=12, fill=(36, 36, 46, 255))
    bolt(md, x0 + 225, y0 + 95, 90, YEL + (255,))
    k = ease_out((t - 9.06) / 0.4)
    if k > 0:
        cx, cy, r = x1 - 120, y0 + 95, 66 * (0.6 + 0.4 * k)
        for a in range(0, 360, 30):
            colr = [(255, 90, 90), (255, 170, 60), (255, 225, 77), (120, 220, 120), (90, 200, 255), (150, 120, 255)][(a // 60) % 6]
            md.pieslice([cx - r, cy - r, cx + r, cy + r], a, a + 30, fill=colr + (int(255 * k),))
        md.ellipse([cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35], fill=(20, 20, 26, 255))
    timeline(md, x0 + 30, y0 + 190, x1 - 30, t, 8.33)
    out.append((M, appear(t, 6.4, 0.3), (1 - appear(t, 6.4, 0.3)) * 40, 1.0, 0))
    B = layer(); bd = ImageDraw.Draw(B)
    pill(bd, 250, TOP + 650, "EXPORT 4K", font(F_TITLE, 40), YEL, BG, r=18)
    out.append((B, appear(t, 10.6, 0.2), 0, 1.0, 0))
    s = stamp("SANS FILIGRANE", 40, TOP + 611, t, 11.66, rot=-3, cx=720)
    if s:
        S, a, dy, sc, rot = s
        out.append((S, a, dy, 1.0 + 0.25 * (1 - ease_back((t - 11.66) / 0.35)), 0))
    return out

def scene_gratuit(t):
    out = []
    N = layer(); nd = ImageDraw.Draw(N)
    text_center(nd, TOP + 20, "0 €", font(F_TITLE, 260), YEL)
    out.append((N, appear(t, 12.4, 0.2), 0, 1.25 - 0.25 * ease_back((t - 12.4) / 0.35), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 330, "PUBLICATION DIRECTE", font(F_TITLE, 66), WHITE)
    text_center(td, TOP + 420, "sur Instagram", font(F_BOLD, 54), GREY)
    out.append((T, appear(t, 13.1, 0.3), (1 - appear(t, 13.1, 0.3)) * 40, 1.0, 0))
    P = layer(); pd = ImageDraw.Draw(P)
    pill(pd, W / 2, TOP + 600, "MÊME EN TRIAL REEL", font(F_TITLE, 56), YEL, BG, r=22)
    out.append((P, appear(t, 14.9, 0.2), 0, 1.3 - 0.3 * ease_back((t - 14.9) / 0.3), 0))
    return out

def scene_agent(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "LE PLUS FOU ?", font(F_TITLE, 76), GREY)
    out.append((L, appear(t, 15.6, 0.3), (1 - appear(t, 15.6, 0.3)) * 50, 1.0, 0))
    A = layer(); ad = ImageDraw.Draw(A)
    # carte agent IA -> carte Edits
    ad.rounded_rectangle([110, TOP + 130, 470, TOP + 330], radius=30, fill=YEL + (255,))
    w = ad.textlength("TON AGENT", font=font(F_TITLE, 44)); ad.text((290 - w / 2, TOP + 170), "TON AGENT", font=font(F_TITLE, 44), fill=BG + (255,))
    w = ad.textlength("IA", font=font(F_TITLE, 70)); ad.text((290 - w / 2, TOP + 230), "IA", font=font(F_TITLE, 70), fill=BG + (255,))
    ad.rounded_rectangle([610, TOP + 130, 970, TOP + 330], radius=30, fill=(20, 20, 26, 255), outline=(70, 70, 82, 255), width=3)
    w = ad.textlength("EDITS", font=font(F_TITLE, 70)); ad.text((790 - w / 2, TOP + 195), "EDITS", font=font(F_TITLE, 70), fill=WHITE + (255,))
    out.append((A, appear(t, 16.65, 0.3), (1 - appear(t, 16.65, 0.3)) * 40, 1.0, 0))
    # flèche animée
    if t > 17.2:
        R = layer(); rd = ImageDraw.Draw(R)
        k = ease_out((t - 17.2) / 0.4)
        xe = 485 + (595 - 485) * k
        rd.line([(485, TOP + 230), (xe, TOP + 230)], fill=YEL + (255,), width=10)
        rd.polygon([(xe + 4, TOP + 230), (xe - 22, TOP + 212), (xe - 22, TOP + 248)], fill=YEL + (255,))
        out.append((R, 1.0, 0, 1.0, 0))
    for i, (num, txt, t0) in enumerate([("1", "L'IA fait le 1er montage", 18.5), ("2", "Toi, tu peaufines", 19.9)]):
        S = layer(); sd = ImageDraw.Draw(S)
        y = TOP + 400 + i * 150
        sd.rounded_rectangle([110, y, W - 110, y + 120], radius=30, fill=(20, 20, 26, 255), outline=(60, 60, 70, 255), width=2)
        sd.ellipse([140, y + 22, 216, y + 98], fill=YEL + (255,))
        w = sd.textlength(num, font=font(F_TITLE, 48)); sd.text((178 - w / 2, y + 28), num, font=font(F_TITLE, 48), fill=BG + (255,))
        sd.text((250, y + 32), txt, font=font(F_BOLD, 50), fill=WHITE + (255,))
        out.append((S, appear(t, t0, 0.3), (1 - appear(t, t0, 0.3)) * 40, 1.0, 0))
    return out

def scene_attention(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "ATTENTION…", font(F_TITLE, 80), GREY)
    out.append((L, appear(t, 21.2, 0.3), (1 - appear(t, 21.2, 0.3)) * 50, 1.0, 0))
    rows = [("MAC M1 MINIMUM", True, 22.6), ("WINDOWS", False, 25.0)]
    for i, (txt, ok, t0) in enumerate(rows):
        R = layer(); rd = ImageDraw.Draw(R)
        y = TOP + 170 + i * 220
        rd.rounded_rectangle([110, y, W - 110, y + 170], radius=40, fill=(20, 20, 26, 255),
                             outline=(YEL if ok else (90, 90, 100)) + (255,), width=4)
        if ok: check(rd, 160, y + 50, 70, YEL + (255,))
        else: cross(rd, 165, y + 52, 64, (255, 95, 95, 255))
        f = font(F_TITLE, 56 if ok else 64)
        rd.text((275, y + 50), txt, font=f, fill=(WHITE if ok else GREY) + (255,))
        if not ok:
            tw = rd.textlength(txt, font=f)
            rd.line([(270, y + 92), (280 + tw, y + 92)], fill=(255, 95, 95, 255), width=8)
            rd.text((280 + tw + 30, y + 64), "pas encore", font=font(F_BOLD, 42), fill=GREY + (255,))
        out.append((R, appear(t, t0, 0.3), (1 - appear(t, t0, 0.3)) * 40, 1.0, 0))
    return out

def scene_poll(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 20, "ET TOI ?", font(F_TITLE, 150), WHITE)
    out.append((L, appear(t, 25.75, 0.3), 0, 1.15 - 0.15 * ease_back((t - 25.75) / 0.35), 0))
    opts = [("SUR TÉLÉPHONE", 27.0, False), ("SUR ORDI", 28.1, True)]
    for i, (txt, t0, hl) in enumerate(opts):
        R = layer(); rd = ImageDraw.Draw(R)
        y = TOP + 280 + i * 190
        rd.rounded_rectangle([140, y, W - 140, y + 150], radius=40,
                             fill=(YEL if hl else DARK) + (255,), outline=(YEL + (255,)), width=4)
        f = font(F_TITLE, 64)
        w = rd.textlength(txt, font=f)
        rd.text(((W - w) / 2, y + 36), txt, font=f, fill=(BG if hl else WHITE) + (255,))
        out.append((R, appear(t, t0, 0.3), (1 - appear(t, t0, 0.3)) * 40, 1.0, 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 660, "Dis-le en commentaire", font(F_BOLD, 50), GREY)
    out.append((T, appear(t, 28.2, 0.3), 0, 1.0, 0))
    return out

def scene_cta(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy = W / 2, TOP + 200
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=YEL + (255,))
    bolt(d, cx, cy, 210, BG + (255,))
    out.append((L, appear(t, 28.8, 0.3), 0, 0.6 + 0.4 * ease_back((t - 28.8) / 0.45), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 420, "ABONNE-TOI", font(F_TITLE, 120), WHITE)
    text_center(td, TOP + 570, "@flash.ia_reseau", font(F_BOLD, 64), YEL)
    text_center(td, TOP + 670, "L'actu IA & réseaux en 30 s", font(F_SEMI, 46), GREY)
    out.append((T, appear(t, 29.0, 0.35), (1 - appear(t, 29.0, 0.35)) * 50, 1.0, 0))
    return out

SCENES = [  # (start, end, fn)
    (0.0, 5.85, scene_hook),
    (5.85, 12.26, scene_pro),
    (12.26, 15.52, scene_gratuit),
    (15.52, 21.08, scene_agent),
    (21.08, 25.64, scene_attention),
    (25.64, 28.7, scene_poll),
    (28.7, DUR + 1, scene_cta),
]

# ---------- static chrome ----------
def chrome(t):
    L = layer(); d = ImageDraw.Draw(L)
    # progress bar
    d.rectangle([0, 0, W * min(1, t / DUR), 10], fill=YEL + (255,))
    # badge
    f = font(F_TITLE, 44)
    txt = "FLASH IA"
    w = d.textlength(txt, font=f)
    bw = w + 120
    x0, y0 = (W - bw) / 2, 230
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + 84], radius=42, fill=YEL + (255,))
    bolt(d, x0 + 52, y0 + 42, 52, BG + (255,))
    d.text((x0 + 88, y0 + 14), txt, font=f, fill=BG + (255,))
    # source
    fs = font(F_SEMI, 32)
    s = "Source : Instagram (5 nov.) · 9to5Mac · iClarified"
    ws = d.textlength(s, font=fs)
    d.text(((W - ws) / 2, 1400), s, font=fs, fill=GREY + (255,))
    return L

def captions(t):
    L = layer(); d = ImageDraw.Draw(L)
    g = None
    for gr in groups:
        if gr[0]["start"] - 0.05 <= t <= gr[-1]["end"] + 0.15:
            g = gr
    if g is None:
        return L
    f = font(F_BOLD, 74)
    toks = [w["text"] for w in g]
    widths = [d.textlength(x, font=f) for x in toks]
    sp = d.textlength(" ", font=f)
    total = sum(widths) + sp * (len(toks) - 1)
    lines = [list(range(len(toks)))]
    if total > 800:
        lines = [list(range(len(toks) - 1)), [len(toks) - 1]]
    y = 1190 if len(lines) == 1 else 1160
    # backdrop
    for line in lines:
        lw = sum(widths[i] for i in line) + sp * (len(line) - 1)
        x = (W - lw) / 2
        for i in line:
            w = g[i]
            active = w["start"] - 0.03 <= t <= w["end"] + 0.06 or (t > w["end"] and i == len(g) - 1)
            spoken = t >= w["start"] - 0.03
            col = YEL if active else (WHITE if spoken else (110, 110, 120))
            # soft shadow
            d.text((x + 3, y + 5), toks[i], font=f, fill=(0, 0, 0, 200))
            d.text((x, y), toks[i], font=f, fill=col + (255,))
            x += widths[i] + sp
        y += 92
    return L

def render_frame(n):
    t = n / FPS
    frame = BG_IMG.copy()
    # drifting glow
    ox = int(W * 0.55 + 120 * math.sin(t * 0.35)) - 700
    oy = int(H * 0.18 + 90 * math.cos(t * 0.27)) - 700
    mask = Image.new("L", (W, H), 0)
    mask.paste(GLOW, (ox, oy))
    frame = Image.composite(YEL_LAYER, frame, mask)
    frame = frame.convert("RGBA")
    for (s, e, fn) in SCENES:
        if s - 0.01 <= t < e:
            fade = 1.0 if t < e - 0.15 else max(0.0, (e - t) / 0.15)
            for lay, a, dy, sc, ang in fn(t):
                paste_anim(frame, lay, a * fade, dy - (1 - fade) * 40, sc, ang)
    frame.alpha_composite(chrome(t))
    frame.alpha_composite(captions(t))
    rgb = frame.convert("RGB")
    grain = GRAINS[n % 4]
    rgb = Image.blend(rgb, Image.merge("RGB", (grain, grain, grain)), 0.035)
    return rgb

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for ts in [float(x) for x in sys.argv[2:]]:
            render_frame(int(ts * FPS)).save(f"preview_{ts:05.2f}.png")
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "17", "-pix_fmt", "yuv420p", "video_only.mp4"], stdin=subprocess.PIPE)
    for n in range(NFRAMES):
        p.stdin.write(render_frame(n).tobytes())
        if n % 60 == 0:
            print(n, "/", NFRAMES, flush=True)
    p.stdin.close(); p.wait()
    print("done")
