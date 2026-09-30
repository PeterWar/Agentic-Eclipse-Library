"""Fixed-scene diagnostic for a missing broad optical response.
Probe additional Gaussian widths4,12,36px as declared basis functions, not
measured PSFs. Fit only the common wing fraction from the8 training exposures.
The latent fields are frozen, so this cannot validate a new reconstruction.
"""
from forward_model import *

meta=json.loads((OPT/'B3_epoch_stationarity.json').read_text())['epochs'];rows=[a for e in meta for a in e['frames']]
report=json.loads((OUT/'B3_joint_epochs.json').read_text())['epochs'][0];z=np.load(OUT/'B3_vixen_2_5_joint.npz')
assert report['fit']['cg_info']==0
M=z['lunar'];C=z['solar'];P=z['occlusion'];Q=1-P;reference=z['solar_reference']
fm=json.loads((SRC/'B1_full_native_ensemble.json').read_text())['source_frames'];GG=np.load(SRC/'compositor_cache/G.npy',mmap_mode='r');WW=np.load(SRC/'compositor_cache/W.npy',mmap_mode='r')
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);domain=r<500
# At least200px separate this diagnostic domain from the fixed input boundary;
# this is>5.5 times the broadest proposed width. No radial image operator.
f=np.arange(N)/(2*N);f2=f[:,None]**2+f[None,:]**2;H=np.exp(-2*np.pi**2*report['forward_sigma']**2*f2)
conv=lambda a,h:idctn(dctn(a,type=2,norm='ortho')*h,type=2,norm='ortho')
pred=[];obs=[];weights=[];train=[]
for row in rows:
    i=next(i for i,m in enumerate(fm) if m['stem']==row['stem']);w=np.array(WW[i],dtype=float)*domain;g=np.array(GG[i],dtype=float)
    t=Warp(*(np.array(row['solar_center_in_lunar_grid'])-reference)[::-1]);p=conv(P*M+Q*t.forward(C),H)
    pred.append(p);obs.append(g);weights.append(w);train.append(row['stem'] in report['train_frames'])
results=[]
for width in [4.,12.,36.]:
    hw=np.exp(-2*np.pi**2*width**2*f2);der=[conv(p,hw)-p for p in pred]
    num=den=pnum=pden=0.
    for p,g,w,h,tr in zip(pred,obs,weights,der,train):
        if not tr:continue
        good=w>0;wv=w[good];pv=p[good];hv=h[good];d=g[good]-pv
        num+=np.sum(wv*hv*d);den+=np.sum(wv*hv*hv)
        # Remove two per-capture calibration nuisance directions only while
        # estimating the common wing coefficient; never fit heldout pixels.
        Z=np.stack([np.ones_like(pv),pv/1000],axis=1);A=Z.T@(wv[:,None]*Z)
        hp=hv-Z@np.linalg.solve(A,Z.T@(wv*hv));dp=d-Z@np.linalg.solve(A,Z.T@(wv*d))
        pnum+=np.sum(wv*hp*dp);pden+=np.sum(wv*hp*hp)
    fits=[]
    for name,eps in [('wing_only',num/den),('after_gain_offset_projection',pnum/pden)]:
        physical=0<=eps<=1;tests=[]
        if physical:
            for row,p,g,w,h,tr in zip(rows,pred,obs,weights,der,train):
                if tr:continue
                regions=[]
                for lo,hi in [(0,350),(350,435),(435,449),(449,454),(454,480)]:
                    good=(w>0)&(r>=lo)&(r<hi)
                    if good.sum()<100:continue
                    old=float(np.mean(w[good]*(p[good]-g[good])**2));new=float(np.mean(w[good]*(p[good]+eps*h[good]-g[good])**2))
                    regions.append(dict(radius=[lo,hi],pixels=int(good.sum()),baseline=old,wing=new,ratio=new/old))
                tests.append(dict(stem=row['stem'],regions=regions))
        fits.append(dict(method=name,unconstrained_fraction=float(eps),fraction_in_physical_range=bool(physical),heldout=tests))
    results.append(dict(additional_sigma=width,wing_direction_energy_retained_after_nuisance=float(pden/den),fits=fits))
    print(width,[(a['method'],a['unconstrained_fraction'],a['fraction_in_physical_range']) for a in fits],flush=True)
save('B5_broad_response_probe.json',dict(method=__doc__,probes=results,training_domain='r<500px in fixed1400 input; only an analysis footprint',status='Diagnostic derivative directions only, no recovered pixels',limits=['Frozen B3 scenes already contain unphysical lunar negatives; these probes do not repair or validate them','No refit of latent Moon/Sun fields, no blind PSF estimation, no unique measured wing width','Gain/offset projection only tests sensitivity of the coefficient to calibration nuisance; heldout frames receive no fitted offsets','Repeated same-telescope scene-fit holdouts, inherited calibration; no final independent recovery claim']))
