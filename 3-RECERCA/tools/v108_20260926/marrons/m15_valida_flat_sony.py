"""m15 · VALIDACIÓ SONY (com m14): l'estructura NO RADIAL del flat de la Sony (m13) és a les llums de la Vixen? Si ho és, el flat radial la deixa a l'apilat
i la cura a l'origen és calibrar amb el flat 2D. Mètode: el residu no radial del flat (graella del subpla G) es porta al llenç amb el
Sol de la Vixen (apuntament mitjà ponderat) i els eixos mesurats del seu marc; es compara amb el passa alt de ln(apilat Vixen) i de
ln(Vixen/Sony) (la Sony és un altre instrument: el cel s'hi cancel·la) al camp exterior (r > 3 R☉), banda σ 2–30 px. Pendent i correlació;
control nul: el mateix amb el mapa del flat desplaçat 150 px. Afinament de l'encaix (±6 px). Sortida: M14_VALIDA_FLAT_VIXEN.json."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
R97 = ARREL / '4-RESULTATS/v97_refundacio_20260924'; CR = R97 / 'cadena_raw'
import os
AP = os.environ.get('AP', 'A')
res = np.load(OUT / 'flat_sony_residu_no_radial.npy')                       # (2660, 4000) subpla G
meta = [m for m in json.loads((CR / 'sources_v36/cau/sony_meta.json').read_text())['frames'] if m['group'] == 'sony_' + AP]
ws = np.array([m['w_max'] for m in meta]); sx = np.array([m['sol_xy_sensor'] for m in meta]); SUN_RAW = (ws[:, None] * sx).sum(0) / ws.sum()
ux = np.array([0.7230, -0.6909]); uy = np.array([0.6909, 0.7230]); K = 3.2020 / 2.149
def mapa_flat_al_llenc(dx=0.0, dy=0.0, desp=0.0, box=(0, 0, W, H)):
    x0, y0, x1, y1 = box; yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); cx = xx - SOL[0] + desp; cy = yy - SOL[1]
    sx_ = SUN_RAW[0] + (cx * ux[0] + cy * ux[1]) / K + dx; sy_ = SUN_RAW[1] + (cx * uy[0] + cy * uy[1]) / K + dy
    # G del subpla: (fila parell, col senar) i (fila senar, col parell) → centre ≈ (s − 0,5)/2
    return cv2.remap(res, ((sx_ - 0.5) / 2).astype(np.float32), ((sy_ - 0.5) / 2).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
def hp(x, m, sa=2, sb=30):
    w = m.astype(np.float32); x = np.where(m, x, 0)
    ng = lambda a, s: cv2.GaussianBlur(a * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
    return np.where(m, ng(x, sa) - ng(x, sb), np.nan).astype(np.float32)
# caixa: tota la Vixen al camp exterior (a pas complet, però per trossos per la memòria)
V = np.load(os.environ.get('STACK') or (CR / ('b2_sony_A/cau/sony_A_total_v36.npy' if AP == 'A' else 'b2_sony_B/cau/sony_B_total_v42.npy')), mmap_mode='r'); S = np.load(R97 / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', mmap_mode='r')
TROSSOS = [(x, y, min(W, x + 2400), min(H, y + 2400)) for y in range(0, H, 2400) for x in range(0, W, 2400)]
def estadistica(dx, dy, desp):
    sxy = sxx = syy = n = 0.0; sxy2 = syy2 = 0.0
    for box in TROSSOS:
        x0, y0, x1, y1 = box
        v = np.asarray(V[y0:y1, x0:x1, 1], np.float32); s = np.asarray(S[y0:y1, x0:x1, 1], np.float32)
        yy, xx = np.mgrid[y0:y1, x0:x1]; r = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del yy, xx
        Rm = mapa_flat_al_llenc(dx, dy, desp, box)
        s = np.where(np.isfinite(s) & (s > 0), s, np.nan)
        m = np.isfinite(v) & (v > 0) & np.isfinite(Rm) & (r > 3.0)
        m = cv2.erode(m.astype(np.uint8), np.ones((61, 61), np.uint8)) > 0
        if m.sum() < 1e5: continue
        a = hp(np.log(np.maximum(v, 1e-9)), m); mb = m & np.isfinite(s); b = hp(np.log(np.maximum(v, 1e-9)) - np.log(np.where(mb, s, 1.0)), mb) if mb.sum() > 1e5 else np.full_like(a, np.nan); f = hp(Rm, m)
        k = m & np.isfinite(a) & np.isfinite(f)
        sa_ = 1.4826 * np.median(np.abs(a[k])); k &= np.abs(a) < 5 * sa_           # fora estrelles i guspires
        fk = f[k].astype(np.float64); ak = a[k].astype(np.float64); bk = np.nan_to_num(b[k].astype(np.float64)); kb = np.isfinite(b[k])
        sxy += (fk * ak).sum(); sxx += (fk * fk).sum(); syy += (ak * ak).sum(); sxy2 += (fk * bk * kb).sum(); syy2 += (bk * bk * kb).sum(); n += k.sum()
    return dict(n=int(n), pendent_lnV=sxy / sxx, corr_lnV=sxy / np.sqrt(sxx * syy), pendent_lnV_S=sxy2 / sxx, corr_lnV_S=sxy2 / np.sqrt(sxx * syy2 + 1e-30))
out = {'sol_raw_mitja': SUN_RAW.tolist()}
best = None
OFS = [(int(v.split(',')[0]), int(v.split(',')[1])) for v in os.environ['OFS'].split(';')] if os.environ.get('OFS') else [(dx, dy) for dx in (-4, -2, 0, 2, 4) for dy in (-4, -2, 0, 2, 4)]
for dx, dy in OFS:
    if True:
        q = estadistica(dx, dy, 0.0); print(f'[{AP}] encaix dx {dx:+d} dy {dy:+d}: corr lnSony {q["corr_lnV"]:+.4f} pendent {q["pendent_lnV"]:+.3f} | corr ln(Sony/Vixen) {q["corr_lnV_S"]:+.4f} pendent {q["pendent_lnV_S"]:+.3f}', flush=True)
        if best is None or q['corr_lnV'] > best[2]['corr_lnV']: best = (dx, dy, q)
out['encaix'] = dict(dx=best[0], dy=best[1], **best[2])
out['nul_desplacat_150px'] = estadistica(best[0], best[1], 150.0); print('NUL (150 px):', out['nul_desplacat_150px'], flush=True)
desa(OUT / f"M15_VALIDA_FLAT_SONY_{AP}{os.environ.get('SUFIX', '')}.json", out)
