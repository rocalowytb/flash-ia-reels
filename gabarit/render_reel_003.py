"""Rendu du Reel Flash IA n°003 (ChatGPT Images 2.6 : les GIF) — 1080x1920, 30 fps, charte noir/jaune."""
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
VOICE_END = 31.12 + OFF
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

def stamp(txt, size, cy, t, t0, rot=-4):
    S = layer(); sd = ImageDraw.Draw(S)
    fs = font(F_TITLE, size)
    w = sd.textlength(txt, font=fs)
    asc, desc = fs.getmetrics()
    x0 = (W - w) / 2 - 40
    sd.rounded_rectangle([x0, cy, x0 + w + 80, cy + asc + desc + 30], radius=18, fill=YEL + (255,))
    sd.text(((W - w) / 2, cy + 12), txt, font=fs, fill=BG + (255,))
    if t < t0:
        return None
    return (S, min(1, (t - t0) / 0.12), 0, 1.6 - 0.6 * ease_back((t - t0) / 0.35), rot)

def mini_bolt_frame(d, x, y, s, phase, hl=False):
    """une vignette de « GIF » : un éclair qui saute selon la phase (0..1)"""
    d.rounded_rectangle([x, y, x + s, y + s], radius=int(s * 0.14), fill=((40, 38, 20) if hl else (24, 24, 30)) + (255,),
                        outline=(YEL if hl else (60, 60, 70)) + (255,), width=4 if hl else 2)
    hop = abs(math.sin(phase * math.pi)) * s * 0.18
    cx, cy = x + s / 2, y + s * 0.56 - hop
    d.ellipse([cx - s * 0.2, y + s * 0.82, cx + s * 0.2, y + s * 0.88], fill=(8, 8, 10, 255))
    bolt(d, cx, cy, s * 0.55, YEL + (255,))

def scene_hook(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    f = font(F_TITLE, 108)
    text_center(d, TOP + 30, "CHATGPT FAIT", f, WHITE)
    text_center(d, TOP + 160, "DES GIF ?", f, WHITE)
    out.append((L, 1.0, 0, 1.0, 0))  # titre visible dès la 1re image (couverture)
    s = stamp("OFFICIEL", 140, TOP + 335, t, 2.35)
    if s: out.append(s)
    C = layer(); cd = ImageDraw.Draw(C)
    pill(cd, W / 2, TOP + 640, "OPENAI · IMAGES 2.6 · 4 NOVEMBRE", font(F_BOLD, 40), DARK, YEL)
    out.append((C, appear(t, 0.9, 0.3), (1 - appear(t, 0.9, 0.3)) * 30, 1.0, 0))
    return out

def scene_marche(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "UNE IDÉE OU", font(F_TITLE, 80), WHITE)
    text_center(d, TOP + 105, "UNE PHOTO…", font(F_TITLE, 80), WHITE)
    out.append((L, appear(t, 5.65, 0.3), (1 - appear(t, 5.65, 0.3)) * 50, 1.0, 0))
    # carte prompt
    P = layer(); pd = ImageDraw.Draw(P)
    pd.rounded_rectangle([110, TOP + 250, 520, TOP + 450], radius=30, fill=(20, 20, 26, 255), outline=(60, 60, 70, 255), width=2)
    pd.text((145, TOP + 275), "PROMPT", font=font(F_BOLD, 34), fill=YEL + (255,))
    pd.text((145, TOP + 330), "« un éclair", font=font(F_SEMI, 38), fill=WHITE + (255,))
    pd.text((145, TOP + 380), "qui saute »", font=font(F_SEMI, 38), fill=WHITE + (255,))
    out.append((P, appear(t, 7.6, 0.3), (1 - appear(t, 7.6, 0.3)) * 40, 1.0, 0))
    # carte photo
    Q = layer(); qd = ImageDraw.Draw(Q)
    qd.rounded_rectangle([560, TOP + 250, 970, TOP + 450], radius=30, fill=(20, 20, 26, 255), outline=(60, 60, 70, 255), width=2)
    qd.text((595, TOP + 275), "PHOTO", font=font(F_BOLD, 34), fill=YEL + (255,))
    qd.polygon([(600, TOP + 420), (700, TOP + 330), (770, TOP + 400), (820, TOP + 360), (930, TOP + 420)], fill=(90, 90, 100, 255))
    qd.ellipse([860, TOP + 320, 900, TOP + 360], fill=YEL + (255,))
    out.append((Q, appear(t, 8.7, 0.3), (1 - appear(t, 8.7, 0.3)) * 40, 1.0, 0))
    # flèche + GIF en boucle
    G = layer(); gd = ImageDraw.Draw(G)
    gd.polygon([(W / 2 - 26, TOP + 475), (W / 2 + 26, TOP + 475), (W / 2, TOP + 515)], fill=GREY + (255,))
    phase = ((t - 9.7) * 1.6) % 1 if t > 9.7 else 0
    mini_bolt_frame(gd, W / 2 - 230, TOP + 530, 160, phase, hl=True)
    gd.text((W / 2 - 40, TOP + 545), "GIF", font=font(F_TITLE, 64), fill=WHITE + (255,))
    gd.text((W / 2 - 40, TOP + 625), "en boucle ↻", font=font(F_BOLD, 40), fill=YEL + (255,))
    out.append((G, appear(t, 9.7, 0.25), 0, 1.15 - 0.15 * ease_back((t - 9.7) / 0.3), 0))
    return out

def scene_editeur(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "TU CONTRÔLES TOUT", font(F_TITLE, 74), WHITE)
    out.append((L, appear(t, 11.2, 0.3), (1 - appear(t, 11.2, 0.3)) * 50, 1.0, 0))
    C = layer(); cd = ImageDraw.Draw(C)
    x0, y0, x1 = 110, TOP + 130, W - 110
    cd.rounded_rectangle([x0, y0, x1, y0 + 330], radius=36, fill=(20, 20, 26, 255), outline=(55, 55, 66, 255), width=2)
    cd.text((x0 + 40, y0 + 28), "Vitesse", font=font(F_BOLD, 40), fill=WHITE + (255,))
    sx0, sx1, sy = x0 + 250, x1 - 50, y0 + 55
    cd.rounded_rectangle([sx0, sy - 6, sx1, sy + 6], radius=6, fill=(60, 60, 70, 255))
    k = 0.25 + 0.55 * ease_out((t - 11.5) / 0.8)
    kx = sx0 + (sx1 - sx0) * k
    cd.rounded_rectangle([sx0, sy - 6, kx, sy + 6], radius=6, fill=YEL + (255,))
    cd.ellipse([kx - 22, sy - 22, kx + 22, sy + 22], fill=YEL + (255,))
    cd.text((x0 + 40, y0 + 110), "Images", font=font(F_BOLD, 40), fill=WHITE + (255,))
    sel = int(((t - 12.4) / 0.25)) % 6 if t >= 12.4 else -1
    if t >= 13.95: sel = 3
    for i in range(6):
        fx = x0 + 40 + i * 132
        mini_bolt_frame(cd, fx, y0 + 175, 112, i / 6, hl=(i == sel))
    out.append((C, appear(t, 11.3, 0.3), (1 - appear(t, 11.3, 0.3)) * 40, 1.0, 0))
    R = layer(); rd = ImageDraw.Draw(R)
    text_center(rd, TOP + 500, "IMAGE DE RÉFÉRENCE", font(F_BOLD, 46), GREY)
    out.append((R, appear(t, 14.2, 0.3), (1 - appear(t, 14.2, 0.3)) * 30, 1.0, 0))
    for txt, cx, t0 in [("TON PERSO", W / 2 - 200, 14.75), ("TON CHIEN", W / 2 + 200, 15.45)]:
        Pp = layer(); ppd = ImageDraw.Draw(Pp)
        pill(ppd, cx, TOP + 620, txt, font(F_TITLE, 46), YEL, BG, r=18)
        out.append((Pp, appear(t, t0, 0.2), 0, 1.3 - 0.3 * ease_back((t - t0) / 0.3), 0))
    return out

def scene_chiffre(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "LE PLUS FOU ?", font(F_TITLE, 76), GREY)
    out.append((L, appear(t, 17.0, 0.3), (1 - appear(t, 17.0, 0.3)) * 50, 1.0, 0))
    N = layer(); nd = ImageDraw.Draw(N)
    n = 4 * ease_out((t - 18.5) / 0.7)
    val = f"{n:.1f}".replace(".", ",") if n < 3.99 else "4"
    text_center(nd, TOP + 110, val, font(F_TITLE, 300), YEL)
    out.append((N, appear(t, 18.5, 0.2), 0, 1.25 - 0.25 * ease_back((t - 18.5) / 0.35), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 470, "MILLIARDS D'IMAGES", font(F_TITLE, 72), WHITE)
    text_center(td, TOP + 565, "créées chaque semaine", font(F_BOLD, 52), GREY)
    out.append((T, appear(t, 18.95, 0.3), (1 - appear(t, 18.95, 0.3)) * 40, 1.0, 0))
    return out

def scene_twist(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "ET ATTENTION…", font(F_TITLE, 76), GREY)
    out.append((L, appear(t, 21.05, 0.3), (1 - appear(t, 21.05, 0.3)) * 50, 1.0, 0))
    N = layer(); nd = ImageDraw.Draw(N)
    text_center(nd, TOP + 110, "+50 %", font(F_TITLE, 200), YEL)
    text_center(nd, TOP + 330, "DE VITESSE", font(F_TITLE, 64), WHITE)
    out.append((N, appear(t, 21.95, 0.2), 0, 1.25 - 0.25 * ease_back((t - 21.95) / 0.35), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 460, "Sur tous les forfaits", font(F_BOLD, 52), WHITE)
    out.append((T, appear(t, 23.4, 0.3), (1 - appear(t, 23.4, 0.3)) * 30, 1.0, 0))
    s = stamp("MÊME GRATUIT", 84, TOP + 560, t, 24.45, rot=-3)
    if s: out.append(s)
    return out

def scene_poll(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 20, "ET TOI ?", font(F_TITLE, 150), WHITE)
    out.append((L, appear(t, 25.15, 0.3), 0, 1.15 - 0.15 * ease_back((t - 25.15) / 0.35), 0))
    opts = [("JE VAIS TESTER", 26.4, True), ("UN GADGET", 27.35, False)]
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
    out.append((T, appear(t, 27.6, 0.3), 0, 1.0, 0))
    return out

def scene_cta(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy = W / 2, TOP + 200
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=YEL + (255,))
    bolt(d, cx, cy, 210, BG + (255,))
    out.append((L, appear(t, 28.15, 0.3), 0, 0.6 + 0.4 * ease_back((t - 28.15) / 0.45), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 420, "ABONNE-TOI", font(F_TITLE, 120), WHITE)
    text_center(td, TOP + 570, "@flash.ia_reseau", font(F_BOLD, 64), YEL)
    text_center(td, TOP + 670, "L'actu IA & réseaux en 30 s", font(F_SEMI, 46), GREY)
    out.append((T, appear(t, 28.4, 0.35), (1 - appear(t, 28.4, 0.35)) * 50, 1.0, 0))
    return out

SCENES = [  # (start, end, fn)
    (0.0, 5.58, scene_hook),
    (5.58, 11.12, scene_marche),
    (11.12, 16.95, scene_editeur),
    (16.95, 20.99, scene_chiffre),
    (20.99, 25.08, scene_twist),
    (25.08, 28.07, scene_poll),
    (28.07, DUR + 1, scene_cta),
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
    s = "Source : OpenAI (Images 2.6, 4 nov.) · The Verge"
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
