"""A12 (V37) · El WOW bilateral en ROI amb variants del farcit: A (V35), B(L,cap) per a diversos (L, cap). Mètrica: rivet per sector (màx/mediana) i biaix d'anell 1,03–1,3."""
import os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.argv = [sys.argv[0]]; sys.path.insert(0, str(HERE))
import a11_roi_rivet as R
import numpy as np, cv2
from common import RS, CX, CY, log, savejson
from wow_filters import wow
C36 = ROOT / 'research/tools/v36_20260908/cau'; REB37 = ROOT / 'output/v37_20260908/4-rebuts'; RAD = 2.9; NB = 24


def farcit_B(a, m, r_px, L_PX, CAP):
    ri = np.round(r_px).astype('int32'); L = np.where(m, np.log(np.maximum(a, 1e-9)), 0).astype('float64'); n = np.bincount(ri[m]); s = np.bincount(ri[m], weights=L[m]); prof = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    nodes = np.arange(len(n)); full = np.flatnonzero(n >= 0.999 * 2 * np.pi * np.maximum(nodes, 1)); first_full = int(full[full > 0.9 * RS][0]); has = np.flatnonzero(n > 0); first_data = int(has[has > 0.5 * RS][0])
    p = prof.copy(); ok = np.flatnonzero((n >= 30) & (nodes >= first_data))[:10]; slope = float(np.polyfit(ok, prof[ok], 1)[0]); d = first_data - np.arange(first_data); p[:first_data] = prof[first_data] + np.minimum(-slope * L_PX * (1.0 - np.exp(-d / L_PX)), CAP)
    bad = ~np.isfinite(p[:first_full]); idx = np.flatnonzero(bad)
    if idx.size:
        good = np.flatnonzero(~bad); p[idx] = np.interp(idx, good, p[:first_full][good])
    last = int(np.flatnonzero(np.isfinite(p))[-1]); p[last + 1:] = p[last]; bad = ~np.isfinite(p); p[bad] = np.interp(nodes[bad], nodes[~bad], p[~bad])
    return np.where(m, a, np.exp(np.interp(r_px, nodes, p))).astype(np.float32)


def main():
    G = np.load(C36 / 'base_G_v36.npy', mmap_mode='r'); M = np.load(C36 / 'support_v36.npy'); y0, y1, x0, x1 = int(CY - RAD * RS), int(CY + RAD * RS), int(CX - RAD * RS), int(CX + RAD * RS)
    a = np.array(G[y0:y1, x0:x1], np.float32); m = M[y0:y1, x0:x1].copy(); yy, xx = np.ogrid[:a.shape[0], :a.shape[1]]; r_px = np.hypot(xx + x0 - CX, yy + y0 - CY).astype(np.float32); r = r_px / RS; t = np.degrees(np.arctan2(yy + y0 - CY, xx + x0 - CX)); m &= a > 0
    dist = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5) * (r < 1.3); sec = np.floor((t + 180) / 360 * NB).astype(int) % NB; full = np.ones_like(m); rep = {}
    eA, _ = R.farcit(a, m, r_px, 'A'); variants = [('A', eA)] + [(f'B L{L} cap{c}', farcit_B(a, m, r_px, L, c)) for L, c in ((60, 5), (60, 2), (30, 2), (100, 3), (20, 1))]
    for name, e in variants:
        out = np.where(m, wow(e, full, 7, True, False), np.nan); rep[name] = R.metrics(out, m, r, dist, sec); log(f"WOWbil {name}: rivet màx {rep[name]['rivet_max_abs']:.2f} mediana {rep[name]['rivet_mediana_abs']:.2f} · biaix anell {rep[name]['biaix_anell_1.03_1.3']:.2f} · std vora/σ {rep[name]['std_a_la_vora_sobre_sd']:.2f}")
    for name, e in variants[:3]:
        out = np.where(m, wow(e, full, 7, False, False), np.nan); mt = R.metrics(out, m, r, dist, sec); rep['WOW ' + name] = mt; log(f"WOW {name}: rivet màx {mt['rivet_max_abs']:.2f} mediana {mt['rivet_mediana_abs']:.2f} · biaix anell {mt['biaix_anell_1.03_1.3']:.2f}")
    savejson(REB37 / 'A12_roi_p05.json', rep); log('A12 fet')


if __name__ == '__main__':
    main()
