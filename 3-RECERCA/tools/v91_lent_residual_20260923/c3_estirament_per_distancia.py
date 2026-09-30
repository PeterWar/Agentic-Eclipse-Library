"""c3 · A quina distància del limbe hi ha l'estirament radial dels filtres, i si ve de la continuació a4 (els 2–4 px sense dada) o de la
resposta dels filtres. Perfil r(d) = E_d/E_s per fila de distància (0,25 px), dividit pel de 16–30 px (>1 = més estirat que la corona
de més enfora), per sectors, als ràsters de la V88 abans (filtres/) i després (filtres_finals/) de la continuació. Sortida: C3_PER_DISTANCIA.json."""
from pathlib import Path
import json, time
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v91_lent_residual_20260923'
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
GEO = json.loads((ARREL / '4-RESULTATS/v91_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
V88 = ARREL / '4-RESULTATS/v88_20260923'; Q = np.load(V88 / 'A3A_franja_un_instant.npz'); print('claus a3a:', Q.files)
DT = 0.05; NT = int(360 / DT); DR = 0.25; DS = np.arange(-3, 30.001, DR); TS = np.radians((np.arange(NT) + 0.5) * DT)
TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
x0, x1, y0, y1 = int(MX.min()) - 2, int(MX.max()) + 3, int(MY.min()) - 2, int(MY.max()) + 3
ds_arc = np.radians(DT) * (R + DS)[:, None]; far = (DS >= 16) & (DS <= 30); t = np.arange(NT) * DT
sect = [(60, 100), (100, 135), (150, 210), (240, 270), (270, 300), (300, 330)]
dom = Q['domini']; by0, by1, bx0, bx1 = [int(v) for v in Q['box']]
D = np.zeros((7506, 10551), np.float32); D[by0:by1, bx0:bx1] = dom.astype(np.float32)
PD = cv2.remap(D[y0:y1, x0:x1], MX - x0, MY - y0, cv2.INTER_LINEAR)
rep = dict(inici_domini_px={f'{a}-{b}': round(float(np.mean([DS[np.argmax(PD[:, j] > 0.5)] for j in range(int(a / DT), int(b / DT), 20)])), 2) for a, b in sect}, capes={})
print('on comença la dada (px del limbe):', rep['inici_domini_px'])
def perfil(u):
    X = np.asarray(u[y0:y1, x0:x1], np.float32) / 65535; P = cv2.remap(X, MX - x0, MY - y0, cv2.INTER_LINEAR)
    T = P - gaussian_filter1d(P, 3.0 / ds_arc.mean(), axis=1, mode='wrap')
    Ed = (np.diff(T, axis=0) / DR) ** 2; Ed = np.vstack([Ed, Ed[-1:]]); Es = (np.diff(T, axis=1, append=T[:, :1]) / ds_arc) ** 2
    out = {}
    for a, b in sect:
        c = (t >= a) & (t < b); r = Ed[:, c].mean(1) / np.maximum(Es[:, c].mean(1), 1e-12); rf = r[far].mean()
        out[f'{a}-{b}'] = {f'{d:.0f}': round(float(rf / np.maximum(r[np.abs(DS - d) < 0.5].mean(), 1e-12)), 2) for d in (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 18)}
    return out
for tag in ['P05_WOW_bilateral', 'P01_NRGF_extrap', 'P04_WOW', 'P01_NRGF', '07', '04']:
    for fase in ('filtres', 'filtres_finals'):
        u = np.load(V88 / fase / f'{tag}_u16.npy', mmap_mode='r'); rep['capes'][f'{tag}|{fase}'] = perfil(u)
        print(tag, fase, json.dumps({k: v for k, v in rep['capes'][f'{tag}|{fase}'].items() if k in ('270-300', '100-135', '60-100')}), flush=True)
(SORT / 'C3_PER_DISTANCIA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n')
