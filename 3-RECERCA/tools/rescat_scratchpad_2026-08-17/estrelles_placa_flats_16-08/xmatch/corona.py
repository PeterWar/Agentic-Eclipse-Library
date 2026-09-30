"""Perfil radial de brillantor de la corona als dos trens, convertit a B/B_sol.
Prova creuada de la calibracio absoluta."""
import numpy as np, rawpy, json, pandas as pd
from scipy import ndimage as ndi

SONY = '/Users/USUARI/Desktop/Eclipse 2026/300mm/'
VIX = '/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/'
RSUN_AS = 947.07
zp2 = json.load(open('zp2.json'))
sol = json.load(open('final_solution.json'))
SCALE = {'sony': sol['sony']['scale'], 'r6': sol['r6']['scale']}
PED = {'sony': 512.0, 'r6': 511.5}
SAT = {'sony': 15600.0, 'r6': 15800.0}

FRAMES = {
    'sony': [('DSC06983', 1/30.), ('DSC06982', 1/4.), ('DSC06986', 1/8.),
             ('DSC06996', 2.0), ('DSC06993', 8.0)],
    'r6':   [('572A2970', 1/30.), ('572A2977', 1/4.), ('572A2971', 1/8.),
             ('572A2979', 2.0), ('572A2982', 10.3)],
}


def read_green(tag, name):
    path = (SONY+name+'.ARW') if tag == 'sony' else (VIX+name+'.CR3')
    with rawpy.imread(path) as r:
        raw = r.raw_image_visible.astype(np.float32)
        col = r.raw_colors_visible
    g = (col == 1) | (col == 3)
    sat = raw >= SAT[tag]
    return raw - PED[tag], g, sat


def moon_center(img, g, scale):
    """Centre del disc lunar: forat fosc envoltat de corona."""
    sm = ndi.uniform_filter(np.where(g, img, 0), 25)/np.maximum(
        ndi.uniform_filter(g.astype(np.float32), 25), 1e-3)
    hi = np.percentile(sm, 99.5)
    bright = sm > 0.05*hi
    fill = ndi.binary_fill_holes(bright)
    hole = fill & ~bright
    hole = ndi.binary_opening(hole, np.ones((15, 15)))
    lab, n = ndi.label(hole)
    if n == 0:
        return None
    sz = ndi.sum(hole, lab, range(1, n+1))
    k = 1+int(np.argmax(sz))
    ys, xs = np.nonzero(lab == k)
    return xs.mean(), ys.mean(), np.sqrt(len(xs)/np.pi)


rows = []
for tag in ('sony', 'r6'):
    s = SCALE[tag]
    Rsun_px = RSUN_AS/s
    ZP = zp2[tag]['ZPsun']
    Fsun = 10**(0.4*(ZP+26.75))          # ADU/s que faria el Sol sencer
    fac = np.pi*Rsun_px**2/Fsun          # B/B_sol per (ADU/s i pixel verd)
    print(f'=== {tag} ===  escala {s:.4f} "/px  Rsol={Rsun_px:.1f} px  '
          f'ZP={ZP:.3f}  F_sol={Fsun:.4e} ADU/s')
    print(f'    FACTOR = {fac:.4e} (B/B_sol) per (ADU/s per pixel verd)')
    for name, exp in FRAMES[tag]:
        img, g, sat = read_green(tag, name)
        mc = moon_center(img, g, s)
        if mc is None:
            print('   sense centre', name); continue
        cx, cy, rr = mc
        H, W = img.shape
        Y, X = np.mgrid[0:H, 0:W]
        R = np.hypot(X-cx, Y-cy)/Rsun_px
        bad = ndi.binary_dilation(sat, iterations=4)
        ok = g & ~bad
        prof = {}
        for r0 in (1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0, 10.0):
            m = ok & (R >= r0) & (R < r0*1.10)
            if m.sum() < 500:
                prof[r0] = np.nan; continue
            v = img[m]
            prof[r0] = float(np.median(v))/exp        # ADU/s
        rows.append(dict(tren=tag, frame=name, exp=exp, cx=cx, cy=cy,
                         rmoon_px=rr, rmoon_Rsun=rr/Rsun_px, fac=fac,
                         **{f'r{r0}': prof[r0] for r0 in prof}))
        print(f'   {name} {exp:8.4f}s centre=({cx:7.1f},{cy:7.1f}) '
              f'rlluna={rr/Rsun_px:.3f} Rsol  sat={100*sat.mean():.2f}%')
        del img, g, sat, R, X, Y
pd.DataFrame(rows).to_csv('corona_raw.csv', index=False)
print('\nfet')
