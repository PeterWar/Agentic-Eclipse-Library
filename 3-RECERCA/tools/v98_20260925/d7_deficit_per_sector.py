"""d7 (V98) · El dèficit de vora per fotograma (ln fotograma/referència neta en funció de D_obs, per classe) és el mateix a tots els sectors?
Si ho és, és una resposta de l'instrument (PSF + vora de la Lluna) i es pot calibrar com un camp pla; si depèn del lloc, no.
Sectors on hi ha referència neta (la Lluna s'allunya): 300–360, 0–60, 240–300. Limb frames de finestra comuna."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v98_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = float(meta['radius_model']) - RL
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - LX, yy - LY) - RL).astype(np.float32); th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
zona = (d >= 0) & (d < 40); d_z = d[zona]; th_z = th[zona]; nF = len(fr)
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
V = np.zeros((nF, zona.sum()), np.float32); Wz = np.zeros_like(V); Dz = np.zeros_like(V)
for j in range(nF):
    n_ = np.asarray(N[j, :, :, 1])[zona]; w_ = np.asarray(Wt[j, :, :, 1])[zona]; Dz[j] = np.asarray(Dm[j])[zona] + DR; V[j] = np.where(w_ > 0, n_ / np.maximum(w_, 1e-30), np.nan); Wz[j] = w_
net = Dz >= 25; ref = np.nansum(np.where(net, V * Wz, 0), 0) / np.maximum(np.nansum(np.where(net, Wz, 0), 0), 1e-30); okref = (net.sum(0) >= 10) & (ref > 0)
cls = np.array([classe(f['exposure']) for f in fr]); bins = np.arange(1, 14, 1.0); rep = {}
for c in ('curts', 'mitjans'):
    rep[c] = {}
    for nom, (a0, a1) in dict(dreta_baix=(300, 360), dreta_dalt=(0, 60), baix=(240, 300)).items():
        sec = okref & (th_z >= a0) & (th_z < a1); lr = []; dd = []
        for j in np.flatnonzero(cls == c):
            ok = sec & np.isfinite(V[j]) & (Wz[j] > 0); lr.append(np.log(V[j][ok] / ref[ok])); dd.append(Dz[j][ok])
        lr = np.concatenate(lr); dd = np.concatenate(dd); k = np.digitize(dd, bins)
        rep[c][nom] = {f'{bins[i-1]:.0f}': round(float(np.median(lr[k == i])), 3) for i in range(1, len(bins)) if (k == i).sum() > 200}
        print(c, nom, rep[c][nom], flush=True)
(O / 'D7_DEFICIT_PER_SECTOR.json').write_text(json.dumps(rep, indent=1))
