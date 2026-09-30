"""s1 (V106 · Separació, Claude, 26-09-2026) · Extreu, fotograma a fotograma, les dades polars que la c1 (V105) combinava i llençava:
ln L_j (L = (R'+2G'+B')/4 post-matriu, com la c1), pes W_G,j, validesa bàsica i D_real,j (silueta d'ordre 2 de la V99), a la graella polar de la c1 ESTESA cap endins (d −32…40 px, perquè els fotogrames amb la Lluna desplaçada veuen
graella polar de la c1 (d −4…40 px, pas 0,25; θ a 0,5 px d'arc). No combina res: la inversió conjunta (s2) fa el pas alt i la combinació."""
import json, numpy as np, cv2, time
from pathlib import Path
R0 = Path.home() / 'Desktop/Eclipse 2026'
LF = R0 / '4-RESULTATS/v106_inversio_20260926/limb_frames_sense_llindar'
OUT = Path('/private/tmp/claude_v106/separacio/dades'); OUT.mkdir(parents=True, exist_ok=True)
meta = json.loads((LF/'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(LF/'numerator.npy', mmap_mode='r'); wt = np.load(LF/'weight.npy', mmap_mode='r'); Dm = np.load(LF/'distance_model.npy', mmap_mode='r')
geo = json.loads((R0/'4-RESULTATS/v97_refundacio_20260924/lineal_v97_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
Rm = float(meta['radius_model']); DR = Rm - R
sil = np.load(R0/'4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'); SIL_PA = np.asarray(sil['pa'], float); SIL_E = np.asarray(sil['e'], float)
M = np.array(meta['matrix'], np.float64); gain = np.array(meta['gain'], np.float64)
hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]
CEN = []
def dreal(j):
    Dj = np.asarray(Dm[j], np.float64); gy_, gx_ = np.gradient(Dj); iy_, ix_ = hb // 2, wb - 100
    cxj = ix_ + bx0 - (Dj[iy_, ix_] + Rm) * gx_[iy_, ix_]; cyj = iy_ + by0 - (Dj[iy_, ix_] + Rm) * gy_[iy_, ix_]; CEN.append((cxj, cyj))
    PAj = (np.degrees(np.arctan2(-(yy - cyj), xx - cxj)) + 360) % 360
    return (Dj + DR - np.interp(PAj.ravel(), SIL_PA, SIL_E, period=360).reshape(hb, wb)).astype(np.float32)
dgrid = np.arange(-32.0, 40.0001, 0.25).astype(np.float32); nth = int(round(2 * np.pi * R / 0.5)); th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
X = (cx + np.cos(th)[None, :] * (R + dgrid[:, None]) - bx0).astype(np.float32); Y = (cy - np.sin(th)[None, :] * (R + dgrid[:, None]) - by0).astype(np.float32)
def pol(a): return cv2.remap(np.ascontiguousarray(a, np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
nF = len(fr); sh = (nF, len(dgrid), nth)
LNL = np.lib.format.open_memmap(OUT/'LNL.npy', 'w+', np.float32, sh); WG = np.lib.format.open_memmap(OUT/'WG.npy', 'w+', np.float32, sh)
DP = np.lib.format.open_memmap(OUT/'DP.npy', 'w+', np.float32, sh); OK = np.lib.format.open_memmap(OUT/'OK.npy', 'w+', np.bool_, sh)
t0 = time.time()
for j in range(nF):
    W = np.asarray(wt[j], np.float32); N = np.asarray(num[j], np.float32)
    Wp = np.stack([pol(W[..., c]) for c in range(3)], -1); Np = np.stack([pol(N[..., c]) for c in range(3)], -1); Dp = pol(dreal(j))
    ok = (Wp > 1e-12).all(-1)
    V = np.where(ok[..., None], Np / np.maximum(Wp, 1e-30), 0) * gain; P = V @ M.T; L = (P[..., 0] + 2 * P[..., 1] + P[..., 2]) / 4
    ok &= L > 0
    LNL[j] = np.where(ok, np.log(np.maximum(L, 1e-9)), 0); WG[j] = Wp[..., 1]; DP[j] = Dp; OK[j] = ok
    print(j, fr[j]['name'], int(ok.sum()), round(time.time() - t0, 1), flush=True)
LNL.flush(); WG.flush(); DP.flush(); OK.flush()
np.savez(OUT/'META.npz', dgrid=dgrid, nth=nth, centre=np.array([cx, cy, R]), centres=np.array(CEN), t=np.array([f['time'] for f in fr]), e=np.array([f['exposure'] for f in fr]))
print('fet', time.time() - t0)
