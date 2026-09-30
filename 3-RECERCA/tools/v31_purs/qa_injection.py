from common import *
from local_filters import mgn
from wow_filters import wow
from nafe_filter import lib,ref
def nafe(a,m,limit):
 a=np.ascontiguousarray(np.maximum(a,0),np.float32);mm=m.astype('uint8');k=np.ascontiguousarray(ref.membership_function(65),np.float64);out=np.empty_like(a)
 lib.nafe_full(a.ctypes.data,mm.ctypes.data,*a.shape,65,k.ctypes.data,5.,4,out.ctypes.data)
 return .2*(a/limit)**(1/2.4)+.8*out
def main():
 base,_=readbase();a=np.array(base[2326-256:2326+256,5890-256:5890+256]);m=np.ones(a.shape,bool);y,x=np.mgrid[:512,:512]
 rng=np.random.default_rng(982471);centers=rng.integers(130,380,size=(3,2));sigmas=[2,8,24];inj=np.zeros_like(a);amp=.01*float(np.median(a))
 for (cy,cx),s in zip(centers,sigmas):inj+=amp*np.exp(-((x-cx)**2+(y-cy)**2)/(2*s*s))
 rows=[]
 limit=float(base.max())
 for name,fn in [('MGN',lambda b:mgn(b,m,limits=[0,limit])),('WOW',lambda b:wow(b,m,6,False,False)),('WOW bilateral',lambda b:wow(b,m,6,True,False)),('NAFE',lambda b:nafe(b,m,limit))]:
  d=fn(a+inj)-fn(a)
  for (cy,cx),s in zip(centers,sigmas):
   rr=(x-cx)**2+(y-cy)**2;good=rr<max(8,3*s)**2;response=float(np.sum(d[good]*inj[good])/np.sum(inj[good]**2));assert response>0
   roi=np.where(good,d,-np.inf);iy,ix=np.unravel_index(np.argmax(roi),roi.shape)
   rows.append({'method':name,'injection_sigma_px':s,'center_xy':[int(cx),int(cy)],'matched_response':response,'strongest_positive_response_shift_px':float(np.hypot(ix-cx,iy-cy))})
 savejson(D/'receipts/injection.json',{'PASS_positive_matched_response':True,'seed':982471,'source_native_roi_origin_xy':[5890-256,2326-256],'amplitude_base_units':amp,'rows':rows,'scope':'fixed unfitted synthetic probes survive each local operator; does not certify every real outer feature or all PSF/noise scales'})
 log('injection QA saved')
if __name__=='__main__':main()
