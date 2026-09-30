"""Els perfils azimutals, cara a cara, als radis que decideixen."""
from __future__ import annotations
import json, os
import numpy as np
import nucli as N
from registra import a_la_resolucio

NTH = 720
RAD = np.array([1.040, 1.050, 1.060, 1.070, 1.080, 1.090, 1.100, 1.120,
                1.150, 1.200, 1.300])

lum, pes, LL, S = N.carrega_nostre()
reg = json.load(open(os.path.join(N.AQUI, "registre.json")))
cy, cx = LL["H"] / 2.0, LL["W"] / 2.0
nom = "TSE2026_Trigaza_800mm.png"; r = reg[nom]
br, _, _, _ = N.carrega_brno(nom)

nos = a_la_resolucio(N.mostreja(lum, cy, cx, LL["R_sol_px"], RAD, NTH),
                     RAD, r["R_sol_px"], NTH)
bro = N.mostreja(br, r["cy"], r["cx"], r["R_sol_px"], RAD, NTH,
                 ang0=np.deg2rad(r["gir_deg"]))
wp = N.mostreja(pes, cy, cx, LL["R_sol_px"], RAD, NTH)

print("perfils azimutals, 24 sectors de 15° (θ=0 a la dreta, creix cap avall)")
print("N = nosaltres normalitzat  ·  B = Brno normalitzat  ·  w = pes relatiu\n")
for i, rr in enumerate(RAD):
    n = nos[i]; b = bro[i]
    nn = (n - np.nanmedian(n)) / max(np.nanmedian(np.abs(n - np.nanmedian(n))), 1e-12)
    bb = (b - np.nanmedian(b)) / max(np.nanmedian(np.abs(b - np.nanmedian(b))), 1e-12)
    c = N.corr_per_anell(nn[None], bb[None])[0]
    sec = lambda a: [np.nanmean(a[k*30:(k+1)*30]) for k in range(24)]
    print(f"r = {rr:.3f} R☉   corr {c:+.3f}   pes {np.nanmedian(wp[i]):.3g}")
    print("   N " + " ".join(f"{v:+5.1f}" for v in sec(nn)))
    print("   B " + " ".join(f"{v:+5.1f}" for v in sec(bb)))
    print("   w " + " ".join(f"{v:5.2f}" for v in
                             np.array(sec(wp[i])) / max(np.nanmedian(wp[i]), 1e-12)))
    print()
