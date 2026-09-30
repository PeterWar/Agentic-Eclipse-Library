"""Freeze and execute temporal, noise and PSF source pilots before Sony judging.
All operators use Vixen pixels only. No legacy module is imported.
"""
from common import *
from scipy.ndimage import map_coordinates,gaussian_filter
from scipy.fft import dctn,idctn
from scipy.optimize import lsq_linear
from scipy.special import ndtr
claim()
G=np.load(SRC/'compositor_cache/G.npy',mmap_mode='r');W=np.load(SRC/'compositor_cache/W.npy',mmap_mode='r')
fr=[m for m in frame_list() if m['tren']=='vixen'];r,theta,d=geometry()
run=Path('/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/019_VIXEN_CIENCIA_20260827T212404Z')
pos=json.loads((run/'4-rebuts/F1.3_registre.json').read_text())['fotogrames']
J=np.load(SRC/'A0_native_samples_572A2978.npz')['native_to_world']
vec=np.array([J@np.array([pos[m['nom']]['lluna_dx'],pos[m['nom']]['lluna_dy']]) for m in fr])
# Alternate within exposure classes balances exposure, unlike the stored order.
ids=[[],[]]
for ex in sorted(set(m['exp'] for m in fr)):
    ix=sorted([i for i,m in enumerate(fr) if m['exp']==ex],key=lambda i:fr[i]['t_mid_C2'])
    for j,i in enumerate(ix):ids[j%2].append(i)
save('B1_design.json',dict(partitions=[[fr[i]['stem'] for i in a] for a in ids],
    temporal=dict(rule='W times exp((maximum projected lunar-solar separation minus current projection)/-20px); positive continuous bounded weights',scale_px=20.,vectors=vec.tolist()),
    psf=dict(bands_sigma_px=[4,8,16,32,64,128],fit='even radial bins; odd bins held out; nuisance lunar baseline degree0/1/2',d_range=[-80,-5]),
    judge=dict(bands_px=[[8,16],[16,24],[24,40],[40,64],[64,96]],radial_zones=[[100,300],[300,370],[370,435],[435,449]],sectors=12,fit_sectors='even',heldout='odd; all Sony pixels excluded from producer',null_rotation_degrees=list(range(30,360,30)),injection_seed=540913)))
proj=vec[:,0,None,None]*np.cos(theta)[None]+vec[:,1,None,None]*np.sin(theta)[None]
best=proj.max(0);del proj
num={k:np.zeros((N,N)) for k in ['all','temporal','half0','half1','early','late']};den={k:np.zeros((N,N)) for k in num}
for i,m in enumerate(fr):
    g=G[i].astype(float);w=W[i].astype(float)
    p=vec[i,0]*np.cos(theta)+vec[i,1]*np.sin(theta)
    wt=w*np.exp((p-best)/20.)
    for k,q in [('all',w),('temporal',wt),('half'+str(0 if i in ids[0] else 1),w),('early' if m['t_mid_C2']<50 else 'late',w)]:num[k]+=q*g;den[k]+=q
    if i%16==0:print('STACK',i,flush=True)
st={k:num[k]/np.maximum(den[k],1e-30) for k in num}
np.savez_compressed(OUT/'arrays/B1_stacks.npz',**st,**{'den_'+k:v for k,v in den.items()})
print('Stacks saved',flush=True)
# Edge spread fit is an identifiability experiment, NOT an assertion of a PSF.
dd=np.arange(-79.,-4.,2.);sig=np.array([4,8,16,32,64,128.]);E=ndtr(dd[:,None]/sig)
rows=[]
for sector in range(12):
    med=np.array([np.median(st['all'][(d>=x-1)&(d<x+1)&(theta>=sector*np.pi/6)&(theta<(sector+1)*np.pi/6)]) for x in dd])
    # Actual exterior level is uncertain because profiles and saturation differ.
    ext=np.median(st['all'][(d>=8)&(d<14)&(theta>=sector*np.pi/6)&(theta<(sector+1)*np.pi/6)])
    for degree in range(3):
        P=np.stack([(dd/80.)**j for j in range(degree+1)],1);A=np.c_[P,E];train=np.arange(len(dd))%2==0
        lo=np.r_[np.full(degree+1,-np.inf),np.zeros(len(sig))];hi=np.full(A.shape[1],np.inf)
        fit=lsq_linear(A[train],med[train],bounds=(lo,hi),tol=1e-10,max_iter=500)
        residual=med-A@fit.x;wing=fit.x[degree+1:]/max(ext-fit.x[0],1e-9)
        rows.append(dict(sector=sector,degree=degree,baseline=fit.x[:degree+1].tolist(),wing_coeff=wing.tolist(),wing_sum=float(wing.sum()),exterior=float(ext),heldout_rms=float(np.sqrt(np.mean(residual[~train]**2)))))
save('B1_PSF_identifiability.json',dict(rows=rows,sigma=sig.tolist(),method='Linear half-plane Gaussian mixture edge spread. Nuisance lunar baseline sensitivity, no Camera Raw veil treated as a kernel.',qualification='Identifiability and source deconvolution still require evaluation'))
print('PSF fits saved',flush=True)
# Noise estimated from real capture partitions, never var_* maps. Broad biases
# are excluded with spectral bands. Temporal split is an explicit upper check.
freq=np.hypot((np.arange(N)/(2*N))[:,None],(np.arange(N)/(2*N))[None,:])
F={k:dctn(v,type=2,norm='ortho') for k,v in st.items() if not k.startswith('den_')}
bands=[(8,16),(16,24),(24,40),(40,64),(64,96)]
rows=[];cand=st['all'].copy()
for lo,hi in bands:
    # Hard non-overlapping Fourier analysis bands; full frame, no tiled FFT.
    H=(freq>=1/hi)&(freq<1/lo)
    b=idctn(F['all']*H,type=2,norm='ortho')
    alt=idctn((F['half0']-F['half1'])*H,type=2,norm='ortho')*.5
    tmp=idctn((F['early']-F['late'])*H,type=2,norm='ortho')*.5
    # Actual unequal half weights: variance of full mean <= this conservative
    # half-difference estimate. FPN need not decorrelate: Sony checks follow.
    noise=gaussian_filter(alt*alt,64.)
    power=gaussian_filter(b*b,64.)
    wi=np.clip(1-noise/np.maximum(power,1e-30),0,1)
    ga=np.clip(1-9*noise/np.maximum(b*b,1e-30),0,1)
    gain=np.maximum(wi,ga)
    cand+=(gain-1)*b
    for a,z in [(100,300),(300,370),(370,435),(435,449)]:
        m=(r>=a)&(r<z)
        rows.append(dict(band=[lo,hi],radius=[a,z],signal_rms=float(np.std(b[m])),alternate_noise=float(np.std(alt[m])),temporal_difference=float(np.std(tmp[m])),gain_median=float(np.median(gain[m]))))
    np.save(OUT/f'arrays/B1_gain_{lo}_{hi}.npy',gain.astype('float32'))
np.save(OUT/'arrays/B1_noise_candidate.npy',cand)
save('B1_noise.json',dict(rows=rows,method='V40 max(regional Wiener,garrote k3), sigma64 regional power; observed balanced alternate halves; temporal split reported separately, no cross-sensor term in producer.',warning='Same-sensor FPN can cancel in halves; these gains are conditional until independent judging.'))
print('Noise pilot saved',flush=True)
