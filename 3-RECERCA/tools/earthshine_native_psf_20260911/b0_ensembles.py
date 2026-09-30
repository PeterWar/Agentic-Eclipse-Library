"""Frozen V48 compositor, changing only native green interpolation and variance.
Early/late disjoint captures provide conditional temporal checks. Calibration,
geometry and the old temporal preference remain frozen and were jointly fitted.
The historical effective FPN factors are held fixed for an ablation, not refitted.
"""
from native_common import *
import sys
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from f2_temporal import ng,component,ALPHA,epoch
from scipy.fft import dctn,idctn

frames=[m for m in json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'] if m['tren']=='vixen']
inputs={m['stem']:m for m in json.loads((OUT/'A2_all_native.json').read_text())['frames']};assert len(inputs)==len(frames)==67
original=json.loads((SRC/'B1_full_native_ensemble.json').read_text())['source_frames'];assert [m['stem'] for m in frames]==[m['stem'] for m in original]
CAU45=ROOT/'research/tools/v45_earthshine_20260910/cau'
keys=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F2_temporal.json').read_text())['groups']['vixen']['keys'];pref=np.load(CAU45/'vixen_epoch_preference.npy');pi=[keys.index(epoch(m)) for m in frames]
cache=OUT/'compositor_cache';cache.mkdir(exist_ok=False)
GG=np.lib.format.open_memmap(cache/'G.npy',mode='w+',dtype=np.float32,shape=(67,N,N));WW=np.lib.format.open_memmap(cache/'W.npy',mode='w+',dtype=np.float32,shape=GG.shape)
for i,m in enumerate(frames):
    z=np.load(inputs[m['stem']]['output']);g,q,v=[z[k].astype(float) for k in ['g','q','variance']];valid=np.isfinite(g)&np.isfinite(v)&(q>0)&(v>0);vs,_=ng(v,valid,4.)
    GG[i]=np.nan_to_num(g);WW[i]=np.where(valid,q/np.maximum(vs*ALPHA[component(m)],1e-12),0).astype(np.float32)
    if i%16==0:print('CACHE',i,flush=True)
GG.flush();WW.flush();oldG=np.load(SRC/'compositor_cache/G.npy',mmap_mode='r');oldW=np.load(SRC/'compositor_cache/W.npy',mmap_mode='r')
lap=(2-2*np.cos(np.pi*np.arange(N)/N))[:,None]+(2-2*np.cos(np.pi*np.arange(N)/N))[None,:];a=1/8**2
freq=np.hypot((np.arange(N)/(2*N))[:,None],(np.arange(N)/(2*N))[None,:]);t=np.clip((freq-1/16)/(1/8-1/16),0,1);H=.5-.5*np.cos(np.pi*t)

def stack(GG,WW,indices):
    da=np.zeros((N,N));dp=da.copy();na=da.copy();pn=da.copy();vn=da.copy()
    for i in indices:
        g=GG[i].astype(float);w=WW[i].astype(float);wp=w*pref[pi[i]];da+=w;dp+=wp;na+=w*g;pn+=wp*g
    assert np.all(da>0)&np.all(dp>0)
    allg=na/da;reference=pn/dp;base=.5*(allg+reference)
    gy=np.zeros((N-1,N));wy=gy.copy();gx=np.zeros((N,N-1));wx=gx.copy();effective=np.zeros((N,N))
    for i in indices:
        g=GG[i].astype(float);w=WW[i].astype(float);wm=.5*w/da+.5*w*pref[pi[i]]/dp;u=np.arcsinh(g/20.);effective+=wm*wm
        for axis,G,W in [(0,gy,wy),(1,gx,wx)]:
            aa=[slice(None)]*2;bb=aa.copy();aa[axis]=slice(None,-1);bb[axis]=slice(1,None);aa=tuple(aa);bb=tuple(bb);we=2*wm[aa]*wm[bb]/np.maximum(wm[aa]+wm[bb],1e-30);G+=we*(u[bb]-u[aa]);W+=we
    assert np.all(wy>0)&np.all(wx>0)
    gy/=wy;gx/=wx;rhs=np.zeros((N,N));rhs[:-1]-=gy;rhs[1:]+=gy;rhs[:,:-1]-=gx;rhs[:,1:]+=gx;ub=np.arcsinh(base/20.)
    ug=idctn(dctn(rhs+a*ub,type=2,norm='ortho')/(lap+a),type=2,norm='ortho');uc=ub+idctn(dctn(ug-ub,type=2,norm='ortho')*H,type=2,norm='ortho')
    return dict(base=base,all=allg,reference=reference,candidate=20*np.sinh(uc),gradient_candidate=20*np.sinh(ug),den_all=da,den_preference=dp,effective_number=1/np.maximum(effective,1e-30))

rows=[]
groups={'all':list(range(67)),'early':[i for i,m in enumerate(frames) if m['t_mid_C2']<50],'late':[i for i,m in enumerate(frames) if m['t_mid_C2']>=50]}
assert not set(groups['early'])&set(groups['late']) and len(groups['early'])+len(groups['late'])==67
for version,G,W in [('old',oldG,oldW),('new',GG,WW)]:
    for name,ids in groups.items():
        result=stack(G,W,ids);f=OUT/f'B0_{version}_{name}.npz';assert not f.exists();np.savez_compressed(f,**result)
        receipt=dict(version=version,group=name,frames=[frames[i]['stem'] for i in ids],negative_values=int((result['candidate']<=0).sum()))
        if version=='old' and name=='all':
            z=np.load(SRC/'B1_full_native_ensemble.npz');receipt['max_reproduction_error']={k:float(np.max(abs(result[k]-z[k]))) for k in z.files};assert max(receipt['max_reproduction_error'].values())<1e-8
        rows.append(receipt);print('STACK',version,name,len(ids),'DONE',flush=True)
        save('B0_ensembles.json',dict(method=__doc__,groups=rows,source_qualification='Frozen old ALPHA effective weights, not a new noise-calibration claim',operator=dict(transform='asinh(G/20)',poisson_screen_length=8,frequency_transition=[8,16])))
