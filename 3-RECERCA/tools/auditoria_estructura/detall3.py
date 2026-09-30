"""Fins a quina ESCALA el nostre detall és real? Referència: el 800 mm de Brno.

Cada parella s'iguala a la resolució de la MÉS BASTA de les dues, i el control
són les altres imatges de Brno contra el mateix 800 mm. Així cap banda no es
compara per sota del que un dels dos pot resoldre.

⛔ La versió anterior igualava tothom al 200 mm (R☉ 37,8 px) i llavors la banda
fina queda per sota de la resolució de tots: el 0,79 que hi treia Brno×Brno no
és estructura compartida sinó pipeline compartit.
"""
from __future__ import annotations
import json, os
import numpy as np
import nucli as N
from registra import a_la_resolucio

NTH = 2880
RADIS = np.exp(np.linspace(np.log(1.15), np.log(2.40), 60))
CAPES = ("PASSA_ALT", "RADIAL", "NRGF", "MGN")
REF = "TSE2026_Trigaza_800mm.png"
BANDES = [(1, 4), (5, 12), (13, 30), (31, 80), (81, 200), (201, 500)]


def banda(e, lo, hi):
    F = np.fft.rfft(np.nan_to_num(e), axis=1)
    G = np.zeros_like(F); G[:, lo:hi + 1] = F[:, lo:hi + 1]
    return np.fft.irfft(G, n=e.shape[1], axis=1)


if __name__ == "__main__":
    reg = json.load(open(os.path.join(N.AQUI, N.REGISTRE)))
    Rref = reg[REF]["R_sol_px"]
    br, _, _, _ = N.carrega_brno(REF)
    pref = N.mostreja(br, reg[REF]["cy"], reg[REF]["cx"], Rref, RADIS, NTH,
                      ang0=np.deg2rad(reg[REF]["gir_deg"]))
    mref = N.mascara_brno(REF, reg[REF], RADIS, NTH, 0.030)

    lum, pes, LL, S = N.carrega_nostre()
    cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
    wp = N.mostreja(pes, cy, cx, LL["R_sol_px"], RADIS, NTH)
    rf = np.nanpercentile(wp, 90, axis=1, keepdims=True)
    mn = np.isfinite(wp) & (wp > 0.05 * np.maximum(rf, 1e-12))
    cm = mn & mref
    ple = cm.all(axis=1)
    print(f"anells sencers: {ple.sum()}  ({RADIS[ple].min():.3f}–{RADIS[ple].max():.3f} R☉)")
    print(f"resolució de la referència: R☉ = {Rref:.1f} px\n")

    nostres = {"COMPOST": lum}
    for c in CAPES:
        nostres[c] = np.load(os.path.join(N.RUN, "3-filtres", f"DETALL_{c}.npy"))

    # nosaltres, desenfocats al 800 mm
    E = {}
    for k, a in nostres.items():
        E[k] = N.estructura_mask(a_la_resolucio(
            N.mostreja(a, cy, cx, LL["R_sol_px"], RADIS, NTH), RADIS, Rref, NTH),
            cm)[ple]
    del nostres, lum

    # control: les altres Brno contra el 800 mm, cadascuna al seu límit
    ctrl = {}
    for n in sorted(reg):
        if n == REF:
            continue
        b2, _, _, _ = N.carrega_brno(n)
        Rn = reg[n]["R_sol_px"]
        p2 = N.mostreja(b2, reg[n]["cy"], reg[n]["cx"], Rn, RADIS, NTH,
                        ang0=np.deg2rad(reg[n]["gir_deg"]))
        ctrl[n] = (N.estructura_mask(p2, cm)[ple],
                   N.estructura_mask(a_la_resolucio(pref, RADIS, Rn, NTH), cm)[ple])
    Eref = N.estructura_mask(pref, cm)[ple]

    ok = np.ones((int(ple.sum()), NTH), bool)
    print(f"{'banda m':>10s} {'tret de':>8s} {'px@1,5R☉':>9s} | {'B×800':>6s} | "
          + " ".join(f"{k:>9s}" for k in ["COMPOST"] + list(CAPES)))
    for lo, hi in BANDES:
        px = 1.5 * Rref * 2 * np.pi / hi
        bb = np.nanmean([np.nanmean(N.corr_per_anell_mask(
            banda(a, lo, hi), banda(b, lo, hi), ok)[0]) for a, b in ctrl.values()])
        rr = banda(Eref, lo, hi)
        fila = [np.nanmean(N.corr_per_anell_mask(banda(E[k], lo, hi), rr, ok)[0])
                for k in ["COMPOST"] + list(CAPES)]
        print(f"{lo:4d}–{hi:<5d} {360/hi:6.1f}° {px:9.1f} | {bb:6.3f} | "
              + " ".join(f"{v:9.3f}" for v in fila))
