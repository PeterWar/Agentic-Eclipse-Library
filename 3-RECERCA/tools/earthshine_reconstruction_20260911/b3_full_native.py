"""Full1400 source rectangle, six RAW; physical bad-pixel validity added, single CFA remap, candidate lunar registration. No final crop or output PSB."""
"""Derived geometry pilot from compatibility/d0; lunar residual correction on2977/2978, no radius change."""
"""Derived pilot: geometry changes sourced from C0_early_geometry.json; diagnostic only.
Parent script SHA256 be875b86128a33d4559a0d8f591be81895cd8cefbc85701ce70b3691f52c8d1e
"""
"""Upper-sector source-weight pilot, never a PSB edit or a delivered correction.

Radiance: ordinary bilinear interpolation of four unsaturated CFA samples.
Confidence: existing exposure quality times a continuous distance to the
invalid interpolation footprint, over one CFA cell (2 sensor pixels).
This changes weights, never blurs image values or admits saturated samples.
The no-fine-shift arm is a diagnostic control, not a registration solution.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from b1_native import *
from f2_temporal import ng, ALPHA, component, epoch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
OUT=ROOT/'output/earthshine_reconstruction_20260911/full_epoch2'
OUT.mkdir(exist_ok=True)
(OUT/'vistes').mkdir(exist_ok=True)
SOLAR_SHIFTS=json.loads((OUT.parent/'B1_candidate_shifts.json').read_text())['source_shifts']
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_RECONSTRUCTION_20260911'
ys,xs=slice(0,1400),slice(0,1400)
cy,cx=slice(240,267),slice(620,780)
path=RUNS['vixen'];ctx=f2.Ctx(comu.Run.obre(str(path)))
pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames']
kq=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k']
meta=json.loads((CAU36/'vixen_meta.json').read_text())['frames']
fr=json.loads((REB45/'B1_inputs.json').read_text())['frames'];fr=[m for m in fr if epoch(m)=='vixen_2']
phis=np.load(CAU36/'vixen_G_phi.npy',mmap_mode='r');fcorr,frep=B.flat_ripple_correction(ctx,'vixen')
inv=cv2.invertAffineTransform(COMMON_TO_FINAL)
yy,xx=np.mgrid[Y0+ys.start:Y0+ys.stop,X0+xs.start:X0+xs.stop].astype(np.float32)
qmx=inv[0,0]*MC[0]+inv[0,1]*MC[1]+inv[0,2];qmy=inv[1,0]*MC[0]+inv[1,1]*MC[1]+inv[1,2]
dmx=(qmx-ctx.CX)*ctx.k;dmy=(qmy-ctx.CY)*ctx.k
rows=[];arrays={};data={'source_confidence':{}}
for m in fr:
    n=int(m['stem'][-4:]);nom=m['stem']+'.CR3';old=np.load(m['native']['file'])
    cached={key:old[key][ys,xs] for key in ['g','q','variance']}
    for arm in data:data[arm][m['stem']]=cached.copy()
    v=pos[nom];j=next(i for i,mm in enumerate(meta) if mm['name']==nom);mm=meta[j]
    with rawpy.imread(ctx.ruta[nom]) as rr:raw=rr.raw_image.astype(np.float32)
    dark=ctx.dark(v['exp']);phi_full=B.upsample(phis[j])
    for arm in ['source_confidence']:
        sx,sy=SOLAR_SHIFTS.get(str(n),[0.,0.]) if arm=='source_confidence' else (0.,0.)
        xm=xx-sx;ym=yy-sy
        qx=inv[0,0]*xm+inv[0,1]*ym+inv[0,2];qy=inv[1,0]*xm+inv[1,1]*ym+inv[1,2]
        dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
        offx=v['lluna_dx']-(ctx.ca*dmx+ctx.sa*dmy);offy=v['lluna_dy']-(-ctx.sa*dmx+ctx.ca*dmy)
        rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']+offx).astype(np.float32);ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']+offy).astype(np.float32)
        field=np.exp(-cv2.remap(phi_full,xm,ym,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE))
        num=np.zeros_like(xx);den=num.copy();vnum=num.copy();plainnum=num.copy();plainden=num.copy();strictany=np.zeros_like(xx,dtype=bool)
        for i in range(4):
            if comu.IDX_CANAL[i]!=1:continue
            oy,ox=ctx.orig[i];rp=raw[oy::2,ox::2];flat=ctx.flat[oy::2,ox::2]
            pl=comu.calibra_pla(rp,dark[oy::2,ox::2],flat,v['exp'],ctx.wb,ctx.mc,i)
            if fcorr is not None:pl*=fcorr[i]
            mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32)
            span=ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn'];rn=(rp-ctx.cfg['pedestal_dn'])/span
            u=np.clip((rn-.35)/.5,0,1);quality=(1-u*u*(3-2*u)).astype(np.float32)
            ix=np.floor(mx).astype(int);iy=np.floor(my).astype(int)
            # Invalid CFA interpolation cells are unions of closed unit squares.
            # Exact distance to nearby invalid squares is continuous in mapping
            # coordinates, unlike a max-of-four mask multiplied at the end.
            bad=(rn>=.85)|(ctx.valid[oy::2,ox::2]<=0)|~np.isfinite(pl)
            invalid=bad[:-1,:-1]|bad[1:,:-1]|bad[:-1,1:]|bad[1:,1:]
            strict=~invalid[iy,ix];strictany|=strict
            dist=np.ones_like(mx,dtype=float)
            for di in range(-2,3):
                for dj in range(-2,3):
                    xi=ix+dj;yi=iy+di;bad=invalid[yi,xi]
                    ddx=np.maximum(np.maximum(xi-mx,mx-xi-1),0);ddy=np.maximum(np.maximum(yi-my,my-yi-1),0)
                    dist=np.minimum(dist,np.where(bad,np.hypot(ddx,ddy),1.))
            taper=dist*dist*(3-2*dist)
            qold=cv2.remap(quality,mx,my,cv2.INTER_LINEAR)*strict
            qnew=qold*taper
            assert not np.any((qnew>0)&~strict)
            g=(cv2.remap(pl*kq.get(nom,1),mx,my,cv2.INTER_LINEAR)+mm['offset_RGB'][1])*field
            rnvar=np.maximum(rp-ctx.cfg['pedestal_dn'],0)/5.08+2*(1.05 if v['exp']>=1 else 2.72)**2
            scale=kq.get(nom,1)/(np.maximum(flat,1e-12)*v['exp'])
            if fcorr is not None:scale*=fcorr[i]
            rnvar*=scale**2
            qx1=np.rint(mx*32)/32;qy1=np.rint(my*32)/32;vx=np.floor(qx1).astype(int);vy=np.floor(qy1).astype(int);fx=qx1-vx;fy=qy1-vy
            var=np.zeros_like(xx,dtype=float)
            for di,dj,b in [(0,0,(1-fy)*(1-fx)),(0,1,(1-fy)*fx),(1,0,fy*(1-fx)),(1,1,fy*fx)]:var+=b*b*rnvar[vy+di,vx+dj]
            var*=field**2
            num+=g*qnew;den+=qnew;vnum+=var*qnew*qnew
            plainnum+=g*qold;plainden+=qold
        candidate=dict(g=np.where(den>0,num/np.maximum(den,1e-30),np.nan),q=den/2,variance=np.where(den>0,vnum/np.maximum(den**2,1e-30),np.nan))
        data[arm][m['stem']]=candidate
        rows.append(dict(frame=nom,arm=arm,shift=[sx,sy],saturated_samples_admitted=0,valid_core=int((candidate['q'][cy,cx]>0).sum())))
    del phi_full
    print(n,flush=True)


for stem,d in data['source_confidence'].items():
    for key,value in d.items():arrays[stem+'_'+key]=value
np.savez_compressed(OUT/'source_arrays.npz',**arrays)
(OUT/'source_inputs.json').write_text(json.dumps(dict(frames=rows,order=[m['stem'] for m in fr],alpha={m['stem']:ALPHA[component(m)] for m in fr}),indent=2))
