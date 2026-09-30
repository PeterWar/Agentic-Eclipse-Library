"""Frozen local spectral QA: identical windows, colour decoding, Brno registration and thresholds for every V112 candidate."""
from pathlib import Path
import sys,json,numpy as np,tifffile
from scipy.fft import rfft2,rfftfreq,fftfreq
R=Path(__file__).resolve().parents[3];O=R/'4-RESULTATS/v112_20260928';sys.path.insert(0,str(R/'3-RECERCA/tools/v73_marques_v71_20260917'));from psb69 import PSB
WINDOWS={'N':[4850,1728,5874,2752],'NW':[3826,2240,4850,3264],'NE':[5874,2240,6898,3264],'W':[3314,3264,4338,4288],'E':[6386,3264,7410,4288],'SW':[3826,4288,4850,5312],'SE':[5874,4288,6898,5312],'S':[4850,4800,5874,5824]}
N=1024;u=np.arange(N)-511.5;den=N*np.sum(u*u);hann=np.outer(np.hanning(N),np.hanning(N));fy,fx=np.meshgrid(fftfreq(N),rfftfreq(N),indexing='ij');freq=np.hypot(fx,fy);weights=np.where((fx==0)|(fx==.5),1.,2.);bands={l:(freq>=1/(1.25*l))&(freq<=1/(.8*l)) for l in [96,160,256]}
def spectrum(rgb,log=False):
 Y=np.sum(np.array([.2973769,.6273491,.0752741])*(rgb.astype(np.float64)/65535)**(563/256),axis=-1)
 z=np.log(np.maximum(Y,1e-8)) if log else Y
 plane=z.mean()+u[None,:]*np.sum(z*u[None,:])/den+u[:,None]*np.sum(z*u[:,None])/den
 return rfft2((z-plane)*hann)
def run(candidate):
 base=tifffile.memmap(O/'control_natiu/visible_complet.tif',mode='r');cand=tifffile.memmap(candidate,mode='r');p=PSB(str(R/'4-RESULTATS/v110_torre_20260928/V111.psb'));out=dict(candidate=str(candidate),windows=WINDOWS,band_order=[96,160,256],required_retention=.90,min_corr_delta=-.02,results={},failures=[],support_checks=[])
 from brno_astronomical_support_v112 import check as astronomical_support
 out['astronomical_support']=astronomical_support(R,WINDOWS)
 out['failures'].extend(out['astronomical_support']['failures'])
 support=np.load(R/'4-RESULTATS/v108_20260926/cadena/v108/lineal/support.npy',mmap_mode='r')
 for name,(x0,y0,x1,y1) in WINDOWS.items():
  valid=bool(support[y0-32:y1+32,x0-32:x1+32].all());out['support_checks'].append(dict(window=name,science_support=valid))
  if not valid:out['failures'].append(dict(check='science_support',window=name))
 F={}
 for name,(x0,y0,x1,y1) in WINDOWS.items():
  for typ,log in [('linear',False),('log',True)]:F[name,typ]=[spectrum(im[y0:y1,x0:x1],log) for im in (base,cand)]
 for ref,lid in [('200',230),('400',231),('530',232)]:
  channels=[p.channel(lid,c) for c in [0,1,2]];origin=channels[0][1];rgb=np.stack([a for a,_ in channels],axis=-1);del channels
  alpha,alpha_origin=p.channel(lid,-1)
  for name,(x0,y0,x1,y1) in WINDOWS.items():
   if ref=='530' and name=='NE':continue
   a=alpha[y0-32-alpha_origin[1]:y1+32-alpha_origin[1],x0-32-alpha_origin[0]:x1+32-alpha_origin[0]]
   valid=a.shape==(1088,1088) and bool((a==65535).all());out['support_checks'].append(dict(reference=ref,window=name,opaque_with_margin=valid))
   if not valid:out['failures'].append(dict(check='reference_support',reference=ref,window=name))
  del alpha
  out['results'][ref]={}
  for typ,log in [('linear',False),('log',True)]:
   rows={};sums={l:np.zeros(5) for l in bands}
   for name,(x0,y0,x1,y1) in WINDOWS.items():
    if ref=='530' and name=='NE':continue
    rb=rgb[y0-origin[1]:y1-origin[1],x0-origin[0]:x1-origin[0]];B=spectrum(rb,log);A,C=F[name,typ];vals={}
    for l,sel in bands.items():
     w=weights[sel];a,c,b=A[sel],C[sel],B[sel];vec=np.array([np.sum(w*(a*np.conj(b)).real),np.sum(w*(c*np.conj(b)).real),np.sum(w*abs(a)**2),np.sum(w*abs(c)**2),np.sum(w*abs(b)**2)])
     sums[l]+=vec;pb,cb,pp,cc,bb=vec;corr0=pb/np.sqrt(pp*bb);corr1=cb/np.sqrt(cc*bb);ret=cb/pb
     vals[str(l)]=dict(retention=float(ret),correlation_base=float(corr0),correlation_candidate=float(corr1),delta_correlation=float(corr1-corr0))
     if typ=='linear' and (ret<.90 or corr1-corr0<-.02):out['failures'].append(dict(reference=ref,window=name,band=l,**vals[str(l)]))
    rows[name]=vals
   aggregate={}
   for l,(pb,cb,pp,cc,bb) in sums.items():aggregate[str(l)]=dict(retention=float(cb/pb),correlation_base=float(pb/np.sqrt(pp*bb)),delta_correlation=float(cb/np.sqrt(cc*bb)-pb/np.sqrt(pp*bb)))
   out['results'][ref][typ]=dict(local=rows,aggregate=aggregate)
  del rgb
 out['status']='PASS' if not out['failures'] else 'FAIL';return out
if __name__=='__main__':
 out=run(Path(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(out,indent=2)+'\n');print(out['status'],len(out['failures']));print({k:v['linear']['aggregate'] for k,v in out['results'].items()})
 sys.exit(out['status']!='PASS')
