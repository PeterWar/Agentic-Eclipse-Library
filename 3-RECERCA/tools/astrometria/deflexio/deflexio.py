#!/usr/bin/env python3
"""Predicció GR i sensibilitat Fisher per a l'eclipsi del 12-08-2026.

Per a cada estrella detectada als dos trens calcula el desplaçament que prediu
la relativitat general i la sensibilitat que implicaria el residu de placa.
No ajusta epsilon a posicions de catàleg sense deflexió i no produeix una
detecció mesurada.
"""
import csv
import math
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu  # noqa: E402

BASE = str(comu.out())      # estrelles_sony.csv / estrelles_r6.csv (fusiona_csv.py)

# Solució de placa (research/75 §5.1)
TRENS = {
    "Sony A7RIIIA + FE 300 GM": dict(
        csv=f"{BASE}/estrelles_sony.csv",
        escala=3.2020,          # ″/px
        sol=(3894.7, 2768.7),   # px
        resid_rms_px=0.71,
        resid_med_px=0.54,
    ),
    "Vixen VSD90SS + R6 III": dict(
        csv=f"{BASE}/estrelles_r6.csv",
        escala=2.1495,
        sol=(3570.8, 2267.1),
        resid_rms_px=0.42,
        resid_med_px=0.32,
    ),
}

# ---------------------------------------------------------------- efemèrides
from skyfield.api import load, wgs84

ts = load.timescale()
eph = comu.efemeride()      # DE440s de la cau, mai un load() relatiu
# MIRADOR FINAL 2
lloc = wgs84.latlon(42.299407, -5.02503, elevation_m=798)
obs = eph["earth"] + lloc
# mig de la totalitat: C2 18:28:46 UTC + ~52 s
t = ts.utc(2026, 8, 12, 18, 29, 38)

sol = obs.at(t).observe(eph["sun"]).apparent()
dist_au = sol.distance().au
R_SOL_KM = 695700.0
AU_KM = 149597870.7
R_sol_arcsec = math.degrees(math.asin(R_SOL_KM / (dist_au * AU_KM))) * 3600.0
alt, az, _ = sol.altaz()

print("=" * 78)
print("GEOMETRIA DEL MOMENT (skyfield + DE440s, MIRADOR FINAL 2)")
print("=" * 78)
print(f"  Instant                 : {t.utc_strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"  Distància Terra-Sol     : {dist_au:.6f} UA")
print(f"  Radi solar aparent      : {R_sol_arcsec:.2f}″  ({R_sol_arcsec/60:.3f}′)")
print(f"  Altura del Sol          : {alt.degrees:.2f}°   azimut {az.degrees:.1f}°")

# Constant de deflexió: 4GM/c^2 R = 1.75087″ al limbe (valor exacte)
G = 6.67430e-11
M_SOL = 1.98892e30
C = 299792458.0
alpha_limbe = 4 * G * M_SOL / (C ** 2 * R_SOL_KM * 1000)  # rad
alpha_limbe_as = math.degrees(alpha_limbe) * 3600
print(f"  Deflexió GR al limbe    : {alpha_limbe_as:.4f}″   (Newton: {alpha_limbe_as/2:.4f}″)")
print()


def llegeix(path):
    files = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            files.append(row)
    return files


resultats = {}

for nom, cfg in TRENS.items():
    rows = llegeix(cfg["csv"])
    esc = cfg["escala"]
    sx, sy = cfg["sol"]
    dades = []
    for r in rows:
        x, y = float(r["x"]), float(r["y"])
        dx, dy = (x - sx) * esc, (y - sy) * esc      # ″ respecte del centre del Sol
        rad = math.hypot(dx, dy)
        r_sol = rad / R_sol_arcsec                    # en radis solars
        alpha = alpha_limbe_as / r_sol                # ″ de deflexió GR
        dades.append(dict(id=r["id"], nom=r["nom"], dx=dx, dy=dy, r=rad,
                          r_sol=r_sol, alpha=alpha, alpha_px=alpha / esc))
    dades.sort(key=lambda d: d["r_sol"])
    resultats[nom] = (cfg, dades)

    print("=" * 78)
    print(nom.upper())
    print("=" * 78)
    print(f"  {len(dades)} estrelles · escala {esc}″/px · residu rms "
          f"{cfg['resid_rms_px']} px = {cfg['resid_rms_px']*esc:.2f}″")
    print()
    print(f"  {'id':<6} {'estrella':<34} {'r/R☉':>6} {'deflexió':>9} {'px':>7}")
    print("  " + "-" * 68)
    for d in dades[:8]:
        etiqueta = d["nom"].split(",")[0].replace("S0", "S").strip() if d["nom"] else "—"
        etiqueta = re.sub(r"^[SVA]-?\d+ ?/? ?", "", etiqueta).strip(" =") or "—"
        print(f"  {d['id']:<6} {etiqueta[:34]:<34} {d['r_sol']:6.2f} "
              f"{d['alpha']:8.3f}″ {d['alpha_px']:7.3f}")
    print(f"  {'...':<6}")
    d = dades[-1]
    print(f"  {d['id']:<6} {'(la més allunyada)':<34} {d['r_sol']:6.2f} "
          f"{d['alpha']:8.3f}″ {d['alpha_px']:7.3f}")
    print()

# ------------------------------------------------------- test de detectabilitat
print("=" * 78)
print("FORECAST DE FISHER: SENSIBILITAT ESPERADA, NO AJUST NI DETECCIÓ")
print("=" * 78)
print("""
Model: posició mesurada = transformació de placa · posició de catàleg
                          + eps · alpha_GR(r) · (radial cap enfora)

La transformació de placa absorbeix translació (2), rotació (1) i escala (1).
L'escala és RADIAL i creix amb r; la deflexió és RADIAL i cau com 1/r: es
barregen. eps = 1 vol dir relativitat general, eps = 0,5 Newton, eps = 0 res.

La matriu següent només propaga la geometria i el residu rms cap a σ(eps).
No resol eps sobre residus observats; els valors en σ són un forecast.
""")

for nom, (cfg, dades) in resultats.items():
    esc = cfg["escala"]
    n = len(dades)
    for model, ncol in (("similitud (4 par.)", 4), ("afí (6 par.)", 6)):
        A = np.zeros((2 * n, ncol + 1))
        for i, d in enumerate(dades):
            x, y, r = d["dx"], d["dy"], d["r"]
            A[2 * i, 0] = 1.0                 # translació x
            A[2 * i + 1, 1] = 1.0             # translació y
            A[2 * i, 2] = -y                  # rotació
            A[2 * i + 1, 2] = x
            A[2 * i, 3] = x                   # escala
            A[2 * i + 1, 3] = y
            if ncol == 6:
                A[2 * i, 4] = x               # shear 1
                A[2 * i + 1, 4] = -y
                A[2 * i, 5] = y               # shear 2
                A[2 * i + 1, 5] = x
            A[2 * i, ncol] = d["alpha"] * x / r     # deflexió GR (eps)
            A[2 * i + 1, ncol] = d["alpha"] * y / r
        cov = np.linalg.inv(A.T @ A)
        for etiqueta, sigma_px in (("σ = rms/√2", cfg["resid_rms_px"] / math.sqrt(2)),
                                   ("σ = rms   ", cfg["resid_rms_px"])):
            sigma = sigma_px * esc
            s_eps = math.sqrt(cov[ncol, ncol]) * sigma
            print(f"  {nom:<26} {model:<19} {etiqueta}  "
                  f"σ(eps) = {s_eps:5.2f}   →  GR a {1/s_eps:4.1f}σ "
                  "(forecast; no detecció)")
    print()

# combinat: els dos trens són mesures independents
print("  Combinat (dos trens independents, cas similitud + σ = rms/√2):")
inv = 0.0
for nom, (cfg, dades) in resultats.items():
    esc = cfg["escala"]
    n = len(dades)
    A = np.zeros((2 * n, 5))
    for i, d in enumerate(dades):
        x, y, r = d["dx"], d["dy"], d["r"]
        A[2 * i, 0] = 1.0
        A[2 * i + 1, 1] = 1.0
        A[2 * i, 2] = -y
        A[2 * i + 1, 2] = x
        A[2 * i, 3] = x
        A[2 * i + 1, 3] = y
        A[2 * i, 4] = d["alpha"] * x / r
        A[2 * i + 1, 4] = d["alpha"] * y / r
    cov = np.linalg.inv(A.T @ A)
    s = math.sqrt(cov[4, 4]) * (cfg["resid_rms_px"] / math.sqrt(2)) * esc
    inv += 1 / s ** 2
s_comb = 1 / math.sqrt(inv)
print(f"     σ(eps) = {s_comb:.2f}  →  GR a {1/s_comb:.1f}σ  ·  "
      f"separar GR de Newton (Δeps=0,5) a {0.5/s_comb:.1f}σ  "
      "[forecast de Fisher; no detecció]")
print()

# Quina precisió caldria
print("=" * 78)
print("QUÈ CALDRIA PER ARRIBAR-HI")
print("=" * 78)
for nom, (cfg, dades) in resultats.items():
    esc = cfg["escala"]
    n = len(dades)
    A = np.zeros((2 * n, 5))
    for i, d in enumerate(dades):
        x, y, r = d["dx"], d["dy"], d["r"]
        A[2*i, 0] = 1.0; A[2*i+1, 1] = 1.0
        A[2*i, 2] = -y;  A[2*i+1, 2] = x
        A[2*i, 3] = x;   A[2*i+1, 3] = y
        A[2*i, 4] = d["alpha"] * x / r
        A[2*i+1, 4] = d["alpha"] * y / r
    c = math.sqrt(np.linalg.inv(A.T @ A)[4, 4])   # σ(eps) = c · σ_posició
    # per a eps al 10 % (nivell Eddington 1919) cal:
    sigma_10 = 0.10 / c
    print(f"  {nom:<26} σ per estrella necessària per a eps ±10 %: "
          f"{sigma_10:.3f}″ = {sigma_10/esc:.3f} px  "
          f"(ara: {cfg['resid_rms_px']/math.sqrt(2)*esc:.2f}″)")
print()
