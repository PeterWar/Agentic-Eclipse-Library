"""Controlled padding-domain ablation: preserve every accepted physical sample.
Same D/T equations and parameters as selected V85; change only unknown mask.
No input source, output lunar mask or photometric weight is changed.
"""
from a24_biharmonic_boundary import *
from a29_screened_boundary import ScreenedBoundary

class PhysicalLunarBoundary(LunarBoundary):
 def __init__(self,out):
  z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=map(int,z['box']);self.sl=(slice(y0,y1),slice(x0,x1));physical=np.load(O/'d4_baseline/products/sources/support.npy',mmap_mode='r');base=np.load(O/'d4_baseline/products/sources/base_G.npy',mmap_mode='r');validity=(physical[self.sl]&np.isfinite(base[self.sl])&(base[self.sl]>0)) if self._validity is None else self._validity;self.mask=~np.asarray(validity);self.out=out;self.cache={};self.receipts=[];mask=self.mask;assert not np.any(mask&~z['support'])
  h,w=mask.shape;idx=np.full(mask.shape,-1,np.int32);idx[mask]=np.arange(mask.sum());iy,ix=np.where(mask);n=len(iy);rows=[np.arange(n)];cols=[np.arange(n)];values=[np.full(n,4.,np.float64)];self.outer=[];assert not(mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any())
  for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
   ny,nx=iy+dy,ix+dx;nb=idx[ny,nx];inside=nb>=0;rows.append(np.flatnonzero(inside));cols.append(nb[inside]);values.append(np.full(inside.sum(),-1.));self.outer.append((np.flatnonzero(~inside),ny[~inside],nx[~inside]))
  self.A=coo_matrix((np.concatenate(values),(np.concatenate(rows),np.concatenate(cols))),shape=(n,n)).tocsr();self.n=n
  save(out/'PHYSICAL_DOMAIN.json',{'physical_support_sha256':sha(O/'d4_baseline/products/sources/support.npy'),'unknown_pixels':self.n,'retained_physical_pixels_below_final_photo':int(np.sum(physical[self.sl]&z['support'])),'photographic_mask_used_for_output_only':True,'radiance_unchanged':True,'single_supported_G_zero':'G=0 at5770,3949 is already rejected by historical E2/E3 positive-input test; retained in physical source, handled as unknown for numerical padding','purpose':'controlled physical vs presentation-domain ablation; not a claim all historical support is photometrically clean'})

class PhysicalBiharmonic(BiharmonicBoundary,PhysicalLunarBoundary):
 def __init__(self,out,validity=None):
  self._validity=validity;super().__init__(out)
 def extend(self,result,source,m,r,nodes,profile,islog,method):
  assert np.array_equal(self.mask,~m[self.sl]),'Padding mask must match actual operator validity inside diagnostic box'
  return super().extend(result,source,m,r,nodes,profile,islog,method)
class PhysicalScreened(PhysicalBiharmonic):
 def __init__(self,out,validity=None):
  super().__init__(out,validity);self.A=self.A+self.laplace;self.outer2 += [(ids,yy,xx,-1.) for ids,yy,xx in self.outer];self.M=self.ml.aspreconditioner(cycle='V')
  save(out/'SCREENED_SOLVER.json',{'equation':'L^2+L','tension':1,'domain':'unknown physical pixels','preconditioner':'one fixed symmetric AMG V-cycle'})

def install_physical(ns,out,screened=False,validity=None):
 from functools import partial
 engine=install(ns,out,engine_class=partial(PhysicalScreened if screened else PhysicalBiharmonic,validity=validity));row=json.loads((out/'BOUNDARY_METHOD.json').read_text());row.update(method='same residual equation on unknown physical-support pixels inside lunar diagnostic box',unknown_mask='complement of unchanged baseline physical support, no final-photo exclusion',equation='L^2+L' if screened else 'L^2',tension=1 if screened else 0,retained_observed_pixels_under_photo=36581,source_correction=False)
 save(out/'BOUNDARY_METHOD.json',row);return engine

if __name__=='__main__':
 guard();out=O/'physical_boundary_R02';out.mkdir();save(out/'FROZEN_ABLATION.json',{'status':'declared before new filter/judge evaluation','change':'only use physical support and complement mask; same selected padding equation and parameters','E2':'MGN B+D; WOW standard A+D; WOW bilateral A+D','E3':'same selected screened L^2+L, unit tension','photometric_source':'same unchanged d4_baseline arrays','source_validity_limit':'physical support accepted historically, not automatically proven free of temporal limb contamination','comparison':'same operators on domain_v1 vs physical support; original output Moon mask unchanged','acceptance':'existing analytical transfer and marks/Brno scopes unchanged; no automatic PASS','deferred':'no fitted 1/3200 correction; fixed-pair radiance study remains diagnostic'})
 print('PHYSICAL_ABLATION_FROZEN')
