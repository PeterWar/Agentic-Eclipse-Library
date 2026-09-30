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
OUT=ROOT/'output/limb_top_pilot_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_LIMB_TOP_PILOT_20260911'
ys,xs=slice(215,300),slice(585,815)
cy,cx=slice(25,52),slice(35,195)
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
rows=[];arrays={};data={'original':{},'plain_same_weights':{},'source_confidence':{},'source_confidence_no_fine_control':{}}
for m in fr:
    n=int(m['stem'][-4:]);nom=m['stem']+'.CR3';old=np.load(m['native']['file'])
    cached={key:old[key][ys,xs] for key in ['g','q','variance']}
    for arm in data:data[arm][m['stem']]=cached.copy()
    if n not in [2976,2977,2978]:continue
    v=pos[nom];j=next(i for i,mm in enumerate(meta) if mm['name']==nom);mm=meta[j]
    with rawpy.imread(ctx.ruta[nom]) as rr:raw=rr.raw_image.astype(np.float32)
    dark=ctx.dark(v['exp']);phi_full=B.upsample(phis[j])
    for arm in ['source_confidence','source_confidence_no_fine_control']:
        sx,sy=m['native']['shift'] if arm=='source_confidence' else (0.,0.)
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
            invalid=(rn[:-1,:-1]>=.85)|(rn[1:,:-1]>=.85)|(rn[:-1,1:]>=.85)|(rn[1:,1:]>=.85)
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
            arrays[f'{n}_{arm}_G{i}_confidence']=qnew
            arrays[f'{n}_{arm}_G{i}_distance_CFA']=dist
        candidate=dict(g=np.where(den>0,num/np.maximum(den,1e-30),np.nan),q=den/2,variance=np.where(den>0,vnum/np.maximum(den**2,1e-30),np.nan))
        data[arm][m['stem']]=candidate
        arrays[f'{n}_{arm}_g']=candidate['g'];arrays[f'{n}_{arm}_q']=candidate['q']
        if arm=='source_confidence':
            data['plain_same_weights'][m['stem']]['g']=np.where(plainden>0,plainnum/np.maximum(plainden,1e-30),np.nan)
            assert np.all((candidate['q']<=cached['q']+1e-4)[cy,cx])
        rows.append(dict(frame=nom,arm=arm,shift=[sx,sy],saturated_samples_admitted=0,valid_core=int((candidate['q'][cy,cx]>0).sum())))
    del phi_full
    print(n,flush=True)

results={};weights={}
for arm,dd in data.items():
    num=np.zeros_like(xx,dtype=float);den=num.copy();ww=[]
    for m in fr:
        d=dd[m['stem']];g=d['g'];q=d['q'];v=d['variance'];ok=np.isfinite(g)&np.isfinite(v)&(v>0)&(q>0)
        vs,_=ng(v,ok,4.);w=np.where(ok,q/np.maximum(vs*ALPHA[component(m)],1e-12),0)
        num+=np.nan_to_num(g)*w;den+=w;ww.append(w)
    results[arm]=num/np.maximum(den,1e-30);weights[arm]=np.array(ww)/np.maximum(den,1e-30)
    arrays[arm]=results[arm];arrays[arm+'_frame_fractions']=weights[arm]
original=results['original'];cached=np.load(CAU45/'epoch_vixen_2.npz')['g'][ys,xs]
assert np.max(abs(original[cy,cx]-cached[cy,cx]))<.02
entry=np.load(ROOT/'output/limb_top_trace_20260911/B1_weight_trace_arrays.npz')['entry']-ys.start
cols=np.arange(620,780)-xs.start
def quant(a):return dict(median=float(np.median(a)),p95=float(np.percentile(a,95)))
measures={}
for arm,g in results.items():
    d=-np.diff(np.log(np.maximum(g[cy,cx],1)),axis=0)
    # Compare the entire fixed fringe, not just the former seam location.
    maxstep=d.max(0); j=np.argmax(d,axis=0)
    sub=j.astype(float)
    for c in range(len(j)):
        i=j[c]
        if 0<i<len(d)-1:
            aa,bb,cc=d[i-1:i+2,c];sub[c]+=.5*(aa-cc)/(aa-2*bb+cc)
    measures[arm]=dict(max_fractional_one_pixel_drop=quant(1-np.exp(-maxstep)),
      fractional_drop_at_old_entry=quant(1-g[entry,cols]/g[entry-1,cols]),
      edge_position_highpass_rms=float(np.std(sub-gaussian_filter1d(sub,5))),
      fraction_2978_first_entry=quant(weights[arm][0,entry,cols]),
      # Descriptive only: no inference of recovered lunar texture.
      common_inner_difference_p95=float(np.percentile(abs(g[55:75,cx]-original[55:75,cx]),95)))
report=dict(scope='Upper sector, epoch2 only; no final reference recombination or PSB',source_window_CFA_cells=1.,source_window_sensor_pixels=2.,frames=rows,measures=measures,
   no_fine_arm_status='CONTROL ONLY: unvalidated registration',no_saturated_samples=True,
   method_limit='Confidence taper tests the identified source support discontinuity; evolving halo and uncertain geometry remain. Not a final correction.')
(OUT/'A0_pilot.json').write_text(json.dumps(report,indent=2));np.savez_compressed(OUT/'A0_pilot_arrays.npz',**arrays)
fig,axs=plt.subplots(2,1,figsize=(12,7),layout='constrained')
labels={'original':'V45 original','plain_same_weights':'Interpolació sense biaix, mateixos pesos','source_confidence':'Confiança contínua a la font','source_confidence_no_fine_control':'Control sense registre fi (no validat)'}
for arm,g in results.items():
    axs[0].plot(np.arange(215,300),g[:,115],label=labels[arm]);axs[1].plot(np.arange(215,300),100*weights[arm][0,:,115],label=labels[arm])
axs[0].set(yscale='log',xlim=(243,260),ylim=(700,120000),ylabel='G lineal',title='Pilot al mateix sector: canviar la confiança no resol per si sol el registre');axs[0].legend(fontsize=9)
axs[1].set(xlim=(243,260),ylim=(-3,103),ylabel='Pes de la presa d’1 s (%)',xlabel='Fila local, exterior → interior lunar')
for a in axs:a.grid(alpha=.25)
fig.savefig(OUT/'vistes/A0_pilot_profiles.png',dpi=150);plt.close(fig)
print(json.dumps(measures,indent=2),flush=True)
