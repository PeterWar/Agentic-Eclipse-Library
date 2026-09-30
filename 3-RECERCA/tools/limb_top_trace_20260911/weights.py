"""First-entry audit of Vixen epoch 2; local crop + exact Gaussian padding.

Omitting one frame is only a diagnostic ablation. No image is promoted.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from f2_temporal import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
OUT=ROOT/'output/limb_top_trace_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_LIMB_TOP_TRACE_20260911'
ys,xs=slice(215,300),slice(585,815)
cy,cx=slice(240-ys.start,267-ys.start),slice(620-xs.start,780-xs.start)
fr=json.loads((REB45/'B1_inputs.json').read_text())['frames']
fr=[m for m in fr if epoch(m)=='vixen_2']
gg=[];ww=[]
for m in fr:
    d=np.load(m['native']['file']);g=d['g'][ys,xs];q=d['q'][ys,xs];v=d['variance'][ys,xs]
    ok=np.isfinite(g)&np.isfinite(v)&(v>0)&(q>0);vs,_=ng(v,ok,4)
    w=np.where(ok,q/np.maximum(vs*ALPHA[component(m)],1e-12),0)
    gg.append(g);ww.append(w)
gg=np.array(gg);ww=np.array(ww);ws=ww.sum(0)
mix=np.sum(np.nan_to_num(gg)*ww,0)/np.maximum(ws,1e-30)
k=next(i for i,m in enumerate(fr) if m['stem']=='572A2978')
fraction=ww[k]/np.maximum(ws,1e-30)
keep=np.arange(len(fr))!=k
control=np.sum(np.nan_to_num(gg[keep])*ww[keep],0)/np.maximum(ww[keep].sum(0),1e-30)
ep=np.load(CAU45/'epoch_vixen_2.npz')['g'][ys,xs]
ref=np.load(CAU45/'combined_reference.npy',mmap_mode='r')[ys,xs]
keys=json.loads((REB45/'F2_temporal.json').read_text())['groups']['combined']['keys']
rw=np.load(CAU45/'combined_epoch_ref_weights.npy',mmap_mode='r')[:,ys,xs]
fracep=rw[keys.index('vixen_2')]/np.maximum(rw.sum(0),1e-30)
linecols=np.arange(620,780)-xs.start
sub=ww[k,cy,cx]>0
entry=np.argmax(sub,axis=0)+cy.start
assert np.all(sub.any(0))
refstep=np.argmax(-np.diff(ref[cy,cx],axis=0),axis=0)+cy.start+1
epstep=np.argmax(-np.diff(ep[cy,cx],axis=0),axis=0)+cy.start+1
before=ref[entry-1,linecols];after=ref[entry,linecols]
def quant(a):return dict(median=float(np.median(a)),p05=float(np.percentile(a,5)),p95=float(np.percentile(a,95)))
col=700-xs.start;row=247-ys.start
raw=np.load(OUT/'B0_raw_trace_arrays.npz');no=np.load(OUT/'A2_control_without_fine_shift_arrays.npz')
# Profile offset is not a geometric registration measurement: the halo evolves.
# Fit log-tail translation on all available common, unsaturated samples.
def offset_fit(a,b):
    aa=a[240-ys.start:268-ys.start,cx];bb=b[240-ys.start:268-ys.start,cx]
    yy0,xx0=np.mgrid[:aa.shape[0],:aa.shape[1]]
    base=np.isfinite(bb)&(bb>1600)&(bb<7000)
    def fun(p):
        sh=cv2.remap(aa.astype(np.float32),xx0.astype(np.float32),(yy0+p[0]).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        ok=base&np.isfinite(sh)&(sh>0)
        # Fixed fit population is valid in the short image throughout bounds.
        assert np.all(ok[base])
        return (np.log(sh[base])-np.log(bb[base]))
    # Discrete profile sweep avoids numerical differentiation of OpenCV 1/32 quantization.
    shifts=np.arange(-4,4.001,1/32);loss=np.array([np.mean(fun([s])**2) for s in shifts]);j=int(np.argmin(loss))
    return dict(apparent_tail_shift_px=float(shifts[j]),rms_log=float(np.sqrt(loss[j])),n=int(base.sum()),meaning='profile offset only; not validated physical motion')
report=dict(
 sector_local=[620,240,780,267],epoch='vixen_2',frames=[m['stem'] for m in fr],
 reproduction_max_abs=float(np.max(abs(mix[cy,cx]-ep[cy,cx]))),
 control='omit only 572A2978, retain other frame values and weights; diagnosis only',
 reference_strongest_step_at_2978_entry=dict(count=int(np.sum(refstep==entry)),total=160),
 epoch_strongest_step_at_2978_entry=dict(count=int(np.sum(epstep==entry)),total=160),
 first_entry_fraction_2978_in_epoch=quant(fraction[entry,linecols]),
 first_entry_fraction_epoch2_in_reference=quant(fracep[entry,linecols]),
 first_entry_reference_relative_drop=quant((before-after)/np.maximum(before,1e-30)),
 x700_y247=dict(reference_before=float(ref[row-1,col]),reference_after=float(ref[row,col]),
   epoch_before=float(ep[row-1,col]),epoch_after=float(ep[row,col]),short_control_before=float(control[row-1,col]),short_control_after=float(control[row,col]),
   incoming_native_G=float(gg[k,row,col]),incoming_plain_G=float(raw['2978_plain_same_support'][row,col]),
   incoming_fraction=float(fraction[row,col]),epoch_fraction_in_final=float(fracep[row,col])),
 apparent_profile_fit_actual=offset_fit(raw['2976_g'],raw['2978_plain_same_support']),
 apparent_profile_fit_without_fine_shift=offset_fit(raw['2976_g'],no['2978_plain_same_support']),
 limits=['single upper sector; no full-limb claim','frame omission is not an acceptable final recovery',
 'fine-shift asymmetry is proven; its physical accuracy is not established by fitting an evolving bright halo',
 'matched support bilinear control excludes interpolation bias as sole cause'])
(OUT/'B1_weight_trace.json').write_text(json.dumps(report,indent=2))
np.savez_compressed(OUT/'B1_weight_trace_arrays.npz',epoch=ep,reference=ref,without_2978=control,fraction_2978=fraction,entry=entry+ys.start,refstep=refstep+ys.start,epoch2_fraction=fracep)
print(json.dumps(report,indent=2))

fig,axs=plt.subplots(3,1,figsize=(12,8),layout='constrained')
yy0=np.arange(ys.start,ys.stop)
for a,label in [(ref,'Referència final'),(ep,'Apilat del grup temporal'),(control,'Control: excloure només la presa 2978')]:axs[0].plot(yy0,a[:,col],label=label)
axs[0].set(xlim=(242,257),ylim=(700,150000),yscale='log',ylabel='G lineal per segon',title='La primera costura apareix en combinar les exposicions');axs[0].legend(fontsize=9);axs[0].grid(alpha=.2)
axs[1].plot(np.arange(620,780),entry+ys.start,label='Primera dada vàlida de la presa d’1 s')
axs[1].plot(np.arange(620,780),refstep+ys.start,ls='--',label='Salt màxim de la referència')
axs[1].set(ylabel='Fila del contorn (y)',xlabel='Columna local (x)');axs[1].legend(fontsize=9);axs[1].grid(alpha=.2)
axs[2].plot(yy0,100*fraction[:,col],label='Pes de 2978 dins del grup temporal')
axs[2].plot(yy0,100*fracep[:,col],label='Pes del grup dins de la referència')
axs[2].set(xlim=(242,257),ylim=(-3,103),ylabel='Pes (%)',xlabel='Fila local y, exterior → interior lunar');axs[2].legend(fontsize=9);axs[2].grid(alpha=.2)
fig.savefig(OUT/'vistes/B1_first_seam.png',dpi=150);plt.close(fig)
