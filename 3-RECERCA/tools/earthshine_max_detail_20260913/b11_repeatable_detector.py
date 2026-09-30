"""New bounded hypothesis: suppress detector modes not repeatable across frames.
Two disjoint halves stratified by exposure, alternating time. Estimate detector
with exactly the full-safe operator. Noise-aware Fourier gains from the two
estimates: positive cross-power / (positive cross-power + half-difference power).
Five predeclared wavelength bins and eight undirected orientation bins. No
external image, region mark, photographic radius or heldout score enters gains.
"""
from common import *
from load_model_state import load_state
from scipy.fft import rfft2,irfft2
from scipy.sparse.linalg import LinearOperator,cg
import time
claim();allframes={z['stem']:z for z in frames()};st=load_state(['G','--all67','--robust','--hetero','--full-error-safe']);names=st['names'];groups={}
for i,name in enumerate(names):groups.setdefault(allframes[name]['exp'],[]).append(i)
ids=[[],[]]
for exp,g in sorted(groups.items()):
    g=sorted(g,key=lambda i:allframes[names[i]]['t_mid_C2'])
    for j,i in enumerate(g):ids[j%2].append(i)
bands=[12,16,24,40,64,96];angles=8
save('B11_protocol.json',dict(method=__doc__,halves=[[names[i] for i in ii] for ii in ids],bands=bands,orientations=angles,rule='g=max(Re(Da*conj(Db)),0)/(max(cross,0)+abs(Da-Db)^2/4), summed by fixed spectral bin; apply to full-data detector once, fixed original source weights',limits=['Conditional split: shared calibration, geometry and nuisance covariance remain; not independent sensors','Unequal half exposure counts and common support can bias spectral variance; external judge is unchanged','D0 loses one inherited texture claim and is rejected; this is a distinct source-identification model, no gain search to recover that claim']))
W,Y,OW=st['W'],st['Y'],st['originalW'];filt,pull,push=st['filt'],st['pull'],st['push'];rad=st['rad'];Ns=N*N
for h,ii in enumerate(ids):
    path=OUT/f'arrays/B11_half{h}.npz';assert not path.exists();den=W[ii].sum(0);base=sum(W[i]*Y[i] for i in ii)/np.maximum(den,1e-30);rhs=filt(sum(push(W[i]*(Y[i]-base),i) for i in ii));lm=.1*np.median(den[(rad<300)&(den>0)])
    def op(v):
        z=v.reshape(N,N);d=filt(z);pp=[pull(d,i) for i in ii];av=sum(W[i]*p for i,p in zip(ii,pp))/np.maximum(den,1e-30);return (filt(sum(push(W[i]*(p-av),i) for i,p in zip(ii,pp)))+lm*z).ravel()
    tick=time.time();count=[0]
    def cb(v):
        count[0]+=1
        if count[0]%5==0:print('HALF',h,'CG',count[0],'s',round(time.time()-tick),flush=True)
    A=LinearOperator((Ns,Ns),matvec=op,dtype=np.float64);z,info=cg(A,rhs.ravel(),rtol=2e-5,maxiter=60,callback=cb);assert info==0
    np.savez_compressed(path,detector=filt(z.reshape(N,N)),iterations=count[0]);print('HALF',h,'DONE',flush=True)
a=rfft2(np.load(OUT/'arrays/B11_half0.npz')['detector']);b=rfft2(np.load(OUT/'arrays/B11_half1.npz')['detector']);fy=np.fft.fftfreq(N)[:,None];fx=np.fft.rfftfreq(N)[None,:];fr=np.hypot(fx,fy);ang=np.arctan2(fy,fx)%np.pi;gain=np.zeros(a.shape);rows=[]
for lo,hi in zip(bands[:-1],bands[1:]):
    for j in range(angles):
        m=(fr>=1/hi)&(fr<1/lo)&(ang>=j*np.pi/angles)&(ang<(j+1)*np.pi/angles);sig=max(float(np.real(a[m]*b[m].conj()).sum()),0);noise=float((abs(a[m]-b[m])**2).sum()/4);g=sig/max(sig+noise,1e-30);gain[m]=g;rows.append(dict(band=[lo,hi],orientation=j,gain=g,positive_cross_power=sig,noise_power=noise))
# A single global multiplier; no window mosaic or spatially painted gain.
z=np.load(OUT/'arrays/B3_G67_robust_hetero_full_safe_all.npz');D=irfft2(rfft2(z['detector'])*gain,s=(N,N));corr=sum(OW[i]*pull(D,i) for i in range(len(names)))/np.maximum(OW.sum(0),1e-30)
np.savez_compressed(OUT/'arrays/B11_repeatable_all.npz',detector=D,correction=corr,source=z['raw_baseline']-corr,raw_baseline=z['raw_baseline'],gain=gain)
save('B11_repeatability.json',dict(rows=rows,detector_before_rms=float(np.std(z['detector'][rad<410])),detector_after_rms=float(np.std(D[rad<410])),correction_p95_inner=float(np.percentile(abs(corr[(rad>60)&(rad<350)]),95)),correction_p95_outer=float(np.percentile(abs(corr[(rad>435)&(rad<449)]),95)),status='New source pilot; unchanged external/photo gates pending'))
print('REPEATABILITY DONE',rows,flush=True)
