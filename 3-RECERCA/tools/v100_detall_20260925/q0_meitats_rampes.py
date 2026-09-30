"""q0 (V100 detall, dada) · La candidata d29 refeta a l'anell del limbe per a diverses RAMPES sobre D_real, amb quatre particions de fotogrames.
Mateixa física que d29_candidat_banda.py (còpia: cap canvi d'operador): cada fotograma Vixen de limb_frames_comuna, dividit per la seva transmissió
de vora mesurada T_classe(D_real) (TCORR_V99.json), pes LDIC · smoothstep(D_real, LO, HI) · T², post-matriu (G').
Només es calcula l'anell d = −12…+45 px del cercle de presentació (on hi ha la banda i les referències), per no refer tota la caixa.
Particions (totes disjuntes dos a dos dins de cada parella):
  · parells / senars: índex parell o senar dins de cada classe d'exposició (com d29) → meitats intercalades en el temps.
  · TA / TB: MEITATS TEMPORALS. TA = t < 23 s o 82 ≤ t < 100 s; TB = la resta. A la banda (que només veuen els primerencs, t 15–42 s) separa
    t 15–22 de t 23–42; a la dreta (tardans) separa 82–100 de 100–118 s. Serveix per descartar un patró fix del sensor, que camina amb la deriva
    (~0,27 px/s, G2c del 09-09) i que les meitats parells/senars comparteixen gairebé sencer.
Sortida: 4-RESULTATS/v100_detall_20260925/dada/Q0_meitats_rampes.npz (arrays plans sobre els índexs de l'anell `idx` de la caixa 1400×1400).
Ús: python q0_meitats_rampes.py   (rampes fixes: 0,5→2; 1→2,5; 1,5→3; 2→3,5)"""
import json, time
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
O = ARREL / '4-RESULTATS/v100_detall_20260925/dada'; O.mkdir(parents=True, exist_ok=True)
SORT = O / 'Q0_meitats_rampes.npz'
assert not SORT.exists(), f'ja existeix {SORT}: no se sobreescriu'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
Mx = np.array(meta['matrix'], np.float32); gn = np.array(meta['gain'], np.float32)
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']; TC = json.loads((R9 / 'TCORR_V99.json').read_text())
RAMPES = [(0.5, 2.0), (1.0, 2.5), (1.5, 3.0), (2.0, 3.5)]
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]
dc = np.hypot(xx - LX, yy - LY) - RL; anell = (dc >= -12) & (dc <= 45); idx = np.flatnonzero(anell.ravel()); iy, ix = np.unravel_index(idx, (hb, wb))
ya, xa = yy.ravel()[idx].astype(np.float64), xx.ravel()[idx].astype(np.float64); npx = idx.size
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
def smoothstep(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
cls = [classe(f['exposure']) for f in fr]; paritat = {}; comptador = {}
for j, c in enumerate(cls): comptador[c] = comptador.get(c, 0) + 1; paritat[j] = comptador[c] % 2
tt = np.array([f['time'] for f in fr]); TA = (tt < 23) | ((tt >= 82) & (tt < 100))
PARTS = ('tot', 'parells', 'senars', 'TA', 'TB')
def parts_de(j): return ('tot', 'parells' if paritat[j] == 0 else 'senars', 'TA' if TA[j] else 'TB')
acc = {(r, p): [np.zeros((npx, 3)), np.zeros((npx, 3))] for r in range(len(RAMPES)) for p in PARTS}
NF = {(r, p): np.zeros(npx, np.int16) for r in range(len(RAMPES)) for p in PARTS}
DX = {r: np.full(npx, -99.0) for r in range(len(RAMPES))}; TMED = {r: np.zeros(npx) for r in range(len(RAMPES))}
WCL = {(r, k): np.zeros(npx) for r in range(len(RAMPES)) for k in ('curts', 'mitjans', 'llargs')}
t0 = time.time()
for j in range(len(fr)):
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); jy, jx = hb // 2, wb - 100
    cx = jx + bx0 - (Dj[jy, jx] + Rm) * gx[jy, jx]; cy = jy + by0 - (Dj[jy, jx] + Rm) * gy[jy, jx]
    pa = (np.degrees(np.arctan2(-(ya - cy), xa - cx)) + 360) % 360; Dr = Dj[iy, ix] + DR - np.interp(pa, pag, eg, period=360)
    Wj = np.asarray(Wt[j], np.float64)[iy, ix, :]; Nj = np.asarray(N[j], np.float64)[iy, ix, :]
    t = TC[cls[j]]
    for r, (LO, HI) in enumerate(RAMPES):
        s = smoothstep(Dr, LO, HI); T = np.exp(np.interp(Dr, t['D'], t['lnT'], left=t['lnT'][0], right=0.0)); T = np.where(s > 0, T, 1.0)
        ws = Wj * (s * T * T)[:, None]; ns = Nj * (s * T)[:, None]
        for p in parts_de(j):
            acc[(r, p)][0] += ns; acc[(r, p)][1] += ws; NF[(r, p)] += (ws[:, 1] > 0)
        DX[r] = np.where(ws[:, 1] > 0, np.maximum(DX[r], Dr), DX[r]); TMED[r] += ws[:, 1] * tt[j]; WCL[(r, cls[j])] += ws[:, 1]
    if j % 10 == 0: print(f'fotograma {j + 1}/{len(fr)} · {time.time() - t0:.0f} s', flush=True)
def post(a):
    num, den = a; E = np.where(den > 0, num / np.maximum(den, 1e-30), 0).astype(np.float32)
    return np.einsum('ij,...j->...i', Mx, E * gn).astype(np.float32)[:, 1], den[:, 1].astype(np.float32)
out = dict(idx=idx, box=np.array([by0, by1, bx0, bx1]), centre=np.array([LX, LY, RL]), rampes=np.array(RAMPES), temps=tt, TA=TA,
           paritat=np.array([paritat[j] for j in range(len(fr))]), classes=np.array(cls))
for r in range(len(RAMPES)):
    for p in PARTS:
        G, W = post(acc[(r, p)]); out[f'G_{p}_r{r}'] = G; out[f'W_{p}_r{r}'] = W; out[f'NF_{p}_r{r}'] = NF[(r, p)]
    W = out[f'W_tot_r{r}'].astype(np.float64); out[f'DX_r{r}'] = DX[r].astype(np.float32); out[f'TMED_r{r}'] = np.where(W > 0, TMED[r] / np.maximum(W, 1e-30), np.nan).astype(np.float32)
    for k in ('curts', 'mitjans', 'llargs'): out[f'WCL_{k}_r{r}'] = WCL[(r, k)].astype(np.float32)
np.savez_compressed(SORT, **out)
# comprovació: la rampa 1→2,5 (r1) ha de reproduir la D29 (mateixa física)
Z = np.load(ARREL / '4-RESULTATS/v100_detall_20260925/D29_candidat_banda.npz')
for p, k in (('tot', 'G'), ('parells', 'G_parells'), ('senars', 'G_senars')):
    a = out[f'G_{p}_r1']; b = Z[k].ravel()[idx]; ok = (np.abs(b) > 0)
    print(f'control D29 {k}: max |rel| = {np.max(np.abs(a[ok] - b[ok]) / np.abs(b[ok])):.2e} (n={ok.sum()})')
print('fet', SORT, f'{time.time() - t0:.0f} s')
