"""Resposta del sensor mesurada entre DOS FOTOGRAMES CRUS, sense composició.

⛔ La mesura sobre esglaons **compostos** no serveix per a això: hi entren el
`taper`, el drizzle i l'anivellament de cel, que ja depenen del nivell. Aquí es
comparen dos fotogrames calibrats (fosc, PRNU, flat) i prou, tan propers en el
temps com sigui possible perquè el Sol no s'hagi mogut ni la transparència hagi
canviat.

Si el sensor fos lineal, `(taxa_llarga / taxa_curta)` seria **constant**. El que
en surti depenent del **senyal cru en ADU de la llarga** és la corba de resposta.

⚠️ I les dues signatures que cal separar, que tenen forma OPOSADA:

| causa | a senyal BAIX | a senyal ALT |
|---|---|---|
| pedestal/fosc mal restat | **molt** (∝ 1/S) | gens |
| no-linealitat de pou | gens | **molt** |
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402
import pilot as PL  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--curta", required=True, help="nom del fotograma curt")
    ap.add_argument("--llarga", required=True)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()
    fg = {f.nom: f for f in C.llegeix_manifest()}
    PL.centres_finals(list(fg.values()))
    fc, fl = fg[a.curta], fg[a.llarga]
    print(f"curt  {fc.nom}  {fc.exp_s:.6g} s  t={fc.t_rel_c2:.2f}")
    print(f"llarg {fl.nom}  {fl.exp_s:.6g} s  t={fl.t_rel_c2:.2f}")
    dc = math.hypot(fl.sol_usat[0] - fc.sol_usat[0], fl.sol_usat[1] - fc.sol_usat[1])
    print(f"desplaçament del Sol entre els dos: {dc:.2f} px")

    mc, sc = C.calibra(fc); ml, sl = C.calibra(fl)
    # ⛔ desplaçament sencer en píxels de MOSAIC: ha de ser parell per no barrejar
    # plans de Bayer. Amb un desplaçament sub-píxel no s'interpola: es descarta
    # la part fraccionària i s'ho menja el calaix, que és ample.
    dy = int(round((fl.sol_usat[1] - fc.sol_usat[1]) / 2.0)) * 2
    dx = int(round((fl.sol_usat[0] - fc.sol_usat[0]) / 2.0)) * 2
    mc = np.roll(mc, (dy, dx), axis=(0, 1))
    sc = np.roll(sc, (dy, dx), axis=(0, 1))
    out = []
    for nom in ("G1", "G2"):
        pc, oy, ox = C.plans(mc)[nom]
        pl_, _, _ = C.plans(ml)[nom]
        satc = C.plans(sc.astype(np.uint8))[nom][0]
        satl = C.plans(sl.astype(np.uint8))[nom][0]
        rr = C.anells(*pc.shape, (fl.sol_usat[1] - oy) / 2, (fl.sol_usat[0] - ox) / 2) * 2 / C.R_SOL_PX
        # ⛔ només corona: fora del disc lunar amb marge i dins del camp útil
        bo = ((satc == 0) & (satl == 0) & (pc > 30.0) & (pl_ > 30.0)
              & (pl_ < C.POU - C.PEDESTAL) & (rr > 1.15) & (rr < 4.0))
        if bo.sum() < 50000:
            continue
        # ⛔ **El CEL es resta ABANS del quocient, i sense això la mesura no
        # val.** El cel és additiu i `calibra` no el treu; la seva taxa varia un
        # 85 % durant la totalitat, o sigui que dos fotogrames separats set
        # segons en tenen quantitats diferents. Mesurat el 25-08-2026, sense
        # restar-lo el quocient anava de −4,41 % al 27 % del pou a −2,90 % al
        # 82 %, i **tota** aquella dependència del nivell s'explicava amb una
        # diferència de cel de −9,5 ADU/s: `R∞ + Δs/C`. Zero no-linealitat.
        # L'estadístic bo és **corona menys cel**, el mateix de la porta F0.
        anell = (rr > C.FONS_ANELL[0]) & (rr < C.FONS_ANELL[1]) & (satc == 0) & (satl == 0)
        cel_c = float(np.median(pc[anell])) / fc.exp_s
        cel_l = float(np.median(pl_[anell])) / fl.exp_s
        print(f"    cel al {C.FONS_ANELL[0]}-{C.FONS_ANELL[1]} R☉: "
              f"curt {cel_c:.1f} · llarg {cel_l:.1f} ADU/s  (Δ {cel_l-cel_c:+.1f})")
        tc = pc[bo] / fc.exp_s - cel_c
        tl = pl_[bo] / fl.exp_s - cel_l
        k = (tc > 0) & (tl > 0)
        q = (tl[k] / tc[k]) - 1.0
        cru = pl_[bo][k]
        vores = np.quantile(cru, np.linspace(0, 1, a.n + 1))
        vores = np.unique(vores)
        idx = np.clip(np.digitize(cru, vores) - 1, 0, len(vores) - 2)
        o = np.argsort(idx, kind="stable")
        i_s, q_s, c_s = idx[o], q[o], cru[o]
        t = np.searchsorted(i_s, np.arange(len(vores)))
        pts = [(float(np.median(c_s[lo:hi])), float(np.median(q_s[lo:hi])), int(hi - lo))
               for lo, hi in zip(t[:-1], t[1:]) if hi - lo >= 2000]
        out.append({"pla": nom, "punts": pts, "n": int(bo.sum())})
        print(f"\n  pla {nom}  ({bo.sum()/1e6:.2f} Mpx)")
        print("   ADU cru : " + " ".join(f"{p[0]:7.0f}" for p in pts[::max(len(pts)//10, 1)]))
        print("   % pou   : " + " ".join(f"{100*p[0]/(C.POU-C.PEDESTAL):7.1f}" for p in pts[::max(len(pts)//10, 1)]))
        print("   quocient: " + " ".join(f"{100*p[1]:+7.3f}" for p in pts[::max(len(pts)//10, 1)]))
    if a.json:
        C.desa_json(a.json, {"curta": fc.nom, "llarga": fl.nom,
                             "exp_curta": fc.exp_s, "exp_llarga": fl.exp_s,
                             "plans": out})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
