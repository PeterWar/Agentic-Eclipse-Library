"""o2 (V120, 29-09-2026) · EL GUANY (κ) DE L'ORDIT I DE LA TRAMA, calibrat contra el COMPOST COMPLET de la pila de la V120 (els ajustos de Pere inclosos, com el V115_natiu de la V117–V119; l'ordit i la trama de la V119, ocults). Contra la pila
SENSE els ajustos el β surt un 12–20 % més baix (desat a <ot>/beta_sense_ajustos/, no es fa servir). Mateixa recepta que la V118/V119, amb la referència nova:
  · ORDIT: β = pendent del detall radial del render (operador del b25: DoG azimutal 0,15°–1,5°, sobre el G) contra l'ordit, per anells de 0,4 R☉;
    null on el detall de tres testimonis cobreix < 90 % del que cobreix A·B (b25b; A·B: el b1 de la V117).
  · TRAMA: β = pendent del detall tangencial del render (el mateix operador de la trama, sobre el G) contra la trama, per anells de 0,4 R☉;
    null a r ≥ 3,6 R☉ o β ≤ 0 (b25t).
Sortides: <ot>/ordit/BETA_V115.json i <ot>/trama/BETA_V115.json (el nom que llegeix el b3t; la referència és la V120, ho diu el camp «referencia»),
i els β bruts. Ús: o2_kappa_v120.py <carpeta_ot> <render visible_complet.tif>"""
import sys, json, time, importlib.util, numpy as np, cv2, tifffile
from pathlib import Path
OT, TIF = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.argv = [sys.argv[0], str(OT / '_b1')]
R = Path(__file__).resolve().parents[3]; t0 = time.time()
spec = importlib.util.spec_from_file_location('b1', R / '3-RECERCA/tools/v117_20260929/b1_filtre_coherent_AB.py'); b1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b1)
H, W, SOL, RS = b1.H, b1.W, b1.SOL, b1.RS; f = 2
def log(*a): print(f'[{time.time() - t0:5.0f}s]', *a, flush=True)
U = tifffile.memmap(TIF, mode='r'); assert U.shape[:2] == (H, W), U.shape
GR = np.asarray(U[..., 1], np.float32) / 65535
EDGES = np.arange(1.2, 9.6, 0.4); RC = [(a + b) / 2 for a, b in zip(EDGES[:-1], EDGES[1:])]
yy, xx = np.mgrid[0:H:f, 0:W:f]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
# ------------------------------------------------------------------ ORDIT (b25 + b25b)
def detall_radial(img):
    r0, r1 = 1.12 * RS / f, 10.5 * RS / f; NR, NT = 2048, 12288; rho = np.linspace(np.log(r0), np.log(r1), NR); th = np.arange(NT) * 2 * np.pi / NT
    s0 = (SOL[0] / f, SOL[1] / f); rrp = np.exp(rho)[:, None]
    MX = (s0[0] + rrp * np.cos(th)[None, :]).astype(np.float32); MY = (s0[1] - rrp * np.sin(th)[None, :]).astype(np.float32)
    P = cv2.remap(img, MX, MY, cv2.INTER_LINEAR, borderValue=0); pm = P > 0; x = np.where(pm, np.log(np.maximum(P, 1e-9)), 0).astype(np.float32)
    dr = rho[1] - rho[0]; dth = 2 * np.pi / NT
    def g(v, sr, st):
        p = int(4 * st) + 2; vp = np.concatenate([v[:, -p:], v, v[:, :p]], 1); return cv2.GaussianBlur(vp, (0, 0), sigmaX=float(st), sigmaY=float(sr), borderType=cv2.BORDER_REFLECT)[:, p:-p]
    den1 = g(pm.astype(np.float32), 0.015 / dr, np.radians(0.15) / dth); den2 = g(pm.astype(np.float32), 0.015 / dr, np.radians(1.5) / dth)
    d = g(x, 0.015 / dr, np.radians(0.15) / dth) / np.maximum(den1, 1e-6) - g(x, 0.015 / dr, np.radians(1.5) / dth) / np.maximum(den2, 1e-6); d[~pm] = 0
    yq, xq = np.mgrid[0:img.shape[0], 0:img.shape[1]].astype(np.float32); rc = np.hypot(xq - s0[0], yq - s0[1]); tc = np.mod(np.arctan2(-(yq - s0[1]), xq - s0[0]), 2 * np.pi)
    IX = (tc / (2 * np.pi) * NT).astype(np.float32); IY = ((np.log(np.maximum(rc, 1)) - rho[0]) / dr).astype(np.float32)
    dd = cv2.remap(np.concatenate([d, d[:, :2]], 1).astype(np.float32), IX, IY, cv2.INTER_LINEAR, borderValue=0); dd[(IY < 0) | (IY > NR - 1)] = 0; return dd
def regressio(X, Y, k0, rr_):
    out = []
    for a, b in zip(EDGES[:-1], EDGES[1:]):
        k = k0 & (rr_ >= a) & (rr_ < b); x_, y_ = X[k], Y[k]; out.append(float(np.sum(x_ * y_) / np.sum(x_ * x_)) if k.sum() > 1000 else None)
    return out
D = np.asarray(np.load(OT / 'ordit/D_minim_f32.npy', mmap_mode='r')[::f, ::f], np.float32); DU = detall_radial(np.ascontiguousarray(GR[::f, ::f]))
bo = regressio(D, DU, (D != 0) & (DU != 0), rr); del DU
DA = np.asarray(np.load(OT / 'ordit/DA_f16.npy', mmap_mode='r')[::f, ::f]); DAB = np.asarray(np.load(R / '4-RESULTATS/v117_20260929/AB/b1/DA_f16.npy', mmap_mode='r')[::f, ::f])
cob, bof = [], []
for rc, bt in zip(RC, bo):
    k = (rr >= rc - 0.2) & (rr < rc + 0.2); c = float(np.count_nonzero(DA[k]) / max(np.count_nonzero(DAB[k]), 1)); cob.append(round(c, 3)); bof.append(bt if (bt is not None and c >= 0.9) else None)
del D, DA, DAB
json.dump(dict(r_centres=RC, beta=bof, beta_brut=bo, cobertura_tres_sobre_AB=cob, referencia=str(TIF.relative_to(R)),
               nota='β de l\'ordit contra el render de la pila de la V120 (b25); null on la Vixen cobreix < 90 % del que cobreixen A i B (b25b)'), open(OT / 'ordit/BETA_V115.json', 'w'), ensure_ascii=False, indent=1)
log('ordit β:', ' '.join(f'{r:.1f}:{("—" if v is None else f"{v:.2f}")}' for r, v in zip(RC, bof)))
# ------------------------------------------------------------------ TRAMA (el β del b9 + b25t), al pla polar reduït de la trama de l'o1
FR_, FT_ = 2, 4; NRt, NTt = b1.NR // FR_, b1.NT // FT_; DRt = float(b1.dr * FR_); DTHt = 360.0 / NTt; RHOt = b1.rho.reshape(NRt, FR_).mean(1); RRt = (np.exp(RHOt) / RS)[:, None] * np.ones((1, NTt), np.float32)
def gt(x, sr, st):
    p = int(4 * st) + 2; xp = np.concatenate([x[:, -p:], x, x[:, :p]], 1); return cv2.GaussianBlur(xp, (0, 0), sigmaX=float(st), sigmaY=float(sr), borderType=cv2.BORDER_REFLECT)[:, p:-p]
def gnt(x, M, sr, st):
    den = gt(M.astype(np.float32), sr, st); return gt(np.where(M, x, 0).astype(np.float32), sr, st) / np.maximum(den, 1e-6), den
def pla(L, mm):
    Mf = cv2.resize(b1.polar(mm.astype(np.float32)), (NTt, NRt), interpolation=cv2.INTER_AREA)
    P = cv2.resize(b1.polar(np.where(mm, np.log(np.maximum(L, 1e-9)), 0).astype(np.float32)), (NTt, NRt), interpolation=cv2.INTER_AREA)
    M = Mf > 0.999; return np.where(M, P / np.maximum(Mf, 1e-6), 0).astype(np.float32), M
def tangencial(x, M):
    xm = np.where(M, x, np.nan); med = np.nanmedian(xm, axis=1, keepdims=True); med = np.where(np.isfinite(med), med, 0); y = np.where(M, x - med, 0).astype(np.float32)
    S1, S2, S3, ST = 0.012 / DRt, 0.12 / DRt, 0.30 / DRt, 2.0 / DTHt
    a, _ = gnt(y, M, S1, ST); c, _ = gnt(y, M, S2, ST); T = np.where(M, a - c, 0).astype(np.float32); g_, den = gnt(T, M, S3, ST); T = np.where(M & (den > 0.3), T - g_, 0).astype(np.float32)
    Mk = M & (T != 0); n_ = Mk.sum(1, keepdims=True); mu = np.where(n_ > 0, np.where(Mk, T, 0).sum(1, keepdims=True) / np.maximum(n_, 1), 0); return np.where(Mk, T - mu, 0).astype(np.float32)
TU = tangencial(*pla(GR, GR > 0)); del GR
TD = np.load(OT / 'trama/D_minim_f32.npy', mmap_mode='r')
TP = cv2.resize(b1.polar(np.asarray(TD, np.float32)), (NTt, NRt), interpolation=cv2.INTER_AREA); MP = cv2.resize(b1.polar((np.asarray(TD) != 0).astype(np.float32)), (NTt, NRt), interpolation=cv2.INTER_AREA) > 0.999
bt_ = regressio(TP, TU, MP & (TP != 0) & (TU != 0), RRt)
btf = [v if (v is not None and v > 0 and r < 3.6) else None for r, v in zip(RC, bt_)]
json.dump(dict(r_centres=RC, beta=btf, beta_brut=bt_, referencia=str(TIF.relative_to(R)),
               nota='β de la trama contra el detall tangencial del render de la pila de la V120 (b9); null a r ≥ 3,6 R☉ o β ≤ 0 (b25t)'), open(OT / 'trama/BETA_V115.json', 'w'), ensure_ascii=False, indent=1)
log('trama β:', ' '.join(f'{r:.1f}:{("—" if v is None else f"{v:.2f}")}' for r, v in zip(RC, btf)))
