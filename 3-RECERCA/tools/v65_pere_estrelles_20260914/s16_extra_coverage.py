from pathlib import Path
import numpy as np,json,pandas as pd,rawpy
from astropy.io import fits
from scipy.ndimage import gaussian_filter
from s4_native_psf import prf,X,Y
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';W=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17');meta=json.loads((O/'S9_native_manifest.json').read_text());catalog=pd.read_csv(R/'output/v58_correccions_20260913/catalog_projected.csv');plate=json.loads((W/'xmatch/final_solution.json').read_text())['sony_radial'];mp=json.loads((O/'S7_refined_maps.json').read_text());coef=np.array(mp['interpointing']['coefficients_C_to_A']);reg=mp['native_transforms'];seen={(r['kind'],r['TYC']) for r in meta['rows'] if r['kind']!='psf_reference'};models=json.loads((O/'S10_native_detection.json').read_text())['models'];params={n:v['parameters'] for n,v in models.items()};ann=np.hypot(X,Y)>8
u=catalog.xh_as.to_numpy();v=catalog.yh_as.to_numpy();Q=np.c_[u*0+1,u,v,u*(u*u+v*v),v*(u*u+v*v)];Cpos=Q@np.array([plate['px'],plate['py']]).T

def point(c,fr):
 if fr['name'] in ['DSC06984','DSC06985','DSC06987']:
  u,v=(c-np.array(mp['interpointing']['centre']))/mp['interpointing']['scale'];p=np.array([1,u,v,u*u,u*v,v*v])@coef
 else:p=c.copy()
 p+=fr['offset'];r=reg[fr['name']];u,v=(p-r['centre'])/r['scale_unit'];a,b,k,t=r['parameters'];return p+np.array([a+k*u-t*v,b+k*v+t*u])
rows=[]
for kind in ['catalog','rotated_null']:
 for i,c in enumerate(Cpos):
  r=catalog.iloc[i]
  if (kind,r.TYC) in seen:continue
  if kind=='rotated_null':c=2*np.array([plate['sun_x'],plate['sun_y']])-c
  if np.linalg.norm(c-[plate['sun_x'],plate['sun_y']])<310:continue
  pos={fr['name']:point(c,fr).tolist() for fr in meta['frames']};ok={n:20<p[0]<7948 and 20<p[1]<5300 for n,p in pos.items()};A=sum(ok[n] for n in ['DSC06984','DSC06985','DSC06987']);C=sum(ok[n] for n in ['DSC06991','DSC06993','DSC06996','DSC06999'])
  if max(A,C)<3:continue
  rows.append(dict(kind=kind,TYC=r.TYC,HIP=r.HIP,V=float(r.Vuse),BV=float(r.BVuse),x_final=float(r.x_pred),y_final=float(r.y_pred),positions=pos,coverage=ok,split='A' if A==3 else 'C'))
print('extra candidates',len(rows),flush=True);records=[]
with fits.open(meta['flat'],memmap=True) as hd:
 flat=hd[0].data
 for fr in meta['frames']:
  name=fr['name'];e=fr['exposure'];dark=np.load(W/'sony'/f'masterdark_{int(e)}s.npy',mmap_mode='r');st=[];co=[];va=[];org=[];expected=[]
  with rawpy.imread(fr['path']) as rr:
   raw=rr.raw_image_visible;col=rr.raw_colors_visible
   for r in rows:
    p=np.array(r['positions'][name]);ix,iy=np.rint(p).astype(int)
    if not r['coverage'][name]:st.append(np.zeros((25,25),np.float32));co.append(np.zeros((25,25),np.uint8));va.append(np.zeros((25,25),bool));org.append([ix,iy]);expected.append(p);continue
    sl=np.s_[iy-12:iy+13,ix-12:ix+13];fl=np.array(flat[sl]);z=(raw[sl].astype(float)-dark[sl])/fl/e;st.append(z.astype('float32'));co.append(col[sl].copy());va.append((raw[sl]<15600)&np.isfinite(z)&(fl>.1));org.append([ix,iy]);expected.append(p)
  np.savez_compressed(O/f'S16_{name}.npz',data=np.array(st),colour=np.array(co),valid=np.array(va),origin=np.array(org),expected=np.array(expected));print(name,flush=True)
# Discover centroid offset only on the 8s frame, then validate it on disjoint short exposures.
for i,r in enumerate(rows):
 n='DSC06987' if r['split']=='A' else 'DSC06993';f=np.load(O/f'S16_{n}.npz');z=f['data'][i];col=f['colour'][i];valid=f['valid'][i];mask=valid&((col==1)|(col==3));v=z[mask].astype(float);x=X[mask]/12;y=Y[mask]/12;B=np.c_[x*0+1,x,y,x*x,y*y,x*y];Bi=np.linalg.pinv(B);v0=v-B@(Bi@v);p0=f['expected'][i]-f['origin'][i];best=(-np.inf,0,0)
 for dy in np.arange(-3,3.1,.5):
  for dx in np.arange(-3,3.1,.5):
   p=params[n].copy();p[:2]=(p0+[dx,dy]).tolist();t=prf(p)[mask];t-=B@(Bi@t);score=(t@v0)/max(np.sqrt(t@t),1e-10)
   if score>best[0]:best=(score,dx,dy)
 r['long_frame_centroid_offset']=[best[1],best[2]]
(O/'S16_extra_manifest.json').write_text(json.dumps(dict(rows=rows,frames=meta['frames'],models=params,purpose='Recover native parts of Sony A/C outside the legacy coadd rectangle; use separate short exposures for confirmation, same reflected controls.'),indent=2));print('COMPLETE')
