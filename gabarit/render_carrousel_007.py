"""Carrousel n°7 (LinkedIn et les posts IA) + 4 stories du 9 novembre 2026 — charte Flash IA."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from charte import *

OUT_P = sys.argv[1]; OUT_S = sys.argv[2]
W, H = 1080, 1350
TOTAL = 8
slides = []

# 1 — couverture
im = background(W, H); d = ImageDraw.Draw(im); badge(d, W)
y = rich_lines(d, 0, 280, [[("LINKEDIN", WHITE)], [("ENTERRE", WHITE)], [("TES POSTS IA", YEL)]], f(F_TITLE, 108), 130, W, True)
ft = f(F_BOLD, 52)
y = rich_lines(d, 0, y + 50, [[("-40 % de vues ", YEL), ("pour les posts", WHITE)], [("« génériques ». Voilà comment passer.", WHITE)]], ft, 70, W, True)
d.rounded_rectangle([W / 2 - 170, H - 260, W / 2 + 170, H - 180], radius=40, outline=YEL, width=4)
s = "SWIPE  →"; fs = f(F_TITLE, 40); d.text(((W - d.textlength(s, font=fs)) / 2, H - 247), s, font=fs, fill=YEL)
footer(d, W, H, 1, TOTAL); slides.append(im)

# 2 — deuxième accroche
im = background(W, H, (0.2, 0.85)); d = ImageDraw.Draw(im); badge(d, W)
y = rich_lines(d, 0, 300, [[("TON POST", WHITE)], [("SENT LE", WHITE)], [("CHATGPT ?", YEL)]], f(F_TITLE, 108), 128, W, True)
ft = f(F_BOLD, 48)
for i, l in enumerate(wrap(d, "LinkedIn a un détecteur, un bouton de signalement et des chiffres. Les 5 choses à savoir avant ton prochain post.", ft, 860)):
    d.text(((W - d.textlength(l, font=ft)) / 2, y + 50 + i * 66), l, font=ft, fill=GREY)
footer(d, W, H, 2, TOTAL); slides.append(im)

points = [
    ("01", ["-40 %", "DE VUES"], "le chiffre officiel de LinkedIn",
     "Les posts classés « AI slop » (génériques, répétitifs, sans vraie info) perdent 40 % de vues, selon le directeur produit de LinkedIn.",
     "Pas supprimés : juste moins poussés."),
    ("02", ["UN DÉTECTEUR", "SUR CHAQUE POST"], "94 % de précision, selon LinkedIn",
     "Dès qu'un post sort de ton réseau direct, des classifieurs l'analysent. Les cas difficiles passent par des humains.",
     "Reformuler ne suffit pas : il juge le fond."),
    ("03", ["UN BOUTON", "« AI SLOP »"], "caché dans le menu de chaque post",
     "Depuis cet été, tout le monde peut signaler un post qui « ressemble à de la bouillie IA ». Plus d'un million de clics en 3 semaines.",
     "Bientôt : une notif si on te signale."),
    ("04", ["L'IA N'EST PAS", "INTERDITE"], "c'est le générique qui coule",
     "LinkedIn le dit : écrire avec l'IA, c'est OK. Ce qui perd en portée, c'est le post qu'on aurait pu écrire sur n'importe qui.",
     "L'IA pour structurer, pas pour penser."),
    ("05", ["LA RECETTE", "QUI PASSE"], "du vécu, des chiffres, un avis",
     "Un vrai projet, une contrainte, un résultat chiffré, une opinion assumée. Ton expérience, l'IA ne peut pas l'inventer.",
     "Le test : toi seul pouvais l'écrire ?"),
]
for k, (num, title, sub, body, tip) in enumerate(points):
    im = background(W, H, (0.85 if k % 2 else 0.15, 0.2)); d = ImageDraw.Draw(im); badge(d, W)
    d.text((80, 200), num, font=f(F_TITLE, 190), fill=YEL)
    tf = f(F_TITLE, 84)
    for t in title: assert d.textlength(t, font=tf) < W - 160, t
    y = rich_lines(d, 80, 430, [[(t, WHITE)] for t in title], tf, 100)
    d.text((80, y + 6), sub, font=f(F_BOLD, 44), fill=YEL)
    fb = f(F_SEMI, 44); yy = y + 100
    for l in wrap(d, body, fb, 900):
        d.text((80, yy), l, font=fb, fill=(220, 220, 228)); yy += 62
    assert yy < H - 270, (num, yy)
    assert d.textlength("→ " + tip, font=f(F_BOLD, 40)) < W - 230, tip
    d.rounded_rectangle([80, H - 250, W - 80, H - 150], radius=28, fill=DARK, outline=(60, 60, 70), width=2)
    d.text((115, H - 225), "→ " + tip, font=f(F_BOLD, 40), fill=WHITE)
    footer(d, W, H, 3 + k, TOTAL); slides.append(im)

# 8 — CTA
im = background(W, H, (0.5, 0.3)); d = ImageDraw.Draw(im)
cx, cy = W / 2, 330
d.ellipse([cx - 130, cy - 130, cx + 130, cy + 130], fill=YEL); bolt(d, cx, cy, 180, BG)
y = rich_lines(d, 0, 520, [[("ENVOIE-LE", YEL)], [("AU POTE QUI POSTE", WHITE)], [("AVEC CHATGPT", WHITE)]], f(F_TITLE, 84), 104, W, True)
ft = f(F_BOLD, 48)
y = rich_lines(d, 0, y + 30, [[("et enregistre-le avant ton prochain post", WHITE)]], ft, 64, W, True)
y = rich_lines(d, 0, y + 40, [[("Abonne-toi : ", GREY), ("@flash.ia_actu", YEL)]], ft, 64, W, True)
fs = f(F_SEMI, 30)
for i, src in enumerate(["Sources : LinkedIn (Tim Jurka, VP Engineering),", "CNN, SocialDay · oct.-nov. 2026"]):
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
chip(d, 440, "GOOGLE · GEMINI OMNI 1.2")
y = rich_lines(d, 0, 590, [[("DES VIDÉOS IA", WHITE)], [("DE 15 SECONDES", YEL)], [("EN UN PROMPT", WHITE)]], f(F_TITLE, 80), 104, SW, True)
fb = f(F_BOLD, 46); yy = y + 50
for t in ["Durée au choix, 3 à 15 s", "Tu corriges en discutant", "Dans Google Vids et Flow"]:
    assert d.textlength(t, font=fb) < SW - 380, t
    d.rounded_rectangle([150, yy, SW - 150, yy + 100], radius=28, fill=DARK, outline=(60, 60, 70), width=2)
    d.text((195, yy + 24), "→", font=fb, fill=YEL); d.text((265, yy + 24), t, font=fb, fill=WHITE); yy += 120
src_line(d, "Source : Google DeepMind, 5 nov. 2026")
stories["story-1-matin"] = im

# S2 — 12 h 30 : renvoi vers le post
im = background(SW, SH, (0.2, 0.3)); d = ImageDraw.Draw(im); badge(d, SW, 260)
chip(d, 440, "NOUVEAU POST", BG, YEL)
y = rich_lines(d, 0, 600, [[("LINKEDIN", WHITE)], [("ENTERRE TES", WHITE)], [("POSTS IA", YEL)]], f(F_TITLE, 94), 116, SW, True)
fb = f(F_BOLD, 52)
y = rich_lines(d, 0, y + 50, [[("-40 % de vues pour le générique", WHITE)], [("la recette pour passer", YEL)]], fb, 70, SW, True)
d.rounded_rectangle([200, y + 70, SW - 200, y + 180], radius=55, outline=YEL, width=4)
s = "VA VOIR LE POST"; fs = f(F_TITLE, 46); d.text(((SW - d.textlength(s, font=fs)) / 2, y + 98), s, font=fs, fill=YEL)
stories["story-2-post"] = im

# S3 — 17 h 30 : teasing du Reel de 18 h
im = background(SW, SH, (0.5, 0.2)); d = ImageDraw.Draw(im); badge(d, SW, 260)
chip(d, 440, "REEL À 18 H")
y = rich_lines(d, 0, 600, [[("UNE VILLE", WHITE)], [("INTERDIT LA", WHITE)], [("SUPER-IA", YEL)]], f(F_TITLE, 100), 122, SW, True)
fb = f(F_BOLD, 52)
y = rich_lines(d, 0, y + 50, [[("Amendes, procureur…", WHITE)], [("et ce n'est pas une blague", YEL)]], fb, 70, SW, True)
fs = f(F_TITLE, 60); s = "DANS 30 MIN"; d.text(((SW - d.textlength(s, font=fs)) / 2, y + 80), s, font=fs, fill=GREY)
stories["story-3-reel"] = im

# S4 — 21 h : sondage
im = background(SW, SH, (0.5, 0.75)); d = ImageDraw.Draw(im); badge(d, SW, 260)
y = rich_lines(d, 0, 440, [[("ET TOI ?", WHITE)]], f(F_TITLE, 140), 150, SW, True)
fb = f(F_BOLD, 54)
y = rich_lines(d, 0, y + 30, [[("Interdire la superintelligence", WHITE)], [("avant qu'elle existe ?", WHITE)]], fb, 72, SW, True)
for i, (t, hl) in enumerate([("OUI, BONNE IDÉE", False), ("NON, TROP TÔT", True)]):
    yy = y + 70 + i * 190
    d.rounded_rectangle([150, yy, SW - 150, yy + 150], radius=40, fill=YEL if hl else DARK, outline=YEL, width=4)
    ft = f(F_TITLE, 64); assert d.textlength(t, font=ft) < SW - 340, t
    d.text(((SW - d.textlength(t, font=ft)) / 2, yy + 36), t, font=ft, fill=BG if hl else WHITE)
fs = f(F_BOLD, 48); s = "Réponds-moi en DM"; d.text(((SW - d.textlength(s, font=fs)) / 2, yy + 200), s, font=fs, fill=GREY)
src_line(d, "Source : Indiana Daily Student, 4 nov. 2026")
stories["story-4-sondage"] = im
for k, im in stories.items():
    im.save(f"{OUT_S}/{k}.jpg", quality=95)

sheet = Image.new("RGB", (270 * 5, 338 * 2 + 480), BG)
for i, sl in enumerate(slides):
    sheet.paste(sl.resize((270, 338)), ((i % 5) * 270, (i // 5) * 338))
for i, im in enumerate(stories.values()):
    sheet.paste(im.resize((270, 480)), (i * 270, 676))
sheet.save(sys.argv[3])
