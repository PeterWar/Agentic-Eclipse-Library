"""m10 · Cerca CEGA de rectes fosques (sense la geometria de M3 ni les marques): transformada de Radon local del contrast fi (σ 4/40 relatiu)
de cada apilat independent, en una caixa de ±(L/2 + 600) px al voltant de cada traç, a tots els angles (pas 0,25°) i desplaçaments
(pas 2 px), normalitzada per la dada vàlida; la línia és un segment de llargada L (la del traç) centrat on sigui dins de la caixa.
Per a cada apilat, les 5 rectes més fosques (z contra tot el mapa) i si coincideixen amb el traç (|Δθ| < 2°, |Δt| < 20 px).
Si els apilats independents (Sony A, Sony B, Vixen) troben CEGAMENT la mateixa recta, aquesta és real (cel o procés), no gra.
Sortida: M10_CERCA_CEGA.json."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text())
R97 = ARREL / '4-RESULTATS/v97_refundacio_20260924'; CR = R97 / 'cadena_raw'
import os
FONTS = {'sony_A': CR / 'b2_sony_A/cau/sony_A_total_v36.npy', 'sony_B': CR / 'b2_sony_B/cau/sony_B_total_v42.npy', 'vixen': R97 / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy',
         'base_E': ARREL / '4-RESULTATS/v103_banda_20260926/E/lineal_v103/base_G.npy'}
ES = ARREL / '4-RESULTATS/v105_limbe_20260926/claude/estat_v105'
if os.environ.get('M10_FONTS') == 'filtres':      # la mateixa cerca cega al ràster de les WOW i de la NRGF (on Pere veu els traços)
    FONTS = {'L55_P04_WOW': ES / 'L55_G.npy', 'L56_P05_WOW_bil': ES / 'L56_G.npy', 'L41_P01_NRGF': ES / 'L41_G.npy', 'L54_P03_MGN': ES / 'L54_G.npy'}
ANG = np.arange(0, 180, 0.25)
res = {}
for tr in TRACOS:
    z = g[str(tr['k'])]; c = np.array(z['centre']); ang_tr = z['angle_graus']; L = min(z['llarg'], 1500.0)
    half = int(L / 2 + 600); x0, y0 = int(max(0, c[0] - half)), int(max(0, c[1] - half)); x1, y1 = int(min(W, c[0] + half)), int(min(H, c[1] + half))
    res[tr['k']] = {'caixa': [x0, y0, x1, y1]}
    for nom, p in FONTS.items():
        a = np.load(p, mmap_mode='r'); img = np.asarray(a[y0:y1, x0:x1, 1] if a.ndim == 3 else a[y0:y1, x0:x1], np.float32)
        m = np.isfinite(img) & (img > 0); w = m.astype(np.float32); img = np.where(m, img, 0)
        if m.mean() < 0.3: continue
        ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
        ok = (cv2.erode(w, np.ones((81, 81), np.uint8)) > 0)
        # fora del camp exterior (r < 5 R☉) les serpentines radials dominen: s'exclouen
        yy, xx = np.mgrid[y0:y1, x0:x1]; ok &= np.hypot(xx - SOL[0], yy - SOL[1]) > 5 * RSOL; del yy, xx
        ok[:80] = False; ok[-80:] = False; ok[:, :80] = False; ok[:, -80:] = False     # la vora de la CAIXA fa un fals graó al DoG (vora reflectida): fora
        r = np.where(ok, ng(img, 4) / np.maximum(ng(img, 40), 1e-12) - 1, 0).astype(np.float32); wk = ok.astype(np.float32)
        # retall del soroll extrem (estrelles residuals) abans d'integrar
        sd = 1.4826 * np.median(np.abs(r[ok])) if ok.any() else 1; r = np.clip(r, -5 * sd, 5 * sd) * wk
        hh, ww = r.shape; ctr = (ww / 2, hh / 2); best = []
        # a cada angle: gir de la imatge perquè la recta quedi horitzontal; mitjana en finestres de llargada L al llarg de cada fila
        Lk = int(L)
        for th in ANG:
            Mr = cv2.getRotationMatrix2D(ctr, th, 1.0)   # gira θ en sentit antihorari: una recta a angle θ (y avall) queda horitzontal
            R_ = cv2.warpAffine(r, Mr, (ww, hh), flags=cv2.INTER_LINEAR, borderValue=0); Wr = cv2.warpAffine(wk, Mr, (ww, hh), flags=cv2.INTER_LINEAR, borderValue=0)
            R2 = cv2.resize(R_, (ww, hh // 2), interpolation=cv2.INTER_AREA); W2 = cv2.resize(Wr, (ww, hh // 2), interpolation=cv2.INTER_AREA)
            S = cv2.boxFilter(R2, -1, (Lk, 1), normalize=False, borderType=cv2.BORDER_CONSTANT); N = cv2.boxFilter(W2, -1, (Lk, 1), normalize=False, borderType=cv2.BORDER_CONSTANT)
            V = np.where(N > 0.7 * Lk, S / np.maximum(N, 1), np.nan)
            if np.isfinite(V).sum() > 1000:
                # z DINS de cada angle: la interpolació del gir suavitza el soroll a angles no alineats (a 0° i 90° no n'hi ha i els extrems són més grans)
                vv = V[np.isfinite(V)]; md = np.median(vv); sdv = 1.4826 * np.median(np.abs(vv - md)) + 1e-15; Z = (V - md) / sdv
                j = np.nanargmin(Z); iy, ix = np.unravel_index(j, Z.shape); best.append((float(Z[iy, ix]), float(th), int(iy) * 2, int(ix), float(V[iy, ix])))
        vals = np.array([b[0] for b in best]); med = np.median(vals); mad = 1.4826 * np.median(np.abs(vals - med))
        # 5 millors rectes DIFERENTS (separades > 3° o > 40 px)
        ordre = []; 
        for q in np.argsort(vals):
            if all(abs(((best[q][1] - best[o][1]) + 90) % 180 - 90) > 3 or abs(best[q][2] - best[o][2]) > 40 for o in ordre): ordre.append(q)
            if len(ordre) == 5: break
        top = []
        for q in ordre:
            zv, th, iy, ix, v = best[q]
            # de coordenades girades a llenç: punt (ix, iy) girat → invers
            Mi = cv2.invertAffineTransform(cv2.getRotationMatrix2D(ctr, th, 1.0)); px, py = Mi @ np.array([ix, iy + 1, 1.0]); px += x0; py += y0
            ang_llenc = (-th) % 180; da = abs((ang_llenc - ang_tr + 90) % 180 - 90)
            n_tr = np.array([-np.sin(np.radians(ang_tr)), np.cos(np.radians(ang_tr))]); dt = float((np.array([px, py]) - c) @ n_tr)
            top.append(dict(valor=v, z_dins_angle=zv, z_entre_angles=float((zv - med) / mad), angle_llenc=float(ang_llenc), centre=[float(px), float(py)], dtheta_vs_traç=float(da), dt_vs_traç=dt, coincideix=bool(da < 2 and abs(dt) < 20)))
        res[tr['k']][nom] = top
        print(f"T{tr['k']} {nom:7s} " + ' | '.join(f"{t_['valor']*1e4:+.1f}‱ z{t_['z_dins_angle']:+.1f} {t_['angle_llenc']:.1f}° dθ{t_['dtheta_vs_traç']:.1f} dt{t_['dt_vs_traç']:+.0f}{' ✓' if t_['coincideix'] else ''}" for t_ in top[:5]), flush=True)
desa(OUT / ('M10_CERCA_CEGA_FILTRES.json' if os.environ.get('M10_FONTS') == 'filtres' else 'M10_CERCA_CEGA.json'), res)
