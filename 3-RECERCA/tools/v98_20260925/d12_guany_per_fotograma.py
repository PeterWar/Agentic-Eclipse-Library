"""d12 (V98) · Guany relatiu de cada fotograma Vixen de la caixa lunar (limb_frames comuna): mediana de ln(V_f / referència) als píxels on el
fotograma i la referència són nets (D_obs ≥ 12 px) i a 15–150 px del limbe de presentació. Referència: mitjana ponderada (pesos LDIC) de tots
els fotogrames nets al píxel. Si les classes d'exposició tenen nivells diferents, la barreja de fotogrames que canvia arran del limbe fa un
anell de nivell. També per bandes de brillantor (per veure si és un guany o una no-linealitat)."""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; O = ARREL / '4-RESULTATS/v98_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = float(meta['radius_model']) - RL
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
yy, xx = np.mgrid[by0:by1:3, bx0:bx1:3]; d = np.hypot(xx - LX, yy - LY) - RL; zona = (d > 15) & (d < 150)
nF = len(fr); V = np.zeros((nF, zona.sum()), np.float32); W = np.zeros_like(V); D = np.zeros_like(V)
for j in range(nF):
    n_ = np.asarray(N[j, ::3, ::3, 1])[zona]; w_ = np.asarray(Wt[j, ::3, ::3, 1])[zona]; D[j] = np.asarray(Dm[j, ::3, ::3])[zona] + DR
    V[j] = np.where(w_ > 0, n_ / np.maximum(w_, 1e-30), np.nan); W[j] = np.where(D[j] >= 12, w_, 0)
ref = np.nansum(np.where(W > 0, V * W, 0), 0) / np.maximum(W.sum(0), 1e-30); ok = (W > 0).sum(0) >= 10
Lr = np.log(np.maximum(ref, 1e-9)); qs = np.quantile(Lr[ok], [0, .33, .66, 1])
rows = []
for j in range(nF):
    s = ok & (W[j] > 0) & np.isfinite(V[j]) & (V[j] > 0)
    lr = np.log(V[j][s] / ref[s]); bands = [float(np.median(lr[(Lr[s] >= qs[b]) & (Lr[s] < qs[b + 1])])) if ((Lr[s] >= qs[b]) & (Lr[s] < qs[b + 1])).sum() > 50 else None for b in range(3)]
    rows.append(dict(i=j, t=round(fr[j]['time'], 1), exp=fr[j]['exposure'], n=int(s.sum()), ln_mediana=round(float(np.median(lr)), 4) if s.sum() > 50 else None, ln_per_brillantor_fosc_mig_clar=[None if b is None else round(b, 4) for b in bands]))
for r_ in rows: print(r_)
(O / 'D12_GUANY_PER_FOTOGRAMA.json').write_text(json.dumps(rows, indent=1))
