#!/usr/bin/env python3
"""FASE 0 · pas 4 (bis) — flat RADIAL amb centre DECLARAT i validació creuada.

⛔ El centre NO s'ajusta. Mesurat el 26-08: amb el centre lliure, el residu
del model radial baixa monotonament cap enfora perquè un cercle molt gran és
un PLA — la cerca fuig i no convergeix. És la degeneració que `research/100`
declara quan diu que l'eix òptic no és mesurable amb flats. El centre adoptat
és el **centre del sensor**, declarat al rebut.

Validació: els **28 flats invertits** (cos girat 173,5°) donen un perfil radial
independent. Si el flat és fix al sensor i radial, els dos han de coincidir.
"""

from __future__ import annotations

import json, os, subprocess, sys, time
import numpy as np, rawpy
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

NB = 260


def exp_de(c):
    o = subprocess.run(["exiftool","-q","-n","-T","-FileName","-ExposureTime",c],
                       capture_output=True,text=True,timeout=900).stdout
    d={}
    for l in o.splitlines():
        p=l.split("\t")
        if len(p)>=2:
            try: d[p[0]]=float(p[1])
            except ValueError: pass
    return d


def dark_proper(e):
    import glob
    fs=glob.glob(os.path.join(comu.F0,"masters_dark","*.fits"))
    return min(fs,key=lambda p: abs(float(p.split("_E")[1].rstrip("s.fits"))-e))


def master(rutes,e,sostre=40):
    if len(rutes)>sostre:
        i=np.linspace(0,len(rutes)-1,sostre).round().astype(int)
        rutes=[rutes[k] for k in sorted(set(i.tolist()))]
    with rawpy.imread(rutes[0]) as r: h,w=r.raw_image.shape
    pila=np.empty((len(rutes),h,w),np.uint16)
    for i,p in enumerate(rutes):
        with rawpy.imread(p) as r: pila[i]=r.raw_image
    med=np.empty((h,w),np.float32)
    for y0 in range(0,h,512):
        y1=min(y0+512,h); med[y0:y1]=np.median(pila[:,y0:y1].astype(np.float32),axis=0)
    del pila
    return med - fits.getdata(dark_proper(e)).astype(np.float32)


def perfil(vals, r, rmax, nb=NB):
    idx=np.clip((r/rmax*nb).astype(np.int32),0,nb-1)
    s=np.bincount(idx,vals,nb); c=np.bincount(idx,None,nb)
    bo=c>300
    p=np.where(bo,s/np.maximum(c,1),np.nan)
    # normalitza al centre (primers calaixos amb dada)
    ref=np.nanmedian(p[:12])
    return p/ref, bo


def main():
    t0=time.time()
    os.makedirs(os.path.join(comu.F0,"flat"),exist_ok=True)
    with rawpy.imread(comu.llista(comu.VIXEN,".CR3")[0]) as r:
        g=comu.geometria(r); mc=comu.mapa_colors(r)
    CY,CX = g.alt/2.0, g.ample/2.0          # CENTRE DECLARAT = centre del sensor
    yy,xx=np.mgrid[0:g.alt,0:g.ample].astype(np.float32)
    rad=np.hypot(yy-CY,xx-CX); RMAX=float(rad[g.visible].max())
    vis=np.zeros((g.alt,g.ample),bool); vis[g.visible]=True

    ex=exp_de(comu.VIXEN_FLATS); gr={}
    for n,e in ex.items():
        if n.upper().endswith(".CR3"): gr.setdefault(e,[]).append(os.path.join(comu.VIXEN_FLATS,n))
    e_ref=max(gr,key=lambda k:len(gr[k]))
    M=master(sorted(gr[e_ref]),e_ref)
    print(f"[{time.time()-t0:4.0f}s] màster flat normal  {e_ref:g}s  n={min(len(gr[e_ref]),40)}",flush=True)

    exi=exp_de(comu.VIXEN_FLATS_INV)
    e_inv=list(exi.values())[0]
    MI=master(sorted(os.path.join(comu.VIXEN_FLATS_INV,n) for n in exi),e_inv)
    print(f"[{time.time()-t0:4.0f}s] màster flat invertit {e_inv:g}s  n={len(exi)}",flush=True)

    flat=np.ones((g.alt,g.ample),np.float32)
    info={"centre_yx":[CY,CX],"centre":"CENTRE DEL SENSOR, declarat (no ajustat)",
          "exp_normal":e_ref,"exp_invertit":e_inv,"rmax_px":RMAX,"canals":{}}
    print(f"\n{'canal':>3} | {'vinyetatge vora':>15} | {'desacord amb els INVERTITS':>26}")
    print("-"*56)
    for i in range(4):
        cn=comu.nom_canal(i,g.desc); sel=vis&(mc==i)
        pn,bo = perfil(M[sel], rad[sel], RMAX)
        pi,boi= perfil(MI[sel],rad[sel], RMAX)
        both=bo&boi&np.isfinite(pn)&np.isfinite(pi)
        amp=float(1-np.nanmin(pn[bo]))
        dif=np.abs(pn[both]-pi[both])
        desac=float(np.nanmedian(dif)/amp*100); desac_max=float(np.nanmax(dif)/amp*100)
        pr=np.where(np.isfinite(pn),pn,np.nanmedian(pn))
        idx=np.clip((rad/RMAX*NB).astype(np.int32),0,NB-1)
        flat[mc==i]=pr[idx][mc==i]
        info["canals"][cn]={"vinyetatge_pct":100*amp,
            "desacord_invertits_mediana_pct":desac,"desacord_invertits_max_pct":desac_max,
            "perfil":np.where(np.isfinite(pn),pn,-1).tolist(),
            "perfil_invertit":np.where(np.isfinite(pi),pi,-1).tolist(),
            "r_px":((np.arange(NB)+0.5)/NB*RMAX).tolist()}
        print(f"{cn:>3} | {100*amp:14.2f}% | mediana {desac:5.2f}%  màx {desac_max:5.2f}%")

    fits.PrimaryHDU(flat).writeto(os.path.join(comu.F0,"flat","FLAT_RADIAL_R6III.fits"),overwrite=True)
    json.dump(info,open(os.path.join(comu.REBUTS,"F0_flat.json"),"w"),indent=1)
    print(f"\nfet en {time.time()-t0:.0f} s")
    return 0

if __name__=="__main__": raise SystemExit(main())
