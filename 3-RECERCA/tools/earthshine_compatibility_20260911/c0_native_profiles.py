# Derived diagnostic only; parent SHA256 7f66d0d66e2a8f52577f9f20c8281c13a200991bfb977660ab5e4b9c391340ef
"""Measure exposure-dependent edge response after coronal registration.
Forward profile fit only. No deconvolution, halo subtraction or PSB output.
Fit widths on non-top sectors, reserve top sector as an external spatial test.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from b1_native import *
from scipy.optimize import least_squares
from scipy.special import ndtr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=ROOT/'output/earthshine_compatibility_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_COMPATIBILITY_20260911'
shifts=json.loads((OUT/'B1_relative_geometry.json').read_text())['source_shifts']
theta=np.arange(0,360,.25);dist=np.arange(-40,41,.25);edge=np.load(CAU44/'vixen_optical_edge.npy')
rad=np.interp(theta*4,np.arange(len(edge)),edge)
rr=rad[None]+dist[:,None];ang=np.deg2rad(theta)[None]
xx=(X0+CXT+rr*np.cos(ang)).astype(np.float32);yy=(Y0+CYT+rr*np.sin(ang)).astype(np.float32)
ctx=f2.Ctx(comu.Run.obre(str(RUNS['vixen'])));pos=json.loads((RUNS['vixen']/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((RUNS['vixen']/'4-rebuts/F2.2_coherencia.json').read_text())['k']
meta=json.loads((CAU36/'vixen_meta.json').read_text())['frames'];phis=np.load(CAU36/'vixen_G_phi.npy',mmap_mode='r');fcorr,frep=B.flat_ripple_correction(ctx,'vixen');inv=cv2.invertAffineTransform(COMMON_TO_FINAL)
qmx=inv[0,0]*MC[0]+inv[0,1]*MC[1]+inv[0,2];qmy=inv[1,0]*MC[0]+inv[1,1]*MC[1]+inv[1,2];dmx=(qmx-ctx.CX)*ctx.k;dmy=(qmy-ctx.CY)*ctx.k
observed={};valids={};native={};fields={}
for n in sorted(map(int,shifts)):
    nom=f'572A{n}.CR3';v=pos[nom];j=next(j for j,m in enumerate(meta) if m['name']==nom);m=meta[j];sx,sy=shifts[str(n)];xm=xx-sx;ym=yy-sy
    qx=inv[0,0]*xm+inv[0,1]*ym+inv[0,2];qy=inv[1,0]*xm+inv[1,1]*ym+inv[1,2];dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
    rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']+v['lluna_dx']-(ctx.ca*dmx+ctx.sa*dmy)).astype(np.float32)
    ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']+v['lluna_dy']-(-ctx.sa*dmx+ctx.ca*dmy)).astype(np.float32)
    with rawpy.imread(ctx.ruta[nom]) as rf:raw=rf.raw_image.astype(np.float32)
    dark=ctx.dark(v['exp']);phi_full=B.upsample(phis[j]);field=np.exp(-cv2.remap(phi_full,xm,ym,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE));del phi_full
    total=np.zeros_like(xx);total_native=total.copy();valid=np.ones_like(xx,dtype=bool)
    for i in range(4):
        if comu.IDX_CANAL[i]!=1:continue
        oy,ox=ctx.orig[i];rp=raw[oy::2,ox::2];pl=comu.calibra_pla(rp,dark[oy::2,ox::2],ctx.flat[oy::2,ox::2],v['exp'],ctx.wb,ctx.mc,i)
        if fcorr is not None:pl*=fcorr[i]
        mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32);ix=np.floor(mx).astype(int);iy=np.floor(my).astype(int)
        rn=(rp-ctx.cfg['pedestal_dn'])/(ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn'])
        valid&=np.maximum.reduce([rn[iy,ix],rn[iy+1,ix],rn[iy,ix+1],rn[iy+1,ix+1]])<.85
        total_native+=cv2.remap(pl*kq.get(nom,1),mx,my,cv2.INTER_LINEAR)/2
        total+=(cv2.remap(pl*kq.get(nom,1),mx,my,cv2.INTER_LINEAR)+m['offset_RGB'][1])*field/2
    observed[n]=total;valids[n]=valid;native[n]=total_native;fields[n]=field;print('profile',n,flush=True)
np.savez_compressed(OUT/'C0_native_profiles.npz',theta=theta,distance=dist,**{f'g{n}':g for n,g in observed.items()},**{f'valid{n}':v for n,v in valids.items()},**{f'native{n}':v for n,v in native.items()},**{f'field{n}':v for n,v in fields.items()})

