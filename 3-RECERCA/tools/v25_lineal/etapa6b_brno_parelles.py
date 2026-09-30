#!/usr/bin/env python3
"""V28 · parella a parella contra els composts AMPLES de Brno (200 i 400 mm DHS), fins a 9 R☉, a 4,5° i 9°:
el TOTAL lineal (corona + cel, font de la base), la corona sola (descomposició) i la base display, i el
control 200 × 400 (i 200 × 530, 400 × 530). Si el total × 200 s'acosta al 200 × 400, l'estructura és real."""
import os, sys, json, numpy as np
from scipy.ndimage import gaussian_filter1d
AQUI = os.path.dirname(os.path.abspath(__file__)); CAU = os.path.join(AQUI, "cau_v25")
sys.path.insert(0, os.path.join(AQUI, "..", "auditoria_estructura")); import nucli as N
OUT = "/Users/USUARI/Desktop/Eclipse 2026/IA/output/v28_20260905"
NOMS = ["TSE_2026_200mm_DHS.png", "TSE_2026_400mm_DHS.png", "TSE_2026_530mm_DHS.png"]
RADIS = np.round(np.arange(1.2, 9.01, 0.2), 2); NTH = 1440
def estr(p, deg):
    q = gaussian_filter1d(np.nan_to_num(p, nan=0.0), deg / 360.0 * NTH, axis=1, mode="wrap"); q = np.where(np.isfinite(p), q, np.nan); return N.estructura(q)
reg = json.load(open(os.path.join(N.AQUI, N.REGISTRE))); B = {}
for n in NOMS:
    br, _, _, _ = N.carrega_brno(n); B[n] = N.mostreja(br, reg[n]["cy"], reg[n]["cx"], reg[n]["R_sol_px"], RADIS, NTH, ang0=np.deg2rad(reg[n]["gir_deg"]))
lum, pes, LL, S = N.carrega_nostre(run="/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/019_VIXEN_CIENCIA_20260827T212404Z"); H, W = lum.shape; cy, cx = H / 2.0, W / 2.0; Rs = LL["R_sol_px"]; del lum, pes
mf = np.load(os.path.join(CAU, "mascara_fusio.npy"))
uf = np.load(os.path.join(CAU, "fusio_srgb_lin_total.npy")); Lt = np.where(mf, (uf[..., 0] + 2 * uf[..., 1] + uf[..., 2]) / 4, np.nan); del uf
cf = np.load(os.path.join(CAU, "cf_corona_lin.npy")); Lc = np.where(mf, (cf[..., 0] + 2 * cf[..., 1] + cf[..., 2]) / 4, np.nan); del cf
base = np.load(os.path.join(CAU, "base_B_rgb16.npy")).astype(np.float32) / 65535.0; Lb = np.where(mf, (base[..., 0] + 2 * base[..., 1] + base[..., 2]) / 4, np.nan); del base
P = {"total lineal": N.mostreja(Lt, cy, cx, Rs, RADIS, NTH), "corona sola": N.mostreja(Lc, cy, cx, Rs, RADIS, NTH), "base display": N.mostreja(Lb, cy, cx, Rs, RADIS, NTH)}
res = {"radis": RADIS.tolist()}
for deg in (4.5, 9.0):
    Eb = {n: estr(B[n], deg) for n in NOMS}; Ep = {k: estr(v, deg) for k, v in P.items()}
    tab = {"200×400": N.corr_per_anell(Eb[NOMS[0]], Eb[NOMS[1]]), "200×530": N.corr_per_anell(Eb[NOMS[0]], Eb[NOMS[2]]), "400×530": N.corr_per_anell(Eb[NOMS[1]], Eb[NOMS[2]])}
    for k in P:
        for n, nm in zip(NOMS, ("200", "400", "530")): tab[f"{k}×{nm}"] = N.corr_per_anell(Ep[k], Eb[n])
    res[f"{deg}"] = {k: v.tolist() for k, v in tab.items()}
    print(f"\n=== escala {deg}° ===\n  r   " + " ".join(f"{k[:16]:>17s}" for k in tab))
    for i, r in enumerate(RADIS): print(f"{r:4.1f}  " + " ".join(f"{tab[k][i]:+17.2f}" for k in tab))
json.dump(res, open(os.path.join(OUT, "compara_brno_parelles.json"), "w"), indent=1)
