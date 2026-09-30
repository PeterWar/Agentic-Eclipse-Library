"""a4m (V92) · Continuació dels ràsters de filtre als píxels sense dada plena tocant la Lluna, AMB MIRALL DE LA TEXTURA.
Per què: a la V88 (a4) aquests ~4–6 px es continuaven COPIANT radialment el valor de r_ref = R + DMIN(θ) + VORA + 2 px. La textura hi queda
estirada al llarg del radi: és la vora fina de «lent» que Pere encara veia a la V91 (marques roses de la V90 a 0–32°, 45–98° i 230–305°; índex
d'estirament radial a 1–5 px del compost: 4,8 a baix i 1,6 a dalt, contra ≈1 de la corona de més enfora; la capa que més la porta és la 56 WOW
bilateral, research v91_lent_residual c1–c6).
Ara: nivell = mitjana AL LLARG DE L'ARC (gaussiana d'azimut σ 3 px, només dada) a cada radi; textura = ràster − nivell. A dins de r_ref:
valor = nivell(θ, r_ref) (el nivell es continua com a la V88, sense pendent) + textura(θ, 2·r_ref − ρ) (mirall a través de r_ref).
El nivell mitjà no canvia (la textura té mitjana zero a cada radi) i la textura hi conserva la isotropia. Mateixos pesos que la V88 (VORA 2,
smoothstep de VORA−1 a VORA+2 px). Després s'hi aplica el suavitzat radial a5c de la V91 (104–228°).
Entrada: 4-RESULTATS/v88_20260923/filtres/<tag>_u16.npy (els 16, abans de la continuació) i A3A_franja_un_instant.npz.
Sortida: 4-RESULTATS/v92_20260924/filtres_mirall/<tag>_u16.npy (continuació amb mirall, sense a5c) i A4M_MIRALL.json."""
from pathlib import Path
import json, sys, time, hashlib
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v92_20260924'; OUT = SORT / 'filtres_mirall'; OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923'))
from v86_operadors import smoothstep, ng
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
V88 = ARREL / '4-RESULTATS/v88_20260923'; FONTS = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'
TAGS = ['P01_NRGF', 'P01_NRGF_extrap', 'P02_RHEF', 'P02b_RHEF_ups0.35', 'P02c_RHEF_local60_native', 'P02d_RHEF_local30_native', '01', '04', '05', '06', '03', '03v30', '07', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral']
Q = np.load(V88 / 'A3A_franja_un_instant.npz'); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; dom = Q['domini']; DMIN = Q['DMIN']; NBZ = len(DMIN); cx, cy, R = [float(v) for v in Q['centre']]
VORA = 2.0; yq, xq = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xq - cx, yq - cy).astype('float32'); th = (np.degrees(np.arctan2(-(yq - cy), xq - cx)) + 360) % 360
dmin = DMIN[(th / 360 * NBZ).astype(int) % NBZ]; dist = (rL - R) - dmin; pes = (smoothstep(dist, VORA - 1, VORA + 2) * dom).astype('float32')
zona = (pes < 0.999) & (rL < R + 60); r_ref = (R + dmin + VORA + 2.0).astype('float32')
# polars (θ 0,05°, ρ de R−40 a R+80 px cada 0,25 px), amb 8 columnes de marge per costat per a la periodicitat
DT = 0.05; NT = int(360 / DT); PAD = 8; R0, DR = R - 40.0, 0.25; RHO = R0 + np.arange(int(120 / DR) + 1) * DR
TS = np.radians((np.arange(-PAD, NT + PAD) + 0.5) * DT); TT, RR = np.meshgrid(TS, RHO)
PX = (cx + RR * np.cos(TT) - bx0).astype('float32'); PY = (cy - RR * np.sin(TT) - by0).astype('float32')
sig_cols = (3.0 / (RHO * np.radians(DT)))                                                                    # σ de 3 px d'arc, en columnes, per fila
MV = cv2.remap(dom.astype('float32'), PX, PY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
IXc = (th / DT - 0.5 + PAD).astype('float32')
IYref = ((r_ref - R0) / DR).astype('float32'); IYmir = ((np.clip(2 * r_ref - rL, R0, RHO[-1]) - R0) / DR).astype('float32')
def arc(Z):
    out = np.empty_like(Z)
    for i in range(Z.shape[0]): out[i] = gaussian_filter1d(Z[i], sig_cols[i], mode='wrap')
    return out
den = arc(MV); rep = dict(vora_px=VORA, sigma_arc_px=3.0, capes={})
for tag in TAGS:
    u = np.load(V88 / 'filtres' / f'{tag}_u16.npy'); box = u[by0:by1, bx0:bx1].astype('float32') / 65535
    P = cv2.remap(box, PX, PY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    niv = arc(P * MV) / np.maximum(den, 1e-6); tex = np.where(MV > 0.999, P - niv, 0).astype('float32'); niv = niv.astype('float32')
    new = cv2.remap(niv, IXc, IYref, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) + cv2.remap(tex, IXc, IYmir, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    fos = np.where(zona, pes * box + (1 - pes) * new, box); out = u.copy(); out[by0:by1, bx0:bx1] = np.round(np.clip(fos, 0, 1) * 65535).astype('uint16')
    np.save(OUT / f'{tag}_u16.npy', out); rep['capes'][tag] = dict(sha256=sha(OUT / f'{tag}_u16.npy'), px_zona=int(zona.sum())); log(tag + ' continuat amb mirall')
(SORT / 'A4M_MIRALL.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); log('A4M fet')
