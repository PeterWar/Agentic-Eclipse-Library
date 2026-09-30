"""A8 (V36) · Prova en ROI (2,9 R☉) del farcit separable + normalització sobre el suport real, contra el farcit V35 (perfil mitjà,
exponencial fins al centre, una màscara): biaix d'anell 1,03–1,3 (mediana per anell / σ) i GRAÓ A LA VORA DEL FORAT (mitjana de
|sortida| a 0–8 px de la vora contra 30–60 px, en σ). Base V35 (idèntica a la V36 al limbe: Vixen sola)."""
import os, sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.argv = [sys.argv[0]]
import b4c_purs as B
import numpy as np, cv2
from common import RS, CX, CY, log, savejson
from wow_filters import wow
from local_filters import mgn
C35 = ROOT / 'research/tools/v35_20260908/cau'; REB36 = ROOT / 'output/v36_20260908/4-rebuts'; RAD = 2.9


def ring_bias(out, m, r):
    sd = float(np.nanstd(out[m & (r > 1.05) & (r < 1.6)])); rs = np.arange(0.98, 1.6, 0.01); med = []
    for a0 in rs:
        k = m & (r >= a0) & (r < a0 + 0.01); med.append(float(np.median(out[k])) / sd if k.sum() > 50 else np.nan)
    z = np.array(med); zz = z - np.nanmedian(z[rs > 1.3]); return float(np.nanmax(np.abs(zz[(rs >= 1.03) & (rs < 1.3)]))), sd


def edge_step(out, m, dist, sd):
    near = m & (dist > 0) & (dist <= 8); far = m & (dist > 30) & (dist <= 60)
    return float((np.nanmean(out[near]) - np.nanmean(out[far])) / sd)


def farcit_v35(a, m, r_px):
    ri = np.round(r_px).astype('int32'); L = np.where(m, np.log(np.maximum(a, 1e-9)), 0).astype('float64'); n = np.bincount(ri[m]); s = np.bincount(ri[m], weights=L[m]); prof = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    nodes = np.arange(len(n)); full = np.flatnonzero(n >= 0.999 * 2 * np.pi * np.maximum(nodes, 1)); first = int(full[full > 0.9 * RS][0]); k = np.arange(first, first + 20); slope = float(np.polyfit(k, prof[k], 1)[0])
    p = prof.copy(); p[:first] = prof[first] + slope * (np.arange(first) - first); last = int(np.flatnonzero(np.isfinite(p))[-1]); p[last + 1:] = p[last]; bad = ~np.isfinite(p); p[bad] = np.interp(nodes[bad], nodes[~bad], p[~bad])
    return np.where(m, a, np.exp(np.interp(r_px, nodes, p))).astype(np.float32)


def main():
    G = np.load(C35 / 'base_G_v35.npy', mmap_mode='r'); M = np.load(C35 / 'support_v35.npy')
    y0, y1, x0, x1 = int(CY - RAD * RS), int(CY + RAD * RS), int(CX - RAD * RS), int(CX + RAD * RS)
    a = np.array(G[y0:y1, x0:x1], np.float32); m = M[y0:y1, x0:x1].copy(); yy, xx = np.ogrid[:a.shape[0], :a.shape[1]]
    r_px = np.hypot(xx + x0 - CX, yy + y0 - CY).astype(np.float32); r = r_px / RS; t = np.arctan2(yy + y0 - CY, xx + x0 - CX).astype(np.float32); m &= a > 0
    dist = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5) * (r < 1.3)
    full = np.ones_like(m); e35 = farcit_v35(a, m, r_px); e36, frep = B.farcit_separable(a, m, r_px, t); log(f'farcit V36: {frep}')
    lim = [float(np.maximum(a, 0)[m].min()), float(np.maximum(a, 0)[m].max())]; NS = 7; rep = {'farcit_v36': frep, 'cases': {}}
    cases = {'V35 (perfil mitjà exponencial, 1 màscara)': [('MGN', lambda: mgn(np.maximum(e35, 0), full, limits=lim)), ('WOW', lambda: wow(e35, full, NS, False, False)), ('WOWbil', lambda: wow(e35, full, NS, True, False))],
             'V36 (separable + 2 màscares)': [('MGN', lambda: B.mgn2(np.maximum(e36, 0), full, m, limits=lim)), ('WOW', lambda: B.wow2(e36, full, m, NS, False)), ('WOWbil', lambda: B.wow2(e36, full, m, NS, True))],
             'V36 farcit, 1 màscara (per separar efectes)': [('MGN', lambda: mgn(np.maximum(e36, 0), full, limits=lim)), ('WOW', lambda: wow(e36, full, NS, False, False))]}
    for tag, lst in cases.items():
        for name, fn in lst:
            out = np.where(m, fn(), np.nan); rb, sd = ring_bias(out, m, r); es = edge_step(out, m, dist, sd)
            rep['cases'][f'{tag} / {name}'] = {'biaix_anell_1.03_1.3_sigma': rb, 'grao_vora_forat_sigma': es}; log(f'{tag} / {name}: biaix d\'anell {rb:.2f} σ · graó a la vora del forat {es:+.2f} σ')
    savejson(REB36 / 'A8_roi_farcit.json', rep); log('A8 fet')


if __name__ == '__main__':
    main()
