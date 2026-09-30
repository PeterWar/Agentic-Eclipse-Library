"""El desacord fi, és REGISTRE? Escombrada de gir i escala jutjada a escala fina.

El registre global es va ajustar sobre l'estructura sencera, que la manen els
harmònics baixos: un error de mig grau de gir no hi es nota gens i en canvi
mata la banda de 4,5°. Si movent el gir o l'escala la banda fina puja molt,
el desacord era meu i no del producte.
"""
from __future__ import annotations
import json, os
import numpy as np
import nucli as N
from registra import a_la_resolucio
from detall3 import banda

NTH = 2880
RADIS = np.exp(np.linspace(np.log(1.20), np.log(2.40), 50))
REF = "TSE2026_Trigaza_800mm.png"
BANDES = [(5, 12), (13, 30), (31, 80), (81, 200)]

reg = json.load(open(os.path.join(N.AQUI, "registre.json")))[REF]
br, _, _, _ = N.carrega_brno(REF)
Rb = reg["R_sol_px"]
lum, pes, LL, S = N.carrega_nostre()
cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
wp = N.mostreja(pes, cy, cx, LL["R_sol_px"], RADIS, NTH)
rf = np.nanpercentile(wp, 90, axis=1, keepdims=True)
mn = np.isfinite(wp) & (wp > 0.05 * np.maximum(rf, 1e-12))
nos_p = a_la_resolucio(N.mostreja(lum, cy, cx, LL["R_sol_px"], RADIS, NTH),
                       RADIS, Rb, NTH)
del lum, pes


def prova(dgir, desc, ddx=0.0, ddy=0.0):
    p = N.mostreja(br, reg["cy"] + ddy, reg["cx"] + ddx, Rb * desc, RADIS, NTH,
                   ang0=np.deg2rad(reg["gir_deg"] + dgir))
    m = mn & N.mascara_brno(REF, reg, RADIS, NTH, 0.030)
    ple = m.all(axis=1)
    if ple.sum() < 10:
        return None
    e0 = N.estructura_mask(nos_p, m)[ple]; e1 = N.estructura_mask(p, m)[ple]
    ok = np.ones((int(ple.sum()), NTH), bool)
    return [np.nanmean(N.corr_per_anell_mask(banda(e0, lo, hi),
                                             banda(e1, lo, hi), ok)[0])
            for lo, hi in BANDES]


print("gir (graus respecte del registre)")
print(f"{'Δgir':>7s} | " + " ".join(f"m{lo}-{hi:<4d}" for lo, hi in BANDES))
for dg in (-2.0, -1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0):
    r = prova(dg, 1.0)
    if r:
        print(f"{dg:+7.2f} | " + " ".join(f"{v:8.3f}" for v in r))
print("\nescala (multiplicador de R☉ de Brno)")
print(f"{'Δesc':>7s} | " + " ".join(f"m{lo}-{hi:<4d}" for lo, hi in BANDES))
for ds in (0.98, 0.99, 0.995, 1.0, 1.005, 1.01, 1.02):
    r = prova(0.0, ds)
    if r:
        print(f"{ds:7.3f} | " + " ".join(f"{v:8.3f}" for v in r))
