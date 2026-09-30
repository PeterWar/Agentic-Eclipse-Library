"""Mòdul comú de la recerca dels traços marrons (V108): geometria dels sis traços (capa 269 de Pere, la mateixa que C5_PERFILS de la V93),
perfils perpendiculars promitjats al llarg del traç i mesura del «solc» (profunditat relativa respecte d'una recta ajustada als flancs)."""
import json, sys
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]
OUT = ARREL / '4-RESULTATS/v108_20260926/marrons'
W, H = 10551, 7506
SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RLLUNA = 452.98
_c5 = json.loads((ARREL / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())
NOMS = ['T1 dalt (curt)', 'T2 diagonal llarga dalt-esquerra', 'T3 dalt-dreta (curt)', 'T4 diagonal dalt-dreta', 'T5 L vertical baix-dreta', 'T6 L horitzontal baix-dreta']
TRACOS = []
for k, t in enumerate(_c5['tracos']):
    i = t['info']; d = np.array(i['direccio'], float); d /= np.linalg.norm(d); n = np.array([-d[1], d[0]])
    TRACOS.append(dict(k=k + 1, nom=NOMS[k], centre=np.array(i['centre'], float), d=d, n=n, llarg=float(i['llarg'])))

def caixa(tr, marge=460):
    c, d, L = tr['centre'], tr['d'], tr['llarg']; p = np.array([c + d * L / 2, c - d * L / 2])
    x0 = int(max(0, np.floor(p[:, 0].min() - marge))); x1 = int(min(W, np.ceil(p[:, 0].max() + marge)))
    y0 = int(max(0, np.floor(p[:, 1].min() - marge))); y1 = int(min(H, np.ceil(p[:, 1].max() + marge)))
    return x0, y0, x1, y1

def graella(tr, tmax=400, dt=1.0, ds=2.0, s0=None, s1=None, dtheta=0.0, dt0=0.0):
    """Coordenades (x,y) de la graella (s al llarg, t perpendicular). dtheta (graus) gira el traç; dt0 el desplaça."""
    c, d = tr['centre'], tr['d']
    if dtheta:
        a = np.radians(dtheta); d = np.array([d[0] * np.cos(a) - d[1] * np.sin(a), d[0] * np.sin(a) + d[1] * np.cos(a)])
    n = np.array([-d[1], d[0]]); L = tr['llarg']
    s = np.arange(-L / 2 if s0 is None else s0, (L / 2 if s1 is None else s1) + 1e-6, ds); t = np.arange(-tmax, tmax + 1e-6, dt) + dt0
    X = c[0] + s[:, None] * d[0] + t[None, :] * n[0]; Y = c[1] + s[:, None] * d[1] + t[None, :] * n[1]
    return s, t, X.astype(np.float32), Y.astype(np.float32)

def mostreja(img, X, Y, org=(0, 0)):
    """img: 2D float32 (retall amb origen org). Fora → NaN."""
    Xl = X - org[0]; Yl = Y - org[1]
    P = cv2.remap(np.ascontiguousarray(img, np.float32), Xl, Yl, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
    fora = (Xl < 0) | (Yl < 0) | (Xl > img.shape[1] - 1) | (Yl > img.shape[0] - 1); P[fora] = np.nan
    return P

def perfil(img, tr, org=(0, 0), tmax=400, dt=1.0, ds=2.0, red='mediana', **kw):
    s, t, X, Y = graella(tr, tmax, dt, ds, **kw); P = mostreja(img, X, Y, org)
    with np.errstate(all='ignore'):
        pr = np.nanmedian(P, 0) if red == 'mediana' else np.nanmean(P, 0)
    return t, pr

def solc(t, pr, fin=(-60, 60), flancs=(120, 380), relatiu=True):
    """Profunditat del solc: mínim (o valor a la finestra) respecte d'una recta ajustada als flancs. relatiu → fracció del nivell."""
    k = np.isfinite(pr) & (np.abs(t) >= flancs[0]) & (np.abs(t) <= flancs[1])
    if k.sum() < 10: return None
    a = np.polyfit(t[k], pr[k], 1); tend = np.polyval(a, t); r = (pr - tend) / (tend if relatiu else 1.0)
    f = (t >= fin[0]) & (t <= fin[1]) & np.isfinite(r)
    if f.sum() == 0: return None
    j = np.argmin(np.where(f, r, np.inf)); jm = np.argmax(np.where(f, r, -np.inf))
    soroll = float(np.nanstd(r[k]))
    return dict(minim=float(r[j]), t_minim=float(t[j]), maxim=float(r[jm]), t_maxim=float(t[jm]), soroll_flancs=soroll, nivell=float(np.nanmedian(pr[k])))

def desa(path, d):
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else (x.tolist() if isinstance(x, np.ndarray) else str(x))) + '\n')
