#!/usr/bin/env python3
"""Perfil de corona amb centrat pel LLIMB (gradient maxim radial), comparacio
final entre trens, i brillantor del cel.

Promogut del rescat estrelles_placa_flats_16-08/xmatch/corona2.py (16-08-2026):
rutes per comu.py, cwd = comu.work("xmatch"); algorisme intacte."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("xmatch"))

import numpy as np, rawpy, json, pandas as pd
from scipy import ndimage as ndi, optimize

SONY = str(comu.DADES_300MM) + '/'
VIX = str(comu.DADES_VIXEN_UNF) + '/'
RSUN_AS = 947.07
zp2 = json.load(open('zp2.json'))
sol = json.load(open('final_solution.json'))
SCALE = {'sony': sol['sony']['scale'], 'r6': sol['r6']['scale']}
PED = {'sony': 512.0, 'r6': 511.5}
SAT = {'sony': 15600.0, 'r6': 15800.0}
FRAMES = {'sony': [('DSC06983', 1/30.), ('DSC06986', 1/8.), ('DSC06982', 1/4.)],
          'r6': [('572A2970', 1/30.), ('572A2971', 1/8.), ('572A2977', 1/4.)]}
RADII = [1.15, 1.3, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0]


def limb_center(img, g, guess, Rmoon_px):
    """Centre pel llimb: maximitza la simetria del gradient radial."""
    sm = ndi.uniform_filter(np.where(g, img, np.nan)*1.0, 5)
    sm = np.where(np.isfinite(sm), sm, 0)
    th = np.linspace(0, 2*np.pi, 180, endpoint=False)

    def edge(cx, cy):
        rr = np.linspace(0.80, 1.25, 90)*Rmoon_px
        P = np.array([ndi.map_coordinates(
            sm, [cy+r*np.sin(th), cx+r*np.cos(th)], order=1) for r in rr])
        d = np.gradient(P, axis=0)
        k = np.argmax(d, axis=0)
        return rr[k]

    def cost(p):
        r = edge(p[0], p[1])
        return np.std(r)
    r0 = optimize.minimize(cost, guess, method='Nelder-Mead',
                           options=dict(xatol=0.3, fatol=0.02, maxiter=200))
    cx, cy = r0.x
    return cx, cy, float(np.median(edge(cx, cy)))


# Terme de color del Sol (correccio ordenada a la promocio, 17-08-2026; abans
# es feia a ma a partir de skeptic2/chain.py): el ZP s'ha ajustat amb el model
# V - m_inst = ZP - k(X-Xsun) - c(B-V), o sigui que el flux instrumental d'un
# astre de magnitud V i color (B-V) es 10^(0,4(ZP - c(B-V) - V)). Per al Sol,
# V = -26,75 i (B-V) = 0,653:  F_sol = 10^(0,4(ZP + 26,75 - 0,653 c)).
BV_SOL = 0.653
rows = []
FACS = {}
print('=== factor B/B_sol per (ADU/s i pixel verd): F_sol = 10^(0,4(ZP+26,75-0,653c)) ===')
for tag in ('sony', 'r6'):
    s = SCALE[tag]
    Rsun_px = RSUN_AS/s
    c_col = zp2[tag]['c']
    fac_nocolor = np.pi*Rsun_px**2/10**(0.4*(zp2[tag]['ZPsun']+26.75))
    fac = np.pi*Rsun_px**2/10**(0.4*(zp2[tag]['ZPsun']+26.75-BV_SOL*c_col))
    FACS[tag] = (fac, fac_nocolor)
    print(f'  {tag:5s} ZP={zp2[tag]["ZPsun"]:+.3f} c={c_col:+.4f}  '
          f'fac SENSE color = {fac_nocolor:.4e}   fac AMB color = {fac:.4e}  '
          f'(x{fac/fac_nocolor:.4f}, {100*(fac/fac_nocolor-1):+.1f} %)')
    for name, exp in FRAMES[tag]:
        path = (SONY+name+'.ARW') if tag == 'sony' else (VIX+name+'.CR3')
        with rawpy.imread(path) as r:
            raw = r.raw_image_visible.astype(np.float32)
            col = r.raw_colors_visible
        g = (col == 1) | (col == 3)
        sat = raw >= SAT[tag]
        img = raw - PED[tag]
        # llavor: centroide del forat fosc
        smm = ndi.uniform_filter(np.where(g, img, 0), 31)
        lo = smm < 0.05*np.percentile(smm, 99.5)
        lab, n = ndi.label(ndi.binary_fill_holes(smm > 0.05*np.percentile(smm, 99.5)) & lo)
        if n:
            sz = ndi.sum(lo, lab, range(1, n+1))
            ys, xs = np.nonzero(lab == 1+int(np.argmax(sz)))
            guess = [xs.mean(), ys.mean()]
        else:
            guess = [img.shape[1]/2, img.shape[0]/2]
        cx, cy, rlimb = limb_center(img, g, guess, 1.03*Rsun_px)
        H, W = img.shape
        Y, X = np.mgrid[0:H, 0:W]
        R = np.hypot(X-cx, Y-cy)/Rsun_px
        ok = g & ~ndi.binary_dilation(sat, iterations=4)
        rec = dict(tren=tag, frame=name, exp=exp, cx=cx, cy=cy,
                   rlimb_Rsun=rlimb/Rsun_px, fac=fac, fac_nocolor=fac_nocolor)
        for r0 in RADII:
            m = ok & (R >= r0) & (R < r0*1.08)
            rec[f'r{r0}'] = float(np.median(img[m]))/exp if m.sum() > 500 else np.nan
        rows.append(rec)
        print(f'{tag:5s} {name} {exp:8.4f}s centre=({cx:7.1f},{cy:7.1f}) '
              f'llimb={rlimb/Rsun_px:.4f} Rsol')
        del raw, img, g, sat, R, X, Y
d = pd.DataFrame(rows)
d.to_csv('corona2.csv', index=False)
import shutil
shutil.copy2('corona2.csv', comu.out()/'corona2.csv')

print('\n=== B/B_sol total (corona + cel), mediana azimutal (fac AMB color) ===')
cols = [f'r{r}' for r in RADII]
print(f'{"tren":5s} {"frame":10s} {"exp":>8s} ' + ' '.join(f'{r:>9.2f}' for r in RADII))
for _, r in d.iterrows():
    print(f'{r.tren:5s} {r.frame:10s} {r.exp:8.4f} ' +
          ' '.join(f'{r[c]*r.fac:9.3e}' if np.isfinite(r[c]) else f'{"-":>9s}' for c in cols))
print('\n=== quocient R6/Sony ===')
rat = []
for e in [1/30., 1/8., 1/4.]:
    a = d[(d.tren == 'sony') & (np.isclose(d.exp, e))].iloc[0]
    b = d[(d.tren == 'r6') & (np.isclose(d.exp, e))].iloc[0]
    q = [b[c]*b.fac/(a[c]*a.fac) if np.isfinite(a[c]) and np.isfinite(b[c]) else np.nan
         for c in cols]
    rat.append(q)
    print(f'  exp={e:7.4f}s  ' + ' '.join(f'{v:9.3f}' if np.isfinite(v) else f'{"-":>9s}' for v in q))
rat = np.array(rat)
med = np.nanmedian(rat, axis=0)
print('  MEDIANA     ' + ' '.join(f'{v:9.3f}' for v in med))
inner = ~np.isnan(rat[:, :7])
print(f'\n  quocient global R6/Sony a 1,15-3 Rsol: mediana '
      f'{np.nanmedian(rat[:, :7]):.3f}, interval '
      f'{np.nanmin(rat[:, :7]):.3f}-{np.nanmax(rat[:, :7]):.3f}'
      f'  ({-2.5*np.log10(np.nanmedian(rat[:, :7])):+.3f} mag)')
qnc = np.nanmedian(rat[:, :7])*(FACS['r6'][1]/FACS['r6'][0])/(FACS['sony'][1]/FACS['sony'][0])
print(f'  (el mateix quocient SENSE el terme de color: {qnc:.3f})')
print(f'\n=== RESUM factors B/B_sol per (ADU/s, pixel verd) ===')
for tag in ('sony', 'r6'):
    print(f'  {tag:5s} amb color {FACS[tag][0]:.4e}   sense color {FACS[tag][1]:.4e}')
