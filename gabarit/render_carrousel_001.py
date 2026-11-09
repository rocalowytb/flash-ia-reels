"""Carrousel n°1 + story de lancement Flash IA — charte noir/jaune."""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BG = (11, 11, 15); YEL = (255, 225, 77); WHITE = (255, 255, 255); GREY = (150, 150, 160); DARK = (24, 24, 30)
F_TITLE = "/home/claude/flash-ia/fonts/ArchivoBlack.ttf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
F_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
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

W, H = 1080, 1350
TOTAL = 8
slides = []

# 1 — couverture
im = background(W, H); d = ImageDraw.Draw(im); badge(d, W)
y = rich_lines(d, 0, 300, [[("L'ALGORITHME", WHITE)], [("INSTAGRAM", WHITE)], [("EN 2026", YEL)]], f(F_TITLE, 118), 140, W, True)
ft = f(F_BOLD, 52)
y = rich_lines(d, 0, y + 50, [[("5 règles ", WHITE), ("confirmées", YEL)], [("par Instagram lui-même", WHITE)]], ft, 70, W, True)
d.rounded_rectangle([W / 2 - 170, H - 260, W / 2 + 170, H - 180], radius=40, outline=YEL, width=4)
s = "SWIPE  →"; fs = f(F_TITLE, 40); d.text(((W - d.textlength(s, font=fs)) / 2, H - 247), s, font=fs, fill=YEL)
footer(d, W, H, 1, TOTAL); slides.append(im)

# 2 — deuxième accroche
im = background(W, H, (0.2, 0.85)); d = ImageDraw.Draw(im); badge(d, W)
y = rich_lines(d, 0, 330, [[("TU POSTES", WHITE)], [("MAIS PERSONNE", WHITE)], [("NE TE VOIT ?", YEL)]], f(F_TITLE, 104), 128, W, True)
ft = f(F_BOLD, 50)
for i, l in enumerate(wrap(d, "Ce n'est pas un hasard. Instagram a dévoilé ce qui fait vraiment grimper la portée.", ft, 860)):
    d.text(((W - d.textlength(l, font=ft)) / 2, y + 60 + i * 68), l, font=ft, fill=GREY)
footer(d, W, H, 2, TOTAL); slides.append(im)

rules = [
    ("01", ["LE TEMPS DE", "VISIONNAGE"], "passe avant tout",
     "Un Reel court regardé jusqu'au bout (et revu) bat une vidéo plus longue que les gens quittent au bout de 3 secondes.",
     "Soigne les 2 premières secondes."),
    ("02", ["LES ENVOIS", "EN DM"], "le signal n°1 pour les inconnus",
     "Quand quelqu'un envoie ton post à un ami, Instagram le montre à plus de gens qui ne te suivent pas.",
     "Crée du contenu qu'on veut partager."),
    ("03", ["5 HASHTAGS", "MAXIMUM"], "depuis décembre 2025",
     "Et selon Adam Mosseri, ils n'augmentent plus la portée. Ce qui compte : les mots-clés dans ta légende.",
     "3 à 5 hashtags précis, pas #viral."),
    ("04", ["L'ORIGINALITÉ", "OBLIGATOIRE"], "photos et carrousels inclus",
     "Les comptes qui republient le contenu des autres sortent des recommandations. Depuis avril 2026, ça touche aussi les photos et les carrousels.",
     "Crée, ne recopie pas."),
    ("05", ["TESTE AVEC LES", "TRIAL REELS"], "montrés d'abord aux non-abonnés",
     "Ils montrent ta vidéo à des gens qui ne te suivent pas, sans toucher tes abonnés. Idéal pour tester une accroche.",
     "Teste 2 accroches, garde la meilleure."),
]
for k, (num, title, sub, body, tip) in enumerate(rules):
    im = background(W, H, (0.85 if k % 2 else 0.15, 0.2)); d = ImageDraw.Draw(im); badge(d, W)
    d.text((80, 200), num, font=f(F_TITLE, 190), fill=YEL)
    y = rich_lines(d, 80, 430, [[(t, WHITE)] for t in title], f(F_TITLE, 84), 100)
    d.text((80, y + 6), sub, font=f(F_BOLD, 44), fill=YEL)
    fb = f(F_SEMI, 44); yy = y + 100
    for l in wrap(d, body, fb, 900):
        d.text((80, yy), l, font=fb, fill=(220, 220, 228)); yy += 62
    d.rounded_rectangle([80, H - 250, W - 80, H - 150], radius=28, fill=DARK, outline=(60, 60, 70), width=2)
    d.text((115, H - 225), "→ " + tip, font=f(F_BOLD, 40), fill=WHITE)
    footer(d, W, H, 3 + k, TOTAL); slides.append(im)

# 8 — CTA
im = background(W, H, (0.5, 0.3)); d = ImageDraw.Draw(im)
cx, cy = W / 2, 330
d.ellipse([cx - 130, cy - 130, cx + 130, cy + 130], fill=YEL); bolt(d, cx, cy, 180, BG)
y = rich_lines(d, 0, 520, [[("ENREGISTRE", YEL)], [("CE POST", WHITE)]], f(F_TITLE, 110), 130, W, True)
ft = f(F_BOLD, 48)
y = rich_lines(d, 0, y + 30, [[("et envoie-le à un pote créateur", WHITE)]], ft, 64, W, True)
y = rich_lines(d, 0, y + 50, [[("Abonne-toi : ", GREY), ("@flash.ia_actu", YEL)]], ft, 64, W, True)
fs = f(F_SEMI, 30)
for i, src in enumerate(["Sources : Adam Mosseri / Instagram,", "Social Media Today, Blog du Modérateur"]):
    d.text(((W - d.textlength(src, font=fs)) / 2, H - 200 + i * 42), src, font=fs, fill=GREY)
footer(d, W, H, 8, TOTAL); slides.append(im)

for i, im in enumerate(slides, 1):
    im.save(f"slide-{i:02d}.jpg", quality=95)

# story de lancement 1080x1920
SW, SH = 1080, 1920
im = background(SW, SH, (0.5, 0.3)); d = ImageDraw.Draw(im); badge(d, SW, 260)
cx, cy = SW / 2, 620
d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=YEL); bolt(d, cx, cy, 210, BG)
y = rich_lines(d, 0, 840, [[("FLASH IA", WHITE)], [("EST EN LIGNE", YEL)]], f(F_TITLE, 110), 130, SW, True)
ft = f(F_BOLD, 54)
y = rich_lines(d, 0, y + 40, [[("L'actu IA & réseaux sociaux", WHITE)], [("en 30 secondes, chaque jour", WHITE)]], ft, 72, SW, True)
d.rounded_rectangle([170, y + 60, SW - 170, y + 170], radius=55, fill=YEL)
s = "ACTIVE LES NOTIFS 🔔".replace(" 🔔", "")
fs = f(F_TITLE, 48); d.text(((SW - d.textlength(s, font=fs)) / 2, y + 88), s, font=fs, fill=BG)
im.save("story-lancement.jpg", quality=95)

# planche de contrôle
sheet = Image.new("RGB", (270 * 4, 338 * 2 + 480), BG)
for i, sl in enumerate(slides):
    sheet.paste(sl.resize((270, 338)), ((i % 4) * 270, (i // 4) * 338))
sheet.paste(im.resize((270, 480)), (0, 676))
sheet.save("controle.png")
