#!/usr/bin/env python3
"""FASE 1 · pas 1 — centre de la LLUNA per fotograma, ajustant el limbe.

El que es veu durant la totalitat NO és el limbe del Sol: és el de la Lluna.
Aquí es mesura aquest, i el centre del SOL en sortirà de l'efemèride (pas 2).

Mètode: per 720 azimuts, es camina radialment i es troba on la intensitat
creua el punt mig entre l'interior (disc lunar) i l'exterior (corona),
amb interpolació subpíxel. Després, ajust robust d'una circumferència amb
retall sigma — les muntanyes lunars, les protuberàncies i les perles són
desviacions locals que el retall se'n va.

⛔ Es treballa sobre el subpla G1 (mitja resolució) per velocitat; el resultat
es dona en píxels de la reixa CRUA sencera.
"""

from __future__ import annotations

import glob, json, os, subprocess, sys, time
import numpy as np, rawpy
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

ESCALA = 2.1494813525884373     # ″/px, solució de placa r6_radial (22 estrelles)
PA_NORD = 57.194988546068025    # graus
RSOL_AS = 947.068               # radi solar aparent del dia
R_LLUNA_PX_NOM = 460.0          # research/75 §6, reixa crua
NAZ = 720


def cronologia() -> dict[str, tuple[float, float]]:
    """{fitxer: (exposicio_s, t_relatiu_s a l'INICI de l'exposicio)}"""
    o = subprocess.run(["exiftool","-q","-n","-T","-FileName","-ExposureTime",
                        "-SubSecDateTimeOriginal", comu.VIXEN],
                       capture_output=True,text=True,timeout=900).stdout
    d={}
    for l in o.splitlines():
        p=l.split("\t")
        if len(p)<3 or not p[0].upper().endswith(".CR3"): continue
        hh,mm,ss = p[2][11:13], p[2][14:16], p[2][17:].split("+")[0]
        d[p[0]] = (float(p[1]), int(hh)*3600+int(mm)*60+float(ss))
    return d


_FLAT=None; _DARKS={}
def calibra(nom: str, e: float, g, mc) -> np.ndarray:
    global _FLAT
    if _FLAT is None:
        _FLAT = fits.getdata(os.path.join(comu.F0,"flat","FLAT_RADIAL_R6III.fits")).astype(np.float32)
    if e not in _DARKS:
        fs=glob.glob(os.path.join(comu.F0,"masters_dark","*.fits"))
        p=min(fs,key=lambda q: abs(float(q.split("_E")[1].rstrip("s.fits"))-e))
        _DARKS[e]=fits.getdata(p).astype(np.float32)
    with rawpy.imread(os.path.join(comu.VIXEN,nom)) as r:
        d=r.raw_image.astype(np.float32)
    return (d-_DARKS[e])/_FLAT


def centre_gros(gp: np.ndarray, R: float) -> tuple[float,float]:
    """Centre aproximat pel CENTROIDE DE L'ANELL BRILLANT de corona interior.

    ⛔ No es busca la zona més fosca: mesurat el 26-08, a 2 s l'interior del
    disc lunar val ~1.030 DN i el cel dels cantons ~880, o sigui que la Lluna
    NO és el mínim de la imatge i el detector de mínims troba els cantons.
    El que sí que és inconfusible és l'anell de corona interior, que envolta
    el disc i és el més brillant del camp.
    """
    import scipy.ndimage as ndi
    s = ndi.uniform_filter(gp, 9)
    llind = np.percentile(s, 99.0)
    m = s >= llind
    if m.sum() < 500:
        return gp.shape[0]/2, gp.shape[1]/2
    w = np.where(m, s - llind, 0.0)
    yy, xx = np.mgrid[0:gp.shape[0], 0:gp.shape[1]]
    tot = w.sum()
    return float((w*yy).sum()/tot), float((w*xx).sum()/tot)


def punts_limbe(gp, cy, cx, R):
    az = np.linspace(0, 2*np.pi, NAZ, endpoint=False)
    rs = np.arange(R-0.13*R, R+0.13*R, 0.25)
    ys = cy + rs[None,:]*np.cos(az)[:,None]
    xs = cx + rs[None,:]*np.sin(az)[:,None]
    ok = (ys>1)&(ys<gp.shape[0]-2)&(xs>1)&(xs<gp.shape[1]-2)
    yi=np.clip(ys,0,gp.shape[0]-1).astype(np.int32); xi=np.clip(xs,0,gp.shape[1]-1).astype(np.int32)
    prof = np.where(ok, gp[yi,xi], np.nan)
    dins  = np.nanmedian(prof[:, :int(0.25*len(rs))], axis=1)
    fora  = np.nanmedian(prof[:, -int(0.25*len(rs)):], axis=1)
    llind = 0.5*(dins+fora)
    pts=[]
    for k in range(NAZ):
        p=prof[k]
        if not np.isfinite(llind[k]) or fora[k]-dins[k] < 3: continue
        idx=np.where(p>=llind[k])[0]
        if idx.size==0 or idx[0]==0: continue
        j=idx[0]
        if not (np.isfinite(p[j-1]) and np.isfinite(p[j])) or p[j]==p[j-1]: continue
        f=(llind[k]-p[j-1])/(p[j]-p[j-1])
        pts.append((rs[j-1]+f*0.25, az[k]))
    return np.array(pts) if pts else np.zeros((0,2))


def ajusta_cercle(pts, cy, cx):
    """pts = (r, az) al voltant de (cy,cx). Ajust robust de centre i radi."""
    r, a = pts[:,0], pts[:,1]
    y = cy + r*np.cos(a); x = cx + r*np.sin(a)
    for _ in range(6):
        A = np.c_[x, y, np.ones_like(x)]
        b = x**2 + y**2
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        Cx, Cy = sol[0]/2, sol[1]/2
        R = np.sqrt(sol[2] + Cx**2 + Cy**2)
        d = np.hypot(x-Cx, y-Cy) - R
        s = 1.4826*np.median(np.abs(d-np.median(d)))
        bo = np.abs(d-np.median(d)) < 2.5*max(s,0.05)
        if bo.sum() < 60: break
        x, y = x[bo], y[bo]
    return float(Cy), float(Cx), float(R), int(len(x)), float(np.std(np.hypot(x-Cx,y-Cy)-R))


def main():
    t0=time.time()
    with rawpy.imread(comu.llista(comu.VIXEN,".CR3")[0]) as r:
        g=comu.geometria(r); mc=comu.mapa_colors(r)
    # subgraella G1: files/cols on mc==1
    fy = np.where((mc[:,0]==1)|(mc[:,1]==1))[0]
    sub_y = np.where(mc[:, np.where(mc[0]==1)[0][0]]==1)[0] if False else None
    yy = np.where(mc[:,:2].max(axis=1)==1)[0]
    cronos = cronologia()
    noms = sorted(cronos)
    t_ini = min(v[1] for v in cronos.values())

    res={}
    print(f"{'fitxer':>13} {'exp':>10} {'t':>7} | {'cy':>9} {'cx':>9} {'R px':>8} {'n':>4} {'rms':>6}")
    for k,n in enumerate(noms,1):
        e,t = cronos[n]
        d = calibra(n,e,g,mc)
        # subpla G1 sencer (inclou marges: no es retalla res)
        y0 = int(np.where(mc[:,0]==1)[0][0]) if (mc[:,0]==1).any() else 0
        x0 = int(np.where(mc[y0]==1)[0][0])
        gp = d[y0::2, x0::2]
        R2 = R_LLUNA_PX_NOM/2
        cy,cx = centre_gros(gp, R2)
        pts = punts_limbe(gp, cy, cx, R2)
        if len(pts) >= 80:
            Cy0, Cx0, R0, _, _ = ajusta_cercle(pts, cy, cx)
            pts = punts_limbe(gp, Cy0, Cx0, R0)
            cy, cx = Cy0, Cx0
        if len(pts) < 80:
            res[n]={"exp":e,"t":t-t_ini,"ok":False,"n_punts":int(len(pts))}
            print(f"{n:>13} {e:>10.6g} {t-t_ini:7.2f} |   -- pocs punts de limbe ({len(pts)})")
            continue
        Cy,Cx,R,nn,rms = ajusta_cercle(pts, cy, cx)
        # a la reixa CRUA: el subpla G1 comença a (y0,x0) i té pas 2
        res[n]={"exp":e,"t":t-t_ini,"ok":True,
                "lluna_cy": y0+2*Cy, "lluna_cx": x0+2*Cx, "R_px": 2*R,
                "n_punts":nn, "rms_px": 2*rms}
        if k%10==0 or k<4:
            print(f"{n:>13} {e:>10.6g} {t-t_ini:7.2f} | {y0+2*Cy:9.2f} {x0+2*Cx:9.2f} "
                  f"{2*R:8.2f} {nn:4d} {2*rms:6.2f}   [{time.time()-t0:.0f}s]", flush=True)
    json.dump({"escala_arcsec_px":ESCALA,"pa_north_deg":PA_NORD,"rsol_arcsec":RSOL_AS,
               "convencio_temps":"EXIF SubSecDateTimeOriginal = INICI de l exposicio "
                                 "(determinat: amb final, els fotogrames d 1 s i 2 s se solapen)",
               "fotogrames":res},
              open(os.path.join(comu.REBUTS,"F1_limbe.json"),"w"), indent=1)
    ok=[v for v in res.values() if v.get("ok")]
    print(f"\n{len(ok)}/{len(res)} amb limbe. R mediana={np.median([v['R_px'] for v in ok]):.2f} px "
          f"rms mediana={np.median([v['rms_px'] for v in ok]):.3f} px   ({time.time()-t0:.0f}s)")
    return 0

if __name__=="__main__": raise SystemExit(main())
