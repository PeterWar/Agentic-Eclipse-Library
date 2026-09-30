from pathlib import Path
import numpy as np,json,time
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from scipy.fft import rfft2,irfft2
from scipy.sparse.linalg import LinearOperator,cg
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';OLD=R/'output/earthshine_max_detail_20260913';N=1400;CX=699.568111973117;CY=699.6475341408573
rows=[q for q in json.loads((OLD/'A1_native_rgb_all.json').read_text())['frames'] if q['tren']=='vixen' and q['exp']>=.5];M0=np.array(rows[0]['roi_to_native']);centres=np.array([np.array(q['roi_to_native'])@np.array([CX,CY,1]) for q in rows]);sh=(np.linalg.inv(M0[:,:2])@(centres-centres[0]).T).T
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);t=np.arctan2(y-CY,x-CX)%(2*np.pi);edge=gaussian_filter1d(np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'),3,mode='wrap');physical=r<np.interp(t,np.linspace(0,2*np.pi,len(edge),endpoint=False),edge,period=2*np.pi)
Y=[];W=[]
for row in rows:
 z=np.load(row['file']);q=z['G1_q']+z['G2_q'];v=(np.nan_to_num(z['G1_var'])*z['G1_q']**2+np.nan_to_num(z['G2_var'])*z['G2_q']**2)/np.maximum(q*q,1e-30);a=(np.nan_to_num(z['G1'])*z['G1_q']+np.nan_to_num(z['G2'])*z['G2_q'])/np.maximum(q,1e-30);good=physical&np.isfinite(a)&(q>0);vs=gaussian_filter(np.where(good,v,0),4)/np.maximum(gaussian_filter(good.astype(float),4),1e-30);Y.append(np.where(good,a,0).astype('float32'));W.append(np.where(good,q/2/np.maximum(vs,1e-12),0).astype('float32'))
Y=np.array(Y);W=np.array(W);OW=W.copy();den=OW.sum(0);num=(Y*OW).sum(0);base=num/np.maximum(den,1e-30)
for i in range(len(rows)):
 rem=den-OW[i];ref=np.divide(num-OW[i]*Y[i],rem,out=base.copy(),where=rem>1e-12);dw=gaussian_filter(OW[i],32);var=gaussian_filter(OW[i]*(Y[i]-ref)**2,32)/np.maximum(dw,1e-30);W[i]/=1+OW[i]*var
fy=np.fft.fftfreq(N)[:,None];fx=np.fft.rfftfreq(N)[None,:];fr=np.hypot(fx,fy);ang=np.arctan2(fy,fx)%np.pi;u=np.clip((fr-1/16)/(1/12-1/16),0,1);v=np.clip((fr-1/4)/(1/3-1/4),0,1);H=((.5-.5*np.cos(np.pi*u))*(.5+.5*np.cos(np.pi*v))).astype('float32')
def filt(a):return irfft2(rfft2(a)*H,s=(N,N))
maps=[]
for sx,sy in sh:
 ix=int(np.floor(sx));iy=int(np.floor(sy));qx=sx-ix;qy=sy-iy;maps.append([(iy,ix,(1-qy)*(1-qx)),(iy,ix+1,(1-qy)*qx),(iy+1,ix,qy*(1-qx)),(iy+1,ix+1,qy*qx)])
def pull(a,i):return sum(w*np.roll(a,(-dy,-dx),(0,1)) for dy,dx,w in maps[i])
def push(a,i):return sum(w*np.roll(a,(dy,dx),(0,1)) for dy,dx,w in maps[i])
indices=[[],[]];groups={}
for i,q in enumerate(rows):groups.setdefault(q['exp'],[]).append(i)
for exp,g in groups.items():
 for j,i in enumerate(sorted(g,key=lambda i:rows[i]['time_C2'])):indices[j%2].append(i)
rep=[];ds=[]
for label,ids in [('half0',indices[0]),('half1',indices[1]),('all',list(range(len(rows))))]:
 dd=W[ids].sum(0);bb=(W[ids]*Y[ids]).sum(0)/np.maximum(dd,1e-30);rhs=filt(sum(push(W[i]*(Y[i]-bb),i) for i in ids));ridge=.1*np.median(dd[(r<300)&(dd>0)]);tick=time.time();n=[0]
 def op(v):
  a=filt(v.reshape(N,N));ps=[pull(a,i) for i in ids];av=sum(W[i]*p for i,p in zip(ids,ps))/np.maximum(dd,1e-30);return (filt(sum(push(W[i]*(p-av),i) for i,p in zip(ids,ps)))+ridge*v.reshape(N,N)).ravel()
 def cb(v):
  n[0]+=1
  if n[0]%10==0:print(label,n[0],round(time.time()-tick),flush=True)
 mat=LinearOperator((N*N,N*N),matvec=op,dtype=np.float32);sol,inf=cg(mat,rhs.ravel(),rtol=3e-5,maxiter=80,callback=cb);assert inf==0,(label,inf);D=filt(sol.reshape(N,N));ds.append(D);np.save(A/f'B9_detector_{label}.npy',D);rep.append(dict(label=label,n=n[0],seconds=time.time()-tick,indices=ids));print(label,'DONE',n[0],flush=True)
aa=rfft2(ds[0]);bb=rfft2(ds[1]);gain=np.zeros_like(fr,dtype='float32');grows=[]
for lo,hi in [(3,4),(4,6),(6,9),(9,12),(12,16)]:
 for j in range(12):
  mask=(fr>=1/hi)&(fr<1/lo)&(ang>=j*np.pi/12)&(ang<(j+1)*np.pi/12);cross=max(float(np.real(aa[mask]*bb[mask].conj()).sum()),0);noise=float((abs(aa[mask]-bb[mask])**2).sum()/4);g=cross/max(cross+noise,1e-30);gain[mask]=g;grows.append(dict(band=[lo,hi],angle=j,gain=g))
D=irfft2(rfft2(ds[2])*gain,s=(N,N));corr=sum(OW[i]*pull(D,i) for i in range(len(rows)))/np.maximum(den,1e-30);np.savez_compressed(A/'B9_fine_detector.npz',detector=D,correction=corr,source=base-corr,raw_baseline=base,gain=gain,H=H)
(O/'B9_result.json').write_text(json.dumps(dict(frames=[q['stem'] for q in rows],shifts=sh.tolist(),solves=rep,gains=grows,rms_correction=float(np.std(corr[r<400]))),indent=2)+'\n');print('FINE DETECTOR COMPLETE',flush=True)
