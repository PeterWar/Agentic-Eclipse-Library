"""A11 (V37) · El rivet a la vora del forat, per sector azimutal, en ROI (2,9 R☉; 7 escales al WOW): variants del farcit dels
operadors isotròpics i del NRGF als anells parcials. Mètrica per sector (24): mitjana de la capa a 0–8 px de la vora del forat
menys a 20–40 px, en σ de la capa (1,05–1,6); i el biaix d'anell global 1,03–1,3. Variants MGN/WOW:
  A  farcit V35 (perfil mitjà; anells parcials sobreescrits per l'extrapolació des del primer anell sencer)
  B  farcit amb les MITJANES DELS ANELLS PARCIALS conservades i continuació cap endins des del primer anell amb dada, amb el pendent local
  C  B + variància/potència només sobre el suport real (dues màscares)
NRGF: (a) estadístiques parcials (V36); (b) μ i σ dels anells parcials extrapolats en ln des dels 40 primers anells sencers."""
import os, sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.argv = [sys.argv[0]]; sys.path.insert(0, str(ROOT / 'research/tools/v36_20260908'))
import b4c_purs_experimental as BX      # mgn2 / wow2 (dues màscares)
import numpy as np, cv2
from common import RS, CX, CY, log, savejson
from wow_filters import wow
from local_filters import mgn
C36 = ROOT / 'research/tools/v36_20260908/cau'; REB37 = ROOT / 'output/v37_20260908/4-rebuts'; RAD = 2.9; NB = 24


def farcit(a, m, r_px, mode):
    ri = np.round(r_px).astype('int32'); L = np.where(m, np.log(np.maximum(a, 1e-9)), 0).astype('float64'); n = np.bincount(ri[m]); s = np.bincount(ri[m], weights=L[m]); prof = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    nodes = np.arange(len(n)); full = np.flatnonzero(n >= 0.999 * 2 * np.pi * np.maximum(nodes, 1)); first_full = int(full[full > 0.9 * RS][0]); has = np.flatnonzero(n > 0); first_data = int(has[has > 0.5 * RS][0])
    p = prof.copy()
    if mode == 'A':
        k = np.arange(first_full, first_full + 20); slope = float(np.polyfit(k, prof[k], 1)[0]); p[:first_full] = prof[first_full] + slope * (np.arange(first_full) - first_full)
    else:   # B: mitjanes parcials conservades; pendent local dels 10 primers anells amb dada (≥ 30 px cadascun)
        ok = np.flatnonzero((n >= 30) & (nodes >= first_data))[:10]; slope = float(np.polyfit(ok, prof[ok], 1)[0]); p[:first_data] = prof[first_data] + slope * (np.arange(first_data) - first_data)
        bad = ~np.isfinite(p[:first_full]); idx = np.flatnonzero(bad)
        if idx.size:
            good = np.flatnonzero(~bad); p[idx] = np.interp(idx, good, p[:first_full][good])
    last = int(np.flatnonzero(np.isfinite(p))[-1]); p[last + 1:] = p[last]; bad = ~np.isfinite(p); p[bad] = np.interp(nodes[bad], nodes[~bad], p[~bad])
    return np.where(m, a, np.exp(np.interp(r_px, nodes, p))).astype(np.float32), {'first_data': first_data, 'first_full': first_full, 'slope': slope}


def nrgf(a, m, r_px, mode):
    ri = np.floor(r_px).astype('int32'); nr = int(ri.max()) + 1; ids = ri[m]; v = a[m].astype('float64'); count = np.bincount(ids, minlength=nr); s = np.bincount(ids, weights=v, minlength=nr); s2 = np.bincount(ids, weights=v * v, minlength=nr)
    mean = np.divide(s, count, out=np.zeros(nr), where=count > 0); std = np.sqrt(np.maximum(0, np.divide(s2, count, out=np.zeros(nr), where=count > 0) - mean * mean)); good = count > 0; nodes = np.arange(nr) + .5
    if mode == 'b':
        full = np.flatnonzero(count >= 0.999 * 2 * np.pi * nodes); r_in = int(full[full > 0.9 * RS][0]); k = np.arange(r_in, r_in + 40)
        cm = np.polyfit(k, np.log(np.maximum(mean[k], 1e-9)), 1); cs = np.polyfit(k, np.log(np.maximum(std[k], 1e-9)), 1); inner = np.flatnonzero(good & (np.arange(nr) < r_in))
        mean[inner] = np.exp(np.polyval(cm, inner)); std[inner] = np.exp(np.polyval(cs, inner))
    mu = np.interp(r_px, nodes[good], mean[good]).astype('float32'); sd = np.interp(r_px, nodes[good], std[good]).astype('float32'); return np.divide(a - mu, sd, out=np.zeros_like(a), where=sd > 0)


def metrics(out, m, r, dist, sec):
    sd = float(np.nanstd(out[m & (r > 1.05) & (r < 1.6)])); riv = []
    for b in range(NB):
        near = m & (sec == b) & (dist > 0) & (dist <= 8) & (r < 1.15); far = m & (sec == b) & (dist > 20) & (dist <= 40) & (r < 1.2); riv.append((np.nanmean(out[near]) - np.nanmean(out[far])) / sd if near.sum() > 20 and far.sum() > 20 else np.nan)
    rs = np.arange(0.98, 1.6, 0.01); med = [np.median(out[m & (r >= a0) & (r < a0 + 0.01)]) / sd if (m & (r >= a0) & (r < a0 + 0.01)).sum() > 50 else np.nan for a0 in rs]; z = np.array(med); zz = z - np.nanmedian(z[rs > 1.3])
    near_all = m & (dist > 0) & (dist <= 8) & (r < 1.15)
    return {'rivet_per_sector': riv, 'rivet_max_abs': float(np.nanmax(np.abs(riv))), 'rivet_mediana_abs': float(np.nanmedian(np.abs(riv))), 'biaix_anell_1.03_1.3': float(np.nanmax(np.abs(zz[(rs >= 1.03) & (rs < 1.3)]))), 'std_a_la_vora_sobre_sd': float(np.nanstd(out[near_all]) / sd)}


def main():
    G = np.load(C36 / 'base_G_v36.npy', mmap_mode='r'); M = np.load(C36 / 'support_v36.npy')
    y0, y1, x0, x1 = int(CY - RAD * RS), int(CY + RAD * RS), int(CX - RAD * RS), int(CX + RAD * RS)
    a = np.array(G[y0:y1, x0:x1], np.float32); m = M[y0:y1, x0:x1].copy(); yy, xx = np.ogrid[:a.shape[0], :a.shape[1]]
    r_px = np.hypot(xx + x0 - CX, yy + y0 - CY).astype(np.float32); r = r_px / RS; t = np.degrees(np.arctan2(yy + y0 - CY, xx + x0 - CX)); m &= a > 0
    dist = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5) * (r < 1.3); sec = np.floor((t + 180) / 360 * NB).astype(int) % NB
    lim = [float(np.maximum(a, 0)[m].min()), float(np.maximum(a, 0)[m].max())]; NS = 7; full = np.ones_like(m); rep = {}
    eA, fA = farcit(a, m, r_px, 'A'); eB, fB = farcit(a, m, r_px, 'B'); log(f'farcit A {fA} · B {fB}')
    cases = [('A/MGN', lambda: mgn(np.maximum(eA, 0), full, limits=lim)), ('B/MGN', lambda: mgn(np.maximum(eB, 0), full, limits=lim)), ('C/MGN', lambda: BX.mgn2(np.maximum(eB, 0), full, m, limits=lim)),
             ('A/WOW', lambda: wow(eA, full, NS, False, False)), ('B/WOW', lambda: wow(eB, full, NS, False, False)), ('C/WOW', lambda: BX.wow2(eB, full, m, NS, False)),
             ('A/WOWbil', lambda: wow(eA, full, NS, True, False)), ('B/WOWbil', lambda: wow(eB, full, NS, True, False)),
             ('a/NRGF', lambda: nrgf(a, m, r_px, 'a')), ('b/NRGF', lambda: nrgf(a, m, r_px, 'b'))]
    for name, fn in cases:
        out = np.where(m, fn(), np.nan); rep[name] = metrics(out, m, r, dist, sec)
        log(f"{name}: rivet màx {rep[name]['rivet_max_abs']:.2f} σ, mediana {rep[name]['rivet_mediana_abs']:.2f} σ · biaix anell {rep[name]['biaix_anell_1.03_1.3']:.2f} σ · std a la vora/σ {rep[name]['std_a_la_vora_sobre_sd']:.2f} · sectors W(−172,−158,−142) " + ' '.join(f"{rep[name]['rivet_per_sector'][i]:+.2f}" for i in (0, 1, 2)) + ' · E(+8,+22,+38) ' + ' '.join(f"{rep[name]['rivet_per_sector'][i]:+.2f}" for i in (12, 13, 14)))
    savejson(REB37 / 'A11_roi_rivet.json', rep); log('A11 fet')


if __name__ == '__main__':
    main()
