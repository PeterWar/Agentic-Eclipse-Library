from pathlib import Path
import json,numpy as np
from scipy.ndimage import gaussian_filter,binary_erosion,map_coordinates,minimum_filter
O=Path('/private/tmp/v105_base_sources_20260926');Q={k:np.load(O/f'572A{k}.npz') for k in ['2969','2975','2993']};R=np.load(O/'09_original_AdobeRGB1998_registered_to_E2975.npz')
RGB={'09':R['RGB'],**{k:q['E'] for k,q in Q.items()}};DR={'09':Q['2975']['dreal'],**{k:q['dreal'] for k,q in Q.items()}};V={'09':R['support_sampled'],**{k:q['valid_rgb'] for k,q in Q.items()}}
by,ey,bx,ex=map(int,Q['2975']['box']);yy,xx=np.mgrid[by:ey,bx:ex];cx,cy=5361.768111973117,3775.747534140857;th=np.degrees(np.arctan2(-(yy-cy),xx-cx))%360;sec=(th//30).astype(int);dref=Q['2975']['dreal'];hold=sec%2==1
scales=[1,2,4,8];bands=[(0,10),(10,30),(30,60),(60,100),(100,150)];pairs=[('09','2975'),('09','2969'),('09','2993'),('2975','2969'),('2975','2993'),('2969','2993')]
def corr(a,b):return float(np.corrcoef(a,b)[0,1]) if len(a)>100 else None
def hp(image,s):
 valid=np.isfinite(image)&(image>0);log=np.where(valid,np.log(np.maximum(np.nan_to_num(image),1e-12)),0)
 def filt(sig):return gaussian_filter(log,sig,truncate=4)/np.maximum(gaussian_filter(valid.astype(float),sig,truncate=4),1e-12)
 return (filt(s)-filt(2*s)).astype('float32')
def remove_ring_means(z,mask):
 ring=np.rint(np.hypot(xx-cx,yy-cy)).astype(int);n=np.bincount(ring[mask]);sm=np.bincount(ring[mask],weights=z[mask]);mean=np.divide(sm,n,out=np.zeros_like(sm),where=n>0);return z-mean[np.minimum(ring,len(mean)-1)]
report={'definition':'log RGB DoG(s,2s), Gaussian truncate4; original09 after native16 ICC to AdobeRGB registered directly on coronal texture to E2975','scales':scales,'heldout':'odd 30-degree solar sectors, not used by registration','strict_guard':'square erosion with radius8*s of valid finite positive data AND dreal>2; guarantees every pixel in separable Gaussian support is observed outside lunar silhouette plus2px model margin; report domain also excludes reference0..10 for corroboration','near_boundary':'0..10px deliberately only edge-sensitive descriptive report, never evidence of small-scale corona','independence':'09 original stack uses RAW2975 and RAW2993, so these correlations may include shared sensor/photon noise; RAW2969 is independent exposure and necessary corroboration. Positive correlations can retain shared systematic errors.','data':[],'physical_validity':{},'caveats':['Original09 is display-referred developed/stacked, E is calibrated linear radiance. Log channel removes scalar gamma approximately, not all development response.','Original09 had interpolation/stacking plus present bilinear resampling; correlation of isolated pixels is attenuated.','All raw frames retain existing solar registration. No new shifts used in primary metrics.']}
for k in RGB:
 report['physical_validity'][k]={'valid_fraction':float(V[k].mean()),'positive_RGB_fraction':float((np.isfinite(RGB[k]).all(-1)&(RGB[k]>0).all(-1)).mean())}
H={}
for s in scales:
 H[s]={k:np.stack([hp(v[...,c],s) for c in range(3)],-1) for k,v in RGB.items()}
 safe={k:minimum_filter((V[k]&np.isfinite(RGB[k]).all(-1)&(RGB[k]>0).all(-1)&(DR[k]>2)).astype('uint8'),size=16*s+1,mode='constant',cval=0)>0 for k in RGB}
 residual={k:np.stack([remove_ring_means(v[...,c],safe[k]&(dref<200)) for c in range(3)],-1) for k,v in H[s].items()}
 for a,b in pairs:
  for lo,hi in bands:
   region=(dref>=lo)&(dref<hi)&hold
   for guard in ['strict','edge_sensitive'] if lo==0 else ['strict']:
    z=region&safe[a]&safe[b] if guard=='strict' else region&V[a]&V[b]&(DR[a]>0)&(DR[b]>0)
    n=int(z.sum());row={'sigma':s,'pair':[a,b],'band_ref2975':[lo,hi],'guard':guard,'n':n,'rho_RGB':None,'rho_azimuthal_RGB':None}
    if n>100:
     row['rho_RGB']=[corr(H[s][a][...,c][z],H[s][b][...,c][z]) for c in range(3)];row['rho_azimuthal_RGB']=[corr(residual[a][...,c][z],residual[b][...,c][z]) for c in range(3)]
     row['G_std_pair']=[float(H[s][k][...,1][z].std()) for k in [a,b]]
     row['sectors_G']=[{'sector':i,'n':int((z&(sec==i)).sum()),'rho':corr(H[s][a][...,1][z&(sec==i)],H[s][b][...,1][z&(sec==i)])} for i in [1,3,5,7,9,11]]
    report['data'].append(row)
 np.savez_compressed(O/f'detail_audit_hp_sigma{s}.npz',**{k:H[s][k][...,1] for k in H[s]},**{f'safe_{k}':safe[k] for k in safe},box=[by,ey,bx,ex])
(O/'DETAIL_CORROBORATION.json').write_text(json.dumps(report,indent=2))
print('HELDOUT GREEN CORRELATIONS strict: pair band sigma:ncc; radial-profile-subtracted in brackets',flush=True)
for a,b in pairs:
 print(a,b,flush=True)
 for lo,hi in bands:
  rows=[r for r in report['data'] if r['pair']==[a,b] and r['band_ref2975']==[lo,hi] and r['guard']=='strict'];print((lo,hi),' '.join(f"{r['sigma']}:{r['rho_RGB'][1]:.3f}({r['rho_azimuthal_RGB'][1]:.3f}) n{r['n']}" if r['rho_RGB'] else f"{r['sigma']}:no-safe-support" for r in rows),flush=True)
