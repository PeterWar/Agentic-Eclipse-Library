#!/usr/bin/env python3
"""Genera les dues figures de la pàgina, en SVG inline i amb tokens de color.

Escriu figA.svg i figB.svg a comu.work("apod") (abans: al cwd), d'on les llegeix munta.py.
"""
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu  # noqa: E402

os.chdir(comu.work("apod"))

# ─────────────────────────────────────────────────── Figura A: escala de moviments
FILES = [
    # (etiqueta, valor en ", categoria)
    ("Sky-Watcher mount jump (filter removed)", 2289.0, "rig"),
    ("Earth's rotation, over 103.7 s", 1507.0, "sky"),
    ("Atmospheric refraction, total", 349.0, "air"),
    ("iOptron tracking drift, over 103.7 s", 63.0, "rig"),
    ("Moon across the Sun, over 103.7 s", 61.2, "sky"),
    ("Aberration of starlight  ·  special relativity", 20.26, "rel"),
    ("Moon across the Sun, in one 10.3 s frame", 6.1, "sky"),
    ("Star trail inside one 10.3 s frame", 6.28, "rig"),
    ("Seeing, Vixen VSD90SS (FWHM)", 5.8, "air"),
    ("Atmospheric dispersion, red to blue", 3.08, "air"),
    ("Astrometric residual, 300 mm train", 2.27, "floor"),
    ("Light deflection at the solar limb  ·  general relativity", 1.7516, "rel"),
    ("Astrometric residual, VSD90SS train", 0.90, "floor"),
    ("Deflection at the innermost star, 2.16 solar radii", 0.811, "rel"),
    ("Deflection at the edge of the field, 13.7 solar radii", 0.128, "rel"),
]

W, LEFT, RIGHT = 940, 372, 872
AX0, AX1 = LEFT, RIGHT
LO, HI = 0.08, 4000.0
TOP, ROW = 62, 27.5
H = TOP + ROW * len(FILES) + 46


def xa(v):
    return AX0 + (math.log10(v) - math.log10(LO)) / (math.log10(HI) - math.log10(LO)) * (AX1 - AX0)


def fmt(v):
    if v >= 120:
        return f"{v/60:.1f}′"
    if v >= 10:
        return f"{v:.1f}″"
    if v >= 1:
        return f"{v:.2f}″"
    return f"{v:.3f}″"


CAT = {"sky": "var(--f-sky)", "air": "var(--f-air)", "rig": "var(--f-rig)",
       "rel": "var(--gold)", "floor": "var(--f-floor)"}

p = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
     f'role="img" aria-label="Angular size of every motion recorded during totality, '
     f'from 38 arcminutes down to 0.13 arcseconds" class="fig">']

# banda per sota del terra de mesura
p.append(f'<rect x="{xa(LO):.1f}" y="{TOP-26:.1f}" width="{xa(0.90)-xa(LO):.1f}" '
         f'height="{ROW*len(FILES)+14:.1f}" fill="var(--f-band)"/>')
p.append(f'<text x="{(xa(LO)+xa(0.90))/2:.1f}" y="{TOP-34:.1f}" text-anchor="middle" '
         f'class="fk">below every measurement floor</text>')

# graella
for d in (0.1, 1, 10, 100, 1000):
    x = xa(d)
    p.append(f'<line x1="{x:.1f}" y1="{TOP-26:.1f}" x2="{x:.1f}" y2="{TOP+ROW*len(FILES)-12:.1f}" '
             f'stroke="var(--f-grid)" stroke-width="1"/>')
    lab = f"{d:g}″"
    p.append(f'<text x="{x:.1f}" y="{TOP+ROW*len(FILES)+8:.1f}" text-anchor="middle" '
             f'class="fk">{lab}</text>')
# minor ticks
for dec in (-1, 0, 1, 2, 3):
    for m in range(2, 10):
        v = m * 10.0 ** dec
        if LO < v < HI:
            x = xa(v)
            p.append(f'<line x1="{x:.1f}" y1="{TOP+ROW*len(FILES)-12:.1f}" x2="{x:.1f}" '
                     f'y2="{TOP+ROW*len(FILES)-7:.1f}" stroke="var(--f-grid)" stroke-width="1"/>')

# terra de mesura del tren de 300 mm
xs = xa(2.27)
p.append(f'<line x1="{xs:.1f}" y1="{TOP-26:.1f}" x2="{xs:.1f}" y2="{TOP+ROW*len(FILES)-12:.1f}" '
         f'stroke="var(--f-floor)" stroke-width="1" stroke-dasharray="3 4"/>')

for i, (lab, v, cat) in enumerate(FILES):
    y = TOP + i * ROW
    col = CAT[cat]
    cls = "fl hi" if cat == "rel" else "fl"
    p.append(f'<text x="{LEFT-16}" y="{y+4}" text-anchor="end" class="{cls}">{lab}</text>')
    p.append(f'<line x1="{xa(LO):.1f}" y1="{y:.1f}" x2="{xa(v):.1f}" y2="{y:.1f}" '
             f'stroke="{col}" stroke-width="1" opacity=".38"/>')
    r = 5.0 if cat == "rel" else 3.6
    if cat == "floor":
        p.append(f'<circle cx="{xa(v):.1f}" cy="{y:.1f}" r="{r}" fill="none" '
                 f'stroke="{col}" stroke-width="1.6"/>')
    else:
        p.append(f'<circle cx="{xa(v):.1f}" cy="{y:.1f}" r="{r}" fill="{col}"/>')
    p.append(f'<text x="{RIGHT+14}" y="{y+4}" class="fv{" hi" if cat=="rel" else ""}">{fmt(v)}</text>')

p.append("</svg>")
open("figA.svg", "w").write("\n".join(p))
print("figA.svg", H)

# ────────────────────────────────────── Figura B: deflexió contra distància al Sol
SONY = [2.16, 2.66, 4.38, 5.58, 5.58, 5.75, 6.01, 6.17, 6.51, 6.92, 6.94, 7.01, 7.12,
        7.13, 7.24, 7.3, 8.18, 8.2, 8.24, 8.42, 8.47, 8.49, 8.68, 8.83, 9.07, 9.37,
        9.76, 10.5, 10.52, 11.24, 11.37, 11.39, 11.41, 12.02, 12.32, 12.88, 13.38, 13.67]
R6 = [2.16, 2.65, 3.04, 4.38, 4.4, 5.58, 5.74, 6.01, 6.16, 6.19, 6.82, 6.92, 6.94, 6.95,
      7.01, 7.12, 7.12, 7.51, 7.68, 7.9, 8.23, 8.46, 8.82, 9.56]

W2, H2 = 940, 560
PL, PR, PT, PB = 78, 232, 44, 84
RX0, RX1 = 1.55, 17.0
AY0, AY1 = 0.06, 3.2


def xb(r):
    return PL + (math.log10(r) - math.log10(RX0)) / (math.log10(RX1) - math.log10(RX0)) * (W2 - PL - PR)


def yb(a):
    return H2 - PB - (math.log10(a) - math.log10(AY0)) / (math.log10(AY1) - math.log10(AY0)) * (H2 - PT - PB)


q = [f'<svg viewBox="0 0 {W2} {H2}" xmlns="http://www.w3.org/2000/svg" role="img" '
     f'aria-label="Predicted light deflection against distance from the Sun, compared with '
     f'the measurement precision of the two telescopes" class="fig">']

# banda d'Eddington
q.append(f'<rect x="{xb(2):.1f}" y="{PT}" width="{xb(6)-xb(2):.1f}" height="{H2-PT-PB:.1f}" '
         f'fill="var(--f-band)"/>')
q.append(f'<text x="{(xb(2)+xb(6))/2:.1f}" y="{PT-14}" text-anchor="middle" class="fk">'
         f'stars measured in 1919</text>')

# graella
for r in (2, 3, 4, 6, 8, 10, 15):
    x = xb(r)
    q.append(f'<line x1="{x:.1f}" y1="{PT}" x2="{x:.1f}" y2="{H2-PB}" stroke="var(--f-grid)" stroke-width="1"/>')
    q.append(f'<text x="{x:.1f}" y="{H2-PB+22}" text-anchor="middle" class="fk">{r}</text>')
for a in (0.1, 0.2, 0.5, 1, 2):
    y = yb(a)
    q.append(f'<line x1="{PL}" y1="{y:.1f}" x2="{W2-PR}" y2="{y:.1f}" stroke="var(--f-grid)" stroke-width="1"/>')
    q.append(f'<text x="{PL-12}" y="{y+4:.1f}" text-anchor="end" class="fk">{a:g}″</text>')

# terres de mesura
for sig, nom, dy in ((1.61, "one star, 300 mm train", -9), (0.64, "one star, VSD90SS train", -9)):
    y = yb(sig)
    q.append(f'<line x1="{PL}" y1="{y:.1f}" x2="{W2-PR}" y2="{y:.1f}" stroke="var(--f-floor)" '
             f'stroke-width="1.4" stroke-dasharray="5 5"/>')
    q.append(f'<text x="{W2-PR-8}" y="{y+dy:.1f}" text-anchor="end" class="fk fo">'
             f'measurement noise, {nom}: {sig:.2f}″</text>')

# corbes
for amp, col, wdt, dash in ((1.7516, "var(--gold)", 2.6, ""),
                            (0.8758, "var(--f-newton)", 1.8, ' stroke-dasharray="7 5"')):
    pts = []
    r = RX0
    while r <= RX1:
        pts.append(f"{xb(r):.1f},{yb(amp/r):.1f}")
        r *= 1.04
    q.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" '
             f'stroke-width="{wdt}"{dash} stroke-linecap="round"/>')

# estrelles sobre la corba
for rs, col, rad in ((SONY, "var(--f-sony)", 3.4), (R6, "var(--f-r6)", 3.4)):
    for r in rs:
        q.append(f'<circle cx="{xb(r):.1f}" cy="{yb(1.7516/r):.1f}" r="{rad}" fill="{col}" opacity=".9"/>')

# etiquetes de corba, dins l'àrea del gràfic
q.append(f'<text x="{xb(4.6):.1f}" y="{yb(1.7516/4.6)-11:.1f}" class="fl hi">'
         f'Einstein — 1.75″ at the limb, falling as 1/r</text>')
q.append(f'<text x="{xb(4.6):.1f}" y="{yb(0.8758/4.6)+19:.1f}" class="fl fo">'
         f'Newton — half as much</text>')

# anotació de l'estrella més interna
q.append(f'<line x1="{xb(2.16):.1f}" y1="{yb(0.811)-10:.1f}" x2="{xb(2.16):.1f}" y2="{PT+34}" '
         f'stroke="var(--gold)" stroke-width="1" opacity=".55"/>')
q.append(f'<text x="{xb(2.16)+9:.1f}" y="{PT+30}" class="fl hi">HIP 46335  ·  0.81″</text>')
q.append(f'<text x="{xb(2.16)+9:.1f}" y="{PT+48}" class="fk">0.25 px  ·  0.38 px</text>')

# eix
q.append(f'<text x="{(PL+W2-PR)/2:.1f}" y="{H2-PB+52}" text-anchor="middle" class="fk">'
         f'distance from the centre of the Sun, in solar radii</text>')
q.append(f'<text x="{PL-12}" y="{PT-14}" text-anchor="start" class="fk">outward shift</text>')

# llegenda
lx, ly = W2 - PR + 18, PT + 96
q.append(f'<circle cx="{lx+5}" cy="{ly}" r="3.4" fill="var(--f-sony)"/>')
q.append(f'<text x="{lx+18}" y="{ly+4}" class="fk">38 stars, 300 mm</text>')
q.append(f'<circle cx="{lx+5}" cy="{ly+20}" r="3.4" fill="var(--f-r6)"/>')
q.append(f'<text x="{lx+18}" y="{ly+24}" class="fk">24 stars, VSD90SS</text>')

q.append("</svg>")
open("figB.svg", "w").write("\n".join(q))
print("figB.svg")
