"""Rendu du Reel Flash IA n°011 (Instagram lance la protection du contenu contre les reposts et les copies IA) — 1080x1920, 30 fps, charte noir/jaune."""
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
VOICE_END = 33.44 + OFF
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

def card_x(d, x0, y, w, h, txt, size, ok):
    col = YEL if ok else RED
    d.rounded_rectangle([x0, y, x0 + w, y + h], radius=30, fill=DARK + (255,), outline=col + (255,), width=4)
    s = 44
    if ok:
        check(d, x0 + 32, y + h / 2 - s / 2, s, col + (255,))
    else:
        cross(d, x0 + 34, y + h / 2 - s / 2 + 2, s - 4, col + (255,))
    f2 = font(F_TITLE, size)
    assert d.textlength(txt, font=f2) < w - 130, txt
    d.text((x0 + 105, y + h / 2 - f2.getmetrics()[0] / 2 - 4), txt, font=f2, fill=WHITE + (255,))

def scene_hook(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 0, "QUELQU'UN", font(F_TITLE, 112), WHITE)
    text_center(d, TOP + 125, "VOLE TON", font(F_TITLE, 112), WHITE)
    text_center(d, TOP + 250, "REEL ?", font(F_TITLE, 112), YEL)
    out.append((L, 1.0, 0, 1.0, 0))  # titre visible dès la 1re image (couverture)
    s = stamp("ALERTE", 120, TOP + 410, t, 3.6 + O, rot=-5)
    if s: out.append(s)
    P = layer(); pd = ImageDraw.Draw(P)
    pill(pd, W / 2, TOP + 680, "INSTAGRAM · 17 NOV. 2026", font(F_BOLD, 36), DARK, YEL, pady=14)
    out.append(slide_in(P, t, 1.2 + O, 0.3, 20))
    return out

def scene_tool(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 0, "LE NOUVEL OUTIL", font(F_TITLE, 66), GREY)
    out.append(slide_in(L, t, 6.12 + O, 0.3, 50))
    P = layer(); pd = ImageDraw.Draw(P)
    text_center(pd, TOP + 90, "PROTECTION", font(F_TITLE, 104), YEL)
    text_center(pd, TOP + 205, "DU CONTENU", font(F_TITLE, 104), YEL)
    out.append(pop(P, t, 6.95 + O, 1.2))
    # radar scan
    R = layer(); rd = ImageDraw.Draw(R)
    cx, cy, r = W / 2, TOP + 470, 105
    for k in (1.0, 0.66, 0.33):
        rd.ellipse([cx - r * k, cy - r * k, cx + r * k, cy + r * k], outline=(70, 70, 82, 255), width=3)
    ang = (t * 3.2) % (2 * math.pi)
    rd.line([(cx, cy), (cx + r * math.cos(ang), cy + r * math.sin(ang))], fill=YEL + (255,), width=6)
    rd.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=YEL + (255,))
    fl = font(F_BOLD, 40)
    rd.text((cx + r + 30, cy - 26), "SCAN", font=fl, fill=WHITE + (255,))
    rd.text((cx + r + 30, cy + 20), "EN CONTINU", font=fl, fill=GREY + (255,))
    assert cx + r + 30 + rd.textlength("EN CONTINU", font=fl) < 960
    a_r = appear(t, 9.12 + O, 0.3) * (1 - appear(t, 11.3 + O, 0.2))
    out.append((R, a_r, 0, 1.0, 0))
    # notification
    N = layer(); nd = ImageDraw.Draw(N)
    y = TOP + 390
    nd.rounded_rectangle([110, y, W - 110, y + 200], radius=34, fill=(30, 30, 38, 255), outline=YEL + (255,), width=4)
    nd.rounded_rectangle([145, y + 45, 255, y + 155], radius=26, fill=YEL + (255,))
    bolt(nd, 200, y + 100, 80, BG + (255,))
    f1 = font(F_TITLE, 44); f2 = font(F_SEMI, 36)
    nd.text((290, y + 42), "TON REEL A ÉTÉ", font=f1, fill=WHITE + (255,))
    nd.text((290, y + 100), "republié par un autre compte", font=f2, fill=GREY + (255,))
    assert 290 + nd.textlength("republié par un autre compte", font=f2) < W - 130
    assert 290 + nd.textlength("TON REEL A ÉTÉ", font=f1) < W - 130
    out.append(slide_in(N, t, 11.44 + O, 0.3, -40))
    s = stamp("ALERTE", 64, TOP + 620, t, 13.04 + O, rot=-3)
    if s: out.append(s)
    return out

def option_card(d, y, title, sub, num):
    d.rounded_rectangle([110, y, W - 110, y + 190], radius=34, fill=DARK + (255,), outline=YEL + (255,), width=4)
    fn = font(F_TITLE, 80)
    d.text((150, y + 40), num, font=fn, fill=YEL + (255,))
    f1 = font(F_TITLE, 50); f2 = font(F_SEMI, 38)
    assert 260 + d.textlength(title, font=f1) < W - 130, title
    assert 260 + d.textlength(sub, font=f2) < W - 130, sub
    d.text((260, y + 38), title, font=f1, fill=WHITE + (255,))
    d.text((260, y + 112), sub, font=f2, fill=GREY + (255,))

def scene_choice(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 0, "T'AS LE CHOIX", font(F_TITLE, 96), WHITE)
    out.append(slide_in(L, t, 13.48 + O, 0.3, 50))
    A = layer(); ad = ImageDraw.Draw(A)
    option_card(ad, TOP + 170, "TU LA BLOQUES", "sur Instagram + Facebook", "1")
    out.append(slide_in(A, t, 14.56 + O, 0.25, 30))
    B = layer(); bd = ImageDraw.Draw(B)
    option_card(bd, TOP + 400, "« ORIGINAL DE »", "une étiquette qui renvoie vers toi", "2")
    out.append(slide_in(B, t, 17.12 + O, 0.25, 30))
    return out

def scene_ai(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 0, "ET LE PLUS FORT…", font(F_TITLE, 76), GREY)
    out.append(slide_in(L, t, 20.12 + O, 0.3, 50))
    P = layer(); pd = ImageDraw.Draw(P)
    pill(pd, W / 2, TOP + 160, "BIENTÔT · EN TEST", font(F_BOLD, 40), DARK, YEL, pady=14)
    out.append(slide_in(P, t, 21.0 + O, 0.3, 20))
    N = layer(); nd = ImageDraw.Draw(N)
    text_center(nd, TOP + 240, "VIDÉOS IA", font(F_TITLE, 150), YEL)
    out.append(pop(N, t, 22.64 + O, 1.25))
    # son identique / images changées
    S = layer(); sd = ImageDraw.Draw(S)
    y = TOP + 430
    cxs = [W / 2 - 215, W / 2 + 215]
    for cx in cxs:
        sd.rounded_rectangle([cx - 190, y, cx + 190, y + 150], radius=30, fill=DARK + (255,), outline=(70, 70, 82, 255), width=3)
    for i in range(13):
        h = 16 + 48 * abs(math.sin(i * 1.3 + 0.5))
        x = cxs[0] - 150 + i * 24
        sd.rounded_rectangle([x, y + 58 - h / 2, x + 12, y + 58 + h / 2], radius=6, fill=YEL + (255,))
    fs = font(F_BOLD, 32)
    for cx, txt in [(cxs[0], "TON SON"), (cxs[1], "AUTRES IMAGES")]:
        w = sd.textlength(txt, font=fs); assert w < 360, txt
        sd.text((cx - w / 2, y + 102), txt, font=fs, fill=WHITE + (255,))
    ix = cxs[1]
    sd.rounded_rectangle([ix - 60, y + 22, ix + 60, y + 92], radius=12, outline=WHITE + (255,), width=4)
    sd.polygon([(ix - 47, y + 84), (ix - 12, y + 48), (ix + 12, y + 72), (ix + 30, y + 56), (ix + 49, y + 84)], fill=GREY + (255,))
    sd.ellipse([ix + 22, y + 32, ix + 40, y + 50], fill=YEL + (255,))
    out.append(slide_in(S, t, 23.92 + O, 0.3, 30))
    s = stamp("DÉTECTÉ", 50, TOP + 600, t, 24.9 + O, rot=-3)
    if s: out.append(s)
    return out

def scene_tip(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 30, "TU REÇOIS", font(F_TITLE, 100), WHITE)
    text_center(d, TOP + 150, "LA NOTIF ?", font(F_TITLE, 100), YEL)
    out.append(slide_in(L, t, 25.72 + O, 0.3, 50))
    s = stamp("ACTIVE-LE", 110, TOP + 340, t, 27.48 + O, rot=-5)
    if s: out.append(s)
    return out

def scene_poll(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    t0 = 28.12 + O
    text_center(d, TOP + 10, "ET TOI ?", font(F_TITLE, 140), WHITE)
    out.append((L, appear(t, t0, 0.3), 0, 1.15 - 0.15 * ease_back((t - t0) / 0.35), 0))
    opts = [("ON M'A DÉJÀ VOLÉ", 28.76 + O, True), ("PAS ENCORE", 29.33 + O, False)]
    for i, (txt, ts, hl) in enumerate(opts):
        R = layer(); rd = ImageDraw.Draw(R)
        y = TOP + 220 + i * 180
        rd.rounded_rectangle([140, y, W - 140, y + 145], radius=40,
                             fill=(YEL if hl else DARK) + (255,), outline=(YEL + (255,)), width=4)
        f = font(F_TITLE, 58)
        w = rd.textlength(txt, font=f)
        assert w < W - 330, txt
        rd.text(((W - w) / 2, y + 37), txt, font=f, fill=(BG if hl else WHITE) + (255,))
        out.append(slide_in(R, t, ts))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 600, "Dis-le en commentaire", font(F_BOLD, 46), GREY)
    out.append((T, appear(t, 29.6 + O, 0.3), 0, 1.0, 0))
    return out

def scene_cta(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy = W / 2, TOP + 200
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=YEL + (255,))
    bolt(d, cx, cy, 210, BG + (255,))
    t0 = 30.03 + O
    out.append((L, appear(t, t0, 0.3), 0, 0.6 + 0.4 * ease_back((t - t0) / 0.45), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 420, "ABONNE-TOI", font(F_TITLE, 120), WHITE)
    text_center(td, TOP + 570, "@flash.ia_actu", font(F_BOLD, 64), YEL)
    text_center(td, TOP + 670, "L'actu IA & réseaux en 30 s", font(F_SEMI, 46), GREY)
    out.append(slide_in(T, t, t0 + 0.15, 0.35, 50))
    return out

SCENES = [  # (start, end, fn)
    (0.0, 6.1 + O, scene_hook),
    (6.1 + O, 13.46 + O, scene_tool),
    (13.46 + O, 20.1 + O, scene_choice),
    (20.1 + O, 25.7 + O, scene_ai),
    (25.7 + O, 28.1 + O, scene_tip),
    (28.1 + O, 30.0 + O, scene_poll),
    (30.0 + O, DUR + 1, scene_cta),
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
    s = "Source : Instagram · TechCrunch · 17 nov. 2026"
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
