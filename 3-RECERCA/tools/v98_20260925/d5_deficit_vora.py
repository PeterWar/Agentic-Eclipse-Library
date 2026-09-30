"""d5 (V98) · El dèficit de vora de cada fotograma, MESURAT a la dada (no la taula V38): per a cada fotograma Vixen de la caixa lunar
(limb_frames, 67 fotogrames), ln(valor del fotograma / referència neta) en funció de la distància D al limbe OBSERVAT d'aquell fotograma
(D_obs = D_model + (R_model − R_Lluna)), per classe d'exposició. Referència neta de cada píxel: mitjana ponderada (pesos LDIC) dels fotogrames
amb D_obs ≥ 25 px. Només píxels a 0–40 px del limbe de presentació on hi ha referència neta (la dreta i baix-dreta: la Lluna s'allunya).
Serveix per triar la guarda física de cada classe: la D a partir de la qual el biaix és < 1 % (Codex, 25-09: selecció física, no amplada fixa)."""
import sys, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; RES = ARREL / '4-RESULTATS/v97_refundacio_20260924'; O = ARREL / '4-RESULTATS/v98_20260925'
import os; LF = Path(os.environ.get('LF', RES / 'cadena_raw/limb_frames')); meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = float(meta['radius_model']) - RL
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32); th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
zona = (d > -30) & (d < 40)
ys, xs = np.nonzero(zona); d_z = d[zona]; th_z = th[zona]; nF = len(fr)
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
C = 1   # verd
V = np.zeros((nF, len(ys)), np.float32); Wz = np.zeros_like(V); Dz = np.zeros_like(V)
for j in range(nF):
    n_ = np.asarray(N[j, :, :, C])[zona]; w_ = np.asarray(Wt[j, :, :, C])[zona]; Dz[j] = np.asarray(Dm[j])[zona] + DR
    V[j] = np.where(w_ > 0, n_ / np.maximum(w_, 1e-30), np.nan); Wz[j] = w_
net = Dz >= 25
ref = np.nansum(np.where(net, V * Wz, 0), 0) / np.maximum(np.nansum(np.where(net, Wz, 0), 0), 1e-30); nref = net.sum(0)
okref = (nref >= 10) & (ref > 0)
bins = np.arange(-4, 30.5, 0.5); rep = dict(DR_px=DR, zona='0–40 px del limbe de presentació, píxels amb ≥ 10 fotogrames nets (D_obs ≥ 25)', classes={}, per_sector={})
cls = np.array([classe(f['exposure']) for f in fr])
for c in ('curts', 'mitjans', 'llargs'):
    js = np.flatnonzero(cls == c); lr = []; dd = []
    for j in js:
        ok = okref & np.isfinite(V[j]) & (Wz[j] > 0) & (d_z >= 0)
        lr.append(np.log(V[j][ok] / ref[ok])); dd.append(Dz[j][ok])
    lr = np.concatenate(lr); dd = np.concatenate(dd); k = np.digitize(dd, bins)
    prof = {f'{bins[i-1]:.1f}': (round(float(np.median(lr[k == i])), 4), int((k == i).sum())) for i in range(1, len(bins)) if (k == i).sum() > 300}
    rep['classes'][c] = dict(fotogrames=int(len(js)), exposicions=sorted(set(round(fr[j]['exposure'], 6) for j in js)), mediana_ln_per_D=prof)
    print(c, len(js), ' '.join(f"{kk}:{v[0]:+.3f}" for kk, v in prof.items()), flush=True)
(O / os.environ.get('D5_OUT', 'D5_DEFICIT_VORA.json')).write_text(json.dumps(rep, ensure_ascii=False, indent=1))
