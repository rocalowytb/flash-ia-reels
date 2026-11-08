"""Rendu du Reel Flash IA n°006 (manifestations contre les data centers IA en Europe) — 1080x1920, 30 fps, charte noir/jaune."""
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
VOICE_END = 34.72 + OFF
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
O = OFF    # les horodatages ci-dessous = transcription + décalage voix

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

def slide_in(L, t, t0, d=0.3, off=40):
    return (L, appear(t, t0, d), (1 - appear(t, t0, d)) * off, 1.0, 0)

def scene_hook(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    f = font(F_TITLE, 96)
    text_center(d, TOP + 20, "DES MILITANTS", f, WHITE)
    text_center(d, TOP + 140, "ENVAHISSENT", f, WHITE)
    text_center(d, TOP + 260, "MICROSOFT", f, YEL)
    out.append((L, 1.0, 0, 1.0, 0))  # titre visible dès la 1re image (couverture)
    s = stamp("À CAUSE DE L'IA", 84, TOP + 420, t, 3.45)
    if s: out.append(s)
    C = layer(); cd = ImageDraw.Draw(C)
    pill(cd, W / 2, TOP + 650, "AMSTERDAM · 6 NOVEMBRE", font(F_BOLD, 40), DARK, YEL)
    out.append(slide_in(C, t, 4.4, 0.3, 30))
    return out

def scene_site(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "AMSTERDAM", font(F_TITLE, 104), YEL)
    text_center(d, TOP + 135, "vendredi 6 novembre", font(F_BOLD, 50), GREY)
    out.append(slide_in(L, t, 6.4 + O, 0.3, 50))
    P = layer(); pd = ImageDraw.Draw(P)
    pd.rounded_rectangle([110, TOP + 250, W - 110, TOP + 560], radius=34, fill=(20, 20, 26, 255), outline=(70, 70, 82, 255), width=3)
    band = Image.new("RGBA", (W - 300, 60), YEL + (255,)); bd = ImageDraw.Draw(band)
    for k in range(-80, W, 60):
        bd.polygon([(k, 60), (k + 30, 60), (k + 90, 0), (k + 60, 0)], fill=BG + (255,))
    P.paste(band, (150, TOP + 285))
    text_center(pd, TOP + 375, "FUTUR DATA CENTER", font(F_TITLE, 64), WHITE)
    text_center(pd, TOP + 465, "Microsoft · quartier de Sloterdijk", font(F_BOLD, 42), GREY)
    out.append(slide_in(P, t, 8.1 + O))
    G = layer(); gd = ImageDraw.Draw(G)
    pill(gd, W / 2, TOP + 650, "GRILLES ESCALADÉES", font(F_TITLE, 52), YEL, BG, r=22)
    out.append((G, appear(t, 8.5 + O, 0.2), 0, 1.25 - 0.25 * ease_back((t - 8.5 - O) / 0.3), 0))
    return out

def scene_police(t):
    out = []
    R = layer(); rd = ImageDraw.Draw(R)
    rd.rounded_rectangle([110, TOP + 10, W - 110, TOP + 160], radius=40, fill=(20, 20, 26, 255), outline=(90, 90, 100, 255), width=4)
    cx, cy, r = 205, TOP + 85, 48
    pts = [(cx + r * math.cos(math.radians(22.5 + 45 * i)), cy + r * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
    rd.polygon(pts, fill=(255, 95, 95, 255))
    rd.rectangle([cx - 26, cy - 7, cx + 26, cy + 7], fill=WHITE + (255,))
    f = font(F_TITLE, 60)
    assert rd.textlength("TRAVAUX STOPPÉS", font=f) < W - 110 - 300
    rd.text((285, TOP + 50), "TRAVAUX STOPPÉS", font=f, fill=WHITE + (255,))
    out.append(slide_in(R, t, 10.3 + O))
    N = layer(); nd = ImageDraw.Draw(N)
    text_center(nd, TOP + 220, "150 À 200", font(F_TITLE, 170), YEL)
    text_center(nd, TOP + 450, "personnes interpellées", font(F_BOLD, 60), WHITE)
    text_center(nd, TOP + 540, "selon l'agence néerlandaise ANP", font(F_SEMI, 40), GREY)
    out.append((N, appear(t, 13.4 + O, 0.2), 0, 1.25 - 0.25 * ease_back((t - 13.4 - O) / 0.35), 0))
    return out

def house(d, cx, by, s, fill):
    d.polygon([(cx - s, by - s * 0.9), (cx, by - s * 1.7), (cx + s, by - s * 0.9)], fill=fill)
    d.rectangle([cx - s * 0.75, by - s * 0.9, cx + s * 0.75, by], fill=fill)

def scene_energy(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "LEUR ARGUMENT", font(F_TITLE, 80), GREY)
    out.append(slide_in(L, t, 15.32 + O, 0.3, 50))
    A = layer(); ad = ImageDraw.Draw(A)
    ad.rounded_rectangle([110, TOP + 150, W - 110, TOP + 300], radius=34, fill=YEL + (255,))
    text_center(ad, TOP + 182, "1 DATA CENTER", font(F_TITLE, 72), BG)
    out.append(slide_in(A, t, 16.3 + O))
    E = layer(); ed = ImageDraw.Draw(E)
    text_center(ed, TOP + 305, "=", font(F_TITLE, 110), WHITE)
    out.append((E, appear(t, 17.1 + O, 0.2), 0, 1.0, 0))
    B = layer(); bd = ImageDraw.Draw(B)
    bd.rounded_rectangle([110, TOP + 460, W - 110, TOP + 650], radius=34, fill=(20, 20, 26, 255), outline=YEL + (255,), width=4)
    for i in range(7):
        house(bd, 200 + i * 113, TOP + 545, 30, (YEL if i % 2 == 0 else WHITE) + (255,))
    fb = font(F_TITLE, 40)
    assert bd.textlength("TOUS LES FOYERS D'AMSTERDAM", font=fb) < W - 300
    text_center(bd, TOP + 568, "TOUS LES FOYERS D'AMSTERDAM", fb, WHITE)
    out.append(slide_in(B, t, 18.1 + O))
    S = layer(); sd = ImageDraw.Draw(S)
    text_center(sd, TOP + 668, "estimation des militants", font(F_SEMI, 36), GREY)
    out.append(slide_in(S, t, 18.6 + O, 0.3, 10))
    return out

def scene_europe(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "PAS UN CAS ISOLÉ", font(F_TITLE, 80), GREY)
    out.append(slide_in(L, t, 19.76 + O, 0.3, 50))
    N = layer(); nd = ImageDraw.Draw(N)
    text_center(nd, TOP + 110, "+10 PAYS", font(F_TITLE, 170), YEL)
    text_center(nd, TOP + 340, "ce week-end, en Europe", font(F_BOLD, 52), WHITE)
    out.append((N, appear(t, 23.2 + O, 0.2), 0, 1.25 - 0.25 * ease_back((t - 23.2 - O) / 0.35), 0))
    chips = [("FINLANDE", 24.0), ("DANEMARK", 24.25), ("PAYS-BAS", 24.5), ("ESPAGNE", 24.7), ("ROYAUME-UNI", 24.9), ("FRANCE", 25.1)]
    pos = [(W / 2 - 300, TOP + 490), (W / 2, TOP + 490), (W / 2 + 300, TOP + 490),
           (W / 2 - 300, TOP + 600), (W / 2, TOP + 600), (W / 2 + 300, TOP + 600)]
    for (txt, t0), (cx, cy) in zip(chips, pos):
        C = layer(); cd = ImageDraw.Draw(C)
        hl = txt == "FRANCE"
        f2 = font(F_BOLD, 40)
        if cd.textlength(txt, font=f2) > 230: f2 = font(F_BOLD, 34)
        pill(cd, cx, cy, txt, f2, YEL if hl else DARK, BG if hl else WHITE, padx=22, pady=14)
        out.append((C, appear(t, t0 + O, 0.25), (1 - appear(t, t0 + O, 0.25)) * 25, 1.0, 0))
    return out

def scene_demand(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "CE QU'ILS VEULENT", font(F_TITLE, 80), GREY)
    out.append(slide_in(L, t, 25.64 + O, 0.3, 50))
    s = stamp("PAUSE IMMÉDIATE", 84, TOP + 170, t, 26.7 + O, rot=-3)
    if s: out.append(s)
    B = layer(); bd = ImageDraw.Draw(B)
    text_center(bd, TOP + 390, "sur les grands", font(F_BOLD, 60), WHITE)
    text_center(bd, TOP + 465, "data centers en Europe", font(F_BOLD, 60), WHITE)
    text_center(bd, TOP + 580, "un moratoire, réclamé par 100+ assos", font(F_SEMI, 40), GREY)
    out.append(slide_in(B, t, 27.6 + O))
    return out

def scene_poll(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "ET TOI ?", font(F_TITLE, 140), WHITE)
    text_center(d, TOP + 180, "L'IA vaut tout ce courant ?", font(F_BOLD, 52), YEL)
    out.append((L, appear(t, 28.88 + O, 0.3), 0, 1.15 - 0.15 * ease_back((t - 28.88 - O) / 0.35), 0))
    opts = [("OUI, ÇA VAUT LE COUP", 30.0 + O, False), ("NON, STOP", 30.6 + O, True)]
    for i, (txt, t0, hl) in enumerate(opts):
        R = layer(); rd = ImageDraw.Draw(R)
        y = TOP + 290 + i * 180
        rd.rounded_rectangle([140, y, W - 140, y + 145], radius=40,
                             fill=(YEL if hl else DARK) + (255,), outline=(YEL + (255,)), width=4)
        f = font(F_TITLE, 56)
        w = rd.textlength(txt, font=f)
        assert w < W - 330, txt
        rd.text(((W - w) / 2, y + 38), txt, font=f, fill=(BG if hl else WHITE) + (255,))
        out.append(slide_in(R, t, t0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 660, "Dis-le en commentaire", font(F_BOLD, 46), GREY)
    out.append((T, appear(t, 30.9 + O, 0.3), 0, 1.0, 0))
    return out

def scene_cta(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy = W / 2, TOP + 200
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=YEL + (255,))
    bolt(d, cx, cy, 210, BG + (255,))
    t0 = 31.39 + O
    out.append((L, appear(t, t0, 0.3), 0, 0.6 + 0.4 * ease_back((t - t0) / 0.45), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 420, "ABONNE-TOI", font(F_TITLE, 120), WHITE)
    text_center(td, TOP + 570, "@flash.ia_reseau", font(F_BOLD, 64), YEL)
    text_center(td, TOP + 670, "L'actu IA & réseaux en 30 s", font(F_SEMI, 46), GREY)
    out.append(slide_in(T, t, t0 + 0.15, 0.35, 50))
    return out

SCENES = [  # (start, end, fn)
    (0.0, 5.88 + O, scene_hook),
    (5.88 + O, 10.2 + O, scene_site),
    (10.2 + O, 15.3 + O, scene_police),
    (15.3 + O, 19.46 + O, scene_energy),
    (19.46 + O, 25.62 + O, scene_europe),
    (25.62 + O, 28.86 + O, scene_demand),
    (28.86 + O, 31.37 + O, scene_poll),
    (31.37 + O, DUR + 1, scene_cta),
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
    s = "Source : AFP · TT · Anadolu · 6-7 nov. 2026"
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
