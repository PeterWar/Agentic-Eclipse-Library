from common58 import *
import pandas as pd
from scipy.ndimage import maximum_filter
claim();F=np.load(O/'sources/fusion_starless.npy',mmap_mode='r');V=np.load(O/'sources/vixen_starless.npy',mmap_mode='r');S=np.load(O/'sources/sony_starless.npy',mmap_mode='r');m=np.load(V42/'cau/support_v42.npy');cat=pd.read_csv(O/'catalog_projected.csv');stars=[]
def detect(a,x,y,search=7):
 x,y=int(round(x)),int(round(y));rad=28
 if min(x,y)<rad or x+rad>=a.shape[1] or y+rad>=a.shape[0]:return None
 q=np.asarray(a[y-rad:y+rad+1,x-rad:x+rad+1,1],float)
 if not np.isfinite(q).all() or (q<=0).any():return None
 sm=gaussian_filter(q,2);bg=gaussian_filter(q,8);hp=sm-bg;noise=q-gaussian_filter(q,1);sd=1.4826*np.median(np.abs(noise-np.median(noise)))+1e-9
 yy,xx=np.mgrid[-rad:rad+1,-rad:rad+1];inner=np.hypot(xx,yy)<=search;iy,ix=np.unravel_index(np.argmax(np.where(inner,hp,-np.inf)),hp.shape);peak=hp[iy,ix];sn=peak/(sd/np.sqrt(4*np.pi*4));bgnoise=1.4826*np.median(np.abs(hp[np.hypot(xx,yy)>15]-np.median(hp[np.hypot(xx,yy)>15])))+1e-9;contrast=peak/bgnoise
 return dict(x=x+ix-rad,y=y+iy-rad,snr=sn,contrast=contrast,peak=peak,noise=sd)
rows=[];null=[]
for i,c in cat.iterrows():
 x,y=c.x_pred,c.y_pred
 if not (35<x<10516 and 35<y<7471) or not m[int(y),int(x)] or np.hypot(x-CX,y-CY)<1.15*RS:continue
 d=detect(F,x,y)
 if d is None:continue
 d.update(TYC=str(c.TYC),Vmag=float(c.Vuse),pred=[x,y]);rows.append(d)
 # Frozen 180deg position, same radius and search window. Shared coverage required.
 dn=detect(F,2*CX-x,2*CY-y)
 if dn:null.append(dn)
 if d['snr']>=7 and d['contrast']>=4:
  dv=detect(V,d['x'],d['y'],3);ds=detect(S,d['x'],d['y'],3);d['vixen']=dv;d['sony']=ds
  d['independent_two_trains']=bool(dv and ds and min(dv['snr'],ds['snr'])>=4 and min(dv['contrast'],ds['contrast'])>=2 and np.hypot(dv['x']-ds['x'],dv['y']-ds['y'])<6)
  stars.append(d)
rep=dict(catalog_count=len(cat),tested=len(rows),candidates=stars,rows=rows,null=null,thresholds=dict(snr=7,local_contrast=4,independent_snr=4,independent_contrast=2));save('D7_stars_remaining.json',rep);print('tested',len(rows),'stars',len(stars),'independent',sum(s['independent_two_trains'] for s in stars),'nullpass',sum(d['snr']>=7 and d['contrast']>=4 for d in null));print([(s['TYC'],round(s['Vmag'],1),s['x'],s['y'],round(s['snr']),round(s['contrast'],1),s['independent_two_trains']) for s in stars])
