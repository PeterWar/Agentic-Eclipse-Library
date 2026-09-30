"""m1 · Perfils perpendiculars dels sis traços al COMPOST FUSIONAT de la V107 (Image Data del PSB, memmap, només lectura).
Per a cada traç: perfil de −400 a +400 px (mediana al llarg del traç), i afinament de l'angle i del desplaçament (±2°, pas 0,1°)
maximitzant la profunditat del solc. Sortida M1_COMPOST_V107.json i M1_perfils.npz."""
import sys, struct
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
psb = ARREL / '1-PHOTOSHOP/V107.psb'
with open(psb, 'rb') as f:
    hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]; Hh, Ww = struct.unpack('>II', hdr[14:22])
    n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1)
    pos = f.tell(); comp = struct.unpack('>H', f.read(2))[0]
assert comp == 0 and (Hh, Ww) == (H, W)
mm = np.memmap(psb, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W))
res = {}; perf = {}
for tr in TRACOS:
    x0, y0, x1, y1 = caixa(tr, 520)
    C = np.stack([np.asarray(mm[c, y0:y1, x0:x1], np.float32) / 65535 for c in range(3)], -1)
    L = C.mean(-1); G = C[..., 1]
    # afinament: angle i desplaçament que fan el solc més profund (al perfil de la mitjana RGB)
    best = None
    for dth in np.arange(-2.0, 2.01, 0.1):
        t, pr = perfil(L, tr, (x0, y0), tmax=420, dt=1, ds=4, dtheta=dth)
        q = solc(t, pr, fin=(-200, 200), flancs=(230, 410))
        if q and (best is None or q['minim'] < best[1]['minim']): best = (dth, q)
    dth = float(best[0]); tr['dtheta'] = dth
    t, pL = perfil(L, tr, (x0, y0), tmax=400, dt=1, ds=2, dtheta=dth)
    q0 = solc(t, pL, fin=(-200, 200), flancs=(230, 390)); t0 = q0['t_minim']
    # perfils centrats al solc
    t, pL = perfil(L, tr, (x0, y0), tmax=400, dt=1, ds=2, dtheta=dth, dt0=t0)
    _, pR = perfil(C[..., 0], tr, (x0, y0), tmax=400, dt=1, ds=2, dtheta=dth, dt0=t0)
    _, pG = perfil(G, tr, (x0, y0), tmax=400, dt=1, ds=2, dtheta=dth, dt0=t0)
    _, pB = perfil(C[..., 2], tr, (x0, y0), tmax=400, dt=1, ds=2, dtheta=dth, dt0=t0)
    tt = t - t0
    q = {c: solc(tt, p, fin=(-40, 40), flancs=(150, 390)) for c, p in (('L', pL), ('R', pR), ('G', pG), ('B', pB))}
    # consistència al llarg: quatre trams
    L4 = tr['llarg']; trams = []
    for a in range(4):
        s0 = -L4 / 2 + a * L4 / 4; _, pp = perfil(L, tr, (x0, y0), tmax=400, dt=1, ds=2, dtheta=dth, dt0=t0, s0=s0, s1=s0 + L4 / 4)
        trams.append(solc(tt, pp, fin=(-40, 40), flancs=(150, 390)))
    # amplada a mitja profunditat
    k = (np.abs(tt) >= 150) & np.isfinite(pL); a = np.polyfit(tt[k], pL[k], 1); r = pL / np.polyval(a, tt) - 1
    half = q['L']['minim'] / 2; inside = np.nonzero((r < half) & (np.abs(tt) < 150))[0]
    fwhm = float(tt[inside].max() - tt[inside].min()) if len(inside) else None
    c = tr['centre'] + tr['n'] * t0; dist_limbe = float(np.hypot(c[0] - LLUNA[0], c[1] - LLUNA[1]) - RLLUNA)
    res[tr['k']] = dict(nom=tr['nom'], dtheta_graus=dth, desplacament_t_px=float(t0), centre_afinat=c.round(1).tolist(), angle_afinat_graus=float((np.degrees(np.arctan2(tr['d'][1], tr['d'][0])) + dth) % 180),
                        dist_centre_al_limbe_px=dist_limbe, solc=q, amplada_mitja_profunditat_px=fwhm, trams=trams)
    perf[f'T{tr["k"]}_t'] = tt; perf[f'T{tr["k"]}_L'] = pL; perf[f'T{tr["k"]}_R'] = pR; perf[f'T{tr["k"]}_G'] = pG; perf[f'T{tr["k"]}_B'] = pB
    print(tr['k'], tr['nom'], f'dθ {dth:+.1f}° t0 {t0:+.0f}', 'L %.4f G %.4f R %.4f B %.4f' % tuple(q[c]['minim'] for c in 'LGRB'), 'soroll %.4f' % q['L']['soroll_flancs'], 'FWHM', fwhm, 'trams', [round(z['minim'], 4) for z in trams], flush=True)
desa(OUT / 'M1_COMPOST_V107.json', dict(font='V107.psb, compost fusionat (Image Data)', tracos=res))
np.savez_compressed(OUT / 'M1_perfils.npz', **perf)
