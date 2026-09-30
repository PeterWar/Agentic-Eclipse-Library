"""w2b (verificador adversari 2) · Perfils perpendiculars sencers (t −200…200 px) dels sis traços, abans i després, al compost, la base i els
apilats (DoG del ln σ3−σ30, com la ronda 1), per trobar on és de debò el solc (la marca 269 no és exactament al centre del solc: C5 en dona
V0_minim_t) i fixar-ne la posició t0 UN COP, a la imatge d'ABANS del compost, abans de mesurar res amb nuls (w2c).
Sortida: W2B_PERFILS.json i W2B_PERFILS.png"""
import json
from pathlib import Path
import numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica2_marrons'
import importlib.util
spec = importlib.util.spec_from_file_location('w2', Path(__file__).with_name('w2_tracos.py'))
W, H = 10551, 7506
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'
PARELLS = {
    'compost': (F2 / 'compost_control.npy', F2 / 'compost_flat2d_v2.npy', None),
    'vixen_G': (CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', F2 / 'apilats/vixen_total.npy', 1),
    'sonyA_G': (CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', F2 / 'apilats/sony_A_total.npy', 1),
    'sonyB_G': (CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy', F2 / 'apilats/cau/sony_B_total_v42.npy', 1),
}
C5 = json.loads((A / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']
TR = []
for k, t in enumerate(C5):
    d = np.array(t['info']['direccio'], float); d /= np.linalg.norm(d); TR.append((k + 1, np.array(t['info']['centre'], float), d, float(t['info']['llarg']), t['info']['V0_minim_t']))
TT = np.arange(-200, 201, 1.0)
def detall(p, ch):
    a = np.load(p, mmap_mode='r'); img = np.asarray(a if ch is None else a[..., ch], np.float32)
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); l = np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32); del img
    g = lambda s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    ok = cv2.erode(m, np.ones((61, 61), np.uint8)) > 0
    return np.where(ok, g(3) - g(30), np.nan).astype(np.float32)
def perfil(D, c, d, L):
    n = np.array([-d[1], d[0]]); s = np.arange(-L / 2, L / 2 + 1e-6, 2.0)
    X = (c[0] + s[:, None] * d[0] + TT[None, :] * n[0]).astype(np.float32); Y = (c[1] + s[:, None] * d[1] + TT[None, :] * n[1]).astype(np.float32)
    P = cv2.remap(D, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
    with np.errstate(all='ignore'): pr = np.nanmean(P, 0); cov = np.isfinite(P).mean(0)
    return np.where(cov > 0.5, 1e4 * pr, np.nan)
R = {}
fig, ax = plt.subplots(len(PARELLS), 6, figsize=(30, 4 * len(PARELLS)))
for i, (nom, (pa, pd, ch)) in enumerate(PARELLS.items()):
    R[nom] = {}
    Da = detall(pa, ch); Pa = {k: perfil(Da, c, d, L) for k, c, d, L, _ in TR}; del Da
    Dd = detall(pd, ch); Pd = {k: perfil(Dd, c, d, L) for k, c, d, L, _ in TR}; del Dd
    for j, (k, c, d, L, t5) in enumerate(TR):
        R[nom][f'T{k}'] = dict(t=TT.tolist(), abans=np.round(Pa[k], 2).tolist(), despres=np.round(Pd[k], 2).tolist(), V0_minim_t_C5=t5)
        ax[i, j].plot(TT, Pa[k], 'k', lw=1, label='abans'); ax[i, j].plot(TT, Pd[k], 'r', lw=1, label='després'); ax[i, j].axvline(t5, color='g', ls=':')
        ax[i, j].axhline(0, color='0.7', lw=.5); ax[i, j].set_title(f'{nom} T{k} (verd: mínim C5)'); ax[i, j].legend(fontsize=7)
    print(nom, flush=True)
plt.tight_layout(); plt.savefig(OUT / 'W2B_PERFILS.png', dpi=60)
(OUT / 'W2B_PERFILS.json').write_text(json.dumps(R))
