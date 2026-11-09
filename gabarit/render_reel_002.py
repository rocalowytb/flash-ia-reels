"""Rendu du Reel Flash IA n°002 (Anthropic S-1/A) — 1080x1920, 30 fps, charte noir/jaune."""
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
VOICE_END = 28.88 + OFF
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
TOP = 430  # top of the content zone

def scene_hook(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    f = font(F_TITLE, 100)
    text_center(d, TOP + 40, "L'IA QUI FAIT", f, WHITE)
    text_center(d, TOP + 165, "AVANCER L'IA ?", f, WHITE)
    out.append((L, 1.0, 0, 1.0, 0))  # titre visible dès la 1re image (couverture, compréhensible sans le son)
    S = layer(); sd = ImageDraw.Draw(S)
    fs = font(F_TITLE, 140)
    w = sd.textlength("IMMINENT", font=fs)
    x0, y0 = (W - w) / 2 - 40, TOP + 345
    sd.rounded_rectangle([x0, y0, x0 + w + 80, y0 + 190], radius=18, fill=YEL + (255,))
    sd.text(((W - w) / 2, y0 + 12), "IMMINENT", font=fs, fill=BG + (255,))
    if t >= 1.6:
        out.append((S, min(1, (t - 1.6) / 0.12), 0, 1.6 - 0.6 * ease_back((t - 1.6) / 0.35), -4))
    C = layer(); cd = ImageDraw.Draw(C)
    pill(cd, W / 2, TOP + 660, "ANTHROPIC · DÉPÔT BOURSIER DU 2 NOV.", font(F_BOLD, 40), DARK, YEL)
    out.append((C, appear(t, 0.9, 0.3), (1 - appear(t, 0.9, 0.3)) * 30, 1.0, 0))
    return out

def scene_seuil(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "LEURS PROCHAINES IA", font(F_TITLE, 74), WHITE)
    text_center(d, TOP + 105, "POURRAIENT…", font(F_TITLE, 74), GREY)
    out.append((L, appear(t, 6.0, 0.3), (1 - appear(t, 6.0, 0.3)) * 50, 1.0, 0))
    Q = layer(); qd = ImageDraw.Draw(Q)
    qd.rounded_rectangle([110, TOP + 230, W - 110, TOP + 390], radius=30, fill=DARK + (255,), outline=(60, 60, 70, 255), width=2)
    text_center(qd, TOP + 255, "ACCÉLÉRER ELLES-MÊMES", font(F_TITLE, 52), YEL)
    text_center(qd, TOP + 320, "LA RECHERCHE EN IA", font(F_TITLE, 52), YEL)
    out.append((Q, appear(t, 8.05, 0.25), 0, 1.12 - 0.12 * ease_back((t - 8.05) / 0.3), 0))
    # jauge vers le seuil
    G = layer(); gd = ImageDraw.Draw(G)
    gx0, gx1, gy = 140, W - 140, TOP + 520
    gd.rounded_rectangle([gx0, gy, gx1, gy + 56], radius=28, fill=(30, 30, 38, 255), outline=(60, 60, 70, 255), width=2)
    fill_k = ease_out((t - 10.6) / 1.6) * 0.86
    if fill_k > 0.02:
        gd.rounded_rectangle([gx0 + 6, gy + 6, gx0 + 6 + (gx1 - gx0 - 12) * fill_k, gy + 50], radius=22, fill=YEL + (255,))
    sx = gx0 + (gx1 - gx0) * 0.92
    gd.line([(sx, gy - 30), (sx, gy + 86)], fill=WHITE + (255,), width=6)
    fl = font(F_BOLD, 40)
    wl = gd.textlength("SEUIL", font=fl)
    gd.text((sx - wl / 2, gy + 100), "SEUIL", font=fl, fill=WHITE + (255,))
    gd.text((gx0, gy + 100), "Surveillé de très près", font=font(F_SEMI, 38), fill=GREY + (255,))
    out.append((G, appear(t, 10.4, 0.3), (1 - appear(t, 10.4, 0.3)) * 40, 1.0, 0))
    return out

def scene_twist(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "ALORS… ATTENTION", font(F_TITLE, 76), GREY)
    out.append((L, appear(t, 12.6, 0.3), (1 - appear(t, 12.6, 0.3)) * 50, 1.0, 0))
    N = layer(); nd = ImageDraw.Draw(N)
    text_center(nd, TOP + 120, "0", font(F_TITLE, 330), YEL)
    out.append((N, appear(t, 13.5, 0.2), 0, 1.3 - 0.3 * ease_back((t - 13.5) / 0.35), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 520, "MODÈLE ACTUEL", font(F_TITLE, 76), WHITE)
    text_center(td, TOP + 615, "n'a franchi ce seuil", font(F_BOLD, 52), GREY)
    out.append((T, appear(t, 14.1, 0.3), (1 - appear(t, 14.1, 0.3)) * 40, 1.0, 0))
    return out

def scene_humains(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "CLAUDE QUI CONÇOIT", font(F_TITLE, 74), WHITE)
    text_center(d, TOP + 105, "LA SUITE SEUL ?", font(F_TITLE, 74), WHITE)
    out.append((L, appear(t, 15.35, 0.3), (1 - appear(t, 15.35, 0.3)) * 50, 1.0, 0))
    S = layer(); sd = ImageDraw.Draw(S)
    pill(sd, W / 2, TOP + 290, "PAS QUESTION", font(F_TITLE, 76), YEL, BG, r=18)
    if t >= 16.8:
        out.append((S, min(1, (t - 16.8) / 0.12), 0, 1.5 - 0.5 * ease_back((t - 16.8) / 0.35), -3))
    # fausse interface
    C = layer(); cd = ImageDraw.Draw(C)
    x0, y0, x1, y1 = 130, TOP + 420, W - 130, TOP + 690
    cd.rounded_rectangle([x0, y0, x1, y1], radius=36, fill=(20, 20, 26, 255), outline=(55, 55, 66, 255), width=2)
    cd.text((x0 + 40, y0 + 30), "Nouvelle IA à concevoir", font=font(F_BOLD, 44), fill=WHITE + (255,))
    cd.text((x0 + 40, y0 + 100), "Supervision humaine", font=font(F_SEMI, 40), fill=GREY + (255,))
    # interrupteur
    on = t >= 20.0
    tx, ty = x1 - 190, y0 + 95
    cd.rounded_rectangle([tx, ty, tx + 130, ty + 64], radius=32, fill=(YEL if on else (60, 60, 70)) + (255,))
    k = ease_out((t - 20.0) / 0.25) if on else 0
    kx = tx + 32 + 66 * k
    cd.ellipse([kx - 26, ty + 6, kx + 26, ty + 58], fill=(BG if on else WHITE) + (255,))
    if on:
        cd.text((x0 + 40, y0 + 180), "OBLIGATOIRE", font=font(F_TITLE, 52), fill=YEL + (int(255 * k),))
    out.append((C, appear(t, 17.9, 0.3), (1 - appear(t, 17.9, 0.3)) * 50, 1.0, 0))
    return out

def scene_poll(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 20, "ET TOI ?", font(F_TITLE, 150), WHITE)
    out.append((L, appear(t, 21.3, 0.3), 0, 1.15 - 0.15 * ease_back((t - 21.3) / 0.35), 0))
    opts = [("ÇA ME RASSURE", 24.2, True), ("ÇA M'INQUIÈTE", 24.95, False)]
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
    out.append((T, appear(t, 25.1, 0.3), 0, 1.0, 0))
    return out

def scene_cta(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy = W / 2, TOP + 200
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=YEL + (255,))
    bolt(d, cx, cy, 210, BG + (255,))
    out.append((L, appear(t, 25.75, 0.3), 0, 0.6 + 0.4 * ease_back((t - 25.75) / 0.45), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 420, "ABONNE-TOI", font(F_TITLE, 120), WHITE)
    text_center(td, TOP + 570, "@flash.ia_actu", font(F_BOLD, 64), YEL)
    text_center(td, TOP + 670, "L'actu IA & réseaux en 30 s", font(F_SEMI, 46), GREY)
    out.append((T, appear(t, 26.0, 0.35), (1 - appear(t, 26.0, 0.35)) * 50, 1.0, 0))
    return out

SCENES = [  # (start, end, fn)
    (0.0, 5.98, scene_hook),
    (5.98, 12.56, scene_seuil),
    (12.56, 15.28, scene_twist),
    (15.28, 21.2, scene_humains),
    (21.2, 25.7, scene_poll),
    (25.7, DUR + 1, scene_cta),
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
    s = "Source : dépôt SEC d'Anthropic (S-1/A) · TechCrunch"
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
