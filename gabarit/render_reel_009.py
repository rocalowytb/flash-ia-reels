"""Rendu du Reel Flash IA n°009 (United interdit les agents IA de réservation) — 1080x1920, 30 fps, charte noir/jaune."""
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
         if w["type"] == "word" and not w["text"].startswith("[") and w["text"] not in (":", "«", "»")]
VOICE_END = 31.6 + OFF
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
    col = YEL if ok else (255, 95, 95)
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
    text_center(d, TOP + 0, "TON IA", font(F_TITLE, 104), WHITE)
    text_center(d, TOP + 120, "RÉSERVE", font(F_TITLE, 104), WHITE)
    text_center(d, TOP + 240, "TON VOL ?", font(F_TITLE, 104), YEL)
    out.append((L, 1.0, 0, 1.0, 0))  # titre visible dès la 1re image (couverture)
    s = stamp("INTERDIT", 120, TOP + 385, t, 3.92 + O, rot=-5)
    if s: out.append(s)
    P = layer(); pd = ImageDraw.Draw(P)
    pill(pd, W / 2, TOP + 680, "UNITED AIRLINES · 12 NOV. 2026", font(F_BOLD, 36), DARK, YEL, pady=14)
    out.append(slide_in(P, t, 1.2 + O, 0.3, 20))
    return out

def scene_where(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "AGENTS IA BLOQUÉS", font(F_TITLE, 76), WHITE)
    out.append(slide_in(L, t, 6.1 + O, 0.3, 50))
    for i, (txt, t0) in enumerate([("SUR LE SITE", 7.85), ("SUR L'APPLI", 8.5), ("VIA LES AGENCES", 9.8)]):
        C = layer(); cd = ImageDraw.Draw(C)
        card_x(cd, 120, TOP + 150 + i * 160, W - 240, 125, txt, 50, False)
        out.append(slide_in(C, t, t0 + O, 0.25, 30))
    S = layer(); sd = ImageDraw.Draw(S)
    text_center(sd, TOP + 640, "même les sites de voyage en ligne", font(F_SEMI, 38), GREY)
    out.append(slide_in(S, t, 10.1 + O, 0.25, 10))
    return out

def scene_pay(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "TON ASSISTANT IA", font(F_TITLE, 72), GREY)
    out.append(slide_in(L, t, 10.62 + O, 0.3, 50))
    A = layer(); ad = ImageDraw.Draw(A)
    card_x(ad, 120, TOP + 140, W - 240, 125, "TE MONTRE LES VOLS", 44, True)
    out.append(slide_in(A, t, 11.3 + O, 0.25, 30))
    B = layer(); bd = ImageDraw.Draw(B)
    card_x(bd, 120, TOP + 300, W - 240, 125, "PAIE À TA PLACE", 44, False)
    out.append(slide_in(B, t, 12.3 + O, 0.25, 30))
    s = stamp("C'EST TOI QUI PAIES", 66, TOP + 490, t, 12.84 + O, rot=-3)
    if s: out.append(s)
    return out

def scene_secu(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "LA RAISON OFFICIELLE", font(F_TITLE, 66), GREY)
    out.append(slide_in(L, t, 13.68 + O, 0.3, 50))
    s = stamp("LA SÉCURITÉ", 100, TOP + 110, t, 14.88 + O, rot=-3)
    if s: out.append(s)
    for i, (txt, t0) in enumerate([("MOT DE PASSE PARTAGÉ", 15.73), ("UN ACHAT NON VOULU", 17.85), ("TES MILES DÉPENSÉS", 19.16)]):
        R = layer(); rd = ImageDraw.Draw(R)
        y = TOP + 320 + i * 125
        rd.rounded_rectangle([140, y, W - 140, y + 100], radius=26, fill=(20, 20, 26, 255), outline=(70, 70, 82, 255), width=3)
        rd.ellipse([175, y + 38, 199, y + 62], fill=(255, 95, 95, 255))
        f2 = font(F_BOLD, 46)
        assert rd.textlength(txt, font=f2) < W - 420, txt
        rd.text((230, y + 50 - f2.getmetrics()[0] / 2 - 2), txt, font=f2, fill=WHITE + (255,))
        out.append(slide_in(R, t, t0 + O, 0.25, 30))
    return out

def scene_twist(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "MAIS FRANCHEMENT…", font(F_TITLE, 74), GREY)
    out.append(slide_in(L, t, 20.2 + O, 0.3, 50))
    P = layer(); pd = ImageDraw.Draw(P)
    text_center(pd, TOP + 125, "le patron de United l'a dit", font(F_BOLD, 50), WHITE)
    out.append(slide_in(P, t, 21.3 + O, 0.3, 20))
    Q = layer(); qd = ImageDraw.Draw(Q)
    fq = font(F_TITLE, 70)
    qd.rounded_rectangle([110, TOP + 220, W - 110, TOP + 440], radius=30, fill=YEL + (255,))
    for j, ln in enumerate(["« PAS DE NOUVEL", "INTERMÉDIAIRE »"]):
        w = qd.textlength(ln, font=fq)
        assert w < W - 280, ln
        qd.text(((W - w) / 2, TOP + 240 + j * 95), ln, font=fq, fill=BG + (255,))
    out.append(pop(Q, t, 23.16 + O, 1.2))
    R = layer(); rd = ImageDraw.Draw(R)
    fr = font(F_TITLE, 40)
    items = [("UNITED", WHITE, None), ("AGENT IA", WHITE, True), ("CLIENTS", WHITE, None)]
    xs = [W / 2 - 330, W / 2, W / 2 + 330]
    for (txt, col, crossed), cx in zip(items, xs):
        w = rd.textlength(txt, font=fr)
        bw = max(w + 60, 150)
        oc = (255, 95, 95) if crossed else (70, 70, 82)
        rd.rounded_rectangle([cx - bw / 2, TOP + 500, cx + bw / 2, TOP + 590], radius=24, fill=DARK + (255,), outline=oc + (255,), width=4)
        rd.text((cx - w / 2, TOP + 545 - fr.getmetrics()[0] / 2 - 2), txt, font=fr, fill=col + (255,))
        if crossed:
            bx, by = cx + bw / 2 - 6, TOP + 500
            rd.ellipse([bx - 24, by - 24, bx + 24, by + 24], fill=(255, 95, 95, 255))
            cross(rd, bx - 11, by - 11, 22, BG + (255,))
    for x1, x2 in [(xs[0] + 108, xs[1] - 136), (xs[1] + 136, xs[2] - 122)]:
        rd.line([(x1, TOP + 545), (x2, TOP + 545)], fill=GREY + (255,), width=4)
    out.append(slide_in(R, t, 24.0 + O, 0.3, 20))
    S = layer(); sd = ImageDraw.Draw(S)
    text_center(sd, TOP + 630, "Scott Kirby, PDG de United", font(F_SEMI, 36), GREY)
    out.append(slide_in(S, t, 23.5 + O, 0.3, 10))
    return out

def scene_poll(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "ET TOI ?", font(F_TITLE, 140), WHITE)
    out.append((L, appear(t, 25.4 + O, 0.3), 0, 1.15 - 0.15 * ease_back((t - 25.4 - O) / 0.35), 0))
    opts = [("OUI, VAS-Y", 26.5 + O, True), ("JAMAIS", 27.2 + O, False)]
    for i, (txt, t0, hl) in enumerate(opts):
        R = layer(); rd = ImageDraw.Draw(R)
        y = TOP + 220 + i * 180
        rd.rounded_rectangle([140, y, W - 140, y + 145], radius=40,
                             fill=(YEL if hl else DARK) + (255,), outline=(YEL + (255,)), width=4)
        f = font(F_TITLE, 60)
        w = rd.textlength(txt, font=f)
        assert w < W - 330, txt
        rd.text(((W - w) / 2, y + 36), txt, font=f, fill=(BG if hl else WHITE) + (255,))
        out.append(slide_in(R, t, t0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 600, "Dis-le en commentaire", font(F_BOLD, 46), GREY)
    out.append((T, appear(t, 27.5 + O, 0.3), 0, 1.0, 0))
    return out

def scene_cta(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy = W / 2, TOP + 200
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=YEL + (255,))
    bolt(d, cx, cy, 210, BG + (255,))
    t0 = 28.15 + O
    out.append((L, appear(t, t0, 0.3), 0, 0.6 + 0.4 * ease_back((t - t0) / 0.45), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 420, "ABONNE-TOI", font(F_TITLE, 120), WHITE)
    text_center(td, TOP + 570, "@flash.ia_actu", font(F_BOLD, 64), YEL)
    text_center(td, TOP + 670, "L'actu IA & réseaux en 30 s", font(F_SEMI, 46), GREY)
    out.append(slide_in(T, t, t0 + 0.15, 0.35, 50))
    return out

SCENES = [  # (start, end, fn)
    (0.0, 6.1 + O, scene_hook),
    (6.1 + O, 10.6 + O, scene_where),
    (10.6 + O, 13.64 + O, scene_pay),
    (13.64 + O, 20.18 + O, scene_secu),
    (20.18 + O, 25.38 + O, scene_twist),
    (25.38 + O, 28.12 + O, scene_poll),
    (28.12 + O, DUR + 1, scene_cta),
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
    s = "Source : United · TechCrunch · The Verge · 12 nov. 2026"
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
