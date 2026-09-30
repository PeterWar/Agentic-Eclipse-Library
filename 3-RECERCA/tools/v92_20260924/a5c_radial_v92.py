"""a5c (V92) · El suavitzat radial de la V91 (a5c_radial_on_hi_havia_linies.py, idèntic: σ 4 px → 0 a 14 px del limbe, NOMÉS a 104–228° amb fosa a
99–104° i 228–232°; polars 0,05° × 0,25 px, aplicat com a diferència) sobre els ràsters continuats amb mirall (a4m).
Entrada: 4-RESULTATS/v92_20260924/filtres_mirall/. Sortida: 4-RESULTATS/v92_20260924/filtres_v92/<tag>_u16.npy i A5C_V92.json."""
from pathlib import Path
import json, sys, time, hashlib
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v92_20260924'; FIN = SORT / 'filtres_mirall'; OUT = SORT / 'filtres_v92'; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923'))
from v86_operadors import smoothstep
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
TAGS = ['P01_NRGF', 'P01_NRGF_extrap', 'P02_RHEF', 'P02b_RHEF_ups0.35', 'P02c_RHEF_local60_native', 'P02d_RHEF_local30_native', '01', '04', '05', '06', '03', '03v30', '07', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral']
GEO = json.loads((ARREL / '4-RESULTATS/v91_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
S0, D1, D2, A0, A1, A2, A3 = 4.0, 4.0, 14.0, 99.0, 104.0, 228.0, 232.0; DMIN_P, DMAX_P, DR = -30.0, 30.0, 0.25; NT = 7200
m = int(R + DMAX_P + 4); bx0, bx1, by0, by1 = int(cx) - m, int(cx) + m + 1, int(cy) - m, int(cy) + m + 1
TS = np.radians((np.arange(NT) + 0.5) * 360 / NT); DS = np.arange(DMIN_P, DMAX_P + 1e-6, DR); TT, DD = np.meshgrid(TS, DS); TSg = np.degrees(TS)
S = S0 * smoothstep(TSg, A0, A1) * (1 - smoothstep(TSg, A2, A3)); SIG = (S[None, :] * (1 - smoothstep(DS, D1, D2))[:, None]).astype(np.float32)
MX = (cx + (R + DD) * np.cos(TT) - bx0).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT) - by0).astype(np.float32)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; tt = (np.arctan2(-(yy - cy), xx - cx) + 2 * np.pi) % (2 * np.pi)
IX = (tt / (2 * np.pi) * NT - 0.5).astype(np.float32); IY = ((d - DS[0]) / DR).astype(np.float32); dins = (d > DMIN_P) & (d < DMAX_P)
K = np.clip(np.floor(SIG).astype(int), 0, 3); FR = (SIG - K).astype(np.float32)
def radial(X):
    P = cv2.remap(X, MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    St = np.stack([P] + [cv2.GaussianBlur(P, (1, 0), sigmaX=1e-3, sigmaY=s / DR) for s in (1.0, 2.0, 3.0, 4.0)])
    A = np.take_along_axis(St, K[None], 0)[0]; B = np.take_along_axis(St, (K + 1)[None], 0)[0]; Q_ = np.where(SIG > 0, (1 - FR) * A + FR * B, P)
    back = lambda Z: cv2.remap(Z, np.mod(IX, NT), IY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.where(dins, X + (back(Q_) - back(P)), X)
rep = dict(finestra_azimut_graus=[A0, A1, A2, A3], sigma_max_px=S0, fosa_radial_px=[D1, D2], capes={})
for tag in TAGS:
    u = np.load(FIN / f'{tag}_u16.npy'); X = u[by0:by1, bx0:bx1].astype(np.float32) / 65535
    out = u.copy(); out[by0:by1, bx0:bx1] = np.round(np.clip(radial(X), 0, 1) * 65535).astype(np.uint16); np.save(OUT / f'{tag}_u16.npy', out)
    ys, xs = np.nonzero(out != u); az = (np.degrees(np.arctan2(-(ys - cy), xs - cx)) + 360) % 360
    rep['capes'][tag] = dict(sha256=sha(OUT / f'{tag}_u16.npy'), px_canviats=int(xs.size), fora_99_232=int(((az < 98.5) | (az > 232.5)).sum())); log(f"{tag}: {xs.size} px; fora de 99–232°: {rep['capes'][tag]['fora_99_232']}")
(SORT / 'A5C_V92.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); log('A5C V92 fet')
