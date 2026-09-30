"""b25 (V117, 29-09-2026) · κ(r) de la capa: el guany amb què el compost DESAT de la V115 ja mostra el detall confirmat A·B (β = pendent de la
regressió, per anells de 0,4 R☉, del detall radial de la V115 —mateix operador que el filtre, sobre el G del render natiu— contra D_min).
Guardat com a guió (a la V116 es va fer en línia). Ús: b25_beta_v115.py <carpeta_b1>  → BETA_V115.json"""
import sys, json, numpy as np, cv2, tifffile
from pathlib import Path
R = Path(__file__).resolve().parents[3]; B1 = Path(sys.argv[1]).resolve(); f = 2; SOL = (5361.768, 3775.748); RS = 440.603; H, W = 7506, 10551
D = np.asarray(np.load(B1 / 'D_minim_f32.npy', mmap_mode='r')[::f, ::f], np.float32)
U = tifffile.memmap(R / '4-RESULTATS/v115_nrgf_20260929/V115_natiu/visible_complet.tif', mode='r'); UL = np.asarray(U[::f, ::f, 1], np.float32) / 65535
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
DU = detall_radial(UL)
yy, xx = np.mgrid[0:H:f, 0:W:f]; rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
edges = np.arange(1.2, 9.6, 0.4); beta = []
for a, b in zip(edges[:-1], edges[1:]):
    k = (rr >= a) & (rr < b) & (D != 0) & (DU != 0)
    x, y = D[k], DU[k]; beta.append(float(np.sum(x * y) / np.sum(x * x)) if k.sum() > 1000 else np.nan)
beta = np.array(beta); print('β(r):', ' '.join(f'{(a + b) / 2:.1f}:{v:.1f}' for a, b, v in zip(edges[:-1], edges[1:], beta)))
json.dump(dict(r_centres=[(a + b) / 2 for a, b in zip(edges[:-1], edges[1:])], beta=[None if not np.isfinite(v) else v for v in beta],
               nota='β = pendent del detall radial del compost desat de la V115 contra el detall confirmat A·B (D_min), per anells de 0,4 R☉'),
          open(B1 / 'BETA_V115.json', 'w'), ensure_ascii=False, indent=1)
