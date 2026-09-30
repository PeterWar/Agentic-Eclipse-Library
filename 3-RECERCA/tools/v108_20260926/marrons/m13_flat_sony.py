"""m13 · El flat de la Sony té els traços T1, T2 o T6? Com m12 per a la A7RIIIA (53 flats; centre radial declarat raw (2660, 4000)).
Cada traç es porta al sensor amb els DOS apuntaments (A: Sol raw (3665,5, 3478,1); B: (3894,9, 2772,6)); eixos del sensor al llenç
mesurats amb el salt (u_x = (0,7230, −0,6909), u_y = (0,6909, 0,7230)), k = 3,202″/2,149″ = 1,490 px del llenç per px del sensor.
Si un traç és una línia del flat, apareix al residu no radial a la posició d'UN apuntament (el que el porta) i la del camp de l'altre
apuntament és on n'hi hauria la còpia. Sortida: M13_FLAT_SONY.json i la vista del SENSOR sencer."""
import sys, json, glob, os
from pathlib import Path
import numpy as np, cv2, rawpy
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
RI = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/raw_inputs/SONYTOT'
fl = sorted(glob.glob(str(RI / 'flats/*.ARW')))
stack = []
for f in fl:
    with rawpy.imread(f) as r:
        raw = r.raw_image.astype(np.float32); pat = r.raw_pattern.copy(); bl = float(np.mean(r.black_level_per_channel)); desc = r.color_desc.decode()
    gi = [(i, j) for i in range(2) for j in range(2) if desc[pat[i, j]] == 'G']
    g = 0.5 * ((raw[gi[0][0]::2, gi[0][1]::2] - bl) + (raw[gi[1][0]::2, gi[1][1]::2] - bl)); stack.append(g / np.median(g[800:1800, 1200:2800]))
print('flats', len(stack), 'patró', pat.tolist(), gi, 'forma', stack[0].shape, flush=True)
M = np.median(np.stack(stack), 0).astype(np.float32); del stack; h, w = M.shape
vis = np.zeros_like(M, bool); vis[:, :7968 // 2] = True
CY, CX = 2660 / 2, 4000 / 2
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); rad = np.hypot(yy - CY, xx - CX); RMAX = float(rad[vis].max()); nb = 260
idx = np.clip((rad / RMAX * nb).astype(np.int32), 0, nb - 1)
s = np.bincount(idx[vis], M[vis], nb); c = np.bincount(idx[vis], None, nb); prof = np.where(c > 75, s / np.maximum(c, 1), np.nan)
prof = np.where(np.isfinite(prof), prof, np.nanmedian(prof)); res = np.where(vis, M / prof[idx] - 1, 0).astype(np.float32)
np.save(OUT / 'flat_sony_residu_no_radial.npy', res)
wv = vis.astype(np.float32); ng = lambda x, s_: cv2.GaussianBlur(x * wv, (0, 0), s_) / np.maximum(cv2.GaussianBlur(wv, (0, 0), s_), 1e-6)
SA, SB, LIM = float(os.environ.get('M13_SA', 4)), float(os.environ.get('M13_SB', 60)), float(os.environ.get('M13_LIM', 0.0015))
hp = np.where(vis, ng(res, SA) - ng(res, SB), 0)
g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text()); K = 3.2020 / 2.149
ux = np.array([0.7230, -0.6909]); uy = np.array([0.6909, 0.7230]); SOLS = {'A': np.array([3665.5, 3478.1]), 'B': np.array([3894.9, 2772.6])}; solc = np.array(SOL)
def a_sensor(p, ap): d = (np.array(p) - solc) / K; return SOLS[ap] + np.array([d @ ux, d @ uy])
u8 = np.clip(128 + 127 * hp / LIM, 0, 255).astype(np.uint8); rgb = cv2.cvtColor(u8, cv2.COLOR_GRAY2BGR); info = {}
r1 = np.where(vis, ng(res, 1.0), np.nan).astype(np.float32)
for tr in TRACOS:
    z = g[str(tr['k'])]; info[tr['k']] = {}
    for ap, col in (('A', (0, 0, 255)), ('B', (255, 120, 0))):
        a0 = a_sensor(z['extrems'][0], ap) / 2; a1 = a_sensor(z['extrems'][1], ap) / 2
        dentro = all(0 <= a[0] < w and 0 <= a[1] < h for a in (a0, a1))
        d = (a1 - a0) / np.linalg.norm(a1 - a0); n = np.array([-d[1], d[0]]); L = np.linalg.norm(a1 - a0)
        s_ = np.arange(0, L, 1.0); t = np.arange(-60, 60.1, 0.5)
        X = (a0[0] + s_[:, None] * d[0] + t[None, :] * n[0]).astype(np.float32); Y = (a0[1] + s_[:, None] * d[1] + t[None, :] * n[1]).astype(np.float32)
        P = cv2.remap(r1, X, Y, cv2.INTER_LINEAR, borderValue=np.nan); cob = float(np.isfinite(P).mean())
        if cob < 0.5: info[tr['k']][ap] = dict(cobertura=cob); continue
        with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
        k = (np.abs(t) >= 12) & (np.abs(t) <= 55); aa = np.polyfit(t[k], pr[k], 1); rr = pr - np.polyval(aa, t); j = np.argmin(np.where(np.abs(t) <= 8, rr, np.inf))
        info[tr['k']][ap] = dict(extrems_subpla=[a0.round(1).tolist(), a1.round(1).tolist()], cobertura=cob, solc_residu_flat=float(rr[j]), t_minim_subpla=float(t[j]), soroll_flancs=float(np.std(rr[k])))
        cv2.line(rgb, tuple(map(int, a0 + 8 * n)), tuple(map(int, a1 + 8 * n)), col, 1); cv2.line(rgb, tuple(map(int, a0 - 8 * n)), tuple(map(int, a1 - 8 * n)), col, 1)
        cv2.putText(rgb, f"T{tr['k']}{ap}", tuple(map(int, a1 + 14 * n)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
        print(f"T{tr['k']} apuntament {ap}: {a0.round(0)}→{a1.round(0)} cob {cob:.2f} solc {rr[j]*1e4:+.1f}‱ a t {t[j]:+.1f} (soroll {np.std(rr[k])*1e4:.1f}‱)", flush=True)
cv2.putText(rgb, f'FLAT Sony ({len(fl)} flats, G) / perfil radial - 1, passa alt s{SA:g}/s{SB:g} a +-{LIM*100:g} % - SENSOR sencer (1/2); vermell = apuntament A, blau = B', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 220, 255), 2)
cv2.imwrite(str(OUT / 'diag_flat_sony_residu_no_radial_sensor.png'), cv2.resize(rgb, (w * 2 // 3, h * 2 // 3), interpolation=cv2.INTER_AREA))
desa(OUT / 'M13_FLAT_SONY.json', dict(n_flats=len(fl), traços=info))
