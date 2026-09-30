"""d36 (V100 detall) · Amb quin pendent el COMPOST NATIU (render del Photoshop amb les capes d'ajust de Pere) mostra el detall tangencial de la dada?
β = regressió del detall tangencial del compost (ln de la lluminància codificada, bandes σ 0–8 px d'arc) sobre δ (el detall de la dada ponderat pel
seu senyal corroborat, CAPA_DETALL_BANDA.npz), per sector i per zona:
  · REFERÈNCIA: d = vora de dada de la V99 + 2 … + 7 px (on el compost ja té la textura dels filtres de la V99);
  · BANDA: la zona de la capa (alfa > 0,5) — amb el compost de la V99 hi ha de sortir β ≈ 0 (sense detall); amb la V100, β ≈ la de referència.
Ús: d36_escala_contra_compost.py <compost_lluna.tif> [<capa.npz>]"""
import sys, json
from pathlib import Path
import numpy as np, cv2, tifffile
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925/B'
T = tifffile.imread(sys.argv[1])[..., :3].astype(np.float64); ox, oy = 4600, 3000
Z = np.load(sys.argv[2] if len(sys.argv) > 2 else O / 'CAPA_DETALL_BANDA.npz'); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
Q9 = np.load(R9 / 'lineal_v99_franja/A3C_franja_silueta.npz'); DMIN9 = np.maximum(Q9['DMIN'], 0); NBZ = DMIN9.size
Lc = np.log(np.maximum((T[..., 0] + 2 * T[..., 1] + T[..., 2]) / 4, 1))
DR_, DS_ = 0.25, 0.5; rr = np.arange(-1.0, 16.0, DR_); nth = int(round(2 * np.pi * RL / DS_)); tt = np.arange(nth) * 2 * np.pi / nth
R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); X = LX + R_ * np.cos(T_); Y = LY - R_ * np.sin(T_)
comp = cv2.remap(Lc.astype(np.float32), (X - ox).astype(np.float32), (Y - oy).astype(np.float32), cv2.INTER_LINEAR)
dl = cv2.remap(Z['delta'].astype(np.float32), (X - bx0).astype(np.float32), (Y - by0).astype(np.float32), cv2.INTER_LINEAR)
al = cv2.remap(Z['alfa'].astype(np.float32), (X - bx0).astype(np.float32), (Y - by0).astype(np.float32), cv2.INTER_LINEAR)
ct = comp - gaussian_filter1d(comp, 8 / DS_, axis=1, mode='wrap')          # detall tangencial del compost (bandes 0–8 px)
thp = np.degrees(tt); dm = DMIN9[(thp / 360 * NBZ).astype(int) % NBZ][None, :]; dd = rr[:, None] - dm
rep = {}
for a0, a1 in ((75, 105), (105, 135), (210, 235), (235, 255)):
    sel = (((thp - a0) % 360) < ((a1 - a0) % 360))[None, :]; r = {}
    for nom, z in (('referencia', sel & (dd >= 2) & (dd < 7) & (np.abs(dl) > 0)), ('banda', sel & (al > 0.5))):
        x = dl[z]; y = ct[z]
        if x.size < 200: continue
        b = float(np.sum(x * y) / np.sum(x * x)); cc = float(np.corrcoef(x, y)[0, 1])
        r[nom] = dict(beta=round(b, 3), corr=round(cc, 3), rms_compost=round(float(np.std(y)), 4), rms_delta=round(float(np.std(x)), 4), n=int(x.size))
    rep[f'{a0}-{a1}'] = r; print(f'{a0}-{a1}', r, flush=True)
out = O / f'D36_ESCALA_{Path(sys.argv[1]).stem}.json'; out.write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print('fet', out)
