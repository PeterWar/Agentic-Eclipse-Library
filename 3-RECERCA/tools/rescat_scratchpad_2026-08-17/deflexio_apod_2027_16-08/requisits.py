#!/usr/bin/env python3
"""Què caldria per detectar la deflexió gravitatòria de manera significativa.

Model paramètric exacte, calibrat sobre les dades del 12-08-2026.
"""
import csv
import math
import numpy as np

R_SOL = 946.66          # ″, radi solar aparent el 12-08-2026
ALPHA = 1.7516          # ″, deflexió al limbe (relativitat general)

# ─────────────────────────────────────────── 1. el model, calibrat sobre el 2026
BASE = "/Users/USUARI/Desktop/Eclipse 2026/Estrelles"
TRENS = {
    "Sony 300 mm": dict(csv=f"{BASE}/estrelles_sony.csv", esc=3.2020, sol=(3894.7, 2768.7),
                        sig=1.61, camp=(7.14, 4.77)),
    "Vixen VSD90SS": dict(csv=f"{BASE}/estrelles_r6.csv", esc=2.1495, sol=(3570.8, 2267.1),
                          sig=0.64, camp=(4.17, 2.78)),
}


def radis(cfg):
    out = []
    for d in csv.DictReader(open(cfg["csv"])):
        dx = (float(d["x"]) - cfg["sol"][0]) * cfg["esc"]
        dy = (float(d["y"]) - cfg["sol"][1]) * cfg["esc"]
        out.append((math.hypot(dx, dy) / R_SOL, math.atan2(dy, dx)))
    return out


def sigma_eps(rt, sigma_star, npar=4):
    """σ(ε) d'un ajust conjunt placa + deflexió. rt = [(r en R☉, angle)]."""
    n = len(rt)
    A = np.zeros((2 * n, npar + 1))
    for i, (r, th) in enumerate(rt):
        x, y = r * math.cos(th), r * math.sin(th)      # en R☉, escala irrellevant
        A[2*i, 0] = 1.0
        A[2*i+1, 1] = 1.0
        A[2*i, 2] = -y;  A[2*i+1, 2] = x               # rotació
        A[2*i, 3] = x;   A[2*i+1, 3] = y               # escala
        if npar == 6:
            A[2*i, 4] = x;  A[2*i+1, 4] = -y
            A[2*i, 5] = y;  A[2*i+1, 5] = x
        a = ALPHA / r
        A[2*i, npar] = a * math.cos(th)
        A[2*i+1, npar] = a * math.sin(th)
    return math.sqrt(np.linalg.inv(A.T @ A)[npar, npar]) * sigma_star


print("=" * 76)
print("1. EL MODEL, CONTRASTAT AMB EL QUE ES VA MESURAR EL 2026")
print("=" * 76)
tot_inv = 0.0
for nom, cfg in TRENS.items():
    rt = radis(cfg)
    rs = sorted(r for r, _ in rt)
    se = sigma_eps(rt, cfg["sig"])
    # informació "ingènua", sense el model de placa
    info = sum((ALPHA / r) ** 2 for r in rs)
    naive = cfg["sig"] / math.sqrt(info)
    area = cfg["camp"][0] * cfg["camp"][1] / (R_SOL / 3600.0) ** 2   # en R☉²
    dens = len(rs) / area
    # llei logarítmica: Σα² = 2·π·n·α²·ln(rmax/rmin)
    llei = 2 * math.pi * dens * ALPHA ** 2 * math.log(rs[-1] / rs[0])
    print(f"\n  {nom}")
    print(f"    {len(rs)} estrelles, r = {rs[0]:.2f} a {rs[-1]:.2f} R☉, σ/estrella {cfg['sig']:.2f}″")
    print(f"    densitat {dens:.4f} estrelles per R☉²  ({len(rs)/ (cfg['camp'][0]*cfg['camp'][1]):.2f} per grau²)")
    print(f"    Σα² mesurat {info:.2f}  ·  llei logarítmica {llei:.2f}  → concorden a {100*(llei/info-1):+.0f} %")
    print(f"    σ(ε) sense model de placa {naive:.3f}  ·  amb model {se:.3f}"
          f"  → el model costa ×{se/naive:.2f}")
    tot_inv += 1 / se ** 2
print(f"\n  COMBINAT: σ(ε) = {1/math.sqrt(tot_inv):.3f}  →  GR a {math.sqrt(tot_inv):.1f}σ")

# ────────────────────────────── 2. el preu de la degeneració segons la cobertura
print("\n" + "=" * 76)
print("2. EL PREU DE LA DEGENERACIÓ ESCALA-DEFLEXIÓ, SEGONS LA COBERTURA RADIAL")
print("=" * 76)
print("  (camp ple d'estrelles distribuïdes a l'atzar entre rmin i rmax)")
print(f"\n  {'rmin':>5} {'rmax':>5} {'penalització':>13}")
rng = np.random.default_rng(7)
for rmin, rmax in ((2.2, 13.7), (2.2, 8.0), (1.5, 13.7), (1.2, 15.0), (1.1, 20.0),
                   (3.0, 6.0), (2.0, 4.5)):
    pen = []
    for _ in range(40):
        n = 200
        r = np.sqrt(rng.uniform(rmin**2, rmax**2, n))       # densitat uniforme al pla
        th = rng.uniform(0, 2*math.pi, n)
        rt = list(zip(r, th))
        info = sum((ALPHA/x)**2 for x in r)
        pen.append(sigma_eps(rt, 1.0) / (1.0/math.sqrt(info)))
    print(f"  {rmin:5.1f} {rmax:5.1f} {np.mean(pen):12.2f}×")

# ──────────────────────────────────────────── 3. què cal per a cada nivell
print("\n" + "=" * 76)
print("3. QUANT CAL MILLORAR")
print("=" * 76)
s0 = 1 / math.sqrt(tot_inv)
objectius = [
    ("detectar la deflexió a 3σ", 1.0/3),
    ("distingir Einstein de Newton a 3σ", 0.5/3),
    ("el ±10 % d'Eddington (i Einstein contra Newton a 5σ)", 0.10),
    ("el ±3 % de Bruns 2017", 0.03),
    ("el ±1 %", 0.01),
]
print(f"\n  Punt de partida 2026: σ(ε) = {s0:.3f}\n")
print(f"  {'objectiu':<54} {'σ(ε)':>7} {'factor':>8}")
print("  " + "-" * 71)
for nom, obj in objectius:
    print(f"  {nom:<54} {obj:7.3f} {s0/obj:7.1f}×")

# ─────────────────────────── 4. d'on pot sortir cada factor
print("\n" + "=" * 76)
print("4. D'ON POT SORTIR CADA FACTOR")
print("=" * 76)
print("""
  σ(ε) = D · σ★ / [ α · sqrt( 2π·n·ln(rmax/rmin) ) ]

     σ★  error de posició d'UNA estrella      → lineal
     n   estrelles per R☉² (fondària)         → arrel
     ln  cobertura radial                     → arrel del logaritme
     D   penalització del model de placa      → depèn de la cobertura
""")
# palanca 1: sigma per estrella
print("  PALANCA 1 — σ per estrella (lineal, la que mana)")
for s, q in ((0.64, "2026, tren Vixen"), (0.30, "amb camp de comparació i bon focus"),
             (0.15, "amb sensor mono ben mostrejat i Gaia"), (0.08, "nivell Bruns 2017"),
             (0.05, "el millor documentat en eclipsi")):
    print(f"     {s:5.2f}″  ×{0.64/s:5.2f} respecte del 2026   {q}")
# palanca 2: fondaria
print("\n  PALANCA 2 — fondària (arrel; ~×2,7 estrelles per magnitud a alta latitud galàctica)")
for dm in (0, 1, 2, 3, 4):
    print(f"     +{dm} mag  ×{math.sqrt(2.7**dm):5.2f}   densitat ×{2.7**dm:5.1f}")
# palanca 3: cobertura radial
print("\n  PALANCA 3 — cobertura radial (arrel del logaritme; poca cosa)")
base = math.log(13.7/2.16)
for rmin, rmax in ((2.16, 13.7), (1.5, 13.7), (1.2, 15.0), (1.1, 20.0)):
    print(f"     r = {rmin:.1f}–{rmax:4.1f} R☉  ×{math.sqrt(math.log(rmax/rmin)/base):5.2f}")

# ─────────────────────────── 5. escenaris per al 2027
print("\n" + "=" * 76)
print("5. ESCENARIS PER AL 2027")
print("=" * 76)


def escenari(nom, sigma, dens_deg2, rmin, rmax, npar=4, mostra=True):
    dens = dens_deg2 * (R_SOL / 3600.0) ** 2          # per R☉²
    # mostra sintètica del camp
    rng2 = np.random.default_rng(11)
    area = math.pi * (rmax**2 - rmin**2)
    n = max(4, int(round(dens * area)))
    r = np.sqrt(rng2.uniform(rmin**2, rmax**2, n))
    th = rng2.uniform(0, 2*math.pi, n)
    se = sigma_eps(list(zip(r, th)), sigma, npar)
    if mostra:
        print(f"  {nom:<44} {n:4d} estr. {sigma:5.2f}″  σ(ε)={se:6.3f}  "
              f"GR {1/se:5.1f}σ  E-vs-N {0.5/se:5.1f}σ")
    return se


print(f"\n  {'escenari':<44} {'N':>4} {'':6} {'σ/estr':>6}")
print("  " + "-" * 74)
escenari("2026 tal com va anar (Vixen sol)", 0.64, 24/11.6, 2.16, 9.6)
escenari("2027, mateix equip, res canviat", 0.64, 24/11.6, 2.2, 9.6)
escenari("+ Sol alt: seeing 2,5″, cel 3 mag més fosc", 0.35, 6.0, 1.6, 9.6)
escenari("+ camp de comparació nocturn", 0.20, 6.0, 1.6, 9.6)
escenari("+ Gaia DR3 en lloc de Tycho-2", 0.17, 6.0, 1.6, 9.6)
escenari("+ sensor mono ben mostrejat", 0.12, 12.0, 1.4, 9.6)
escenari("+ camp més ample (7°) amb la mateixa escala", 0.12, 12.0, 1.4, 16.0)
escenari("tot això i el doble d'exposicions", 0.09, 16.0, 1.3, 16.0)

print("\n  Sensibilitat: quin σ per estrella cal per a cada objectiu,")
print("  amb un camp raonable de 2027 (12 estrelles/grau², r = 1,4 a 16 R☉):")
s_ref = escenari("", 1.0, 12.0, 1.4, 16.0, mostra=False)   # σ(ε) per σ★ = 1″
print()
for nom, obj in objectius:
    print(f"     {nom:<54} σ★ ≤ {obj/s_ref:5.3f}″")
