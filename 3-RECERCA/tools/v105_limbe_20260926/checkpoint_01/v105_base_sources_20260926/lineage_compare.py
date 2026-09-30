from pathlib import Path
import json,numpy as np
from scipy.ndimage import gaussian_filter,binary_erosion
O=Path('/private/tmp/v105_base_sources_20260926');D=Path('/private/tmp/eclipse_v104_diagnosi_20260926');a=np.load(D/'L303.npz');T=np.stack([a[f'c{c}'] for c in range(3)],-1)[77:1477,77:1477]/65535
q=np.load(O/'09_original_AdobeRGB1998_registered_to_current303.npz');P={'CapesInteriors_original':q['RGB'],'CapesInteriors_V5':np.load(O/'09_V5_AdobeRGB1998_registered_to_current303.npz')['RGB'],'EarthshineV56':np.load(O/'EarthshineV56_09_shiftplus2plus4_ROI_RGB.npy').astype(float)/65535};edit=q['source_manual_patch'];yy,xx=np.mgrid[3077:4477,4677:6077];d=np.hypot(xx-5375.7868,yy-3775.9775)-452.9785;th=np.degrees(np.arctan2(-(yy-3775.7475),xx-5361.7681))%360;sec=(th//30).astype(int)
def tex(x):
 x=np.log(np.maximum(x,1e-6));return gaussian_filter(x,1,truncate=4)-gaussian_filter(x,4,truncate=4)
tt=tex(T[...,1]);out={'geometry':'fixed coronal transforms; no lunar contour alignment or shape warping','photometric_test':'per-channel cubic least-squares response only as lineage diagnostic, fitted on even 30deg sectors d60..150 excluding edited patch; not an image correction','sources':{}}
for key,v in P.items():
 pred=np.empty_like(v);models=[]
 for c in range(3):
  z=(d>60)&(d<150)&~edit&(sec%2==0)&(v[...,c]>.01)&(v[...,c]<.90)&np.isfinite(v[...,c]);x=v[...,c][z];y=T[...,c][z];step=max(1,len(x)//50000);x=x[::step];y=y[::step];coef=np.polynomial.polynomial.polyfit(x,y,3);pred[...,c]=np.polynomial.polynomial.polyval(v[...,c],coef);models.append({'coefficients':coef.tolist(),'fit_range':[float(x.min()),float(x.max())]})
 r={'response_models':models,'regions':{}};tv=tex(v[...,1])
 for name,z in [('held_out_outer',(d>60)&(d<150)&(sec%2==1)),('manual_patch',binary_erosion(edit,iterations=2)),('manual_patch_dgt20',binary_erosion(edit,iterations=2)&(d>20)),('near_limb_d5to20',(d>5)&(d<20))]:
  z=z&np.isfinite(v).all(-1);r['regions'][name]={'n':int(z.sum()),'texture_green_ncc':float(np.corrcoef(tt[z],tv[z])[0,1]),'original_RMSE_RGB_DN16':(np.sqrt(np.mean((v[z]-T[z])**2,axis=0))*65535).tolist(),'response_adjusted_RMSE_RGB_DN16':(np.sqrt(np.mean((pred[z]-T[z])**2,axis=0))*65535).tolist(),'outside_fitted_range_fraction':[((v[...,c][z]<models[c]['fit_range'][0])|(v[...,c][z]>models[c]['fit_range'][1])).mean().item() for c in range(3)]}
 out['sources'][key]=r
(O/'LINEAGE_PATCH_DIAGNOSTIC.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
