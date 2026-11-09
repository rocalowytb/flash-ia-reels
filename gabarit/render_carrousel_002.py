"""Carrousel n°2 (Instagram Features) + 4 stories du 4 novembre 2026 — charte Flash IA."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from charte import *

OUT_P = sys.argv[1]; OUT_S = sys.argv[2]
W, H = 1080, 1350
TOTAL = 8
slides = []

# 1 — couverture
im = background(W, H); d = ImageDraw.Draw(im); badge(d, W)
y = rich_lines(d, 0, 280, [[("INSTAGRAM", WHITE)], [("VEUT TES VIDÉOS", WHITE)], [("DE 90 MIN", YEL)]], f(F_TITLE, 104), 128, W, True)
ft = f(F_BOLD, 52)
y = rich_lines(d, 0, y + 50, [[("Features", YEL), (" : tout ce qu'il", WHITE)], [("faut savoir en 5 points", WHITE)]], ft, 70, W, True)
d.rounded_rectangle([W / 2 - 170, H - 260, W / 2 + 170, H - 180], radius=40, outline=YEL, width=4)
s = "SWIPE  →"; fs = f(F_TITLE, 40); d.text(((W - d.textlength(s, font=fs)) / 2, H - 247), s, font=fs, fill=YEL)
footer(d, W, H, 1, TOTAL); slides.append(im)

# 2 — deuxième accroche
im = background(W, H, (0.2, 0.85)); d = ImageDraw.Draw(im); badge(d, W)
y = rich_lines(d, 0, 300, [[("JUSQU'À", WHITE)], [("500 000 $", YEL)], [("POUR POSTER", WHITE)], [("SUR INSTA ?", WHITE)]], f(F_TITLE, 104), 126, W, True)
ft = f(F_BOLD, 48)
for i, l in enumerate(wrap(d, "C'est ce qu'Instagram proposerait à certains YouTubeurs, selon Business Insider. On t'explique.", ft, 860)):
    d.text(((W - d.textlength(l, font=ft)) / 2, y + 50 + i * 66), l, font=ft, fill=GREY)
footer(d, W, H, 2, TOTAL); slides.append(im)

points = [
    ("01", ["C'EST QUOI", "FEATURES ?"], "des vidéos jusqu'à 90 minutes",
     "Un nouveau format de vidéos longues, pensé pour l'horizontal. Tes Reels servent de bande-annonce : on clique et on regarde la vidéo entière sans quitter l'appli.",
     "Pense tes Reels comme des teasers."),
    ("02", ["QUI Y A", "ACCÈS ?"], "un test, pas encore pour tous",
     "Annoncé le 26 octobre, testé avec quelques créateurs aux États-Unis et au Brésil. Adam Mosseri parle d'un accès ouvert petit à petit.",
     "Pas encore en France : prépare-toi."),
    ("03", ["L'ARGENT SUR", "LA TABLE"], "des deals de 50 000 à 500 000 $",
     "Selon Business Insider, Instagram paie certains YouTubeurs pour publier aussi leurs vidéos longues sur Features. Meta confirme financer des créateurs, sans dire combien.",
     "Montants rapportés, pas confirmés."),
    ("04", ["ZÉRO PARTAGE", "DES PUBS"], "pour l'instant",
     "Contrairement à YouTube, aucun partage des revenus publicitaires n'est annoncé. Mosseri dit « explorer plusieurs options » pour payer les créateurs.",
     "Ne lâche pas YouTube trop vite."),
    ("05", ["CAP SUR", "TA TÉLÉ"], "Instagram attaque YouTube",
     "Mosseri était contre la vidéo longue : elle risquait de freiner les Reels. Il a changé d'avis, car Instagram veut s'installer sur les écrans de télé.",
     "Le format long revient en force."),
]
for k, (num, title, sub, body, tip) in enumerate(points):
    im = background(W, H, (0.85 if k % 2 else 0.15, 0.2)); d = ImageDraw.Draw(im); badge(d, W)
    d.text((80, 200), num, font=f(F_TITLE, 190), fill=YEL)
    y = rich_lines(d, 80, 430, [[(t, WHITE)] for t in title], f(F_TITLE, 84), 100)
    d.text((80, y + 6), sub, font=f(F_BOLD, 44), fill=YEL)
    fb = f(F_SEMI, 44); yy = y + 100
    for l in wrap(d, body, fb, 900):
        d.text((80, yy), l, font=fb, fill=(220, 220, 228)); yy += 62
    assert yy < H - 270, (num, yy)
    d.rounded_rectangle([80, H - 250, W - 80, H - 150], radius=28, fill=DARK, outline=(60, 60, 70), width=2)
    d.text((115, H - 225), "→ " + tip, font=f(F_BOLD, 40), fill=WHITE)
    footer(d, W, H, 3 + k, TOTAL); slides.append(im)

# 8 — CTA
im = background(W, H, (0.5, 0.3)); d = ImageDraw.Draw(im)
cx, cy = W / 2, 330
d.ellipse([cx - 130, cy - 130, cx + 130, cy + 130], fill=YEL); bolt(d, cx, cy, 180, BG)
y = rich_lines(d, 0, 520, [[("ENVOIE-LE", YEL)], [("À UN CRÉATEUR", WHITE)]], f(F_TITLE, 100), 124, W, True)
ft = f(F_BOLD, 48)
y = rich_lines(d, 0, y + 30, [[("et enregistre-le pour plus tard", WHITE)]], ft, 64, W, True)
y = rich_lines(d, 0, y + 50, [[("Abonne-toi : ", GREY), ("@flash.ia_actu", YEL)]], ft, 64, W, True)
fs = f(F_SEMI, 30)
for i, src in enumerate(["Sources : Instagram (A. Mosseri, T. Lyons), Business Insider,", "Mashable, The Next Web · 26 oct.–1er nov. 2026"]):
    d.text(((W - d.textlength(src, font=fs)) / 2, H - 200 + i * 42), src, font=fs, fill=GREY)
footer(d, W, H, 8, TOTAL); slides.append(im)

for i, im in enumerate(slides, 1):
    im.save(f"{OUT_P}/slide-{i:02d}.jpg", quality=95)

# ---------- stories 1080x1920 ----------
SW, SH = 1080, 1920
def src_line(d, txt):
    fs = f(F_SEMI, 32); d.text(((SW - d.textlength(txt, font=fs)) / 2, 1450), txt, font=fs, fill=GREY)
def chip(d, y, txt, fg=YEL, bg=DARK):
    fs = f(F_BOLD, 44); w = d.textlength(txt, font=fs)
    d.rounded_rectangle([(SW - w) / 2 - 34, y, (SW + w) / 2 + 34, y + 84], radius=42, fill=bg)
    d.text(((SW - w) / 2, y + 16), txt, font=fs, fill=fg)
stories = {}

# S1 — 9 h : info secondaire
im = background(SW, SH, (0.8, 0.25)); d = ImageDraw.Draw(im); badge(d, SW, 260)
chip(d, 440, "NOUVEAU · 3 NOVEMBRE")
y = rich_lines(d, 0, 590, [[("META BOOSTE", WHITE)], [("SON ASSISTANT", WHITE)], [("IA CRÉATEURS", YEL)]], f(F_TITLE, 96), 118, SW, True)
fb = f(F_BOLD, 50); yy = y + 50
for t in ["Alertes d'opportunités", "Aide à créer tes contenus", "Réponses automatiques"]:
    d.rounded_rectangle([170, yy, SW - 170, yy + 100], radius=28, fill=DARK, outline=(60, 60, 70), width=2)
    d.text((215, yy + 22), "→", font=fb, fill=YEL); d.text((290, yy + 22), t, font=fb, fill=WHITE); yy += 120
src_line(d, "Source : Meta for Creators · Social Media Today")
stories["story-1-matin"] = im

# S2 — 12 h 30 : renvoi vers le post
im = background(SW, SH, (0.2, 0.3)); d = ImageDraw.Draw(im); badge(d, SW, 260)
chip(d, 440, "NOUVEAU POST", BG, YEL)
y = rich_lines(d, 0, 600, [[("INSTAGRAM", WHITE)], [("VEUT TES VIDÉOS", WHITE)], [("DE 90 MIN", YEL)]], f(F_TITLE, 94), 116, SW, True)
fb = f(F_BOLD, 52)
y = rich_lines(d, 0, y + 50, [[("Les 5 points à connaître", WHITE)], [("sur Features", YEL)]], fb, 70, SW, True)
d.rounded_rectangle([200, y + 70, SW - 200, y + 180], radius=55, outline=YEL, width=4)
s = "VA VOIR LE POST"; fs = f(F_TITLE, 46); d.text(((SW - d.textlength(s, font=fs)) / 2, y + 98), s, font=fs, fill=YEL)
stories["story-2-post"] = im

# S3 — 17 h 30 : teasing du Reel
im = background(SW, SH, (0.5, 0.2)); d = ImageDraw.Draw(im); badge(d, SW, 260)
chip(d, 440, "REEL À 18 H")
y = rich_lines(d, 0, 600, [[("UNE IA QUI", WHITE)], [("AIDE À CRÉER", WHITE)], [("LA SUIVANTE ?", YEL)]], f(F_TITLE, 96), 118, SW, True)
fb = f(F_BOLD, 52)
y = rich_lines(d, 0, y + 50, [[("Anthropic l'écrit", WHITE)], [("noir sur blanc", YEL)]], fb, 70, SW, True)
fs = f(F_TITLE, 60); s = "DANS 30 MIN"; d.text(((SW - d.textlength(s, font=fs)) / 2, y + 80), s, font=fs, fill=GREY)
stories["story-3-reel"] = im

# S4 — 21 h : sondage
im = background(SW, SH, (0.5, 0.75)); d = ImageDraw.Draw(im); badge(d, SW, 260)
y = rich_lines(d, 0, 440, [[("ET TOI ?", WHITE)]], f(F_TITLE, 140), 150, SW, True)
fb = f(F_BOLD, 54)
y = rich_lines(d, 0, y + 30, [[("Une IA qui aide à", WHITE)], [("créer la suivante…", WHITE)]], fb, 72, SW, True)
for i, (t, hl) in enumerate([("ÇA ME RASSURE", True), ("ÇA M'INQUIÈTE", False)]):
    yy = y + 70 + i * 190
    d.rounded_rectangle([150, yy, SW - 150, yy + 150], radius=40, fill=YEL if hl else DARK, outline=YEL, width=4)
    ft = f(F_TITLE, 64); d.text(((SW - d.textlength(t, font=ft)) / 2, yy + 36), t, font=ft, fill=BG if hl else WHITE)
fs = f(F_BOLD, 48); s = "Réponds-moi en DM"; d.text(((SW - d.textlength(s, font=fs)) / 2, yy + 200), s, font=fs, fill=GREY)
src_line(d, "Source : dépôt SEC d'Anthropic (S-1/A), 2 nov. 2026")
stories["story-4-sondage"] = im
for k, im in stories.items():
    im.save(f"{OUT_S}/{k}.jpg", quality=95)

sheet = Image.new("RGB", (270 * 4, 338 * 2 + 480), BG)
for i, sl in enumerate(slides):
    sheet.paste(sl.resize((270, 338)), ((i % 4) * 270, (i // 4) * 338))
for i, im in enumerate(stories.values()):
    sheet.paste(im.resize((270, 480)), (i * 270, 676))
sheet.save(sys.argv[3])
