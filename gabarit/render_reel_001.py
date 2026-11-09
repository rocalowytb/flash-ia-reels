"""Rendu du Reel Flash IA n°001 — 1080x1920, 30 fps, charte noir/jaune."""
import json, math, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BG = (11, 11, 15)
YEL = (255, 225, 77)
WHITE = (255, 255, 255)
GREY = (150, 150, 160)
DARK = (24, 24, 30)

F_TITLE = "/home/claude/flash-ia/fonts/ArchivoBlack.ttf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
F_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

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
words = [w for w in json.load(open("words.json"))["words"] if w["type"] == "word" and not w["text"].startswith("[")]
VOICE_END = 23.52
DUR = VOICE_END + 1.0
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
    L = layer(); d = ImageDraw.Draw(L)
    f = font(F_TITLE, 98)
    text_center(d, TOP + 50, "ÊTRE MÉCHANT", f, WHITE)
    text_center(d, TOP + 175, "AVEC CLAUDE ?", f, WHITE)
    out = [(L, appear(t, 0.0, 0.35), (1 - appear(t, 0.0, 0.35)) * 60, 1.0, 0)]
    # stamp INTERDIT
    S = layer(); sd = ImageDraw.Draw(S)
    fs = font(F_TITLE, 150)
    w = sd.textlength("INTERDIT", font=fs)
    x0, y0 = (W - w) / 2 - 40, TOP + 360
    sd.rounded_rectangle([x0, y0, x0 + w + 80, y0 + 200], radius=18, fill=YEL + (255,))
    sd.text(((W - w) / 2, y0 + 12), "INTERDIT", font=fs, fill=BG + (255,))
    k = ease_back((t - 1.9) / 0.35)
    if t >= 1.9:
        out.append((S, min(1, (t - 1.9) / 0.12), 0, 1.6 - 0.6 * k, -4))
    # date chip
    C = layer(); cd = ImageDraw.Draw(C)
    pill(cd, W / 2, TOP + 680, "DÈS LE 12 NOVEMBRE", font(F_BOLD, 46), DARK, YEL)
    out.append((C, appear(t, 1.2, 0.3), (1 - appear(t, 1.2, 0.3)) * 30, 1.0, 0))
    return out

def scene_nuance(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 20, "ENFIN…", font(F_TITLE, 96), GREY)
    text_center(d, TOP + 140, "PAS TOUT À FAIT.", font(F_TITLE, 96), WHITE)
    out.append((L, appear(t, 4.9, 0.3), (1 - appear(t, 4.9, 0.3)) * 50, 1.0, 0))
    items = [("Râler", 6.44), ("Critiquer une", 7.08), ("mauvaise réponse", 7.08)]
    rows = [("Râler", 6.44), ("Critiquer une réponse", 7.08)]
    for i, (txt, t0) in enumerate(rows):
        R = layer(); rd = ImageDraw.Draw(R)
        y = TOP + 330 + i * 150
        rd.rounded_rectangle([150, y, W - 150, y + 130], radius=30, fill=DARK + (255,))
        check(rd, 195, y + 38, 54, YEL + (255,))
        rd.text((290, y + 30), txt, font=font(F_BOLD, 62), fill=WHITE + (255,))
        out.append((R, appear(t, t0, 0.3), (1 - appear(t, t0, 0.3)) * 40, 1.0, 0))
    O = layer(); od = ImageDraw.Draw(O)
    pill(od, W / 2, TOP + 680, "ÇA RESTE OK", font(F_TITLE, 60), YEL, BG)
    out.append((O, appear(t, 8.4, 0.25), 0, 1.25 - 0.25 * ease_back((t - 8.4) / 0.3), 0))
    return out

def scene_cruel(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "CE QUI EST VISÉ :", font(F_BOLD, 58), GREY)
    text_center(d, TOP + 100, "LA CRUAUTÉ", font(F_TITLE, 130), YEL)
    out.append((L, appear(t, 9.15, 0.3), (1 - appear(t, 9.15, 0.3)) * 50, 1.0, 0))
    rows = [("GRATUITE", 10.64), ("RÉPÉTÉE", 11.36), ("SANS RAISON", 12.12)]
    for i, (txt, t0) in enumerate(rows):
        R = layer(); rd = ImageDraw.Draw(R)
        y = TOP + 300 + i * 140
        rd.rounded_rectangle([200, y, W - 200, y + 120], radius=26, fill=DARK + (255,), outline=(60, 60, 70, 255), width=2)
        cross(rd, 245, y + 36, 46, YEL + (255,))
        rd.text((335, y + 22), txt, font=font(F_TITLE, 66), fill=WHITE + (255,))
        out.append((R, appear(t, t0, 0.25), 0, 1.15 - 0.15 * ease_back((t - t0) / 0.3), 0))
    return out

def scene_chat(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 10, "CLAUDE PEUT", font(F_TITLE, 92), WHITE)
    text_center(d, TOP + 120, "COUPER COURT", font(F_TITLE, 92), YEL)
    out.append((L, appear(t, 13.1, 0.3), (1 - appear(t, 13.1, 0.3)) * 50, 1.0, 0))
    # chat window
    C = layer(); cd = ImageDraw.Draw(C)
    x0, y0, x1, y1 = 130, TOP + 270, W - 130, TOP + 690
    cd.rounded_rectangle([x0, y0, x1, y1], radius=40, fill=(20, 20, 26, 255), outline=(55, 55, 66, 255), width=2)
    # user bubbles (redacted)
    for i, wd in enumerate([520, 420, 560]):
        by = y0 + 40 + i * 92
        cd.rounded_rectangle([x1 - 50 - wd, by, x1 - 50, by + 74], radius=30, fill=(46, 46, 56, 255))
        for k in range(int(wd / 46) - 1):
            cd.ellipse([x1 - wd - 20 + k * 46, by + 27, x1 - wd + 2 + k * 46, by + 49], fill=(120, 120, 135, 255))
    out.append((C, appear(t, 13.5, 0.35), (1 - appear(t, 13.5, 0.35)) * 60, 1.0, 0))
    # end banner
    B = layer(); bd = ImageDraw.Draw(B)
    by = y0 + 300
    bd.rounded_rectangle([x0 + 40, by, x1 - 40, by + 130], radius=28, fill=YEL + (255,))
    # stop icon
    bd.ellipse([x0 + 75, by + 30, x0 + 145, by + 100], outline=BG + (255,), width=8)
    bd.line([(x0 + 92, by + 47), (x0 + 128, by + 83)], fill=BG + (255,), width=8)
    bd.text((x0 + 170, by + 20), "Conversation", font=font(F_BOLD, 44), fill=BG + (255,))
    bd.text((x0 + 170, by + 68), "terminée par Claude", font=font(F_SEMI, 38), fill=BG + (255,))
    out.append((B, appear(t, 15.3, 0.2), 0, 1.2 - 0.2 * ease_back((t - 15.3) / 0.3), 0))
    return out

def scene_poll(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    text_center(d, TOP + 30, "ET TOI ?", font(F_TITLE, 150), WHITE)
    out.append((L, appear(t, 16.5, 0.3), 0, 1.15 - 0.15 * ease_back((t - 16.5) / 0.35), 0))
    opts = [("POLI AVEC MON IA", 17.4, True), ("PAS DU TOUT", 19.24, False)]
    for i, (txt, t0, hl) in enumerate(opts):
        R = layer(); rd = ImageDraw.Draw(R)
        y = TOP + 300 + i * 190
        rd.rounded_rectangle([140, y, W - 140, y + 150], radius=40,
                             fill=(YEL if hl else DARK) + (255,), outline=(YEL + (255,)), width=4)
        f = font(F_TITLE, 64)
        w = rd.textlength(txt, font=f)
        rd.text(((W - w) / 2, y + 36), txt, font=f, fill=(BG if hl else WHITE) + (255,))
        out.append((R, appear(t, t0, 0.3), (1 - appear(t, t0, 0.3)) * 40, 1.0, 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 670, "Dis-le en commentaire 👇".replace(" 👇", ""), font(F_BOLD, 50), GREY)
    out.append((T, appear(t, 19.6, 0.3), 0, 1.0, 0))
    return out

def scene_cta(t):
    out = []
    L = layer(); d = ImageDraw.Draw(L)
    cx, cy = W / 2, TOP + 200
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=YEL + (255,))
    bolt(d, cx, cy, 210, BG + (255,))
    out.append((L, appear(t, 20.2, 0.3), 0, 0.6 + 0.4 * ease_back((t - 20.2) / 0.45), 0))
    T = layer(); td = ImageDraw.Draw(T)
    text_center(td, TOP + 420, "ABONNE-TOI", font(F_TITLE, 120), WHITE)
    text_center(td, TOP + 570, "@flash.ia_actu", font(F_BOLD, 64), YEL)
    text_center(td, TOP + 670, "L'actu IA & réseaux en 30 s", font(F_SEMI, 46), GREY)
    out.append((T, appear(t, 20.5, 0.35), (1 - appear(t, 20.5, 0.35)) * 50, 1.0, 0))
    return out

SCENES = [  # (start, end, fn)
    (0.0, 4.88, scene_hook),
    (4.88, 9.12, scene_nuance),
    (9.12, 13.06, scene_cruel),
    (13.06, 16.45, scene_chat),
    (16.45, 20.15, scene_poll),
    (20.15, DUR + 1, scene_cta),
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
    s = "Source : PCWorld · Notebookcheck"
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
