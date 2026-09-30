"""A20: la taca és albedo o vel de la corona? Perfils azimutals (sectors de 10°) a r 0,45–0,65 R del disc: RAW 10 s (normalitzat per anell), capa lunar V69 (id 30), LROC (id 62); i la corona al limbe (r 1,03–1,10 R) al RAW curt (0,5 s), tot al marc del compost."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import gaussian_filter, rotate, zoom, label, binary_fill_holes, map_coordinates
import rawpy
exec(open(SP+'/a10_lluna_raw.py').read().split('res=[]')[0].split('# 2) fotogrames RAW')[1])
ROT=11.0; CXp,CYp,RS=998.88,998.41,456.0
def prof_az(img,cx,cy,R,r0,r1,mask=None):
    yy,xx=np.mgrid[0:img.shape[0],0:img.shape[1]]; rr=np.hypot(xx-cx,yy-cy)/R; az=np.rad2deg(np.arctan2(-(yy-cy),xx-cx))%360
    k=(rr>=r0)&(rr<=r1); 
    if mask is not None: k&=mask
    return np.array([np.nanmedian(img[k&(az>=s)&(az<s+10)]) for s in range(0,360,10)])
out={}
# RAW 10 s: disc normalitzat per anell, girat al marc del compost
for f in ('572A2983.CR3','572A2982.CR3','572A2984.CR3'):
    img=llegeix(f); Lum=img.mean(-1); cx,cy,R,rms=troba_lluna(Lum)
    yy,xx=np.mgrid[0:Lum.shape[0],0:Lum.shape[1]]; rr=np.hypot(xx-cx,yy-cy)
    prof=np.array([np.median(Lum[(rr>=k)&(rr<k+3)]) for k in range(0,int(R*0.98),3)]); rad=np.interp(rr,np.arange(0,int(R*0.98),3)+1.5,prof); norm=np.where(rr<R*0.97,Lum/np.maximum(rad,1e-6),np.nan)
    S=int(R*1.05); sub=norm[int(cy)-S:int(cy)+S,int(cx)-S:int(cx)+S]; sub=rotate(np.nan_to_num(sub,nan=1.0),ROT,reshape=False,order=1,cval=1.0)
    out['RAW '+f[:-4]+' disc']=prof_az(sub,S,S,R,0.45,0.65)
# RAW 0,5 s: corona al limbe (r 1,03–1,10) i el disc també
for f in ('572A2972.CR3','572A2990.CR3'):
    img=llegeix(f); Lum=img.mean(-1); cx,cy,R,rms=troba_lluna(Lum); S=int(R*1.3); sub=rotate(Lum[int(cy)-S:int(cy)+S,int(cx)-S:int(cx)+S],ROT,reshape=False,order=1)
    p=prof_az(sub,S,S,R,1.03,1.10); out['RAW '+f[:-4]+' corona 1,03–1,10 R']=p/np.median(p); print(f,'saturació corona limbe (p99/65535): %.2f'%(np.percentile(sub[(np.hypot(*np.mgrid[-S:S,-S:S][::-1])/R>1.03)&(np.hypot(*np.mgrid[-S:S,-S:S][::-1])/R<1.10)],99)/65535))
# capa lunar i LROC (marc del compost)
for lid,nom in ((30,'capa lunar V69'),(62,'LROC (id 62)')):
    rgb,a=carrega(lid); L=rgb.mean(-1); d=np.load(SP+f'/roi_L{lid}.npz'); al=d['c-1'].astype(np.float32)/65535
    p=prof_az(L,CXp,CYp,RS,0.45,0.65,mask=al>0.5); out[nom]=p/np.median(p)
# base (display) fora del limbe: corona 1,03–1,10 R
rgb,a=carrega(3); out['base V69 corona 1,03–1,10 R (display)']=prof_az(rgb.mean(-1),CXp,CYp,RS,1.03,1.10)/np.median(prof_az(rgb.mean(-1),CXp,CYp,RS,1.03,1.10))
keys=list(out); print('\nsector  '+'  '.join(f'{k[:22]:>22s}' for k in keys))
for i,s in enumerate(range(0,360,10)): print(f'{s:3d}–{s+10:3d} '+'  '.join(f'{out[k][i]:22.4f}' for k in keys))
def corr(a,b): a=np.asarray(a); b=np.asarray(b); k=np.isfinite(a)&np.isfinite(b); return round(float(np.corrcoef(a[k],b[k])[0,1]),3)
raw=np.nanmean([out[k] for k in keys if k.endswith('disc')],0)
print('\ncorrelacions (36 sectors): RAW disc(10 s mitjana) vs LROC: %s · vs corona limbe RAW 0,5 s (2972): %s · vs corona base display: %s · vs capa lunar: %s'%(corr(raw,out['LROC (id 62)']),corr(raw,out['RAW 572A2972 corona 1,03–1,10 R']),corr(raw,out['base V69 corona 1,03–1,10 R (display)']),corr(raw,out['capa lunar V69'])))
print('capa lunar vs LROC: %s · capa lunar vs corona limbe RAW: %s · LROC vs corona: %s'%(corr(out['capa lunar V69'],out['LROC (id 62)']),corr(out['capa lunar V69'],out['RAW 572A2972 corona 1,03–1,10 R']),corr(out['LROC (id 62)'],out['RAW 572A2972 corona 1,03–1,10 R'])))
# regressió: RAW disc = a·LROC + b·corona + c
A=np.stack([out['LROC (id 62)'],out['RAW 572A2972 corona 1,03–1,10 R'],np.ones(36)],1); k=np.all(np.isfinite(A),1)&np.isfinite(raw); x,res,_,_=np.linalg.lstsq(A[k],raw[k],rcond=None)
pred=A[k]@x; print('regressió RAW disc = a·LROC + b·corona + c: a=%.4f b=%.4f c=%.3f · R² %.3f · només LROC R² %.3f · només corona R² %.3f'%(x[0],x[1],x[2],1-np.var(raw[k]-pred)/np.var(raw[k]),corr(raw,out['LROC (id 62)'])**2,corr(raw,out['RAW 572A2972 corona 1,03–1,10 R'])**2))
json.dump({k:[None if not np.isfinite(v) else float(v) for v in out[k]] for k in out},open(SP+'/a20_perfils.json','w'),indent=1)
print('\nhalo params FINAL (ago):',open('/Users/USUARI/Desktop/Eclipse 2026/4-RESULTATS/derivats/Earthshine/Earthshine_FINAL/earthshine_FINAL_halo_params.json').read()[:600])
