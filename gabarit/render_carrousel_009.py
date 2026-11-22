"""Carrousel n°9 (récap de la semaine du 16 au 21 novembre 2026) — charte Flash IA."""
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
y = rich_lines(d, 0, y + 50, [[("Anthropic entre en Bourse, ", WHITE)], [("GPT-6.2 contre Gemini 4", YEL), ("…", WHITE)]], ft, 68, W, True)
d.rounded_rectangle([W / 2 - 170, H - 260, W / 2 + 170, H - 180], radius=40, outline=YEL, width=4)
s = "SWIPE  →"; fs = f(F_TITLE, 40); d.text(((W - d.textlength(s, font=fs)) / 2, H - 247), s, font=fs, fill=YEL)
footer(d, W, H, 1, TOTAL); slides.append(im)

# 2 — deuxième accroche
im = background(W, H, (0.2, 0.85)); d = ImageDraw.Draw(im); badge(d, W)
y = rich_lines(d, 0, 300, [[("T'AS RATÉ", WHITE)], [("LA SEMAINE", WHITE)], [("DE L'IA ?", YEL)]], f(F_TITLE, 108), 128, W, True)
ft = f(F_BOLD, 48)
for i, l in enumerate(wrap(d, "5 infos vérifiées, 30 secondes de lecture. Du 16 au 21 novembre, voilà ce qui a vraiment compté.", ft, 860)):
    d.text(((W - d.textlength(l, font=ft)) / 2, y + 50 + i * 66), l, font=ft, fill=GREY)
footer(d, W, H, 2, TOTAL); slides.append(im)

points = [
    ("01", ["ANTHROPIC", "EN BOURSE"], "un record mondial, devant SpaceX",
     "Le créateur de Claude est coté au Nasdaq depuis le 19 novembre : 81,3 milliards de dollars levés, du jamais vu. L'action, vendue 83 $, a ouvert à 111,50 $ (+34 %).",
     "Son code en Bourse : ANT.", "Source : Reuters, Al Jazeera, NPR · 19 nov. 2026"),
    ("02", ["GPT-6.2", "ASTRA ET SOL"], "les deux nouveaux modèles d'OpenAI",
     "Ils arrivent dans ChatGPT pour les abonnés Plus, Pro, Entreprise et Edu. OpenAI les classe au niveau de risque « critique » en cybersécurité, avec des garde-fous renforcés.",
     "Réservé aux abonnés payants.", "Source : OpenAI, PYMNTS · 17 nov. 2026"),
    ("03", ["GEMINI 4", "NEON"], "la riposte de Google, le lendemain",
     "Il remplace Argon pour les abonnés Google AI Pro : écriture plus claire, meilleure lecture des PDF, tableurs et photos. Score de 61 à l'indice Artificial Analysis, devant GPT-6.2 Sol (57).",
     "Pas de Neon dans l'appli gratuite.", "Source : Google, Notebookcheck, PYMNTS · 18 nov. 2026"),
    ("04", ["L'AGENT IA", "DE META DÉRAPE"], "Muse mélange les conversations",
     "Selon Reuters, des salariés de Meta ont reçu des messages qui ne leur étaient pas destinés : soldes bancaires d'inconnus, commandes jamais passées. Meta évoque des incidents isolés.",
     "Agent IA : limite ses accès au minimum.", "Source : Reuters · 18 nov. 2026"),
    ("05", ["ON VOLE", "TON REEL ?"], "Instagram t'envoie maintenant une alerte",
     "Le nouvel outil « protection du contenu » repère les comptes qui republient ta vidéo. Tu peux la bloquer sur Instagram et Facebook, ou ajouter une étiquette « original de ».",
     "Créateur ? Active-le dès qu'il arrive.", "Source : Instagram, TechCrunch · 17 nov. 2026"),
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
for i, s in enumerate(["Sources : Reuters, Al Jazeera, OpenAI, Google, Instagram,", "PYMNTS, Notebookcheck, TechCrunch · nov. 2026"]):
    assert d.textlength(s, font=fs) < W - 100, s
    d.text(((W - d.textlength(s, font=fs)) / 2, H - 200 + i * 42), s, font=fs, fill=GREY)
footer(d, W, H, 8, TOTAL); slides.append(im)

for i, im in enumerate(slides, 1):
    im.save(f"{OUT_P}/slide-{i:02d}.jpg", quality=95)
