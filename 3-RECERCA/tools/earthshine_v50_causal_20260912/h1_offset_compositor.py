"""Recompose exact coronal-offset ablation through frozen V49 source operator."""
from common50 import *
from scipy.fft import dctn,idctn
SRC=ROOT/'output/earthshine_native_psf_20260911'
frames=[m for m in json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'] if m['tren']=='vixen']
keys=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F2_temporal.json').read_text())['groups']['vixen']['keys']
pref=np.load(ROOT/'research/tools/v45_earthshine_20260910/cau/vixen_epoch_preference.npy');pi=[keys.index('vixen_'+str(int(np.searchsorted([6,12.1,18.5,64,74,80.5,86.5,93,200],m['t_mid_C2'])))) for m in frames]
WW=np.load(SRC/'compositor_cache/W.npy',mmap_mode='r');GG=np.load(OUT/'H0_G_without_coronal_offset.npy',mmap_mode='r')
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
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);rows=[]
for name,ids in {'all':list(range(67)),'early':[i for i,m in enumerate(frames) if m['t_mid_C2']<50],'late':[i for i,m in enumerate(frames) if m['t_mid_C2']>=50]}.items():
 result=stack(GG,WW,ids);np.savez_compressed(OUT/f'H1_no_offset_{name}.npz',**result);old=np.load(SRC/f'B0_new_{name}.npz');delta=result['candidate']-old['candidate']
 rows.append(dict(group=name,regions={f'{lo}_{hi}':dict(before=np.percentile(old['candidate'][(r>=lo)&(r<hi)],[5,50,95]).tolist(),after=np.percentile(result['candidate'][(r>=lo)&(r<hi)],[5,50,95]).tolist(),delta=np.percentile(delta[(r>=lo)&(r<hi)],[5,50,95]).tolist()) for lo,hi in [(0,350),(415,435),(435,449),(449,454),(454,460)]}));print(name,rows[-1],flush=True)
save('H1_recomposition.json',dict(method=__doc__,regions=rows,status='Photographic and independent validation pending'))
