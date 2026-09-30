"""f2b (V97) · La base de pantalla (capa 3) des d'una linealitzada, amb la recepta DECLARADA de la V42 (b4e_bases_v42.base_srgb, k = 1):
  L = (R + 2G + B)/4 · to = corba_to(L) = clip(0,74 + 0,22·log10(L/VA), 0,045, 1) amb VA = 70736,47 (research/108) ·
  color = ràtios q_c = ⟨c⟩σ24/⟨L⟩σ24 (el color local, suau; el detall és a la lluminància) · y = a_lineal(to)·(1 + wg·(q − 1)), wg = el
  màxim que no surt de gamma · codificació sRGB · (opcional) conversió a Adobe RGB · espatlla s75c90 de la V85 (guany comú RGB:
  max → 0,75 + 0,15·(1 − e^{−(max − 0,75)/0,15})), que evita el retall del vermell a la capa d'ajust «Luz 1» (l'«artefacte verd»).
Sense cap correcció local: ni pegats d'estrella, ni guanys de model dins del limbe, ni farcits (els forats queden a alfa 0).
Ús: f2b_base.py <fusion_starless.npy> <support.npy> <sortida_u16.npy> [--espai assigna|converteix] [--compara-v96]"""
import sys, json, argparse, time
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import ARREL, RES, SOL, RSOL, desa
ap = argparse.ArgumentParser(); ap.add_argument('fusio'); ap.add_argument('suport'); ap.add_argument('sortida'); ap.add_argument('--espai', default='assigna', choices=['assigna', 'converteix'])
ap.add_argument('--compara-v96', action='store_true'); a = ap.parse_args(); t0 = time.time()
VA = 70736.46875; PEND, ANC, TERRA = 0.22, 0.74, 0.045
def a_lineal(c): c = np.asarray(c, np.float32); return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)
def a_srgb(c): c = np.clip(np.asarray(c, np.float32), 0, 1); return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055).astype(np.float32)
def gauss(x, s): return cv2.GaussianBlur(np.ascontiguousarray(x, np.float32), (0, 0), s)
# sRGB lineal → Adobe RGB (1998) lineal, via XYZ D65 (conversió colorimètrica relativa)
M_SRGB_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
M_XYZ_ADOBE = np.linalg.inv(np.array([[0.5767309, 0.1855540, 0.1881852], [0.2973769, 0.6273491, 0.0752741], [0.0270343, 0.0706872, 0.9911085]]))
F = np.load(a.fusio, mmap_mode='r'); sup = np.load(a.suport)
data = np.nan_to_num(np.asarray(F, np.float32)); m = sup & np.all(np.isfinite(np.asarray(F[..., 1:2], np.float32)), -1) & (data[..., 1] > 0)
L = (data[..., 0] + 2 * data[..., 1] + data[..., 2]) / 4
x = np.where(m & (L > 0), L, np.nan)
with np.errstate(divide='ignore', invalid='ignore'): tone = ANC + PEND * np.log10(x / VA)
tone = np.clip(np.where(np.isfinite(tone), tone, TERRA), TERRA, 1.0).astype(np.float32); del x
mf = m.astype(np.float32); den = gauss(mf, 24); ls = gauss(L * mf, 24) / np.maximum(den, 1e-8)
q = np.stack([gauss(data[..., i] * mf, 24) / np.maximum(den, 1e-8) / np.maximum(ls, 1e-8) for i in range(3)], axis=2); del data, den, ls
ylin = a_lineal(tone); qmax = q.max(axis=2)
with np.errstate(divide='ignore', invalid='ignore'): wmax = np.where(qmax > 1, (1 / np.maximum(ylin, 1e-8) - 1) / (qmax - 1), 1)
wg = np.clip(np.nan_to_num(wmax, nan=0, posinf=1), 0, 1); lin = ylin[..., None] * (1 + wg[..., None] * (q - 1)); del q, wmax, qmax
if a.espai == 'converteix':
    M = (M_XYZ_ADOBE @ M_SRGB_XYZ).astype(np.float32); lin = np.clip(np.einsum('ij,hwj->hwi', M, lin), 0, 1)
    enc = (np.clip(lin, 0, 1) ** (1 / 2.19921875)).astype(np.float32)
else: enc = a_srgb(lin)
enc = np.clip(np.nan_to_num(enc), 0, 1) * mf[..., None]; del lin
mx = enc.max(-1); newmax = np.where(mx > .75, .75 + .15 * (1 - np.exp(-(mx - .75) / .15)), mx); gain = np.where(mx > 1e-6, newmax / np.maximum(mx, 1e-6), 1.0)
u = np.rint(np.clip(enc * gain[..., None], 0, 1) * 65535).astype(np.uint16); np.save(a.sortida, u); np.save(str(a.sortida).replace('.npy', '_alfa.npy'), (m * 65535).astype(np.uint16))
rep = dict(font=str(a.fusio), suport=str(a.suport), espai=a.espai, parametres=dict(VA=VA, pend=PEND, anc=ANC, terra=TERRA, sigma_color=24, espatlla='s75c90'), px_suport=int(m.sum()), segons=time.time() - t0)
if a.compara_v96:
    V = np.load(RES / 'v96_ref/L3_RGB.npy', mmap_mode='r'); yy, xx = np.mgrid[0:u.shape[0]:4, 0:u.shape[1]:4]; r = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL
    us = u[::4, ::4].astype(np.float32) / 65535; vs = np.asarray(V[::4, ::4], np.float32) / 65535; ms = m[::4, ::4] & (r > 1.3) & (r < 6.0)
    try:
        sf = np.load(Path(a.fusio).parent / 'star_footprints.npy', mmap_mode='r')[::4, ::4]; ms &= ~cv2.dilate(np.asarray(sf, np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    except FileNotFoundError: pass
    d = us - vs; rep['compara_v96'] = dict(zona='suport, 1,3–6 R☉, sense estrelles, pas 4', mediana_dif_RGB=[float(np.median(d[..., c][ms])) for c in range(3)],
        p95_abs_RGB=[float(np.percentile(np.abs(d[..., c][ms]), 95)) for c in range(3)], mitjana_V96=[float(vs[..., c][ms].mean()) for c in range(3)], mitjana_nova=[float(us[..., c][ms].mean()) for c in range(3)])
    print(json.dumps(rep['compara_v96']), flush=True)
desa(str(a.sortida).replace('.npy', '_REBUT.json'), rep); print('FET', f'{time.time()-t0:.0f}s')
