"""d29 (V100 detall) · ESTIMACIÓ CANDIDATA de la corona a la banda (dada real calibrada, cap model de la corona), per als agents i les proves:
per a cada píxel de la caixa lunar, la mitjana ponderada de TOTS els fotogrames Vixen que el veuen a D_real ≥ 1 px del seu limbe REAL (silueta
d'ordre 2, D21_silueta_o2.npz), cadascun dividit per la seva transmissió de vora mesurada T_classe(D_real) (TCORR_V99.json, fotogrames tardans)
i amb pes LDIC · smoothstep(D_real, 1, 2,5) · T² (variància inversa de V/T). Post-matriu (G', i RGB') com l'a3b/a3c.
També dues MEITATS INDEPENDENTS (fotogrames d'índex parell i senar dins de cada classe), per mesurar si el detall de la banda és reproduïble
(detall real) o soroll. Sortida: 4-RESULTATS/v100_detall_20260925/D29_candidat_banda.npz (G, G_parells, G_senars, RGB, NF, W_G, DREAL_MAX, box), o D29_SORTIDA."""
import json, os
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
O = ARREL / '4-RESULTATS/v100_detall_20260925'; O.mkdir(parents=True, exist_ok=True)
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
Mx = np.array(meta['matrix'], np.float32); gn = np.array(meta['gain'], np.float32)
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']; TC = json.loads((R9 / 'TCORR_V99.json').read_text())
LO, HI = float(os.environ.get('D29_LO', 1.0)), float(os.environ.get('D29_HI', 2.5))
TMAX = float(os.environ.get('D29_TMAX', 1e9))   # només fotogrames amb t < TMAX (la capa: primerencs; els tardans deixen traces de vora a dalt)
MEITATS = os.environ.get('D29_MEITATS', 'paritat')   # 'paritat' (parells/senars dins de la classe) o 'temps' (primera/segona meitat en el temps dins de la classe)
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
cls = [classe(f['exposure']) for f in fr]; paritat = {}; comptador = {}
USA = [j for j in range(len(fr)) if fr[j]['time'] < TMAX]
for c in set(cls):
    js = [j for j in USA if cls[j] == c]
    for i, j in enumerate(js): paritat[j] = (i % 2) if MEITATS == 'paritat' else (0 if i < len(js) / 2 else 1)
acc = {k: (np.zeros((hb, wb, 3)), np.zeros((hb, wb, 3))) for k in ('tot', 'parells', 'senars')}; NF = np.zeros((hb, wb), np.int16); DX = np.full((hb, wb), -99.0, np.float32)
for j in USA:
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = hb // 2, wb - 100
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    pa = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; Dr = Dj + DR - np.interp(pa.ravel(), pag, eg, period=360).reshape(hb, wb)
    s = smoothstep(Dr, LO, HI); t = TC[cls[j]]; T = np.exp(np.interp(Dr, t['D'], t['lnT'], left=t['lnT'][0], right=0.0)); T = np.where(s > 0, T, 1.0)
    for c in range(3):
        w = np.asarray(Wt[j, :, :, c], np.float64); n = np.asarray(N[j, :, :, c], np.float64); ws = w * s * T * T; ns = n * s * T
        for k in ('tot', 'parells' if paritat[j] == 0 else 'senars'): acc[k][0][..., c] += ns; acc[k][1][..., c] += ws
        if c == 1: NF += (ws > 0); DX = np.where(ws > 0, np.maximum(DX, Dr), DX)
def post(a):
    num, den = a; E = np.where(den > 0, num / np.maximum(den, 1e-30), 0).astype(np.float32); return np.einsum('ij,...j->...i', Mx, E * gn).astype(np.float32), den[..., 1].astype(np.float32)
Pt, Wg = post(acc['tot']); Pp, _ = post(acc['parells']); Ps, _ = post(acc['senars'])
SORT_ = Path(os.environ['D29_SORTIDA']) if os.environ.get('D29_SORTIDA') else O / 'D29_candidat_banda.npz'
np.savez_compressed(SORT_, box=np.array([by0, by1, bx0, bx1]), centre=np.array([LX, LY, RL]), RGB=Pt, G=Pt[..., 1], G_parells=Pp[..., 1], G_senars=Ps[..., 1], RGB_parells=Pp, RGB_senars=Ps,
                    NF=NF, W_G=Wg, DREAL_MAX=DX, rampa=np.array([LO, HI]))
d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
for a0 in (75, 105, 135, 225):
    z = (np.abs(((th - a0 + 180) % 360) - 180) < 15)
    print(a0, ' '.join(f"d{k}:NF{np.median(NF[z & (d >= k) & (d < k + 1)]):.0f}" for k in range(-1, 7)))
print('fet', SORT_)
