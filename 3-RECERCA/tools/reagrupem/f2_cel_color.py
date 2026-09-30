#!/usr/bin/env python3
"""FASE 2 · el CEL pel COLOR, ara amb els DOS vectors MESURATS.

⛔ **Rectificació del 26-08 (la va veure Codex al contrast).** La primera
versió d'aquest pas deia que el mètode del color no podia funcionar perquè
l'extinció a X~6 enrogeix el cel i la corona igual i les dues direccions
cromàtiques queden paral·leles. **Això era FALS.** Mesurat:

    corona (a 1,05–1,30 R☉, on el cel val ~1 %) :  R/G = 1,77   B/G = 0,485
    cel    (al camp llunyà > 6 R☉)              :  R/G = 1,016  B/G = 0,876

No són paral·leles: se separen molt. **El defecte era meu**: vaig resoldre
`S = (I_B − I_G)/(b_B − 1)`, que assumeix que la corona té **B = G**, o sigui
que és NEUTRA. No ho és — l'extinció cromàtica la deixa molt vermella. Amb la
corona suposada neutra, tota la seva pròpia diferència B−G es comptava com a
cel, i d'aquí sortia el −11.824 DN a 2 R☉.

Ben plantejat són **dos vectors mesurats i tres equacions**:

    [I_R, I_G, I_B]ᵀ  =  C · s  +  S · b        (s = corona, b = cel)

Dues incògnites i tres equacions: queda **un grau de llibertat per fallar**, i
aquest és el control honest que `research/100` §D demanava.
"""

from __future__ import annotations

import json, os, sys
import numpy as np, cv2
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

RS = 440.60
R_CORONA = (1.05, 1.30)     # R☉: on mana la corona
R_CEL = 6.0                 # R☉: a partir d'on mana el cel
SIGMA = 220.0               # px: el cel és de baixa freqüència


def main():
    C = {c: fits.getdata(os.path.join(comu.F2, f"LDIC_{c}.fits")).astype(np.float32)
         for c in ("R", "G", "B")}
    P = fits.getdata(os.path.join(comu.F2, "LDIC_pes_G.fits")).astype(np.float32)
    H, W = C["G"].shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H/2.0, xx - W/2.0); del yy, xx
    m = (P > 0.02*P.max())
    for c in C: m &= np.isfinite(C[c]) & (C[c] > 0)

    din = m & (rad > R_CORONA[0]*RS) & (rad < R_CORONA[1]*RS)
    fora = m & (rad > R_CEL*RS)
    s = np.array([float(np.median(C[c][din]/C["G"][din])) for c in ("R", "G", "B")])
    b = np.array([float(np.median(C[c][fora]/C["G"][fora])) for c in ("R", "G", "B")])
    print(f"vector CORONA s = ({s[0]:.4f}, {s[1]:.4f}, {s[2]:.4f})   "
          f"({int(din.sum()):,} px a {R_CORONA[0]}–{R_CORONA[1]} R☉)")
    print(f"vector CEL    b = ({b[0]:.4f}, {b[1]:.4f}, {b[2]:.4f})   "
          f"({int(fora.sum()):,} px > {R_CEL} R☉)")
    cosang = float(s @ b/(np.linalg.norm(s)*np.linalg.norm(b)))
    A = np.c_[s, b]
    cond = float(np.linalg.cond(A))
    print(f"angle entre els dos vectors: {np.degrees(np.arccos(cosang)):.2f}°   "
          f"nombre de condició: {cond:.2f}   "
          f"{'BEN CONDICIONAT ✓' if cond < 20 else '⚠️ mal condicionat'}")

    # ⚠️ el cel mesurat al camp llunyà encara porta corona; una iteració ho
    # corregeix: es resta la corona estimada i es torna a mesurar b.
    pinv = np.linalg.pinv(A)
    for it in range(3):
        I = np.stack([C[c] for c in ("R", "G", "B")], axis=0)
        Cc = pinv[0, 0]*I[0] + pinv[0, 1]*I[1] + pinv[0, 2]*I[2]
        Ss = pinv[1, 0]*I[0] + pinv[1, 1]*I[1] + pinv[1, 2]*I[2]
        del I
        net = fora & (Cc < 0.15*np.nanmedian(Cc[fora]) + np.abs(np.nanmedian(Cc[fora])))
        if net.sum() < 100000: break
        b_nou = np.array([float(np.median((C[c][net] - Cc[net]*s[c_i]) /
                                          np.maximum(Ss[net], 1e-6)))
                          for c_i, c in enumerate(("R", "G", "B"))])
        b_nou = b_nou/b_nou[1]
        canvi = float(np.max(np.abs(b_nou - b)))
        b = b_nou; A = np.c_[s, b]; pinv = np.linalg.pinv(A)
        print(f"  iteració {it+1}: b = ({b[0]:.4f}, {b[1]:.4f}, {b[2]:.4f})  Δ={canvi:.5f}")
        if canvi < 2e-3: break

    I = np.stack([C[c] for c in ("R", "G", "B")], axis=0)
    Cc = pinv[0, 0]*I[0] + pinv[0, 1]*I[1] + pinv[0, 2]*I[2]
    Ss = pinv[1, 0]*I[0] + pinv[1, 1]*I[1] + pinv[1, 2]*I[2]
    # CONTROL: el grau de llibertat que sobra
    rec = np.stack([Cc*s[i] + Ss*b[i] for i in range(3)], axis=0)
    resid = np.abs(I - rec).sum(axis=0)/np.maximum(np.abs(I).sum(axis=0), 1e-6)
    print(f"CONTROL (el grau de llibertat que sobra): mediana "
          f"{100*float(np.median(resid[m])):.3f} %  p90 "
          f"{100*float(np.percentile(resid[m], 90)):.3f} %   [research/100: 0,01–1,26 %]")
    del I, rec

    # el cel és de baixa freqüència: se suavitza abans de restar-lo
    k = int(6*SIGMA) | 1
    mf = m.astype(np.float32)
    num = cv2.GaussianBlur(np.where(m, Ss, 0.0).astype(np.float32), (k, k), SIGMA)
    den = cv2.GaussianBlur(mf, (k, k), SIGMA)
    Sf = np.where(den > 1e-4, num/np.maximum(den, 1e-9), 0.0).astype(np.float32)

    out = {}
    for i, c in enumerate(("R", "G", "B")):
        out[c] = np.where(m, C[c] - Sf*b[i], np.nan).astype(np.float32)
        fits.PrimaryHDU(out[c]).writeto(
            os.path.join(comu.F2, f"COLOR_cel_restat_{c}.fits"), overwrite=True)
    fits.PrimaryHDU(np.where(m, Sf, np.nan).astype(np.float32)).writeto(
        os.path.join(comu.F2, "COLOR_CEL_S.fits"), overwrite=True)

    sim = fits.getdata(os.path.join(comu.F2, "LDIC_cel_restat_G.fits")).astype(np.float64)
    print(f"\n{'r (R☉)':>8} | {'G brut':>10} {'COLOR':>10} {'SIMETRIA':>10} | {'color/sim':>9}")
    for r0 in (1.1, 1.5, 2.0, 2.6, 3.0, 4.0, 5.0, 7.0, 9.0):
        m2 = m & (rad > r0*RS) & (rad < (r0+0.06)*RS)
        if m2.sum() < 200: continue
        a_ = float(np.nanmedian(C["G"][m2])); c_ = float(np.nanmedian(out["G"][m2]))
        d_ = float(np.nanmedian(sim[m2]))
        print(f"{r0:8.1f} | {a_:10.1f} {c_:10.1f} {d_:10.1f} | {c_/max(d_,1e-6):9.2f}")

    json.dump({"s_corona": s.tolist(), "b_cel": b.tolist(),
               "angle_graus": float(np.degrees(np.arccos(cosang))), "condicio": cond,
               "control_residu_mediana_pct": float(100*np.median(resid[m])),
               "control_residu_p90_pct": float(100*np.percentile(resid[m], 90)),
               "rectificacio": "la primera versió deia que el color no podia funcionar per "
                               "extinció; era FALS. El defecte era suposar la corona NEUTRA."},
              open(os.path.join(comu.REBUTS, "F2_cel_color.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
