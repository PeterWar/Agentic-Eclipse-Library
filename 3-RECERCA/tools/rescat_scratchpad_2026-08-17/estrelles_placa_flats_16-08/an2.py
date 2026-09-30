"""Centre lunar per filtre adaptat centre-vora (FFT) + perfil radial + saturacio."""
import tifffile, numpy as np, sys, os, json
from scipy.signal import fftconvolve

def moon_center(g, R, ds=8):
    gd = g[::ds, ::ds].astype(np.float32)
    gd = np.log1p(np.clip(gd, 0, None))          # comprimeix el rang; la vora es un esglao
    Rd = R/ds
    k = int(np.ceil(Rd + 14)) 
    yy, xx = np.mgrid[-k:k+1, -k:k+1]
    rr = np.hypot(yy, xx)
    ring = (rr >= Rd+1.5) & (rr <= Rd+10)
    disk = (rr <= Rd-10)
    K = np.zeros_like(rr, np.float32)
    K[ring] = 1.0/ring.sum()
    K[disk] = -1.0/disk.sum()
    sc = fftconvolve(gd, K[::-1, ::-1], mode='same')
    # nomes centres plausibles: el disc ha de cabre dins la imatge
    m = np.zeros_like(sc, bool)
    b = int(Rd)+4
    m[b:-b, b:-b] = True
    sc = np.where(m, sc, -1e9)
    iy, ix = np.unravel_index(np.argmax(sc), sc.shape)
    # refinament subpixel parabolic
    def par(v0,v1,v2):
        d = (v0-2*v1+v2)
        return 0.0 if d==0 else 0.5*(v0-v2)/d
    dy = par(sc[iy-1,ix], sc[iy,ix], sc[iy+1,ix]); dx = par(sc[iy,ix-1], sc[iy,ix], sc[iy,ix+1])
    return (ix+dx)*ds, (iy+dy)*ds, float(sc[iy,ix])

def analyse(path, R, ds=4, sat=64000):
    a = tifffile.imread(path)
    H, W, _ = a.shape
    g = a[..., 1].astype(np.float32)
    cx, cy, score = moon_center(g, R)
    gd = g[::ds, ::ds]
    satm = (a[::ds, ::ds] >= sat).any(-1)
    yy, xx = np.mgrid[0:gd.shape[0], 0:gd.shape[1]]
    r = np.hypot(yy*ds-cy, xx*ds-cx)/R
    k = 500//ds
    corners = np.concatenate([gd[:k,:k].ravel(), gd[:k,-k:].ravel(), gd[-k:,:k].ravel(), gd[-k:,-k:].ravel()])
    prof=[]
    for rr0 in np.arange(0.5, 14.001, 0.25):
        sel = (r>=rr0-0.125)&(r<rr0+0.125)
        n=int(sel.sum())
        if n<80: continue
        v=gd[sel]
        prof.append([round(float(rr0),3), float(np.median(v)),
                     float((np.percentile(v,84)-np.percentile(v,16))/2),
                     float(satm[sel].mean()), n])
    rsat = float(np.percentile(r[satm],99.5)) if satm.any() else 0.0
    return dict(file=os.path.basename(path), cx=round(float(cx),1), cy=round(float(cy),1),
                score=round(score,4), H=H, W=W,
                sat_frac=float((a>=sat).any(-1).mean()), r_sat_Rm=round(rsat,2),
                sky_med=float(np.median(corners)), sky_p16=float(np.percentile(corners,16)),
                sky_p84=float(np.percentile(corners,84)),
                inside_moon=float(np.median(gd[r<0.8])), prof=prof)

if __name__=="__main__":
    R=float(sys.argv[1]); out=[]
    for p in sys.argv[2:]:
        try: out.append(analyse(p,R))
        except Exception as e: out.append({"file":os.path.basename(p),"error":repr(e)})
    print(json.dumps(out))
