"""Independent polynomial mean, hidden-value invariance and white-noise diagnostics."""
from a62_moment_operator import *
from scipy.ndimage import distance_transform_edt

def main():
 engine=MomentGaussian();m=engine.m;iy,ix=np.mgrid[:2800,:2800];x=(ix-1400)/1000.;y=(iy-1400)/1000.;poly=2+.4*x-.2*y+.13*x*x-.07*x*y+.08*y*y;noise=np.random.default_rng(2026092202).normal(size=m.shape).astype(np.float32);layers={'01':[2,4,8,16,32],'04':[1,2,4,8,16],'05':[2,4,8,16,32,48],'06':[4,8,16,32,64]};actual={k:np.zeros(m.shape,float) for k in layers};oracle={k:np.zeros(m.shape,float) for k in layers};rows=[]
 for s in SIGMAS:
  result=engine.smooth_roi(poly,s);(yy,xx),alpha=engine.cache[s];kk,rad=kernels(s);mu2=kk[2].sum();expected=poly[yy,xx]+(.13+.08)*s*s*mu2/1e6;err=float(np.max(abs(result[yy,xx]-expected)));assert err<1e-9,(s,err)
  hidden=[]
  if s in [1,64]:
   for value in [np.nan,1e20]:
    altered=np.where(m,poly,value);q=engine.smooth_roi(altered,s);delta=float(np.max(abs(q[m]-result[m])));assert delta==0,(s,value,delta);hidden.append({'hidden_value':'NaN' if np.isnan(value) else value,'max_difference_observed':delta})
  ref=cv2.GaussianBlur(noise,(0,0),s,borderType=cv2.BORDER_REFLECT_101);smooth=engine.smooth_roi(noise,s,ref);untouched=m.copy();untouched[yy,xx]=False;assert np.array_equal(smooth[untouched],ref[untouched]);d=noise-smooth;d0=noise-ref
  for k,scales in layers.items():
   if s in scales:actual[k]+=d/len(scales);oracle[k]+=d0/len(scales)
  rows.append({'sigma':s,'quadratic_mean_max_error':err,'hidden_invariance':hidden,'complete_stencil_control_exact':True});print('MOMENT_NULL',s,err,flush=True)
 distance=distance_transform_edt(m);bands=[(0,2),(2,4),(4,8),(8,16),(16,32),(32,64),(64,128),(128,256),(256,512)];noise_rows=[]
 for k in layers:
  for lo,hi in bands:
   mm=m&(distance>lo)&(distance<=hi);a=actual[k][mm];b=oracle[k][mm];noise_rows.append({'tag':k,'distance':[lo,hi],'n':int(mm.sum()),'SD_new':float(np.std(a)),'SD_full_gaussian':float(np.std(b)),'SD_ratio':float(np.std(a)/np.std(b)),'bias_new':float(a.mean()),'difference_rms':float(np.sqrt(np.mean((a-b)**2)))})
 save(O/'moment_E3_R02/NULL_QA.json',{'PASS':True,'rows':rows,'interpretation':'polynomial exactness, hidden-value invariance and ordinary complete stencil control; not sciencePASS'});save(O/'moment_E3_R02/WHITE_NOISE_QA.json',{'seed':2026092202,'rows':noise_rows,'scope':'one fixed unit white-noise realization, E3 scale combination before profile normalization/median RGB/display/SN/H1; not calibrated RAW noise or independent pixel significance','scientific_PASS':None});print('MOMENT_NULLS_COMPLETE',flush=True)
if __name__=='__main__':guard();main()
