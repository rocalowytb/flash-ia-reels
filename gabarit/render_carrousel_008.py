"""Carrousel n°8 (récap de la semaine du 9 au 15 novembre 2026) — charte Flash IA."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from charte import *

OUT_P = sys.argv[1]
W, H = 1080, 1350
TOTAL = 8
slides = []

# 1 — couverture
im = background(W, H); d = ImageDraw.Draw(im); badge(d, W)
y = rich_lines(d, 0, 280, [[("LA SEMAINE", WHITE)], [("IA EN", WHITE)], [("5 INFOS", YEL)]], f(F_TITLE, 120), 140, W, True)
ft = f(F_BOLD, 50)
y = rich_lines(d, 0, y + 50, [[("Nvidia perd son patron, ", WHITE)], [("ChatGPT paie à ta place", YEL), ("…", WHITE)]], ft, 68, W, True)
d.rounded_rectangle([W / 2 - 170, H - 260, W / 2 + 170, H - 180], radius=40, outline=YEL, width=4)
s = "SWIPE  →"; fs = f(F_TITLE, 40); d.text(((W - d.textlength(s, font=fs)) / 2, H - 247), s, font=fs, fill=YEL)
footer(d, W, H, 1, TOTAL); slides.append(im)

# 2 — deuxième accroche
im = background(W, H, (0.2, 0.85)); d = ImageDraw.Draw(im); badge(d, W)
y = rich_lines(d, 0, 300, [[("T'AS RATÉ", WHITE)], [("LA SEMAINE", WHITE)], [("DE L'IA ?", YEL)]], f(F_TITLE, 108), 128, W, True)
ft = f(F_BOLD, 48)
for i, l in enumerate(wrap(d, "5 infos vérifiées, 30 secondes de lecture. Du 9 au 15 novembre, voilà ce qui a vraiment compté.", ft, 860)):
    d.text(((W - d.textlength(l, font=ft)) / 2, y + 50 + i * 66), l, font=ft, fill=GREY)
footer(d, W, H, 2, TOTAL); slides.append(im)

points = [
    ("01", ["JENSEN HUANG", "QUITTE NVIDIA"], "après 33 ans à la tête du géant des puces",
     "Démission surprise le 12 novembre, sans raison officielle donnée par Nvidia. Colette Kress, sa directrice financière, assure l'intérim. L'action a chuté jusqu'à -14 % dans la journée.",
     "Nvidia fait tourner presque toute l'IA.", "Source : Nvidia, CNBC, Al Jazeera · 12 nov. 2026"),
    ("02", ["CHATGPT PAIE", "À TA PLACE"], "ChatGPT Wallet, lancé le 13 novembre",
     "Tu enregistres ta carte une fois, et l'agent IA fait tes achats. Il ne voit jamais ton numéro de carte, et tu valides chaque paiement (Face ID ou empreinte).",
     "Pour l'instant : abonnés Pro aux USA.", "Source : OpenAI, TechCrunch · 13 nov. 2026"),
    ("03", ["GEMINI 4", "HYDROGEN"], "le nouveau modèle rapide de Google",
     "2,5 fois plus rapide que Gemini 3.8 Flash, selon Google. Il arrive aussi pour les utilisateurs gratuits de l'appli Gemini, et se déploie dans la recherche Google partout dans le monde.",
     "Gratuit : ça vaut le coup de tester.", "Source : Google, VentureBeat · 12 nov. 2026"),
    ("04", ["CLAUDE", "FABLE 5.2"], "le nouveau modèle d'Anthropic",
     "Pensé pour les gros projets techniques : code, maths, ingénierie. Sa version Mythos 5.2, spécialisée en cybersécurité, reste réservée à des organisations vérifiées.",
     "En coulisses : Anthropic vise la Bourse.", "Source : Anthropic, CNBC · 9 nov. 2026"),
    ("05", ["L'IA DEVINE", "TON ÂGE"], "Instagram l'étend au monde entier",
     "Meta utilise l'IA pour repérer les ados qui mentent sur leur âge, même avec une date de naissance d'adulte. Ils basculent en compte ado, plus restreint. L'Europe est concernée.",
     "Un faux âge sur Insta ? Ça ne passe plus.", "Source : Meta, Al Jazeera, Dexerto · 9-11 nov. 2026"),
]
for k, (num, title, sub, body, tip, src) in enumerate(points):
    im = background(W, H, (0.85 if k % 2 else 0.15, 0.2)); d = ImageDraw.Draw(im); badge(d, W)
    d.text((80, 200), num, font=f(F_TITLE, 190), fill=YEL)
    tf = f(F_TITLE, 84)
    for t in title: assert d.textlength(t, font=tf) < W - 160, t
    y = rich_lines(d, 80, 430, [[(t, WHITE)] for t in title], tf, 100)
    sf = f(F_BOLD, 44); assert d.textlength(sub, font=sf) < W - 160, sub
    d.text((80, y + 6), sub, font=sf, fill=YEL)
    fb = f(F_SEMI, 42); yy = y + 100
    for l in wrap(d, body, fb, 920):
        d.text((80, yy), l, font=fb, fill=(220, 220, 228)); yy += 58
    assert yy < H - 320, (num, yy)
    fs = f(F_SEMI, 28); assert d.textlength(src, font=fs) < W - 160, src
    d.text((80, H - 300), src, font=fs, fill=GREY)
    assert d.textlength("→ " + tip, font=f(F_BOLD, 40)) < W - 230, tip
    d.rounded_rectangle([80, H - 250, W - 80, H - 150], radius=28, fill=DARK, outline=(60, 60, 70), width=2)
    d.text((115, H - 225), "→ " + tip, font=f(F_BOLD, 40), fill=WHITE)
    footer(d, W, H, 3 + k, TOTAL); slides.append(im)

# 8 — CTA
im = background(W, H, (0.5, 0.3)); d = ImageDraw.Draw(im)
cx, cy = W / 2, 330
d.ellipse([cx - 130, cy - 130, cx + 130, cy + 130], fill=YEL); bolt(d, cx, cy, 180, BG)
y = rich_lines(d, 0, 520, [[("ENREGISTRE-LE", YEL)], [("ET ENVOIE-LE À", WHITE)], [("UN POTE CURIEUX", WHITE)]], f(F_TITLE, 84), 104, W, True)
ft = f(F_BOLD, 48)
y = rich_lines(d, 0, y + 30, [[("Chaque dimanche : la semaine IA en 5 infos", WHITE)]], f(F_BOLD, 42), 60, W, True)
y = rich_lines(d, 0, y + 40, [[("Abonne-toi : ", GREY), ("@flash.ia_actu", YEL)]], ft, 64, W, True)
fs = f(F_SEMI, 30)
for i, s in enumerate(["Sources : Nvidia, OpenAI, Google, Anthropic, Meta,", "CNBC, Al Jazeera, TechCrunch, VentureBeat · nov. 2026"]):
    assert d.textlength(s, font=fs) < W - 100, s
    d.text(((W - d.textlength(s, font=fs)) / 2, H - 200 + i * 42), s, font=fs, fill=GREY)
footer(d, W, H, 8, TOTAL); slides.append(im)

for i, im in enumerate(slides, 1):
    im.save(f"{OUT_P}/slide-{i:02d}.jpg", quality=95)
