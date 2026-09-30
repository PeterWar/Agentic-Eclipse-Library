"""m5 · Prova SENSE biaix de selecció: el traç és una recta del CEL o del SENSOR, o és gra?
La geometria de M3 es va triar al ràster de la WOW (que surt de la base): qualsevol font que entri a la base hi mostraria un solc per selecció.
Aquí, per a cada traç i cada apilat INDEPENDENT (Sony A, Sony B, Vixen comuna, Sony parells, Sony senars de la V29), es busca la recta
(θ ±4°, t ±150 px respecte de M3) al MATEIX apilat (filtre fi σ 4/40 relatiu, mitjana al llarg), i s'avalua aquesta recta a tots els ALTRES
apilats; z = (valor − mediana del mapa (θ,t) de l'altre apilat) / MAD del mapa. Si la línia és real (cel o procés en coordenades del llenç),
les cerques independents convergeixen i les avaluacions creuades donen z ≪ 0. Sortida: M5_INDEPENDENTS.json."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text())
for tr in TRACOS:
    z = g[str(tr['k'])]; tr['centre'] = np.array(z['centre']); tr['d'] = np.array(z['direccio']); tr['n'] = np.array([-tr['d'][1], tr['d'][0]])
R97 = ARREL / '4-RESULTATS/v97_refundacio_20260924'; CR = R97 / 'cadena_raw'
FONTS = {'sony_A': CR / 'b2_sony_A/cau/sony_A_total_v36.npy', 'sony_B': CR / 'b2_sony_B/cau/sony_B_total_v42.npy', 'vixen': R97 / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy',
         'sony_parells_v29': CR / 'sources_v29/sony_even_total.npy', 'sony_senars_v29': CR / 'sources_v29/sony_odd_total.npy'}
TH = np.arange(-4.0, 4.001, 0.1); TT = np.arange(-150, 151, 1.0)
res = {}
for tr in TRACOS:
    box = caixa(tr, 450); x0, y0, x1, y1 = box; mapes = {}; cober = {}
    for nom, p in FONTS.items():
        img = np.asarray(np.load(p, mmap_mode='r')[y0:y1, x0:x1, 1], np.float32); m = np.isfinite(img) & (img > 0); w = m.astype(np.float32); img = np.where(m, img, 0)
        ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
        r = np.where(m & (cv2.erode(w, np.ones((81, 81), np.uint8)) > 0), ng(img, 4) / np.maximum(ng(img, 40), 1e-12) - 1, np.nan).astype(np.float32)
        M = np.full((len(TH), len(TT)), np.nan, np.float32); C = np.zeros((len(TH), len(TT)), np.float32)
        for i, dth in enumerate(TH):
            s, t, X, Y = graella(tr, tmax=150, dt=1, ds=3, dtheta=dth); P = mostreja(r, X, Y, (x0, y0))
            C[i] = np.isfinite(P).mean(0)
            with np.errstate(all='ignore'): M[i] = np.where(C[i] > 0.6, np.nanmean(P, 0), np.nan)
        mapes[nom] = M; cober[nom] = float(np.nanmean(C))
    out = {'cobertura_mitjana': cober, 'cerques': {}}
    for a, Ma in mapes.items():
        if np.isfinite(Ma).sum() < 0.5 * Ma.size: continue
        i, j = np.unravel_index(np.nanargmin(Ma), Ma.shape); fila = dict(dtheta=float(TH[i]), t=float(TT[j]), creuat={})
        for b, Mb in mapes.items():
            if np.isfinite(Mb).sum() < 0.5 * Mb.size or not np.isfinite(Mb[i, j]): continue
            med = np.nanmedian(Mb); mad = 1.4826 * np.nanmedian(np.abs(Mb - med))
            fila['creuat'][b] = dict(valor=float(Mb[i, j]), z=float((Mb[i, j] - med) / mad))
        out['cerques'][a] = fila
        print(f"T{tr['k']} cerca a {a:17s} → dθ {fila['dtheta']:+.1f} t {fila['t']:+4.0f} | " + ' '.join(f"{b}:{v['valor']*1e4:+.1f}‱ z{v['z']:+.1f}" for b, v in fila['creuat'].items()), flush=True)
    res[tr['k']] = out
desa(OUT / 'M5_INDEPENDENTS.json', dict(nota='valors en fracció (‱ = 1e-4) del filtre fi relatiu σ4/σ40; z contra el mapa (θ,t) de la font avaluada', tracos=res))
