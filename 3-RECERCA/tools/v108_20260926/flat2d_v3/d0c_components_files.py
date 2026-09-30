"""d0c_components_files (V108, flat2d_v3, DIAGNOSI) · La part cromàtica de la C de la Sony SENSE ANELLS (κ' = ln C'_c − ℓ', de f0_flat2d_v3:
<TREN>_components_v3.npz) partida en dues classes, per provar-les a la dada (d2_prova_AB):
  Kfil  = el que va al llarg de les FILES del sensor (mitjana al llarg de x amb σ 100 subplans; hi entren les línies quasi paral·leles a les
          files, com la de T2 a −177,9°, i les franges horitzontals de la meitat esquerra del sensor), en banda de través σ_y 1 … 30 subplans;
  Kresta = la resta de κ' (la textura cromàtica dels píxels i els restes d'anells).
I el mateix a la part comuna ℓ' (Lfil, Lresta), per comparar. Sortida: diag/components/<TREN>_<comp>.npz (clau C, com d0)."""
import json, hashlib, argparse
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; R3 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v3'
ap = argparse.ArgumentParser(); ap.add_argument('--tren', default='SONYTOT'); ap.add_argument('--sigma-fila', type=float, default=100.0); ap.add_argument('--sigma-traves', type=float, default=30.0); ap.add_argument('--sufix', default='')
a = ap.parse_args(); OUT = R3 / 'diag/components'; OUT.mkdir(parents=True, exist_ok=True)
Z = np.load(R3 / f'flat2d/{a.tren}_components_v3.npz'); pat = Z['patró']; ellp = Z['ellp']; V = Z['V']; inter = Z['inter']; hs, ws = ellp.shape
w = inter.astype(np.float32)
def nga(x, sx, sy): return cv2.GaussianBlur(x * w, (0, 0), sigmaX=sx, sigmaY=sy) / np.maximum(cv2.GaussianBlur(w, (0, 0), sigmaX=sx, sigmaY=sy), 1e-6)
def fila(x):
    """part al llarg de les files: mitjana en x (σ_fila), menys el seu fons de través (σ_traves en y)."""
    f = nga(x, a.sigma_fila, 0.01); return ((f - nga(f, 0.01, a.sigma_traves)) * w).astype(np.float32)
CAN = {'R': (0, 0), 'G1': (0, 1), 'G2': (1, 0), 'B': (1, 1)}
comp = {'Kfil': {}, 'Kresta': {}, 'Lfil': {}, 'Lresta': {}}
lf = fila(ellp)
for c, (oy, ox) in CAN.items():
    assert int(pat[oy, ox]) == {'R': 0, 'G1': 1, 'G2': 3, 'B': 2}[c]
    kap = (Z[f'lnp_{c}'] - ellp) * w; kf = fila(kap)
    comp['Kfil'][(oy, ox)] = kf; comp['Kresta'][(oy, ox)] = kap - kf; comp['Lfil'][(oy, ox)] = lf; comp['Lresta'][(oy, ox)] = ellp * w - lf
h, wd = 2 * hs, 2 * ws; rep = {}
for nom, d in comp.items():
    Cn = np.ones((h, wd), np.float32)
    for (oy, ox), v in d.items(): Cn[oy::2, ox::2][:hs, :ws] = np.exp(v)
    p = OUT / f'{a.tren}_{nom}{a.sufix}.npz'; np.savez(p, C=Cn, patró=pat, component=nom)
    rep[nom] = dict(rms_ppm={c: round(1e4 * float(d[CAN[c]][inter].std()), 3) for c in CAN}, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
print(json.dumps(rep, ensure_ascii=False)); (OUT / f'D0C_COMPONENTS{a.sufix}.json').write_text(json.dumps(dict(sigma_fila=a.sigma_fila, sigma_traves=a.sigma_traves, components=rep), ensure_ascii=False, indent=1) + '\n')
