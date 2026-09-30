"""m6 · El solc de cada traç FOTOGRAMA A FOTOGRAMA (Sony 21 i Vixen 67), a la graella 1/4 del llenç (sources_v36/cau/{tren}_v.npy, _w.npy).
Per a cada fotograma amb pes > 0 a tot el tram: r = v / gauss(v, σ 10 cel·les) − 1 (normalitzat per la dada), perfil perpendicular (±60 cel·les,
mitjana al llarg) i solc a t = 0 (±1 cel·la) contra els flancs (6…40 cel·les). Si la línia és del CEL (fixa al llenç), hi és a tots els fotogrames
dels dos apuntaments; si és del SENSOR, només a un apuntament i desplaçada a l'altre; si és d'un fotograma, només en aquell.
Sortida: M6_PER_FOTOGRAMA.json i M6_perfils.npz."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text())
CR = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v36/cau'; Q = 4
res = {}; perf = {}
for tren in ('sony', 'vixen'):
    meta = json.loads((CR / f'{tren}_meta.json').read_text())['frames']; V = np.load(CR / f'{tren}_v.npy', mmap_mode='r'); Wt = np.load(CR / f'{tren}_w.npy', mmap_mode='r')
    for tr in TRACOS:
        z = g[str(tr['k'])]; c = np.array(z['centre']); d = np.array(z['direccio']); n = np.array([-d[1], d[0]]); L = z['llarg']
        # graella a 1/4: centre de la cel·la j ↔ píxel 4j+1,5
        s = np.arange(-L / 2, L / 2 + 1e-6, 4.0); t = np.arange(-240, 240.01, 2.0)
        X = ((c[0] + s[:, None] * d[0] + t[None, :] * n[0]) - 1.5) / Q; Y = ((c[1] + s[:, None] * d[1] + t[None, :] * n[1]) - 1.5) / Q
        xa, xb = int(max(0, X.min() - 40)), int(min(V.shape[2], X.max() + 40)); ya, yb = int(max(0, Y.min() - 40)), int(min(V.shape[1], Y.max() + 40))
        files = []
        for j, m in enumerate(meta):
            v = np.asarray(V[j, ya:yb, xa:xb], np.float32); w = np.asarray(Wt[j, ya:yb, xa:xb], np.float32)
            ok = (w > 0) & np.isfinite(v) & (v > 0)
            Pm = cv2.remap(ok.astype(np.float32), (X - xa).astype(np.float32), (Y - ya).astype(np.float32), cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            cob = float(Pm[:, np.abs(t) <= 160].mean())
            if cob < 0.9: continue
            wf = ok.astype(np.float32); vv = np.where(ok, v, 0)
            sm = cv2.GaussianBlur(vv * wf, (0, 0), 10) / np.maximum(cv2.GaussianBlur(wf, (0, 0), 10), 1e-6)
            r = np.where(ok, vv / np.maximum(sm, 1e-12) - 1, np.nan).astype(np.float32)
            P = cv2.remap(r, (X - xa).astype(np.float32), (Y - ya).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
            with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
            cen = np.abs(t) <= 4; fl = (np.abs(t) >= 24) & (np.abs(t) <= 160)
            sol = float(np.nanmean(pr[cen]) - np.nanmean(pr[fl])); err = float(np.nanstd(pr[fl]) / np.sqrt(max(1, fl.sum() / 4)))
            # nul: la mateixa mesura a ±(40…200) px de la recta
            nul = []
            for t0 in list(range(-200, -39, 8)) + list(range(40, 201, 8)):
                c2 = (np.abs(t - t0) <= 4); f2 = (np.abs(t - t0) >= 24) & (np.abs(t - t0) <= 160)
                if f2.sum() > 10: nul.append(np.nanmean(pr[c2]) - np.nanmean(pr[f2]))
            nul = np.array(nul); zz = float((sol - np.median(nul)) / (1.4826 * np.median(np.abs(nul - np.median(nul))) + 1e-12))
            files.append(dict(i=j, nom=m['name'], grup=m['group'], exp=m['exp'], t_s=m.get('t'), solc=sol, z=zz, cobertura=cob))
            perf[f"T{tr['k']}_{tren}_{j}"] = pr
        res.setdefault(tr['k'], {})[tren] = files
        if files:
            print(f"T{tr['k']} {tren}: " + ' '.join(f"{f['nom'][-8:-4]}({f['exp']:g}s){f['solc']*1e4:+.0f}‱/z{f['z']:+.1f}" for f in files), flush=True)
perf['t'] = t
desa(OUT / 'M6_PER_FOTOGRAMA.json', dict(nota='solc = r(|t|≤4) − r(24≤|t|≤160), r = v/gauss(v,σ40 px) − 1 a la graella 1/4; z contra 42 rectes paral·leles nul·les', tracos=res))
np.savez_compressed(OUT / 'M6_perfils.npz', **perf)
