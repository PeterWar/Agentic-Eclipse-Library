from common import *
from scipy.ndimage import median_filter
from polar_filters import back
import warnings,gc
def fnrgf(a,m):
 r,t=coords();ri=np.floor(r).astype('int32');si=np.floor(np.mod(t,2*np.pi)*50/(2*np.pi)).astype('int32');nr=int(ri.max())+1
 ids=(ri[m]*50+si[m]);v=a[m].astype('float64');n=np.bincount(ids,minlength=nr*50).reshape(nr,50)
 mean=np.bincount(ids,weights=v,minlength=nr*50).reshape(nr,50)/np.maximum(n,1)
 sd=np.sqrt(np.maximum(0,np.bincount(ids,weights=v*v,minlength=nr*50).reshape(nr,50)/np.maximum(n,1)-mean*mean))
 valid=(n>=2).all(axis=1);theta=(np.arange(50)+.5)*2*np.pi/50
 am=[mean.mean(axis=1)];cs=[sd.mean(axis=1)]
 for k in range(1,7):
  for trig in [np.cos,np.sin]:am.append(2/50*(mean@trig(k*theta))*[1,.85,.7,.55,.4,.25,.1][k]);cs.append(2/50*(sd@trig(k*theta))*[1,.9,.8,.7,.6,.5,.4][k])
 out=np.full_like(a,np.nan);bad_denom=0
 for y in range(0,H,128):
  rr=ri[y:y+128];tt=t[y:y+128];mu=am[0][rr].copy();sig=cs[0][rr].copy();j=1
  for k in range(1,7):
   for trig in [np.cos,np.sin]:mu+=am[j][rr]*trig(k*tt);sig+=cs[j][rr]*trig(k*tt);j+=1
  good=m[y:y+128]&valid[rr]&(sig>0);bad_denom+=int((m[y:y+128]&valid[rr]&(sig<=0)).sum())
  block=np.divide(a[y:y+128]-mu,sig,out=np.zeros_like(mu),where=sig>0);out[y:y+128][good]=block[good]
 np.save(C/'FNRGF_domain_only_float.npy',out)
 savejson(D/'receipts/FNRGF_domain.json',{'equations':'Druckmullerova et al.2011 equations2-7','segments':50,'annuli_px':1,'order':10,'attenuation_mean':[1,.85,.7,.55,.4,.25,.1,0,0,0,0],'attenuation_std':[1,.9,.8,.7,.6,.5,.4,0,0,0,0],'complete_annuli':int(valid.sum()),'defined_observed_pixels':int(np.isfinite(out).sum()),'undefined_observed_pixels':int((m&~np.isfinite(out)).sum()),'invalid_denominator_pixels':bad_denom,'disposition':'domain-only scientific NPY; not placed in PSB because a full-FOV pure result would require invented missing angular data or an extra circular boundary','source_preserved':True})
 log('FNRGF domain audit saved')
def swap(a,m):
 # Paper2023 off-limb prescription, not the differing IDL defaults.
 r,_=coords();rv=np.arange(max(0,np.floor(r[m].min())-8),np.ceil(r[m].max())+9,1.);nt=720;th=np.arange(nt)*2*np.pi/nt
 p=np.empty((len(rv),nt),np.float32);af=np.where(m,a,0).astype('float32');mf=m.astype('float32')
 for y in range(0,len(rv),128):
  rr=rv[y:y+128,None];xx=(CX+rr*np.cos(th)).astype('float32');yy=(CY+rr*np.sin(th)).astype('float32')
  v=cv2.remap(af,xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);w=cv2.remap(mf,xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
  p[y:y+128]=np.where(w>1e-6,v/np.maximum(w,1e-20),np.nan)
 filt=np.empty_like(p)
 with warnings.catch_warnings():
  warnings.simplefilter('ignore',RuntimeWarning)
  for y in range(0,len(rv),32):
   padded=np.pad(p[y:y+32],((0,0),(30,30)),mode='wrap');windows=np.lib.stride_tricks.sliding_window_view(padded,61,axis=1)
   filt[y:y+32]=np.nanmedian(windows,axis=-1)
 # Interpolate the numerator and observed validity together, never a zero-valued absent sector.
 wp=np.isfinite(filt);numer=back(np.where(wp,filt,0),rv);den=back(wp.astype('float32'),rv);ff=numer/np.maximum(den,1e-20)
 missing=m&(den<=0)
 if missing.any():
  # Isolated samples missed by the integration grid: evaluate the SAME angular
  # median directly at their native coordinates. This is quadrature refinement,
  # not invented sky, an image patch, or a change to the physical support.
  iy,ix=np.where(missing);rr=r[iy,ix];tt=np.arctan2(iy-CY,ix-CX);angles=tt[:,None]+np.deg2rad(np.arange(-15,15.01,.5))[None,:]
  xx=(CX+rr[:,None]*np.cos(angles)).astype('float32');yy=(CY+rr[:,None]*np.sin(angles)).astype('float32')
  v=cv2.remap(af,xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);w=cv2.remap(mf,xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
  direct=np.nanmedian(np.where(w>1e-6,v/np.maximum(w,1e-20),np.nan),axis=1);assert np.isfinite(direct).all();ff[iy,ix]=direct
  savejson(D/'receipts/SWAP_domain.json',{'native_quadrature_refinement_pixels':len(ix),'undefined_observed_pixels':0,'status':'full observed support'})
 ff=ng(ff,m,4);t0=float(np.median(ff[m]));out=a/np.maximum(ff+t0,1e-20)**.75
 save_output('P09_SWAP_pilot',out,m,{'paper':'Seaton et al.2023, off-limb recipe','angular_median_halfwidth_degrees':15,'polar_angle_nodes':720,'polar_dr_px':1,'filter_gaussian_sigma_px':4,'c0':.75,'t0':t0,'t0_definition':'median of F over actual observed support, intensity-unit aware','display':'global affine only, no optional fourth-root display','status':'EUV-to-white-light transfer pilot; author warns visible-light results can be poor','fill_missing_sectors':False})
def main():
 a,m=readbase();fnrgf(a,m);gc.collect();swap(a,m)
if __name__=='__main__':main()
