"""d0_components_C (V108, flat2d_v3, DIAGNOSI) · Separa la C de la v2 en components, per provar a la dada quins hi són de debò.
Per a cada tren, al subplà de cada canal CFA (R, G1, G2, B): ln C_c = ℓ + κ_c, amb
  ℓ   = la part COMUNA als quatre canals (mitjana dels quatre ln C_c; un factor comú no canvia el color després de la matriu),
  κ_c = la part CROMÀTICA de cada canal (ln C_c − ℓ).
I cada una en dues bandes, fina i gruixuda, tallant amb una gaussiana de σ_tall subplans (normalitzada dins de la zona visible):
  Lf = ℓ − G(ℓ, σ_tall),  Lg = G(ℓ, σ_tall),  Kf = κ − G(κ, σ_tall),  Kg = G(κ, σ_tall).
Com que el canvi de l'apilat és lineal en ln C (els pesos no depenen de C), la suma dels quatre efectes és l'efecte de la v2 (es comprova).
Sortida: <out>/<TREN>_<comp>.npz (clau C, mateix format que f0_flat2d_v2: mosaic CFA a mida del RAW) i D0_COMPONENTS.json.
Ús: d0_components_C.py [--sigma-tall 6] [--trens SONYTOT,VIXEN] [--out …]   (només llegeix la v2; escriu a 4-RESULTATS/v108_20260926/flat2d_v3/diag/)"""
import json, argparse, hashlib, time
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]
V2 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v2/flat2d'
ap = argparse.ArgumentParser(); ap.add_argument('--sigma-tall', type=float, default=6.0); ap.add_argument('--trens', default='SONYTOT,VIXEN')
ap.add_argument('--out', default=str(ARREL / '4-RESULTATS/v108_20260926/flat2d_v3/diag/components'))
a = ap.parse_args(); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True); t0 = time.time(); rep = dict(sigma_tall_subplans=a.sigma_tall, trens={})
for T in a.trens.split(','):
    z = np.load(V2 / f'{T}_flat2d_v2.npz'); C = z['C'].astype(np.float32); pat = z['patró']
    h, w = C.shape; hs, ws = h // 2, w // 2
    L = {(oy, ox): np.log(C[oy::2, ox::2][:hs, :ws]).astype(np.float32) for oy in range(2) for ox in range(2)}
    vis = {k: (v != 0) for k, v in L.items()}          # C = 1 exacte fora de la zona visible (i als píxels aïllats: igual, és pla)
    wv = np.minimum.reduce([np.ones((hs, ws), np.float32)] + [cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32) for m in vis.values()])
    ng = lambda x, s: cv2.GaussianBlur(x * wv, (0, 0), s) / np.maximum(cv2.GaussianBlur(wv, (0, 0), s), 1e-6)
    ell = (sum(L.values()) / 4.0).astype(np.float32)
    ellg = ng(ell, a.sigma_tall) * wv
    comp = {k: {} for k in ('Lf', 'Lg', 'Kf', 'Kg')}
    for k, v in L.items():
        kap = v - ell; kapg = ng(kap, a.sigma_tall) * wv
        comp['Lf'][k] = ell - ellg; comp['Lg'][k] = ellg; comp['Kf'][k] = kap - kapg; comp['Kg'][k] = kapg
    r = {}
    for nom, d in comp.items():
        Cn = np.ones((h, w), np.float32)
        for (oy, ox), v in d.items(): Cn[oy::2, ox::2][:hs, :ws] = np.exp(v)
        p = OUT / f'{T}_{nom}.npz'; np.savez(p, C=Cn, patró=pat, component=nom, sigma_tall=a.sigma_tall)
        sub = {int(pat[oy, ox]): v[150:-150, 150:-150] for (oy, ox), v in d.items()}
        r[nom] = dict(rms_ppm={['R', 'G1', 'B', 'G2'][c]: round(1e4 * float(v.std()), 3) for c, v in sub.items()}, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    # la suma dels quatre ha de ser la v2
    tot = sum(comp[n][(0, 1)] for n in comp); r['comprovacio_suma_G1_max_abs'] = float(np.abs(tot - L[(0, 1)]).max())
    rep['trens'][T] = r; print(T, json.dumps(r, ensure_ascii=False), f'{time.time()-t0:.0f}s', flush=True)
(OUT / 'D0_COMPONENTS.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
