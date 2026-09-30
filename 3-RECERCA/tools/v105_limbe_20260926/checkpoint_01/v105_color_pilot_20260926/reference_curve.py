"""Measure the photographic reference's global tone slopes, independently of
the V104 base, and expose the highlight-headroom cost of constant level matching.
Fit only dreal25..100. No spatial residual transfer or local texture synthesis.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from color_pilot import make_panel,stats

OUT=Path('/private/tmp/v105_color_pilot_20260926');SRC=Path('/private/tmp/v105_base_sources_20260926')
ref=np.load(SRC/'current303_registered_to_E2975.npz');src=np.load(SRC/'572A2975.npz')
b=np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L3.npz')
B=np.stack([b[f'c{c}'] for c in range(3)],-1)[77:1477,77:1477]/65535
R=ref['RGB'];G=src['E'][...,1];d=src['dreal']
valid=src['valid_rgb']&ref['support']&np.isfinite(G)&(G>0)&np.all(np.isfinite(R)&(R>0)&(R<.98),-1)
fit=valid&(d>=25)&(d<100)
yy,xx=np.mgrid[3077:4477,4677:6077]
pa=np.degrees(np.arctan2(-(yy-3775.747534140857),xx-5361.768111973117))%360
train=fit&((pa//30).astype(int)%2==0);test=fit&~train
xref=float(np.median(np.log(G[fit])))
xs=np.log(np.maximum(G,1e-30))-xref
iy,ix=np.nonzero(train);take=np.arange(0,len(iy),max(1,len(iy)//20000));y,x=iy[take],ix[take]
X=np.stack([np.ones(len(x)),xs[y,x]],-1)
init=np.linalg.lstsq(X,R[y,x],rcond=None)[0].T
def residual(p):return (p.reshape(3,2)[:,0]+xs[y,x,None]*p.reshape(3,2)[:,1]-R[y,x]).ravel()
opt=least_squares(residual,init.ravel(),bounds=([-1,.001]*3,[2,1.5]*3),loss='soft_l1',f_scale=.015,max_nfev=100)
coeff=opt.x.reshape(3,2)
fitphoto=coeff[:,0]+xs[...,None]*coeff[:,1]
shift=np.median((B-fitphoto)[fit],axis=0)
report={'fit_domain':'E2975 dreal25..100, positive all RGB, reference RGB 0..0.98; alternating30deg train/holdout.',
 'model':'RGB_c = a_c + b_c * (ln G_E - lnGref). Global photographic tone only; no transferred spatial residual.',
 'lnGref':xref,'coeff_a_b':coeff.tolist(),'constant_RGB_shift_to_old_base':shift.tolist(),
 'heldout_error':stats(fitphoto-R,test),'training_error':stats(fitphoto-R,train),
 'limits':['Per-channel global photographic response inferred from reference, not scientific calibration.',
 'Affine-log approximation, not the exact historical Camera Raw curve.',
 'No output-channel clipping. Unrepresentable output is ineligible, not reconstructed or filled.',
 'No native Photoshop adjustment validation.'], 'sources':{}}
coords={'top':(650,860,210,295),'upper_left':(310,520,275,360),'left':(210,330,600,750)}
for name in ['572A2969','572A2975']:
 q=np.load(SRC/f'{name}.npz');gg=q['E'][...,1]
 observed=q['valid_rgb']&np.isfinite(gg)&(gg>0)&(q['dreal']>=0)&(q['d_presentation_circle']>=0)
 photo=coeff[:,0]+(np.log(np.maximum(gg,1e-30))-xref)[...,None]*coeff[:,1]
 shifted=photo+shift
 r={'bands':{}}
 for lo,hi in [(0,3),(3,10),(10,25),(25,100)]:
  z=observed&(q['dreal']>=lo)&(q['dreal']<hi)
  r['bands'][f'{lo}-{hi}']={'n':int(z.sum()),'reference_curve_RGB':stats(photo,z),
   'shifted_RGB':stats(shifted,z),'shifted_R_above1_fraction':float(np.mean(shifted[...,0][z]>1)),
   'unshifted_all_RGB_representable_fraction':float(np.mean(np.all((photo[z]>=0)&(photo[z]<=1),-1)))}
 for variant,rgb in [('reference_curve',photo),('reference_curve_shifted_NEGATIVE',shifted)]:
  mask=observed&np.all(np.isfinite(rgb)&(rgb>=0)&(rgb<=1),-1)
  np.savez_compressed(OUT/f'{name}_{variant}_ready.npz',RGB=np.where(mask[...,None],rgb,0).astype(np.float32),
    maskwhereupdate=mask,valid_source=observed,box=q['box'],dreal=q['dreal'],d_presentation_circle=q['d_presentation_circle'],
    coeff_a_b=coeff,lnGref=np.asarray(xref),constant_shift=shift if 'shifted' in variant else np.zeros(3))
 for region,(xa,xb,ya,yb) in coords.items():
  sl=np.s_[ya:yb,xa:xb]
  common=np.load(OUT/f'{name}_fixed_slope022_ready.npz')
  photomask=observed&np.all((photo>=0)&(photo<=1),-1)
  shiftmask=observed&np.all((shifted>=0)&(shifted<=1),-1)
  make_panel([('Old base L3',B[sl],np.ones(observed[sl].shape,bool)),
   ('Common shoulder .75-.90',common['RGB'][sl],common['maskwhereupdate'][sl]),
   ('Reference global curve, original level',photo[sl],photomask[sl]),
   ('Constant level shift: absent if >1',shifted[sl],shiftmask[sl])],
   OUT/f'{name}_{region}_REFERENCE_CURVE.png',f'{name}: observed global photo curve; no local residual or contrast tuning',zoom=True)
 report['sources'][name]=r
(OUT/'REFERENCE_CURVE.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'slopes':coeff[:,1].tolist(),'shift':shift.tolist(),'heldout':report['heldout_error'],
 'rim':{s:v['bands']['0-3'] for s,v in report['sources'].items()}},indent=2))
