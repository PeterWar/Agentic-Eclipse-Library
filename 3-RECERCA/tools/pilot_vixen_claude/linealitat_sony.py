"""Resposta del sensor SONY, mesurada entre els dos membres d'una MATEIXA ràfega.

## ⛔ Per què aquesta mesura és la millor del projecte

Els brackets de la Sony surten d'**una sola pulsació**: `DSC06982` (0,25 s) i
`DSC06983` (1/32 s) tenen el mateix desplaçament de registre, o sigui que són
**del mateix instant**. Això elimina d'un cop els tres confusors que a la Vixen
obliguen a fer acrobàcies:

- **cap canvi de cel** (a la Vixen, dos fotogrames a 7 s de distància tenen
  9,5 ADU/s de diferència de cel, i sense restar-la la corba surt tota falsa);
- **cap canvi de transparència** (que cau un 8 % durant la totalitat);
- **cap moviment de la Lluna** ni de la muntura.

I el salt d'exposició és de **×8**, o sigui molt de recorregut de nivell.

## I què decideix

Pere ho va plantejar bé: **cada tren té el seu sensor i el seu flat**. Si els dos
donen la mateixa corba, el flat com a explicació cau —dos flats diferents no fan
la mateixa corba per casualitat—. Si només la Canon, és el sensor.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--curta", required=True)
    ap.add_argument("--llarga", required=True)
    ap.add_argument("--n", type=int, default=26)
    ap.add_argument("--x-min", type=float, default=0.02)
    ap.add_argument("--x-max", type=float, default=0.88)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()
    import sony as SY
    reg = SY.registre()
    vc, vl = reg["fotogrames"][a.curta], reg["fotogrames"][a.llarga]
    print(f"curt  {a.curta}  {vc['exp_s']:.6g} s  t={vc['t']:.2f}")
    print(f"llarg {a.llarga}  {vl['exp_s']:.6g} s  t={vl['t']:.2f}")
    d_reg = float(np.hypot(vl["dx"] - vc["dx"], vl["dy"] - vc["dy"]))
    print(f"⛔ desplaçament de registre entre els dos: {d_reg:.3f} px"
          + ("   → MATEIXA RÀFEGA" if d_reg < 0.05 else ""))
    mc, sc = SY.calibra(a.curta)
    ml, sl = SY.calibra(a.llarga)
    sol = (SY.SOL_REF[0] + vl["dx"], SY.SOL_REF[1] + vl["dy"])
    rs = C.RSOL_ARCSEC / SY.ESCALA
    POU = SY.POU - SY.PEDESTAL
    out = []
    for nom in ("G1", "G2"):
        pc, oy, ox = C.plans(mc)[nom]; pl_, _, _ = C.plans(ml)[nom]
        satc = C.plans(sc.astype(np.uint8))[nom][0]; satl = C.plans(sl.astype(np.uint8))[nom][0]
        rr = C.anells(*pc.shape, (sol[1] - oy) / 2, (sol[0] - ox) / 2) * 2 / rs
        an = (rr > 6.0) & (rr < 8.0) & (satc == 0) & (satl == 0)
        if an.sum() < 5000:
            continue
        cc = float(np.median(pc[an])) / vc["exp_s"]
        cl = float(np.median(pl_[an])) / vl["exp_s"]
        print(f"    cel a 6-8 R☉: curt {cc:.2f} · llarg {cl:.2f} ADU/s (Δ {cl-cc:+.2f})")
        bo = ((satc == 0) & (satl == 0) & (pl_ > a.x_min * POU) & (pl_ < a.x_max * POU)
              & (rr > 1.15) & (rr < 5.0))
        if bo.sum() < 50000:
            print(f"    {nom}: poca mostra ({bo.sum()})"); continue
        tc = pc[bo] / vc["exp_s"] - cc
        tl = pl_[bo] / vl["exp_s"] - cl
        k = (tc > 2.0 * abs(cc)) & (tl > 2.0 * abs(cl))
        q = tl[k] / tc[k]
        x = pl_[bo][k] / POU
        v = np.unique(np.quantile(x, np.linspace(0.01, 0.99, a.n + 1)))
        idx = np.clip(np.digitize(x, v) - 1, 0, len(v) - 2)
        o = np.argsort(idx, kind="stable"); i_s, q_s, x_s = idx[o], q[o], x[o]
        t = np.searchsorted(i_s, np.arange(len(v)))
        pts = [(float(np.median(x_s[i:j])), float(np.median(q_s[i:j])), int(j - i))
               for i, j in zip(t[:-1], t[1:]) if j - i >= 3000]
        if len(pts) < 5:
            print(f"    {nom}: pocs calaixos"); continue
        base = float(np.median([p[1] for p in pts[:3]]))
        out.append({"pla": nom, "punts": pts})
        sel = pts[::max(len(pts) // 10, 1)]
        print(f"\n  pla {nom}  ({k.sum()/1e6:.2f} Mpx)")
        print("   x del pou: " + " ".join(f"{p[0]:7.3f}" for p in sel))
        print("   quocient : " + " ".join(f"{p[1]:7.4f}" for p in sel))
        print("   desviació: " + " ".join(f"{100*(p[1]/base-1):+7.3f}" for p in sel)
              + "   %  (contra els tres primers calaixos)")
    if a.json:
        C.desa_json(a.json, {"curta": a.curta, "llarga": a.llarga, "plans": out})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
