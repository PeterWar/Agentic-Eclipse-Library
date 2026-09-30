from common import *
import ast,sys,importlib.util,gc
from scipy.ndimage import map_coordinates
from local_filters import mgn
from wow_filters import wow,conv
from watroo import B3spline
from watroo.wavelets import convolution
from watroo.utils import wow as author_wow
def fit_receipt():
 rr=np.linspace(2,3.5,121)[:,None];th=np.arange(720)[None,:]*2*np.pi/720;shape=(121,720)
 xy=np.array([np.broadcast_to(CY+rr*RS*np.sin(th),shape),np.broadcast_to(CX+rr*RS*np.cos(th),shape)])
 def sample(p,channel=None,order=1):
  a=np.load(p,mmap_mode='r');a=a[...,channel] if channel is not None else a
  return map_coordinates(a,xy,order=order,prefilter=False)
 v=sample(FIX/'vixen_corrected_G.npy');s=sample(FIX/'sony_corrected_G.npy');good=np.isfinite(v)&np.isfinite(s)&(v>0)&(s>0)
 for tag in ['vixen','sony']:good&=sample(OLD/(tag+'_support.npy'),order=0)>0
 for tag in ['vixen_total','sony_corrected_total']:
  z=sample(OLD/(tag+'.npy'),1);good&=np.isfinite(z)&(z>0)
 good&=np.hypot(xy[1]-4878.66472396041,xy[0]-2549.206007534177)>240
 sectors=np.broadcast_to(np.arange(720)[None,:]//60,shape);fit=good&(sectors%2==0);hold=good&~fit
 gain=float(np.exp(np.median(np.log(v/s)[fit])));assert gain==0.3411462604999542
 e=100*(s*gain/v-1);rb=np.broadcast_to(rr,shape);rows=[]
 for lo,hi in [(2,2.3),(2.3,2.65),(2.65,3),(3,3.5),(2,3.5)]:
  z=e[hold&(rb>=lo)&(rb<=hi)];rows.append({'radii_R':[lo,hi],'median_bias_pct':float(np.median(z)),'median_absolute_error_pct':float(np.median(np.abs(z))),'n':len(z)})
 savejson(D/'receipts/base_fit_holdout.json',{'gain':gain,'fit_n':int(fit.sum()),'holdout_n':int(hold.sum()),'sampling':'121 radii2..3.5R x720angles, bilinear, alternating30deg sectors','ghost_excluded_from_fit_only':[4878.66472396041,2549.206007534177,240],'validation':rows})
def reference_tests():
 rng=np.random.default_rng(314159);y,x=np.mgrid[:96,:128];pattern=.6*np.sin(2*np.pi*x/24)+.3*np.cos(2*np.pi*y/35)+rng.normal(0,.1,x.shape);m=np.ones(x.shape,bool);rows=[]
 for pedestal in [2,1000]:
  a=(pattern+pedestal).astype('float32')
  for bi in [False,True]:
   z=wow(a,m,4,bi,False);ref,_=author_wow(a.astype('float64'),n_scales=4,bilateral=1 if bi else None,h=0,denoise_coefficients=[])
   z=z-z.mean();ref=ref-ref.mean();err=float(np.sqrt(np.mean((z-ref)**2))/np.std(ref));corr=float(np.corrcoef(z.ravel(),ref.ravel())[0,1]);assert err<.005
   rows.append({'pedestal':pedestal,'bilateral':bi,'relative_RMS':err,'correlation':corr})
 for s in [0,3,7]:
  a=rng.normal(size=x.shape).astype('float32');assert np.max(np.abs(conv(a,s)-convolution(a,B3spline(2),s)))<1e-6
 null=[]
 for val in [.3,1.,1000.]:
  a=np.full(x.shape,val,np.float32);mask=np.ones_like(a,bool);mask[20:50,40:65]=False;a[~mask]=np.nan
  for bi in [False,True]:
   out=wow(a,mask,4,bi,False);err=float(np.max(np.abs(out[mask])));assert err==0;null.append({'value':val,'bilateral':bi,'max_abs':err})
  out=mgn(a,mask);assert np.isfinite(out[mask]).all() and np.max(np.abs(out[mask]))==0
 savejson(D/'receipts/local_reference_QA.json',{'PASS':True,'WOW_reference':rows,'constant_with_missing_support':null,'numerical_tolerances':'wave residual8eps32; coarse plane16eps32; constant response defined as0','scope':'algorithm reference and arithmetic, not a claim of artifact-free corona'})
def quadrature():
 a,m=readbase();points=[(5663,2948),(5814,2534),(5965,2120),(5132,5077),(5056,5511),(5362,3200),(6000,3776),(4700,3776)];rows=[]
 for sig,tag in [(16,'P07_ACHF_precursor16'),(32,'P08_ACHF_precursor32')]:
  result=np.load(C/(tag+'_float.npy'),mmap_mode='r')
  for x,y in points:
   rr=np.hypot(x-CX,y-CY);tt=np.arctan2(y-CY,x-CX);means=[]
   for step in [1.,.5,.25]:
    uv=np.arange(-2*sig,2*sig+step/2,step);u,v=np.meshgrid(uv,uv,indexing='ij');rho=rr+u;theta=tt+v/rr;xx=(CX+rho*np.cos(theta)).astype('float32');yy=(CY+rho*np.sin(theta)).astype('float32')
    vals=cv2.remap(np.asarray(a),xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);weights=cv2.remap(m.astype('float32'),xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    ker=np.exp(-(u*u+v*v)/(2*sig*sig));means.append(float(np.sum(vals*ker)/np.sum(weights*ker)))
   actual=float(a[y,x]-result[y,x]);relative=abs(actual-means[-1])/abs(means[-1]);assert relative<.003,(tag,x,y,relative)
   rows.append({'tag':tag,'xy':[x,y],'direct_means_steps_1_half_quarter':means,'production_mean':actual,'relative_error_to_quarter':relative})
 savejson(D/'receipts/ACHF_quadrature_QA.json',{'PASS':True,'tolerance_relative_blurred_mean':.003,'rows':rows,'scope':'integration fidelity at fixed points; radial envelope response is not suppressed'})
def external_judge():
 fixed=np.load(OLD/'vixen_total.npy',mmap_mode='r')[...,1];mv=np.load(OLD/'vixen_support.npy');a,m=readbase();rows=[]
 for p in sorted(C.glob('P*_float.npy')):
  out=np.load(p,mmap_mode='r')
  for x,y in [(5890,2326),(5089,5294),(5965,2120),(5056,5511)]:
   sl=(slice(y-384,y+384),slice(x-384,x+384));good=m[sl]&mv[sl];assert good.all();b=np.asarray(fixed[sl]);cand=np.asarray(out[sl]);src=np.asarray(a[sl]);core=np.s_[256:512,256:512]
   for s1,s2 in [(2,8),(8,32),(32,64)]:
    def band(z):return (gaussian(z,s1)-gaussian(z,s2))[core].ravel()
    j=band(b);z=band(cand);s=band(src);corr=float(np.corrcoef(j,z)[0,1]);baseline=float(np.corrcoef(j,s)[0,1]);rows.append({'tag':p.stem,'xy':[x,y],'band_sigma_px':[s1,s2],'correlation_fixed_Vixen':corr,'base_correlation_fixed_Vixen':baseline,'output_RMS':float(np.std(z))})
 savejson(D/'receipts/external_judge.json',{'fixed_judge':'original uncorrected Vixen G total, no adjustment to outputs','ROIs':'core256; centers3.5/4R, beyond Vixen-to-Sony blend; Sony source independent of Vixen','rows':rows,'conclusion':'correlation reported, no assertion that all outer detail is coronal; no artifact-free PASS from H1'})
def main():
 fit_receipt();reference_tests();quadrature();external_judge();log('science QA recorded')
if __name__=='__main__':main()
