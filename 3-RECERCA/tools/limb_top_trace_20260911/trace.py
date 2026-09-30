"""Bounded, read-only source trace. Writes new diagnostic outputs only.

Reproduce V45 B1 in the upper sector and compare its saturation-weighted
interpolation with ordinary bilinear interpolation on the SAME valid support.
The alternative is a causal control, not a delivered correction.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'research/tools/v45_earthshine_20260910'))
from b1_native import *
from f2_temporal import ng, ALPHA, component
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = ROOT/'output/limb_top_trace_20260911'
CLAIM = 'CODEX_LIMB_TOP_TRACE_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id'] == CLAIM
OUT.mkdir(exist_ok=True)
(OUT/'vistes').mkdir(exist_ok=True)
ys, xs = slice(215,300), slice(585,815)
path=RUNS['vixen']; ctx=f2.Ctx(comu.Run.obre(str(path)))
pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames']
kq=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k']
meta=json.loads((CAU36/'vixen_meta.json').read_text())['frames']
phis=np.load(CAU36/'vixen_G_phi.npy',mmap_mode='r')
fcorr,frep=B.flat_ripple_correction(ctx,'vixen')
inv=cv2.invertAffineTransform(COMMON_TO_FINAL)
yy,xx=np.mgrid[Y0+ys.start:Y0+ys.stop,X0+xs.start:X0+xs.stop].astype(np.float32)
qx=inv[0,0]*xx+inv[0,1]*yy+inv[0,2]; qy=inv[1,0]*xx+inv[1,1]*yy+inv[1,2]
dx=(qx-ctx.CX)*ctx.k; dy=(qy-ctx.CY)*ctx.k
qmx=inv[0,0]*MC[0]+inv[0,1]*MC[1]+inv[0,2];qmy=inv[1,0]*MC[0]+inv[1,1]*MC[1]+inv[1,2]
dmx=(qmx-ctx.CX)*ctx.k;dmy=(qmy-ctx.CY)*ctx.k
rows=[];arrays={}
without_fine_shift='--without-fine-shift' in sys.argv
inputs=json.loads((REB45/'B1_inputs.json').read_text())['frames']
for n in [2976,2977,2978]:
    nom=f'572A{n}.CR3'; v=pos[nom]; j=next(i for i,m in enumerate(meta) if m['name']==nom);m=meta[j]
    sx,sy=next(mm for mm in inputs if mm['stem']==f'572A{n}')['native']['shift']
    if without_fine_shift:sx,sy=0.,0.
    xmap=xx-sx;ymap=yy-sy
    qx=inv[0,0]*xmap+inv[0,1]*ymap+inv[0,2];qy=inv[1,0]*xmap+inv[1,1]*ymap+inv[1,2]
    dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
    offx=v['lluna_dx']-(ctx.ca*dmx+ctx.sa*dmy);offy=v['lluna_dy']-(-ctx.sa*dmx+ctx.ca*dmy)
    rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']+offx).astype(np.float32)
    ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']+offy).astype(np.float32)
    disc=np.clip(((ctx.RL+40*ctx.k)-np.hypot(rx-v['sol_x']-v['lluna_dx'],ry-v['sol_y']-v['lluna_dy']))/(3*ctx.k),0,1)
    with rawpy.imread(ctx.ruta[nom]) as r:raw=r.raw_image.astype(np.float32)
    dark=ctx.dark(v['exp'])
    phi_full=B.upsample(phis[j]); field=np.exp(-cv2.remap(phi_full,xmap,ymap,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE));del phi_full
    num=np.zeros_like(xx);den=num.copy();plain_num=num.copy();plain_den=num.copy();planes=[]
    for i in range(4):
        if comu.IDX_CANAL[i]!=1:continue
        oy,ox=ctx.orig[i];rp=raw[oy::2,ox::2]
        pl=comu.calibra_pla(rp,dark[oy::2,ox::2],ctx.flat[oy::2,ox::2],v['exp'],ctx.wb,ctx.mc,i)
        if fcorr is not None:pl*=fcorr[i]
        mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32)
        span=ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn']; rn=(rp-ctx.cfg['pedestal_dn'])/span
        u=np.clip((rn-.35)/.50,0,1);w=(v['exp']*(1-u*u*(3-2*u))*ctx.valid[oy::2,ox::2]).astype(np.float32)
        ix=np.floor(mx).astype(int);iy=np.floor(my).astype(int)
        maximum=np.maximum.reduce([rn[iy,ix],rn[iy+1,ix],rn[iy,ix+1],rn[iy+1,ix+1]])
        strict=maximum<.85
        dd=cv2.remap(w,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*disc*strict
        nn=cv2.remap(pl*w*kq.get(nom,1),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*disc*strict
        nn=(nn+m['offset_RGB'][1]*dd)*field
        plain=(cv2.remap(pl*kq.get(nom,1),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)+m['offset_RGB'][1])*field
        num+=nn;den+=dd;plain_num+=plain*dd;plain_den+=dd
        planes.append(dict(i=i,green_origin=[int(oy),int(ox)],mx_range=[float(mx.min()),float(mx.max())],my_range=[float(my.min()),float(my.max())]))
        arrays[f'{n}_g{i}_max_raw_fraction']=maximum
        arrays[f'{n}_g{i}_plain']=plain
        arrays[f'{n}_g{i}_strict']=strict
        arrays[f'{n}_g{i}_mapped_raw_fraction']=cv2.remap(rn,mx,my,cv2.INTER_LINEAR)
        x1,x2=int(ix.min()),int(ix.max()+2);y1,y2=int(iy.min()),int(iy.max()+2)
        arrays[f'{n}_g{i}_raw_patch']=rp[y1:y2,x1:x2]
        planes[-1]['raw_patch_cfa_bbox']=[x1,y1,x2,y2]
    g=np.where(den>0,num/np.maximum(den,1e-30),np.nan)
    plain=np.where(den>0,plain_num/np.maximum(plain_den,1e-30),np.nan)
    old=np.load(CAU45/f'native_vixen_572A{n}.npz')
    cached=old['g'][ys,xs];q=den/(2*v['exp'])
    valid=np.isfinite(g)&np.isfinite(cached)
    inner=(R[ys,xs]>440)&(R[ys,xs]<454)&valid
    arrays[f'{n}_g']=g;arrays[f'{n}_plain_same_support']=plain;arrays[f'{n}_q']=q
    rows.append(dict(frame=nom,exposure=v['exp'],raw_path=str(ctx.ruta[nom]),raw_sha256=sha(Path(ctx.ruta[nom])),planes=planes,
      cache_max_abs=float(np.max(abs(g[valid]-cached[valid]))),cache_relative_max=float(np.max(abs(g[valid]-cached[valid])/np.maximum(abs(cached[valid]),1))),
      support_exact=bool(np.array_equal(np.isfinite(g),np.isfinite(cached))),q_max_abs=float(np.max(abs(q-old['q'][ys,xs]))),
      plain_to_weighted_difference_median=float(np.median((plain-g)[inner])),plain_to_weighted_difference_p95=float(np.percentile(abs((plain-g)[inner]),95)),
      geometry=dict(fine_shift=[sx,sy],sensor_arcsec_to_canvas_ratio=float(ctx.k),sol_xy=[v['sol_x'],v['sol_y']],lluna_xy=[v['lluna_dx'],v['lluna_dy']]),disc_min=float(disc.min())))
    print(n, rows[-1]['cache_max_abs'], rows[-1]['support_exact'],flush=True)
prefix='A2_control_without_fine_shift' if without_fine_shift else 'B0_raw_trace'
np.savez_compressed(OUT/f'{prefix}_arrays.npz',**arrays)
(OUT/f'{prefix}.json').write_text(json.dumps(dict(sector_local=[xs.start,ys.start,xs.stop,ys.stop],frames=rows,flat_correction=frep,without_fine_shift=without_fine_shift),indent=2))
fig,ax=plt.subplots(2,1,figsize=(11,7),sharex=True,layout='constrained')
for n in [2976,2977,2978]:
    ax[0].plot(np.arange(ys.start,ys.stop),arrays[f'{n}_g'][:,700-xs.start],label=f'{n} V45')
    ax[0].plot(np.arange(ys.start,ys.stop),arrays[f'{n}_plain_same_support'][:,700-xs.start],ls=':',label=f'{n} bilinear, same valid samples')
    ax[1].plot(np.arange(ys.start,ys.stop),arrays[f'{n}_q'][:,700-xs.start],label=str(n))
ref=np.load(CAU45/'combined_reference.npy',mmap_mode='r')
ax[0].plot(np.arange(ys.start,ys.stop),ref[ys,700],color='black',lw=2,label='Final linear reference')
ax[0].set(yscale='log',ylim=(500,150000),ylabel='Calibrated native G per second',title='Upper sector at local x=700: source interpolation control')
ax[0].legend(ncol=2,fontsize=8);ax[1].legend();ax[1].set(xlim=(238,267),xlabel='Local y: exterior → lunar interior',ylabel='Native validity / exposure weight')
for a in ax:a.grid(alpha=.25)
if without_fine_shift:ax[0].set_title('Diagnostic control: fine shift removed; not V45 reproduction')
figure='A2_control_without_fine_shift.png' if without_fine_shift else 'B0_raw_to_registered.png'
fig.savefig(OUT/'vistes'/figure,dpi=150);plt.close(fig)
