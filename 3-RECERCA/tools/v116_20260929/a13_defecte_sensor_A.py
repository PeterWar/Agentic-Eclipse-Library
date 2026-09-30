"""a13 (29-09-2026) · La marca taronja és un defecte FIX AL SENSOR de la Sony (visible a l'apuntament A)? Si ho és, la B —el mateix sensor, 750 px
desplaçat— l'ha de portar a un altre lloc del cel, desplaçat pel salt (−233, +713) px (research/96; ± la rotació de camp de 7,9′).
Mètode: mapa de detall orientat (θ = 2,8°, σ al llarg 30 px, a través 1,5 px) d'A (sony_A_corr_v42) i de B (sony_B_total_v42 / pesos), canal G.
Plantilla = el mapa d'A en una franja de ±12 px al voltant de la línia (x 5950–6950). Correlació normalitzada (NCC) de la plantilla sobre el mapa de
B en una finestra de ±150 px al voltant de cada desplaçament previst (+ i −), i CONTROL NUL: la mateixa NCC a 300 desplaçaments a l'atzar
(mateix radi al Sol ± 1 R☉, lluny del traç). També la NCC de la plantilla sobre el mapa d'A mateix a aquests llocs (A no hi ha de tenir res).
Sortida: taronja/A13_DEFECTE_SENSOR.json i A13_*.png"""
import json, numpy as np, cv2
from pathlib import Path
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'; OUT = O / 'taronja'
lab = np.load(O / 'marques_V115_etiquetes.npy', mmap_mode='r')
sub = np.asarray(lab[4300:4800, 5900:7100]) == 11; cols = np.nonzero(sub.any(0))[0]; yc = np.array([np.nonzero(sub[:, c])[0].mean() for c in cols]) + 4300; xs = cols + 5900
a_, b_ = np.polyfit(xs, yc + 6, 1)                         # la línia fosca d'A és a +6 px del centre del traç
At = np.load(R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/b3/cau/sony_A_corr_v42.npy', mmap_mode='r')
Bt = np.load(R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_total_v42.npy', mmap_mode='r'); Bw = np.load(R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_weights_v42.npy', mmap_mode='r')
H, W = 7506, 10551; SOL = (5361.768, 3775.748); RS = 440.603
def orientat(d, th_deg, sl=30, sc=1.5):
    k = int(4 * sl) | 1; yy, xx = np.mgrid[-(k // 2):k // 2 + 1, -(k // 2):k // 2 + 1].astype(np.float32); t = np.radians(th_deg)
    u = xx * np.cos(t) - yy * np.sin(t); v = xx * np.sin(t) + yy * np.cos(t); ker = np.exp(-0.5 * (u / sl) ** 2 - 0.5 * (v / sc) ** 2); ker /= ker.sum()
    return cv2.filter2D(d, -1, ker, borderType=cv2.BORDER_REFLECT)
def mapa(src, w, x0, y0, x1, y1):
    s = np.asarray(src[y0:y1, x0:x1, 1], np.float32)
    if w is not None: s = s / np.maximum(np.asarray(w[y0:y1, x0:x1, 1], np.float32), 1e-6)
    m = np.isfinite(s) & (s > 0); mf = m.astype(np.float32); x = np.where(m, np.log(np.maximum(s, 1e-9)), 0).astype(np.float32)
    d = np.where(m, x - cv2.GaussianBlur(x, (0, 0), 15) / np.maximum(cv2.GaussianBlur(mf, (0, 0), 15), 1e-6), 0).astype(np.float32)
    return orientat(d, -2.8), m
# plantilla a A
TX0, TX1 = 5950, 6950; ty = a_ * np.arange(TX0, TX1) + b_; TY0, TY1 = int(ty.min()) - 40, int(ty.max()) + 40
MA, mA = mapa(At, None, TX0, TY0, TX1, TY1)
yy, xx = np.mgrid[TY0:TY1, TX0:TX1]; banda = np.abs(yy - (a_ * xx + b_)) <= 12
T = np.where(banda, MA, 0).astype(np.float32); T[banda] -= T[banda].mean(); T[~banda] = 0; nT = np.sqrt((T[banda] ** 2).sum())
def ncc_a(M, dx, dy, Mx0, My0):
    """NCC de la plantilla col·locada amb el desplaçament (dx, dy) sobre el mapa M (origen Mx0, My0)."""
    y0 = TY0 + dy - My0; x0 = TX0 + dx - Mx0
    if y0 < 0 or x0 < 0 or y0 + T.shape[0] > M.shape[0] or x0 + T.shape[1] > M.shape[1]: return np.nan
    P = M[y0:y0 + T.shape[0], x0:x0 + T.shape[1]][banda]; P = P - P.mean(); return float((P * T[banda]).sum() / max(nT * np.sqrt((P ** 2).sum()), 1e-12))
res = dict(linia_A=dict(a=a_, b=b_, x=[TX0, TX1]), cerques={})
for nom, src, w in (('B', Bt, Bw), ('A', At, None)):
    for sgn in (+1, -1):
        cx, cy = sgn * 233, -sgn * 713; S = 150
        x0, y0 = max(TX0 + cx - S, 0), max(TY0 + cy - S, 0); x1, y1 = min(TX1 + cx + S, W), min(TY1 + cy + S, H)
        M, m = mapa(src, w, x0, y0, x1, y1); best = (-2, 0, 0); grid = {}
        for dy in range(cy - S, cy + S + 1, 2):
            for dx in range(cx - S, cx + S + 1, 4):
                v = ncc_a(M, dx, dy, x0, y0)
                if np.isfinite(v): grid[(dx, dy)] = v; best = max(best, (v, dx, dy))
        # afinament
        v0, bx, by = best
        for dy in range(by - 3, by + 4):
            for dx in range(bx - 5, bx + 6):
                v = ncc_a(M, dx, dy, x0, y0)
                if np.isfinite(v) and v > best[0]: best = (v, dx, dy)
        vals = np.array(list(grid.values()))
        res['cerques'][f'{nom} {sgn:+d}'] = dict(previst=[cx, cy], millor_ncc=round(best[0], 4), a=[best[1], best[2]], ncc_p50_p99_finestra=[round(float(np.percentile(vals, q)), 4) for q in (50, 99)])
        print(f'{nom} desplaçament {sgn:+d}: previst ({cx:+d}, {cy:+d}) · millor NCC {best[0]:+.3f} a ({best[1]:+d}, {best[2]:+d}) · finestra p50 {np.percentile(vals, 50):+.3f} p99 {np.percentile(vals, 99):+.3f}', flush=True)
# control nul: desplaçaments a l'atzar al mateix radi (±1 R☉), lluny del traç, sobre B
rng = np.random.default_rng(7); nul = []; rT = np.hypot((TX0 + TX1) / 2 - SOL[0], np.mean(ty) - SOL[1]) / RS
while len(nul) < 300:
    ang = rng.uniform(0, 2 * np.pi); rr_ = rng.uniform(rT - 1, rT + 1) * RS; cx = int(SOL[0] + rr_ * np.cos(ang) - (TX0 + TX1) / 2); cy = int(SOL[1] - rr_ * np.sin(ang) - np.mean(ty))
    if abs(cx) < 400 and abs(cy) < 200: continue
    x0, y0 = TX0 + cx, TY0 + cy
    if x0 < 0 or y0 < 0 or x0 + T.shape[1] > W or y0 + T.shape[0] > H: continue
    M, m = mapa(Bt, Bw, x0, y0, x0 + T.shape[1], y0 + T.shape[0])
    if m.mean() < 0.95: continue
    nul.append(ncc_a(M, cx, cy, x0, y0))
nul = np.array(nul); res['control_nul_B'] = dict(n=len(nul), p50=round(float(np.median(nul)), 4), p95=round(float(np.percentile(nul, 95)), 4), p99=round(float(np.percentile(nul, 99)), 4), max=round(float(nul.max()), 4))
print('control nul (B, 300 llocs a l\'atzar al mateix radi):', res['control_nul_B'], flush=True)
(OUT / 'A13_DEFECTE_SENSOR.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
