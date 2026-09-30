"""c1b (V106, Claude, 26-09-2026) · El detall tangencial de la c1 (V105), però cada fotograma dividit per la seva TRANSMISSIÓ FÍSICA T = Φ_PSF(D_LOLA)
(vora real de LOLA + δ del centre + PSF per canal, ajust b1): el relleu lunar ja no s'imprimeix com a variació al llarg de l'arc. S'admet on T ≥ 0,5
(rampa 0,5→0,7), pes W·T²; els fotogrames sense ajust b1 (saturats o llargs) no hi entren. Origen (c1) ·
Per a cada fotograma j (limb_frames sense llindar, Codex 26-09): L_j = (R'+2G'+B')/4 post-matriu, en polar al voltant del centre de
presentació; δ_j = ln L_j − mitjana gaussiana normalitzada al llarg de l'arc (σ_c px d'arc), només on el fotograma veu el píxel a
D_real ≥ 0,6 px (silueta D21) i amb el nucli gruixut gairebé complet. Combinació: Σ a_j δ_j / Σ a_j, a_j = W_G,j · smoothstep(D_real,0,6,2).
Mitjana zero per arc per construcció: no pot fer cap anell ni cap línia. Res fora d'on hi ha observació (δ = 0, pes 0)."""
import json, sys, numpy as np, cv2, time
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
import os
R0 = Path(__file__).resolve().parents[3]
LF = Path(os.environ.get('V105_LF', str(R0 / '4-RESULTATS/v106_inversio_20260926/limb_frames_sense_llindar')))   # limb_frames sense llindar (Codex): es refan amb a9b_limb_frames_sense_llindar_codex.py --finestra comuna --floor 0 --indices 0..66
OUT = R0 / '4-RESULTATS/v106_inversio_20260926/c1b'; OUT.mkdir(parents=True, exist_ok=True)
SIGC = float(sys.argv[1]) if len(sys.argv) > 1 else 32.0
RAMPA = tuple(float(v) for v in os.environ.get('V105_RAMPA', '0.6,2.0').split(','))   # rampa física per fotograma sobre D_real (px); la capa V105 lliurada: vegeu el RESULTAT
TAG = os.environ.get('V105_TAG', '')
T_ADM = tuple(json.loads(os.environ.get('V106_TADM', '[0.5, 0.7]')))
RAMPA_PA = json.loads(os.environ['V105_RAMPA_PA']) if os.environ.get('V105_RAMPA_PA') else None   # [[PA, lo, hi], ...] interpolat periòdicament (sobreescriu RAMPA)   # σ de la mitjana al llarg de l'arc (px d'arc); la capa V105 fa servir 32
meta = json.loads((LF/'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(LF/'numerator.npy', mmap_mode='r'); wt = np.load(LF/'weight.npy', mmap_mode='r'); Dm = np.load(LF/'distance_model.npy', mmap_mode='r')
geo = json.loads((R0/'4-RESULTATS/v97_refundacio_20260924/lineal_v97_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
Rm = float(meta['radius_model']); DR = Rm - R
sil = np.load(R0/'4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'); SIL_PA = np.asarray(sil['pa'], float); SIL_E = np.asarray(sil['e'], float)
M = np.array(meta['matrix'], np.float64); gain = np.array(meta['gain'], np.float64)
hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]
def dreal(j):
    Dj = np.asarray(Dm[j], np.float64); gy_, gx_ = np.gradient(Dj); iy_, ix_ = hb // 2, wb - 100
    cxj = ix_ + bx0 - (Dj[iy_, ix_] + Rm) * gx_[iy_, ix_]; cyj = iy_ + by0 - (Dj[iy_, ix_] + Rm) * gy_[iy_, ix_]
    PAj = (np.degrees(np.arctan2(-(yy - cyj), xx - cxj)) + 360) % 360
    return (Dj + DR - np.interp(PAj.ravel(), SIL_PA, SIL_E, period=360).reshape(hb, wb)).astype(np.float32)
# graella polar: files = d (px des del cercle de presentació), columnes = θ (0 = +x, 90 = amunt)
dgrid = np.arange(-4.0, 40.0001, 0.25).astype(np.float32); nth = int(round(2 * np.pi * R / 0.5)); th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
X = (cx + np.cos(th)[None, :] * (R + dgrid[:, None]) - bx0).astype(np.float32); Y = (cy - np.sin(th)[None, :] * (R + dgrid[:, None]) - by0).astype(np.float32)
def pol(a): return cv2.remap(np.ascontiguousarray(a, np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
def smooth_ss(x): return np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))
from scipy.special import erf
B1 = {c: {r['j']: r for r in json.loads((R0 / f'4-RESULTATS/v106_inversio_20260926/b1/B1_PSF_LOLA_canal{c}.json').read_text())['fotogrames']} for c in range(3)}
TH_N = json.loads((R0 / '4-RESULTATS/v106_inversio_20260926/b1/B1_PSF_LOLA_canal1.json').read_text())['nord']
_L = np.load(R0 / '4-RESULTATS/v106_inversio_20260926/lola/PERFIL_prova.npz'); _lh = _L['h_km'] * R / 1737.4; _ang = (TH_N + _L['pa']) % 360; _o = np.argsort(_ang)
_grid = np.arange(0, 360, 0.05); _rl = np.interp(_grid, _ang[_o], _lh[_o], period=360)
_A = np.stack([np.ones_like(_grid), np.cos(np.radians(_grid)), np.sin(np.radians(_grid)), np.cos(2 * np.radians(_grid)), np.sin(2 * np.radians(_grid))], 1)
_cf, *_ = np.linalg.lstsq(_A, _rl, rcond=None); _RL = _rl - _A @ _cf
def dfina(j):
    Dj = np.asarray(Dm[j], np.float64); gy_, gx_ = np.gradient(Dj); iy_, ix_ = hb // 2, wb - 100
    cxj = ix_ + bx0 - (Dj[iy_, ix_] + Rm) * gx_[iy_, ix_] + B1[1][j]['dx']; cyj = iy_ + by0 - (Dj[iy_, ix_] + Rm) * gy_[iy_, ix_] + B1[1][j]['dy']
    a = (np.degrees(np.arctan2(-(yy - cyj), xx - cxj)) + 360) % 360
    return (np.hypot(xx - cxj, yy - cyj) - R - np.interp(a.ravel(), SIL_PA, SIL_E, period=360).reshape(hb, wb) - np.interp(a, _grid, _RL, period=360)).astype(np.float32)
def psf_T(D, s1, f, s2): return (1 - f) * 0.5 * (1 + erf(D / (np.sqrt(2) * s1))) + f * 0.5 * (1 + erf(D / (np.sqrt(2) * s2)))
if RAMPA_PA:
    _t = np.array(RAMPA_PA, np.float64); _o = np.argsort(_t[:, 0]); _pa = np.degrees(th) % 360
    LO = np.interp(_pa, _t[_o, 0], _t[_o, 1], period=360)[None, :].astype(np.float32); HI = np.interp(_pa, _t[_o, 0], _t[_o, 2], period=360)[None, :].astype(np.float32)
else:
    LO = np.float32(RAMPA[0]); HI = np.float32(RAMPA[1])
sc = SIGC / 0.5   # σ en mostres
Sa = np.zeros((len(dgrid), nth)); Sd = np.zeros_like(Sa); Sd2 = np.zeros_like(Sa)
halves = {'h125': [], 'hcurts': [], 'hA': [], 'hB': []}; H = {k: [np.zeros_like(Sa), np.zeros_like(Sa)] for k in halves}
CENTRES = {}   # centre lunar de cada fotograma al llenç (per a la prova «Lluna o corona», m1)
DRMAX = np.full(Sa.shape, -99.0)
t0 = time.time(); rows = []
for j, f in enumerate(fr):
    if not all(j in B1[c] and not B1[c][j]['saturat'] for c in range(3)): continue      # V106: només fotogrames amb transmissió física ajustada
    W = np.asarray(wt[j], np.float32); N = np.asarray(num[j], np.float32)
    if not (W[..., 1] > 0).any(): continue
    Df = dfina(j); Tc = np.stack([psf_T(Df.astype(np.float64), B1[c][j]['s1'], B1[c][j]['f'], B1[c][j]['s2']) * B1[c][j]['g'] for c in range(3)], -1).astype(np.float32)
    Wp = np.stack([pol(W[..., c]) for c in range(3)], -1); Np = np.stack([pol(N[..., c]) for c in range(3)], -1); Dp = pol(Df); Tp = np.stack([pol(Tc[..., c]) for c in range(3)], -1)
    Tg = Tp[..., 1] / B1[1][j]['g']
    ok = (Wp > 1e-12).all(-1) & (Tg >= T_ADM[0]) & (Tp > 0).all(-1)
    V = np.where(ok[..., None], Np / np.maximum(Wp, 1e-30) / np.maximum(Tp, 1e-6), 0) * gain; P = V @ M.T; L = (P[..., 0] + 2 * P[..., 1] + P[..., 2]) / 4
    ok &= L > 0
    if ok.sum() < 1000: continue
    v = ok.astype(np.float64); lL = np.where(ok, np.log(np.maximum(L, 1e-9)), 0)
    cw = gaussian_filter1d(v, sc, axis=1, mode='wrap'); cm = gaussian_filter1d(lL * v, sc, axis=1, mode='wrap') / np.maximum(cw, 1e-12)
    fw = gaussian_filter1d(v, 1.0, axis=1, mode='wrap'); fm = gaussian_filter1d(lL * v, 1.0, axis=1, mode='wrap') / np.maximum(fw, 1e-12)
    okd = ok & (cw >= 0.9)
    dj = np.where(okd, fm - cm, 0)
    a = np.where(okd, Wp[..., 1] * Tg ** 2 * smooth_ss((Tg - T_ADM[0]) / (T_ADM[1] - T_ADM[0])), 0)
    Sa += a; Sd += a * dj; Sd2 += a * dj * dj; DRMAX = np.where(okd, np.maximum(DRMAX, Dp), DRMAX)
    k = 'h125' if abs(f['exposure'] - 1/125) < 1e-6 else ('hcurts' if f['exposure'] <= 1/400 else None)
    if k: H[k][0] += a; H[k][1] += a * dj
    kg = 'hA' if j <= 10 else ('hB' if 13 <= j <= 18 else None)   # grups de la prova «Lluna o corona» (instant de presentació contra 25–30 s)
    if kg: H[kg][0] += a; H[kg][1] += a * dj
    _D = np.asarray(Dm[j], np.float64); _gy, _gx = np.gradient(_D); _iy, _ix = hb // 2, wb - 100
    CENTRES[j] = (float(_ix + bx0 - (_D[_iy, _ix] + Rm) * _gx[_iy, _ix]), float(_iy + by0 - (_D[_iy, _ix] + Rm) * _gy[_iy, _ix]))
    rows.append(dict(j=j, nom=f['name'], t=round(f['time'], 2), exp=f['exposure'], pes_total=float(a.sum())))
    print(j, f['name'], round(time.time() - t0, 1), flush=True)
delta = np.where(Sa > 0, Sd / np.maximum(Sa, 1e-30), 0)
np.savez_compressed(OUT/f'DELTA_sigc{SIGC:g}{TAG}.npz', rampa=np.array(RAMPA), rampa_pa=np.array(RAMPA_PA if RAMPA_PA else []), delta=delta.astype(np.float32), pes=Sa.astype(np.float32), dgrid=dgrid, nth=nth, centre=np.array([cx, cy, R]),
    h125=np.where(H['h125'][0] > 0, H['h125'][1] / np.maximum(H['h125'][0], 1e-30), np.nan).astype(np.float32), p125=H['h125'][0].astype(np.float32),
    hcurts=np.where(H['hcurts'][0] > 0, H['hcurts'][1] / np.maximum(H['hcurts'][0], 1e-30), np.nan).astype(np.float32), pcurts=H['hcurts'][0].astype(np.float32), drmax=DRMAX.astype(np.float32),
    hA=np.where(H['hA'][0] > 0, H['hA'][1] / np.maximum(H['hA'][0], 1e-30), np.nan).astype(np.float32), pA=H['hA'][0].astype(np.float32),
    hB=np.where(H['hB'][0] > 0, H['hB'][1] / np.maximum(H['hB'][0], 1e-30), np.nan).astype(np.float32), pB=H['hB'][0].astype(np.float32),
    centres=np.array([[j, *CENTRES[j]] for j in sorted(CENTRES)]))
(OUT/f'FOTOGRAMES_sigc{SIGC:g}{TAG}.json').write_text(json.dumps(rows, indent=1))
print('fet', time.time() - t0)
