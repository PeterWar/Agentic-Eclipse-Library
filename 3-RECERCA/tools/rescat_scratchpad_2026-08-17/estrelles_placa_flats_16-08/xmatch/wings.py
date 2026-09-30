"""Perfil d'ales de la PSF estel.lar, apilant les estrelles identificades, amb
fons propi ajustat en un anell llunya. Compara amb el model de halo."""
import numpy as np, pandas as pd, pickle, json, rawpy
from scipy import ndimage as ndi

SONY = '/Users/USUARI/Desktop/Eclipse 2026/300mm/'
VIX = '/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/'
SONY_EXP = {'DSC06984': 2.0, 'DSC06985': 1.0, 'DSC06987': 8.0,
            'DSC06991': 1.0, 'DSC06993': 8.0, 'DSC06996': 2.0, 'DSC06999': 2.0}
R6_FR = [('572A2978', 1.0), ('572A2979', 2.0), ('572A2980', 2.0), ('572A2981', 2.0),
         ('572A2982', 10.3), ('572A2983', 10.3), ('572A2984', 10.3), ('572A2996', 1.0)]
GAIN = {'sony': 3.323, 'r6': 3.05}
PAD = 200
BGR = (150, 195)
BINS = np.array([0, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 13, 17, 22, 30, 40, 55, 75,
                 100, 130, 150])


def stamps(tag, tab):
    """Retorna la pila ponderada del perfil radial (unitats: fraccio del flux
    total per pixel) i el seu error."""
    if tag == 'sony':
        off = pickle.load(open('../sony_stars/offsets6.pkl', 'rb'))['off']
        MD = {e: np.load(f'../sony_stars/masterdark_{int(e)}s.npy') for e in (1., 2., 8.)}
        frames = list(SONY_EXP.items())
    else:
        off = {k: (v[1], v[2]) for k, v in json.load(
            open('../vixen/shifts_start.json')).items()}
        frames = R6_FR
    n = len(tab)
    NUM = np.zeros(len(BINS)-1)
    DEN = np.zeros(len(BINS)-1)
    VAR = np.zeros(len(BINS)-1)
    NPX = np.zeros(len(BINS)-1)
    for name, e in frames:
        if tag == 'sony':
            with rawpy.imread(SONY+name+'.ARW') as r:
                raw = r.raw_image_visible.astype(np.float32)
                col = r.raw_colors_visible
            img = raw - MD[e]
            good = ((col == 1) | (col == 3)) & (raw < 15600)
            dx, dy = off[name]
            sky = np.median(img[good][::97])
        else:
            with rawpy.imread(VIX+name+'.CR3') as r:
                raw = r.raw_image_visible[:4638, :6958].astype(np.float32)
                col = r.raw_colors_visible[:4638, :6958]
            img = raw - np.load(f'../vixen/dark_med_{"10" if e>5 else int(e)}.npy')[:4638, :6958]
            good = ((col == 1) | (col == 3)) & (raw < 15800)
            dx, dy = off[name][0], off[name][1]
            sky = np.median(img[good][::97])
        H, W = img.shape
        # mascara de totes les estrelles conegudes (per no contaminar el fons)
        for i in range(n):
            x = tab.x.values[i]+dx
            y = tab.y.values[i]+dy
            xi, yi = int(round(x)), int(round(y))
            if not (PAD < xi < W-PAD and PAD < yi < H-PAD):
                continue
            st = img[yi-PAD:yi+PAD+1, xi-PAD:xi+PAD+1].astype(np.float64)
            gm = good[yi-PAD:yi+PAD+1, xi-PAD:xi+PAD+1]
            Y, X = np.mgrid[-PAD:PAD+1, -PAD:PAD+1]
            rr = np.hypot(X-(x-xi), Y-(y-yi))
            # veines: exclou les altres estrelles
            om = np.ones_like(gm)
            for k in range(n):
                if k == i:
                    continue
                ddx = tab.x.values[k]+dx-x
                ddy = tab.y.values[k]+dy-y
                if abs(ddx) < PAD+20 and abs(ddy) < PAD+20:
                    om &= np.hypot(X-ddx-(x-xi), Y-ddy-(y-yi)) > 25
            base = gm & om & (rr >= BGR[0]) & (rr < BGR[1])
            if base.sum() < 3000:
                continue
            # pla + quadratic al fons
            A = np.column_stack([np.ones(base.sum()), X[base], Y[base],
                                 X[base]**2, Y[base]**2, X[base]*Y[base]])
            s, *_ = np.linalg.lstsq(A, st[base], rcond=None)
            Af = np.column_stack([np.ones(st.size), X.ravel(), Y.ravel(),
                                  X.ravel()**2, Y.ravel()**2, (X*Y).ravel()])
            res = st - (Af@s).reshape(st.shape)
            F = tab.flux_tot.values[i]/2.0 if tag == 'sony' else tab.flux_tot.values[i]
            F = tab.flux_tot.values[i]          # ADU/s, superficie verda
            if not np.isfinite(F) or F <= 0:
                continue
            Fadu = F*e                           # ADU al fotograma
            w = Fadu**2/max(sky, 1.0)            # pes optim
            m = gm & om
            idx = np.digitize(rr, BINS)-1
            v = np.where(m, res, np.nan)
            for b in range(len(BINS)-1):
                sel = m & (idx == b)
                k = sel.sum()
                if k < 4:
                    continue
                NUM[b] += w*np.nanmean(v[sel])/Fadu
                DEN[b] += w
                VAR[b] += w**2*(max(sky, 1.0)/GAIN[tag])/k/Fadu**2
                NPX[b] += k
        del img, good, raw, col
        print('   ', name, 'fet')
    prof = NUM/np.maximum(DEN, 1e-30)
    err = np.sqrt(VAR)/np.maximum(DEN, 1e-30)
    return prof, err, NPX


def halo_model(r, ch='G'):
    p = json.load(open('/Users/USUARI/Desktop/Eclipse 2026/Earthshine_FINAL/'
                       'earthshine_FINAL_halo_params.json'))[ch]
    P = 2048
    ky, kx = np.mgrid[0:P, 0:P]
    kd = np.hypot(np.minimum(kx, P-kx), np.minimum(ky, P-ky))
    out = np.zeros_like(r, float)
    for (s, b), A in ((p['k1'], p['A1']), (p['k2'], p['A2'])):
        K = 1.0/(1.0+(kd/s)**2)**b
        norm = K.sum()
        out += A*(1.0/(1.0+(r/s)**2)**b)/norm
    return out


if __name__ == '__main__':
    rc = 0.5*(BINS[1:]+BINS[:-1])
    res = {}
    for tag in ('sony', 'r6'):
        tab = pd.read_csv(f'zp2_{tag}.csv')
        tab = tab[np.isfinite(tab.flux_tot)].reset_index(drop=True)
        print(f'=== {tag}: apilant {len(tab)} estrelles ===')
        prof, err, npx = stamps(tag, tab)
        res[tag] = dict(r=rc.tolist(), prof=prof.tolist(), err=err.tolist(),
                        npx=npx.tolist())
        np.savez(f'wings_{tag}.npz', r=rc, prof=prof, err=err, npx=npx, bins=BINS)
    json.dump(res, open('wings.json', 'w'), indent=1)
