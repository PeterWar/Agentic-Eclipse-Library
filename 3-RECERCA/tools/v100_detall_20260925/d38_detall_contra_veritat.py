"""d38 (V100 detall) · PROVA DEFINITIVA del detall tangencial de la banda, on hi ha VERITAT: a la dreta (PA 280–60; la Lluna s'hi allunya), el
mateix operador de la capa aplicat a (A) l'estimació feta NOMÉS amb els fotogrames primerencs (t < 32 s, rampa 2→3,5 sobre D_real, dividits per T:
exactament la situació de la banda de dalt, amb la seva contaminació per la vora de la Lluna) i a (B) la veritat (fotogrames t > 40 s amb D_real ≥ 9:
cap vora de Lluna a prop). Per calaix de D_real màxim dels primerencs i per banda d'escala al llarg de l'arc (DoG σ 2→4, 4→8, 8→16 px, i la suma):
correlació A·B, pendent de regressió de B sobre A, i rms del residu (contaminació + soroll) relatiu al rms de B. Només lectura."""
import json, os
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; LF = ARREL / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
O = ARREL / '4-RESULTATS/v100_detall_20260925'
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']; Rm = float(meta['radius_model'])
Mx = np.array(meta['matrix'], np.float64); gn = np.array(meta['gain'], np.float64)
esc = json.loads((R9 / 'B/lineal_v99_franja/A3C_FRANJA_SILUETA.json').read_text())['escales']; cF = [esc[f'c_F{c}'][0] for c in range(3)]
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; DR = Rm - RL
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']; TC = json.loads((R9 / 'TCORR_V99.json').read_text())
N = np.load(LF / 'numerator.npy', mmap_mode='r'); Wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]; t = np.array([f['time'] for f in fr])
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
def ss(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
accA = [np.zeros((hb, wb, 3)), np.zeros((hb, wb, 3))]; accB = [np.zeros((hb, wb, 3)), np.zeros((hb, wb, 3))]; DXA = np.full((hb, wb), -99.0)
for j in range(len(fr)):
    if not (t[j] < 32 or t[j] > 40): continue
    Dj = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(Dj); iy, ix = hb // 2, wb - 100
    cx = ix + bx0 - (Dj[iy, ix] + Rm) * gx[iy, ix]; cy = iy + by0 - (Dj[iy, ix] + Rm) * gy[iy, ix]
    pa = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; Dr = Dj + DR - np.interp(pa.ravel(), pag, eg, period=360).reshape(hb, wb)
    if t[j] < 32:
        s = ss(Dr, float(os.environ.get('D38_LO', 2.0)), float(os.environ.get('D38_HI', 3.5))); tc = TC[classe(fr[j]['exposure'])]; T = np.where(s > 0, np.exp(np.interp(Dr, tc['D'], tc['lnT'], left=tc['lnT'][0], right=0.0)), 1.0); acc = accA
    else:
        s = (Dr >= 9).astype(float); T = np.ones_like(Dr); acc = accB
    for c in range(3):
        w = np.asarray(Wt[j, :, :, c], np.float64); n = np.asarray(N[j, :, :, c], np.float64); acc[0][..., c] += n * s * T; acc[1][..., c] += w * s * T * T
        if c == 1 and t[j] < 32: DXA = np.where(w * s > 0, np.maximum(DXA, Dr), DXA)
def lum(acc):
    E = np.where(acc[1] > 0, acc[0] / np.maximum(acc[1], 1e-30), 0); P = np.einsum('ij,...j->...i', Mx, E * gn); ok = (acc[1] > 0).all(-1) & (P > 0).all(-1)
    return np.where(ok, (cF[0] * P[..., 0] + 2 * cF[1] * P[..., 1] + cF[2] * P[..., 2]) / 4, 0), ok
LA, okA = lum(accA); LB, okB = lum(accB)
DR_, DS_ = 0.25, 0.5; rr = np.arange(-2.0, 20.0, DR_); nth = int(round(2 * np.pi * RL / DS_)); tt = np.arange(nth) * 2 * np.pi / nth
R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); mx = (LX + R_ * np.cos(T_) - bx0).astype(np.float32); my = (LY - R_ * np.sin(T_) - by0).astype(np.float32)
def polar(img, ok):
    a = cv2.remap(np.where(ok, img, 0).astype(np.float32), mx, my, cv2.INTER_LINEAR); w = cv2.remap(ok.astype(np.float32), mx, my, cv2.INTER_LINEAR)
    return np.where(w > 0.999, np.log(np.maximum(a / np.maximum(w, 1e-6), 1e-30)), np.nan)
PA_, PB_ = polar(LA, okA), polar(LB, okB); DXp = cv2.remap(DXA.astype(np.float32), mx, my, cv2.INTER_NEAREST)
OK = np.isfinite(PA_) & np.isfinite(PB_)
def gt(x, s):
    w = OK.astype(float); return gaussian_filter1d(np.where(OK, x, 0) * w, s / DS_, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(w, s / DS_, axis=1, mode='wrap'), 1e-6)
def bands(x): g = {s: gt(x, s) for s in (2, 4, 8, 16)}; b = {'2-4': g[2] - g[4], '4-8': g[4] - g[8], '8-16': g[8] - g[16]}; b['suma'] = b['2-4'] + b['4-8'] + b['8-16']; return b
BA, BB = bands(PA_), bands(PB_); thp = np.degrees(tt); _p0, _p1 = float(os.environ.get('D38_PA0', 280)), float(os.environ.get('D38_PA1', 60)); sec = (((thp - _p0) % 360) < ((_p1 - _p0) % 360))[None, :]
rep = {}
for lo, hi in ((1.5, 2.5), (2.0, 2.5), (2.5, 3.0), (3.0, 3.5), (3.5, 4.5), (4.5, 6.0), (6.0, 9.0), (9.0, 14.0)):
    z = OK & sec & (DXp >= lo) & (DXp < hi); r = {}
    if z.sum() < 500: continue
    for k in BA:
        a = BA[k][z]; b = BB[k][z]; cc = float(np.corrcoef(a, b)[0, 1]); sl = float(np.sum(a * b) / np.sum(a * a)); res = float(np.std(b - sl * a) / np.std(b))
        r[k] = dict(corr=round(cc, 3), pendent_B_sobre_A=round(sl, 3), residu_rel=round(res, 3), rms_A=round(float(np.std(a)), 4), rms_B=round(float(np.std(b)), 4))
    rep[f'{lo}-{hi}'] = dict(n=int(z.sum()), **r)
    print(f'D_real {lo}-{hi} n={z.sum()}', ' | '.join(f"{k}: r {v['corr']:.2f} pend {v['pendent_B_sobre_A']:.2f} rmsA/B {v['rms_A']:.3f}/{v['rms_B']:.3f}" for k, v in r.items()), flush=True)
(O / os.environ.get('D38_SORTIDA', 'D38_DETALL_CONTRA_VERITAT.json')).write_text(json.dumps(rep, ensure_ascii=False, indent=1))
