"""Fotometria d'obertura FOTOGRAMA A FOTOGRAMA, recentrant a cada imatge.
Evita l'esbiaix de la pila Sony (rotacio de camp de 0,138 graus entre grups).
Unitats: ADU/s, superficie verda (equivalent a 'tots els pixels verds')."""
import numpy as np, pandas as pd, pickle, json, sys
from scipy import ndimage as ndi

RMAX = 20
ANN = (26, 40)
SONY_DIR = '/Users/USUARI/Desktop/Eclipse 2026/300mm/'
SONY_EXP = {'DSC06984': 2.0, 'DSC06985': 1.0, 'DSC06987': 8.0,
            'DSC06991': 1.0, 'DSC06993': 8.0, 'DSC06996': 2.0, 'DSC06999': 2.0}
SONY_GAIN = 3.323
R6_FR = [('572A2978', 1.0), ('572A2979', 2.0), ('572A2980', 2.0), ('572A2981', 2.0),
         ('572A2982', 10.3), ('572A2983', 10.3), ('572A2984', 10.3), ('572A2996', 1.0)]


def phot_stamp(res, valid, x, y, rmax=RMAX, ann=ANN, recenter=True, search=9):
    """res: residu (ADU) ; valid: mascara de pixels utilitzables (verds i sans).
    Retorna (flux acumulat per r, fons, x, y, npix)."""
    P = ann[1]+3
    H, W = res.shape
    xi, yi = int(round(x)), int(round(y))
    if not (P < xi < W-P and P < yi < H-P):
        return None
    st = res[yi-P:yi+P+1, xi-P:xi+P+1].astype(np.float64)
    vm = valid[yi-P:yi+P+1, xi-P:xi+P+1]
    Y, X = np.mgrid[-P:P+1, -P:P+1]
    fx, fy = x-xi, y-yi
    if recenter:
        # centroide en una finestra petita, amb suavitzat
        sm = np.where(vm, st, 0.0)
        cnt = ndi.uniform_filter(vm.astype(float), 3)
        sm = ndi.uniform_filter(sm, 3)/np.maximum(cnt, 1e-3)
        box = (np.abs(X-fx) <= search) & (np.abs(Y-fy) <= search)
        w = np.where(box, sm, -1e30)
        j = np.unravel_index(np.argmax(w), w.shape)
        cx0, cy0 = X[j], Y[j]
        rr0 = np.hypot(X-cx0, Y-cy0)
        m = (rr0 <= 4.0) & vm
        b0 = np.median(st[(rr0 >= ann[0]) & (rr0 < ann[1]) & vm])
        s = np.clip(st-b0, 0, None)*m
        tot = s.sum()
        if tot > 0:
            fx = cx0 + (s*(X-cx0)).sum()/tot
            fy = cy0 + (s*(Y-cy0)).sum()/tot
    rr = np.hypot(X-fx, Y-fy)
    a = (rr >= ann[0]) & (rr < ann[1]) & vm
    if a.sum() < 40:
        return None
    b = np.median(st[a])
    s = st - b
    F = np.zeros(rmax)
    N = np.zeros(rmax)
    for k in range(rmax):
        m = (rr <= k+1) & vm
        F[k] = s[m].sum()
        N[k] = m.sum()
    return F, b, xi+fx, yi+fy, N, np.std(st[a])


def do_sony(tab):
    import rawpy
    off = pickle.load(open('../sony_stars/offsets6.pkl', 'rb'))['off']
    MD = {e: np.load(f'../sony_stars/masterdark_{int(e)}s.npy') for e in (1., 2., 8.)}
    n = len(tab)
    FR = {}
    for name, e in SONY_EXP.items():
        with rawpy.imread(SONY_DIR+name+'.ARW') as r:
            raw = r.raw_image_visible.astype(np.float32)
            col = r.raw_colors_visible
        bkg = np.load(f'../sony_stars/bkg_{name}.npy')
        res = raw - MD[e] - bkg
        green = (col == 1) | (col == 3)
        valid = green & (raw < 15600) & (~ndi.binary_dilation(raw >= 15600, iterations=6))
        dx, dy = off[name]
        F = np.full((n, RMAX), np.nan)
        S = np.full(n, np.nan)
        for i in range(n):
            out = phot_stamp(res, valid, tab.x.values[i]+dx, tab.y.values[i]+dy)
            if out is None:
                continue
            F[i], _, _, _, _, sd = out
            F[i] *= 2.0/e            # verd -> superficie verda completa ; ADU/s
            S[i] = sd*2.0/e
        FR[name] = dict(F=F, S=S, exp=e, bg=float(np.median(bkg[valid])))
        print('  sony', name, 'fet'); sys.stdout.flush()
        del raw, res, bkg, valid, green
    return FR


def do_r6(tab):
    SH = json.load(open('../vixen/shifts_start.json'))
    n = len(tab)
    FR = {}
    for name, e in R6_FR:
        res = np.load(f'../vixen/res_{name}.npy')
        msk = np.load(f'../vixen/msk_{name}.npy')
        valid = ~msk
        _, dx, dy = SH[name]
        F = np.full((n, RMAX), np.nan)
        S = np.full(n, np.nan)
        for i in range(n):
            out = phot_stamp(res, valid, tab.x.values[i]+dx, tab.y.values[i]+dy)
            if out is None:
                continue
            F[i], _, _, _, _, sd = out
            F[i] /= e                # res ja es superficie verda completa
            S[i] = sd/e
        FR[name] = dict(F=F, S=S, exp=e)
        print('  r6', name, 'fet'); sys.stdout.flush()
        del res, msk, valid
    return FR


if __name__ == '__main__':
    for tag, fn in (('sony', do_sony), ('r6', do_r6)):
        tab = pd.read_csv(f'final_match_{tag}.csv')
        print(f'=== {tag}: {len(tab)} estrelles identificades ===')
        FR = fn(tab)
        np.savez(f'phot_{tag}.npz',
                 names=np.array(list(FR)),
                 F=np.array([FR[k]['F'] for k in FR]),
                 S=np.array([FR[k]['S'] for k in FR]),
                 exp=np.array([FR[k]['exp'] for k in FR]),
                 det=tab.det.values)
        print()
