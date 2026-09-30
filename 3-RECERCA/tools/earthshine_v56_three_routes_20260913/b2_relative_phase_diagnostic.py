"""Diagnose whether relative phase, rather than sharpness, limits burst gains.
No geometry changes: fit small per-frame shifts to two disjoint references
excluding that frame; even sectors only. Independent agreement and heldout
prediction required before any corrected-source experiment.
"""
from common import *
from scipy.fft import rfft2,irfft2
claim();meta=json.loads((OUT/'A1_clean_frames.json').read_text())['frames'];ids=[i for i,m in enumerate(meta) if m['exp']>=.5];n=384;x0=y0=508;sl=np.s_[y0:y0+n,x0:x0+n];g=np.load(OUT/'arrays/G_frames.npy',mmap_mode='r');w=np.load(OUT/'arrays/W_frames.npy',mmap_mode='r');gs=np.array([g[i][sl] for i in ids],float);ws=np.array([w[i][sl] for i in ids],float);y,x=np.mgrid[:n,:n];win=np.hanning(n)[:,None]*np.hanning(n)[None,:];sec=((np.arctan2(y+y0-CY,x+x0-CX)%(2*np.pi))//(np.pi/6)).astype(int);fit=(win>.25)&(sec%2==0);hold=(win>.25)&(sec%2==1);Q=np.stack([np.ones_like(x),x/n,y/n],-1);fy=np.fft.fftfreq(n)[:,None];fx=np.fft.rfftfreq(n)[None,:];fr=np.hypot(fx,fy);H=(fr>=1/64)&(fr<=1/16);prec=np.array([np.median(v[fit]) for v in ws]);F=[]
save('B2_protocol.json',dict(method=__doc__,band=[16,64],fit='Linear ref,dx,dy small-phase model to each of two excluding-frame references; six even sectors win>.25',gate='Two estimates differ<=0.25px, individual |shift|<=2px, positive signal coefficient, heldout residual improves in both. Rotated90-degree null must not carry comparable correlation. No new source or product.'))
for a in gs:
 co=np.linalg.lstsq(Q.reshape(-1,3)*win.ravel()[:,None],a.ravel()*win.ravel(),rcond=None)[0];F.append(rfft2((a-Q@co)*win))
F=np.array(F);rows=[]
for i in range(len(ids)):
 obs=irfft2(F[i]*H,s=(n,n));fits=[]
 for parity in [0,1]:
  refids=[j for j in range(len(ids)) if j!=i and j%2==parity];ff=np.average(F[refids],axis=0,weights=prec[refids])*H;ref=irfft2(ff,s=(n,n));gx=irfft2(ff*(2j*np.pi*fx),s=(n,n));gy=irfft2(ff*(2j*np.pi*fy),s=(n,n));xx=np.stack([ref,gx,gy],-1);cf=np.linalg.lstsq(xx[fit],obs[fit],rcond=None)[0];pred=xx@cf;gain=float(cf[0]);shift=cf[1:]/max(gain,1e-30);before=float(np.mean((obs[hold]-gain*ref[hold])**2));after=float(np.mean((obs[hold]-pred[hold])**2));fits.append(dict(parity=parity,gain=gain,shift=shift,before=before,after=after,holdout_r=corr(obs,ref,hold),rotated_null_r=corr(obs,np.rot90(ref),hold)))
 diff=float(np.linalg.norm(np.array(fits[0]['shift'])-fits[1]['shift']));passed=diff<=.25 and all(np.linalg.norm(q['shift'])<=2 and q['gain']>0 and q['after']<q['before'] and q['holdout_r']>abs(q['rotated_null_r']) for q in fits);row=dict(stem=meta[ids[i]]['stem'],fits=fits,shift_disagreement=diff,pass_gate=passed);rows.append(row);print('BURST PHASE',row,flush=True)
save('B2_relative_phase.json',dict(rows=rows,status='Diagnostic only, no geometry/source altered. Passing individual frames would still need one anchored graph and separate source/photographic validation.'))
