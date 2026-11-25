"""Rendu du Reel Flash IA n°014 (Jensen Huang de retour à la tête de Nvidia, 11 jours après sa démission) — 1080x1920, 30 fps, charte noir/jaune."""
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
words = []
for w in json.load(open("words.json"))["words"]:
    if w["type"] != "word" or w["text"].startswith("["):
        continue
    core = w["text"].replace("«", "").replace("»", "").strip()
    if core in ("", ":"):
        continue
    if core in (".", ","):  # ponctuation après un guillemet fermant
        if words: words[-1]["text"] += core
        continue
    words.append(dict(w, text=core, start=w["start"] + OFF, end=w["end"] + OFF))
VOICE_END = 29.36 + OFF
DUR = VOICE_END + 1.4
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
O = OFF
RED = (255, 95, 95)
GREEN = (90, 220, 130)

def stamp(txt, size, cy, t, t0, rot=-4, cx=W / 2):
    S = layer(); sd = ImageDraw.Draw(S)
    fs = font(F_TITLE, size)
    w = sd.textlength(txt, font=fs)
    assert w + 80 < W - 60, txt
    asc, desc = fs.getmetrics()
    x0 = cx - w / 2 - 40
    sd.rounded_rectangle([x0, cy, x0 + w + 80, cy + asc + desc + 30], radius=18, fill=YEL + (255,))
    sd.text((cx - w / 2, cy + 12), txt, font=fs, fill=BG + (255,))
    if t < t0:
        return None
    return (S, min(1, (t - t0) / 0.12), 0, 1.6 - 0.6 * ease_back((t - t0) / 0.35), rot)

def slide_in(L, t, t0, d=0.3, off=40):
    return (L, appear(t, t0, d), (1 - appear(t, t0, d)) * off, 1.0, 0)

def pop(L, t, t0, s0=1.2):
    return (L, appear(t, t0, 0.2), 0, s0 - (s0 - 1) * ease_back((t - t0) / 0.3), 0)

def chip(d, cx, cy, s, glow=YEL):
    """puce stylisée : carré noir, bord jaune, broches"""
    h = s / 2
    pin_len, n = s * 0.16, 6
    for i in range(n):
        p = -h + s * (i + 0.5) / n
        for (x1, y1, x2, y2) in [(cx + p, cy - h - pin_len, cx + p, cy - h), (cx + p, cy + h, cx + p, cy + h + pin_len),
                                 (cx - h - pin_len, cy + p, cx - h, cy + p), (cx + h, cy + p, cx + h + pin_len, cy + p)]:
            d.line([(x1, y1), (x2, y2)], fill=GREY + (255,), width=8)
    d.rounded_rectangle([cx - h, cy - h, cx + h, cy + h], radius=26, fill=DARK + (255,), outline=glow + (255,), width=6)
    d.rounded_rectangle([cx - h * 0.55, cy - h * 0.55, cx + h * 0.55, cy + h * 0.55], radius=14, fill=(34, 34, 42, 255))
    bolt(d, cx, cy, s * 0.5, glow + (255,))

def scene_hook(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 0, "LE PATRON", font(F_TITLE, 104), WHITE)
    text_center(d, TOP + 120, "DE NVIDIA", font(F_TITLE, 104), YEL)
    text_center(d, TOP + 240, "A DÉMISSIONNÉ…", font(F_TITLE, 84), WHITE)
    out.append((L, 1.0, 0, 1.0, 0))  # titre visible dès la 1re image (couverture)
    P = layer(); pd = ImageDraw.Draw(P)
    pill(pd, W / 2, TOP + 400, "IL Y A 11 JOURS", font(F_BOLD, 40), DARK, YEL, pady=14)
    out.append((P, 1.0 - appear(t, 4.80 + O, 0.12), 0, 1.0, 0))  # s'efface quand le tampon tombe
    s = stamp("DE RETOUR", 130, TOP + 490, t, 4.86 + O, rot=-5)
    if s: out.append(s)
    return out

def scene_huang(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 0, "JENSEN", font(F_TITLE, 110), WHITE)
    text_center(d, TOP + 120, "HUANG", font(F_TITLE, 110), YEL)
    out.append(slide_in(L, t, 5.72 + O, 0.3, 40))
    C = layer(); cd = ImageDraw.Draw(C)
    chip(cd, W / 2, TOP + 400, 190)
    out.append(pop(C, t, 7.40 + O, 1.3))
    T = layer(); td = ImageDraw.Draw(T)
    fs = font(F_BOLD, 46)
    a, b = "les puces qui font tourner ", "ChatGPT"
    fb = font(F_TITLE, 50)
    wa, wb = td.textlength(a, font=fs), td.textlength(b, font=fb)
    assert wa + wb < 960
    x = (W - wa - wb) / 2
    td.text((x, TOP + 590), a, font=fs, fill=GREY + (255,))
    td.text((x + wa, TOP + 584), b, font=fb, fill=WHITE + (255,))
    out.append(slide_in(T, t, 8.00 + O, 0.25, 20))
    return out

def scene_vote(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 0, "LUNDI 23 NOV.", font(F_TITLE, 90), WHITE)
    out.append(slide_in(L, t, 9.16 + O, 0.3, 40))
    # carte vote du conseil
    V = layer(); vd = ImageDraw.Draw(V)
    y = TOP + 140
    vd.rounded_rectangle([110, y, W - 110, y + 230], radius=34, fill=(30, 30, 38, 255), outline=(70, 70, 82, 255), width=3)
    vd.text((160, y + 30), "Vote du conseil d'administration", font=font(F_SEMI, 36), fill=GREY + (255,))
    out.append(slide_in(V, t, 9.84 + O, 0.3, 30))
    n = 10
    for i in range(n):
        ts = 10.28 + O + i * 0.07
        if t >= ts:
            K = layer(); kd = ImageDraw.Draw(K)
            cx = 160 + i * 80
            kd.rounded_rectangle([cx, y + 100, cx + 62, y + 162], radius=14, fill=YEL + (255,))
            check(kd, cx + 12, y + 112, 38, BG + (255,))
            out.append(slide_in(K, t, ts, 0.15, 14))
    U = layer(); ud = ImageDraw.Draw(U)
    ud.text((160, y + 172), "UNANIME", font=font(F_TITLE, 40), fill=YEL + (255,))
    out.append(slide_in(U, t, 11.28 + O, 0.2, 10))
    # citation Trump
    Q = layer(); qd = ImageDraw.Draw(Q)
    y2 = TOP + 420
    qd.rounded_rectangle([110, y2, W - 110, y2 + 250], radius=34, fill=DARK + (255,), outline=YEL + (255,), width=4)
    qd.text((150, y2 + 4), "“", font=font(F_TITLE, 120), fill=YEL + (255,))
    fq = font(F_TITLE, 52)
    for k, line in enumerate(["C'EST MOI QUI", "AI FAIT LE DEAL"]):
        assert qd.textlength(line, font=fq) < W - 360, line
        qd.text((250, y2 + 40 + k * 70), line, font=fq, fill=WHITE + (255,))
    qd.text((250, y2 + 186), "Donald Trump, sur CNBC", font=font(F_SEMI, 34), fill=GREY + (255,))
    out.append(slide_in(Q, t, 12.24 + O, 0.3, 30))
    return out

def scene_stock(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 0, "L'ACTION NVIDIA", font(F_TITLE, 76), WHITE)
    out.append(slide_in(L, t, 14.85 + O, 0.3, 40))
    # courbe qui grimpe
    t0 = 15.6 + O
    prog = ease_out((t - t0) / 0.9)
    if prog > 0:
        G = layer(); gd = ImageDraw.Draw(G)
        x0, x1, yb = 150, W - 150, TOP + 520
        pts = [(0, 0.00), (0.12, 0.04), (0.24, -0.02), (0.36, 0.03), (0.48, 0.01), (0.58, 0.05), (0.66, 0.30), (0.76, 0.62), (0.86, 0.82), (1.0, 1.0)]
        P = [(x0 + (x1 - x0) * px, yb - 190 * py) for px, py in pts]
        gd.line([(x0, yb + 20), (x1, yb + 20)], fill=(60, 60, 70, 255), width=3)
        n = max(2, int(len(P) * prog + 1))
        seg = P[:n]
        # dernier point interpolé
        f = len(P) * prog - (n - 1)
        if n < len(P) and f > 0:
            a, b = P[n - 1], P[n]
            seg = seg + [(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)]
        gd.line(seg, fill=GREEN + (255,), width=12, joint="curve")
        ex, ey = seg[-1]
        gd.ellipse([ex - 16, ey - 16, ex + 16, ey + 16], fill=GREEN + (255,))
        out.append((G, 1.0, 0, 1.0, 0))
    B = layer(); bd = ImageDraw.Draw(B)
    text_center(bd, TOP + 130, "+30 %", font(F_TITLE, 170), YEL)
    out.append(pop(B, t, 16.40 + O, 1.1))
    s = stamp("EN UN JOUR", 70, TOP + 575, t, 17.12 + O, rot=-4)
    if s: out.append(s)
    return out

def scene_enquete(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 0, "SAUF QUE…", font(F_TITLE, 90), GREY)
    out.append(slide_in(L, t, 18.00 + O, 0.3, 40))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 120, "LES ENQUÊTES", font(F_TITLE, 96), WHITE)
    text_center(td, TOP + 230, "CONTINUENT", font(F_TITLE, 96), YEL)
    out.append(slide_in(T, t, 18.96 + O, 0.3, 30))
    # carte calendrier
    C = layer(); cd = ImageDraw.Draw(C)
    y = TOP + 400
    cd.rounded_rectangle([150, y, W - 150, y + 210], radius=34, fill=DARK + (255,), outline=YEL + (255,), width=4)
    # mini calendrier
    cd.rounded_rectangle([190, y + 35, 330, y + 175], radius=18, fill=WHITE + (255,))
    cd.rounded_rectangle([190, y + 35, 330, y + 80], radius=18, fill=RED + (255,))
    cd.rectangle([190, y + 60, 330, y + 80], fill=RED + (255,))
    fm = font(F_BOLD, 28)
    wm = cd.textlength("DÉC.", font=fm)
    cd.text((260 - wm / 2, y + 42), "DÉC.", font=fm, fill=WHITE + (255,))
    fd = font(F_TITLE, 64)
    wd = cd.textlength("3", font=fd)
    cd.text((260 - wd / 2, y + 80), "3", font=fd, fill=BG + (255,))
    f1 = font(F_TITLE, 46); f2 = font(F_SEMI, 34)
    assert 370 + cd.textlength("AUDITION", font=f1) < W - 170
    cd.text((370, y + 48), "AUDITION", font=f1, fill=WHITE + (255,))
    cd.text((370, y + 116), "au Sénat américain", font=f2, fill=GREY + (255,))
    out.append(slide_in(C, t, 20.64 + O, 0.3, 30))
    return out

def scene_poll(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    t0 = 23.22 + O
    text_center(d, TOP + 10, "ET TOI ?", font(F_TITLE, 140), WHITE)
    out.append((L, appear(t, t0, 0.3), 0, 1.15 - 0.15 * ease_back((t - t0) / 0.35), 0))
    opts = [("RETOUR MÉRITÉ", 24.36 + O, True), ("PAS DU TOUT", 25.28 + O, False)]
    for i, (txt, ts, hl) in enumerate(opts):
        R = layer(); rd = ImageDraw.Draw(R)
        y = TOP + 220 + i * 180
        rd.rounded_rectangle([140, y, W - 140, y + 145], radius=40,
                             fill=(YEL if hl else DARK) + (255,), outline=(YEL + (255,)), width=4)
        f = font(F_TITLE, 54)
        w = rd.textlength(txt, font=f)
        assert w < W - 330, txt
        rd.text(((W - w) / 2, y + 40), txt, font=f, fill=(BG if hl else WHITE) + (255,))
        out.append(slide_in(R, t, ts))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 600, "Dis-le en commentaire", font(F_BOLD, 46), GREY)
    out.append((T, appear(t, 25.4 + O, 0.3), 0, 1.0, 0))
    return out

def scene_cta(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy = W / 2, TOP + 200
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=YEL + (255,))
    bolt(d, cx, cy, 210, BG + (255,))
    t0 = 26.10 + O
    out.append((L, appear(t, t0, 0.3), 0, 0.6 + 0.4 * ease_back((t - t0) / 0.45), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 420, "ABONNE-TOI", font(F_TITLE, 120), WHITE)
    text_center(td, TOP + 570, "@flash.ia_actu", font(F_BOLD, 64), YEL)
    text_center(td, TOP + 670, "L'actu IA & réseaux en 30 s", font(F_SEMI, 46), GREY)
    out.append(slide_in(T, t, t0 + 0.15, 0.35, 50))
    return out

SCENES = [  # (start, end, fn)
    (0.0, 5.70 + O, scene_hook),
    (5.70 + O, 9.14 + O, scene_huang),
    (9.14 + O, 14.83 + O, scene_vote),
    (14.83 + O, 17.98 + O, scene_stock),
    (17.98 + O, 23.18 + O, scene_enquete),
    (23.18 + O, 26.08 + O, scene_poll),
    (26.08 + O, DUR + 1, scene_cta),
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
    s = "Source : Nvidia · CNBC · 23-24 nov. 2026"
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
