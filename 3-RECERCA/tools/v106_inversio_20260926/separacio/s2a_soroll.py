"""s2a · Taula de soroll empíric σ_j(d) de δ_j (residu robust contra la mediana dels fotogrames que veuen el píxel a D ≥ 6), per franges de d.
Franges sense dada: la més propera del mateix fotograma; fotogrames sense cap franja (saturats arran del limbe): σ = 1 (pes negligible)."""
import numpy as np
from nucli import Dades
S = Dades()
DEL = np.zeros((S.nF, len(S.dg), S.nth), np.float32); NET = np.zeros(DEL.shape, bool)
for j in range(S.nF):
    a, D, *_ = S.geom(j); d, ok = S.delta(j, D); DEL[j] = d; NET[j] = ok & (D >= 6)
n = NET.sum(0); med = np.nanmedian(np.where(NET, DEL, np.nan), axis=0)
edges = np.arange(-32, 41, 4.0); dmid = 0.5 * (edges[1:] + edges[:-1]); sig = np.full((S.nF, dmid.size), np.nan)
for j in range(S.nF):
    for b in range(dmid.size):
        rows = (S.dg >= edges[b]) & (S.dg < edges[b + 1]); m = NET[j][rows] & (n[rows] >= 8)
        if m.sum() < 3000: continue
        r = (DEL[j][rows] - med[rows])[m]; sig[j, b] = 1.4826 * np.median(np.abs(r - np.median(r))) * np.sqrt(1 + 1.57 / max(np.median(n[rows][m]), 1))
    ok = np.isfinite(sig[j])
    if ok.any(): sig[j] = np.interp(dmid, dmid[ok], sig[j][ok])
    else: sig[j] = 1.0
np.savez('SIG.npz', dmid=dmid, sig=sig)
for j in range(S.nF): print(j, S.e[j], np.round(sig[j, ::2], 4))
