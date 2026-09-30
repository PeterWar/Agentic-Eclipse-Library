"""Comú de la filera de punts: CÒPIA de 3-RECERCA/tools/v105_limbe_20260926/fila/comu_fila.py per a la cadena V108 (Claude, 26-09-2026, nit), amb les
rutes triables per variables d'entorn (la resta, idèntica): V108_FILA_LINEAL (linealitzada; per defecte la d'E), V108_FILA_FRANJA (A3C_franja_silueta.npz),
V108_FILA_ESTAT (estat per a l'emulació del compost) i V108_FILA_OUT (sortida, obligatòria). Original: NOMÉS lectura del projecte; escrivia a /private/tmp/claude_v105/fila/.
Geometria, entrades de la V104 (linealitzada E + franja A3C), polar al voltant de la Lluna, mètriques i emulació del compost."""
import os, sys, json
os.environ.setdefault('OPENBLAS_NUM_THREADS', '4'); sys.dont_write_bytecode = True
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[5]
E = ARREL / '4-RESULTATS/v103_banda_20260926/E'
OUT = Path(os.environ['V108_FILA_OUT']); OUT.mkdir(parents=True, exist_ok=True)
LIN = Path(os.environ.get('V108_FILA_LINEAL', E / 'lineal_v103')); EST = Path(os.environ.get('V108_FILA_ESTAT', E / 'estat_v103'))
LIN, EST = [p if p.is_absolute() else ARREL / p for p in (LIN, EST)]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924'))
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923'))
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v95_20260924'))
from jutge_comu import Estat, comp, LLUNA, RLLUNA
H, W = 7506, 10551
CXS, CYS, RS = 5361.768111973117, 3775.747534140857, 440.60304883027544      # Sol (v97_comu)
cx, cy = LLUNA; R = RLLUNA
BOXL = (4677, 3077, 6077, 4477)                   # caixa lunar x0, y0, x1, y1
BIG = (3476, 1876, 7276, 5676)                    # caixa gran per a la WOW (±1900 px al voltant de la Lluna)
FR = Path(os.environ.get('V108_FILA_FRANJA', E / 'lineal_v103_franja/A3C_franja_silueta.npz')); FR = FR if FR.is_absolute() else ARREL / FR

def entrades(box=BIG, lum=False):
    """a (base_G amb la franja G), m (domini) dins de `box`; amb lum=True, també x = ln((R+2G+B)/4) i good (entrada de l'ACHF)."""
    x0, y0, x1, y1 = box; Q = np.load(FR); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]
    a = np.array(np.load(LIN / 'base_G.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32)
    ms = np.array(np.load(LIN / 'support.npy', mmap_mode='r')[y0:y1, x0:x1])
    m = ms & np.isfinite(a) & (a > 0); sl = (slice(qy0 - y0, qy1 - y0), slice(qx0 - x0, qx1 - x0))
    a[sl] = Q['G']; m[sl] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
    out = dict(a=a, m=m, sl=sl, Q=Q)
    if lum:
        F = np.array(np.load(LIN / 'fusion_starless.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32); F[sl] = Q['F']
        Lm = (F[..., 0] + 2 * F[..., 1] + F[..., 2]) / 4; del F
        good = m & (Lm > 0); out['x'] = np.where(good, np.log(np.maximum(Lm, 1e-8)), 0).astype(np.float32); out['good'] = good
    return out

def dist_theta(box):
    x0, y0, x1, y1 = box; yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
    return d.astype(np.float32), th.astype(np.float32)

# ---------- polar (caixa lunar) ----------
DG = np.arange(-2, 16.01, 0.25); NTH = int(round(2 * np.pi * R / 0.5)); TH = np.linspace(0, 2 * np.pi, NTH, endpoint=False); DTH = np.degrees(TH)
_X = (cx + np.cos(TH)[None, :] * (R + DG[:, None]) - BOXL[0]).astype(np.float32); _Y = (cy - np.sin(TH)[None, :] * (R + DG[:, None]) - BOXL[1]).astype(np.float32)
def pol(a, interp=cv2.INTER_LINEAR): return cv2.remap(np.ascontiguousarray(a, np.float32), _X, _Y, interp)
SECTORS = {'dalt': (80, 100), 'dalt_esq': (120, 150), 'baix_esq': (210, 240), 'dreta': (330, 30)}
def sec(nm):
    lo, hi = SECTORS[nm]; return ((DTH >= lo) & (DTH < hi)) if lo < hi else ((DTH >= lo) | (DTH < hi))
def id_(d): return int(round((d - DG[0]) / 0.25))

def lum(c): return (c[..., 0] + 2 * c[..., 1] + c[..., 2]) / 4 if c.ndim == 3 else c
def fina(L, s):
    """energia fina (1–3 px al llarg de l'arc) de ln L per fila d, al sector s (com diag_fila.py)."""
    lp = np.log(np.maximum(pol(L), 1e-4)); hp = lp - gaussian_filter1d(lp, 3, axis=1, mode='wrap'); return np.std(hp[:, s], axis=1)
def escales(L, s, sig=(2, 4, 8, 16, 32)):
    """energia per escales d'arc (DoG entre σ consecutives, en mostres de 0,5 px: 1, 2, 4, 8, 16 px)."""
    lp = np.log(np.maximum(pol(L), 1e-4)); lv = [lp] + [gaussian_filter1d(lp, q, axis=1, mode='wrap') for q in sig]
    return {f'{sig[i-1]//2 if i>0 else 0}-{sig[i]//2}': np.std((lv[i] - lv[i + 1])[:, s], axis=1) for i in range(len(sig))}
def arcmean(L, s):
    p = pol(L); return p[:, s].mean(1)

class Compost:
    """Emulador del compost de la V104 a la caixa lunar (fins a la 234, sense les capes d'ajust), amb capes substituïdes."""
    def __init__(self):
        self.S = Estat(EST); self.P = self.S.pila(box=BOXL, fins_a=234)
    def c(self, subst=None, sense=()):
        subst = subst or {}; L = []
        for lid, mode, F, a in self.P:
            if lid in sense: continue
            L.append((mode, subst.get(lid, F), a))
        return comp(L, BOXL[3] - BOXL[1], BOXL[2] - BOXL[0])[0]
    def capa(self, lid): return [F for l, m, F, a in self.P if l == lid][0]

def crop_big_to_moon(arr, big=BIG):
    x0, y0 = BOXL[0] - big[0], BOXL[1] - big[1]; return arr[y0:y0 + 1400, x0:x0 + 1400]

def desa(p, d):
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else (x.tolist() if isinstance(x, np.ndarray) else str(x))) + '\n')

# ---------- resolució que segueix el S/N, conservant el perfil radial ----------
import numexpr as ne
def perfil_arc(A, dom, box, dmax=26.0, st=12.0, sr=0.35):
    """P = mitjana de A al llarg de l'arc a la MATEIXA d (nucli gaussià σ_t d'arc × σ_r radial, només dada), a d < dmax. Retorna (P, reg)."""
    d, th = dist_theta(box); reg = dom & (d > -1) & (d < dmax); iy, ix = np.nonzero(reg); d0 = d[iy, ix]; tr = np.radians(th[iy, ix]); tx, ty = -np.sin(tr), -np.cos(tr)
    rw = int(np.ceil(3 * st)); num = np.zeros(len(iy)); den = np.zeros(len(iy)); hh, ww = A.shape; mf = dom.astype(np.float32); Af = np.where(dom, A, 0).astype(np.float32)
    for dy in range(-rw, rw + 1):
        for dx in range(-rw, rw + 1):
            if dx * dx + dy * dy > rw * rw: continue
            ny = np.clip(iy + dy, 0, hh - 1); nx = np.clip(ix + dx, 0, ww - 1); dd = d[ny, nx] - d0; ts = dx * tx + dy * ty
            wt = ne.evaluate('exp(-0.5*(dd*dd/(sr*sr) + ts*ts/(st*st)))') * mf[ny, nx]; num += wt * Af[ny, nx]; den += wt
    P = np.zeros_like(A, dtype=np.float32); P[iy, ix] = num / np.maximum(den, 1e-20); return P, reg
LVP = [0.0, 0.5, 0.75, 1.0, 1.5, 2.0]
def piramide_sn(A, dom, sig, lv=LVP):
    """Promig per píxel amb σ(x): barreja contínua (barrets) de convolucions gaussianes normalitzades pel domini."""
    w = dom.astype(np.float32); pir = [A] + [cv2.GaussianBlur(np.where(dom, A, 0).astype(np.float32), (0, 0), s_) / np.maximum(cv2.GaussianBlur(w, (0, 0), s_), 1e-8) for s_ in lv[1:]]
    sg = np.clip(sig, 0, lv[-1]); out = np.zeros_like(A, dtype=np.float32); ws = np.zeros_like(out)
    for i in range(len(lv)):
        lo = lv[i - 1] if i > 0 else -1; hi = lv[i + 1] if i + 1 < len(lv) else lv[-1] + 1
        wi = np.where(sg <= lv[i], np.clip((sg - lo) / max(lv[i] - lo, 1e-9), 0, 1), np.clip((hi - sg) / max(hi - lv[i], 1e-9), 0, 1)) if i > 0 else np.clip(1 - sg / lv[1], 0, 1)
        out += wi * pir[i]; ws += wi
    return np.where(dom, out / np.maximum(ws, 1e-9), A).astype(np.float32)
def mitjana_sn(A, dom, sig, box=BOXL, perfil=True, log=False):
    """Resolució que segueix el S/N a la franja: A' = P · promig_σ(A/P) (perfil=True: el perfil radial al llarg de l'arc no es toca)
    o A' = promig_σ(A) (perfil=False). Amb log=True, A és un logaritme: A' = lnP + promig_σ(A − lnP). Només on σ > 0."""
    if not perfil: return np.where(sig > 0, piramide_sn(A, dom, sig), A).astype(np.float32)
    P, reg = perfil_arc(A, dom, box)
    if log: r = np.where(reg, A - P, 0).astype(np.float32); rs = piramide_sn(r, dom, sig); return np.where((sig > 0) & reg, P + rs, A).astype(np.float32)
    r = np.where(reg & (P > 0), A / np.maximum(P, 1e-30), 1).astype(np.float32); rs = piramide_sn(r, dom, sig); return np.where((sig > 0) & reg, P * rs, A).astype(np.float32)
