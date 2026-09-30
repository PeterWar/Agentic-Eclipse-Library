"""Centre lunar per capa, mètode de mig nivell: per azimut (pas 1°) la vora és el radi on G creua la meitat entre
el nivell interior (mediana 430-442 px) i l'exterior (mediana 462-472 px), interpolat linealment. Ajust de cercle
robust; es reporten residus per sector de 30°."""
import json, sys, numpy as np
from scipy import ndimage as ndi
from geom import V2B
def halfedges(G, c0, pas=1.0):
    cx0, cy0 = c0; x0, y0 = int(cx0-540), int(cy0-540); S = 1080
    img = np.asarray(G[y0:y0+S, x0:x0+S], np.float32)
    az = np.radians(np.arange(0, 360, pas)); rr = np.arange(428, 474, 0.25)
    cx, cy = cx0-x0, cy0-y0
    X = cx + rr[None,:]*np.cos(az[:,None]); Y = cy - rr[None,:]*np.sin(az[:,None])
    prof = ndi.map_coordinates(img, [Y.ravel(), X.ravel()], order=1).reshape(len(az), len(rr))
    ins = np.median(prof[:, (rr>=430)&(rr<=442)], axis=1); outs = np.median(prof[:, (rr>=462)&(rr<=472)], axis=1)
    half = 0.5*(ins+outs); rad = np.full(len(az), np.nan)
    for j in range(len(az)):
        above = np.where(prof[j] >= half[j])[0]
        # primer índex per sobre del mig nivell, venint de dins
        k = None
        for idx in above:
            if rr[idx] > 440: k = idx; break
        if k is None or k == 0: continue
        a, b = prof[j, k-1], prof[j, k]
        if b == a: rad[j] = rr[k]
        else: rad[j] = rr[k-1] + (half[j]-a)/(b-a)*0.25
    return az, rad, ins, outs
def fit(az, rad, c0, sel=None):
    ok = np.isfinite(rad) if sel is None else (sel & np.isfinite(rad))
    px = c0[0] + rad[ok]*np.cos(az[ok]); py = c0[1] - rad[ok]*np.sin(az[ok]); azk = az[ok]
    keep = np.ones(len(px), bool)
    for it in range(30):
        A = np.c_[2*px[keep], 2*py[keep], np.ones(keep.sum())]; b = px[keep]**2+py[keep]**2
        a_, b_, c_ = np.linalg.lstsq(A, b, rcond=None)[0]; R = np.sqrt(c_+a_**2+b_**2)
        res = np.hypot(px-a_, py-b_)-R; s = 1.4826*np.median(np.abs(res[keep]))
        nk = np.abs(res) < 3.0*max(s, 0.25)
        if (nk == keep).all(): break
        keep = nk
    sect = {}
    for s0 in range(0, 360, 30):
        m = keep & (np.degrees(azk) >= s0) & (np.degrees(azk) < s0+30)
        sect[s0] = round(float(np.median(res[m])), 2) if m.any() else None
    return dict(cx=float(a_), cy=float(b_), R=float(R), rms=float(res[keep].std()), n=int(keep.sum()), n_tot=int(ok.sum()), sector_res=sect)
if __name__ == '__main__':
    ids = [int(a) for a in sys.argv[1:]] or [7, 8, 9, 10]
    out = {}
    for i in ids:
        G = np.load(f'{V2B}/src_id{i}_G.npy', mmap_mode='r')
        c = (3577.5, 2273.5)
        for it in range(4):
            az, rad, ins, outs = halfedges(G, c)
            r = fit(az, rad, c); c = (r['cx'], r['cy'])
        out[i] = r
        print(i, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items() if k != 'sector_res'}); print('   sectors', r['sector_res'], flush=True)
    json.dump(out, open('lluna2.json', 'w'), indent=1)
