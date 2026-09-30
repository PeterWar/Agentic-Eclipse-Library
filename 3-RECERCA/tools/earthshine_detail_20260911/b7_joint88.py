"""Joint88 source compositor, fixed equal share of two existing temporal estimators.

Both optical trains contribute; validate Vixen versus Sony components before mixing.
The all-epoch estimator corroborates the upper coarse texture; low-glare V45
selection retains right-hand fine texture. Combine their NORMALISED source
weights equally, then use exactly the fixed C5 source-gradient compositor.
No marked-region mask, spatial retouch, external texture or geometry change.
This is a new model to validate, not a claim of optimal or recovered radiance.
"""
from detail_common import *
import sys
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from f2_temporal import ng,component,ALPHA,epoch,GAIN
from scipy.fft import dctn,idctn
meta=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'];frames=meta
epmeta=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F2_temporal.json').read_text());keys=epmeta['groups']['combined']['keys'];pref=np.load(CAU45/'combined_epoch_preference.npy')
newnames=[m['stem'] for m in frames]
assert all((OUT/'native'/(m['tren']+'_'+m['stem']+'.json')).exists() for m in frames)
cache=OUT/'joint88_cache';cache.mkdir(exist_ok=False)
GG=np.lib.format.open_memmap(cache/'G.npy',mode='w+',dtype=np.float32,shape=(len(frames),N,N));WW=np.lib.format.open_memmap(cache/'W.npy',mode='w+',dtype=np.float32,shape=GG.shape)
da=np.zeros((N,N));dp=da.copy();na=da.copy();npref=da.copy();rows=[]
for i,m in enumerate(frames):
    z=np.load(OUT/'native'/(m['tren']+'_'+m['stem']+'.npz'));g,q,v=[z[k].astype(float) for k in ['g','q','variance']];gain=GAIN[m['grup']];g*=gain;v*=gain**2
    valid=np.isfinite(g)&np.isfinite(v)&(q>0)&(v>0);vs,_=ng(v,valid,4);w=np.where(valid,q/np.maximum(vs*ALPHA[component(m)],1e-12),0).astype(np.float32);g=np.nan_to_num(g).astype(np.float32)
    
    if m['grup']=='sony_B':
        yy,xx=np.mgrid[:N,:N];dd=np.hypot(xx+4677-5367,yy+3077-3545);tt=np.clip((dd-140)/40,0,1);w*=tt*tt*(3-2*tt)
    pi=keys.index(epoch(m));p=pref[pi];wp=w.astype(float)*p;GG[i]=g;WW[i]=w;da+=w;dp+=wp;na+=w.astype(float)*g;npref+=wp*g;rows.append(dict(stem=m['stem'],epoch=epoch(m),preference_index=pi))
    if i%15==0:print('cache',i,flush=True)
GG.flush();WW.flush();assert np.all(da>0)&np.all(dp>0)
base_all=na/da;base_pref=npref/dp;base=.5*(base_all+base_pref)
gy=np.zeros((N-1,N));wy=gy.copy();gx=np.zeros((N,N-1));wx=gx.copy()
for i,m in enumerate(rows):
    g=GG[i].astype(float);w=WW[i].astype(float);wm=.5*w/da+.5*w*pref[m['preference_index']]/dp;u=np.arcsinh(g/20.)
    for axis,G,W in [(0,gy,wy),(1,gx,wx)]:
        a=[slice(None)]*2;b=a.copy();a[axis]=slice(None,-1);b[axis]=slice(1,None);a=tuple(a);b=tuple(b);we=2*wm[a]*wm[b]/np.maximum(wm[a]+wm[b],1e-30);G+=we*(u[b]-u[a]);W+=we
assert np.all(wy>0)&np.all(wx>0);gy/=wy;gx/=wx;rhs=np.zeros((N,N));rhs[:-1]-=gy;rhs[1:]+=gy;rhs[:,:-1]-=gx;rhs[:,1:]+=gx
lap=(2-2*np.cos(np.pi*np.arange(N)/N))[:,None]+(2-2*np.cos(np.pi*np.arange(N)/N))[None,:];a=1/8**2;ub=np.arcsinh(base/20.)
ug=idctn(dctn(rhs+a*ub,type=2,norm='ortho')/(lap+a),type=2,norm='ortho')
freq=np.hypot((np.arange(N)/(2*N))[:,None],(np.arange(N)/(2*N))[None,:]);t=np.clip((freq-1/16)/(1/8-1/16),0,1);H=.5-.5*np.cos(np.pi*t)
uc=ub+idctn(dctn(ug-ub,type=2,norm='ortho')*H,type=2,norm='ortho');candidate=20*np.sinh(uc)
np.savez_compressed(OUT/'B7_joint88_ensemble.npz',base=base,all=base_all,reference=base_pref,candidate=candidate,gradient_candidate=20*np.sinh(ug),den_all=da,den_preference=dp)
save('B7_joint88_ensemble.json',dict(method=__doc__,source_fraction=dict(all_epochs=.5,low_glare=.5),source_frames=rows,operator=dict(transform='asinh(G/20)',poisson_screen_length=8,frequency_transition=[8,16]),source_geometry='Original V45 including Sony B +8.10 arcmin and star correction; no optical-profile shifts',new_native_frames=newnames,negative_output=int((candidate<=0).sum()),status='CANDIDATE; new validation required. Neither source estimator is independent of the other.'))
print('DONE',flush=True)
