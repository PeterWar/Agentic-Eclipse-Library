"""Ablate binary S4 output splice with continuous, per-frame tier weights.
Only positive measured contributions are used. No output radius is discarded.
"""
from a11_limb_diagnostics import *
from scipy.ndimage import binary_dilation,binary_erosion

TIERS=[dict(curts=0.,mitjans=.5,llargs=1.5),dict(curts=-2.,mitjans=-.5,llargs=None),dict(curts=-4.,mitjans=None,llargs=None)];GT=[.02,4e-4,8e-6]

def main():
 src=O/'limb_frames'
 for p in [src,O/'s4_baseline']:assert json.loads((p/'COMPLETE.json').read_text())['PASS']
 out=O/'limb_recompose';out.mkdir();meta=json.loads((src/'METADATA.json').read_text());N=np.load(src/'numerator.npy',mmap_mode='r');Wg=np.load(src/'weight.npy',mmap_mode='r');Ds=np.load(src/'distance_model.npy',mmap_mode='r');tables=old_tables();b2=json.loads((H/'v38_limb_round1/cau/correccio_vora_lunar.json').read_text())['taula']
 shape=N.shape[1:];numO=np.zeros(shape,np.float32);denO=numO.copy();extraN={k:numO.copy() for k in ['full','t8','t12']};extraD={k:numO.copy() for k in extraN};extraW2={k:numO.copy() for k in extraN};dall=np.full(shape[:2],99,np.float32)
 for j,f in enumerate(meta['frames']):
  d=Ds[j];c=classe(f['exposure']);tb=b2[c];bo=np.interp(d,np.asarray(tb['d_px'],np.float32),np.asarray(tb['B_ln'],np.float32),left=tb['B_ln'][0],right=0).astype(np.float32);co=np.exp(-bo,dtype=np.float32);dd,bb=tables[c];bn=np.interp(d,dd,bb,right=0).astype(np.float32);cn=np.exp(-bn,dtype=np.float32);fl=np.clip((d-2)/2,0,1).astype(np.float32)
  numO+=N[j]*(fl*co)[...,None];denO+=Wg[j]*fl[...,None];wextra=np.zeros_like(d)
  for tier,g in zip(TIERS,GT):
   d0=tier[c]
   if d0 is not None:wextra+=g*np.clip(d-d0,0,1)/np.maximum(cn,1e-6)**2
  for key in extraN:
   if key=='full':tap=1.
   else:
    end=float(key[1:]);q=np.clip((d-2)/(end-2),0,1);tap=1-q*q*(3-2*q)
   w=wextra*tap;extraN[key]+=N[j]*(w*cn)[...,None];extraD[key]+=Wg[j]*w[...,None];extraW2[key]+=(Wg[j]*(fl+w)[...,None])**2
  dall=np.minimum(dall,np.where((Wg[j,...,1]>0)&((fl+wextra)>0),d,99))
  if j%10==0:print('RECOMPOSE',j+1,len(meta['frames']),flush=True)
 def rgb(num,den):
  cam=np.where(den>0,num/np.maximum(den,1e-20),np.nan);_,v=comu.lluminancia(cam,np.asarray(meta['matrix'],np.float32),meta['gain']);return v.astype(np.float32)
 arrays={'old':rgb(numO,denO),'den_old':denO,'min_contributing_D':dall}
 for key in extraN:
  den=denO+extraD[key];arrays[key]=rgb(numO+extraN[key],den);arrays['den_'+key]=den;arrays['neff_'+key]=den**2/np.maximum(extraW2[key],1e-30)
 np.savez(out/'STACKS.npz',**arrays,box=np.array(meta['box_y0y1x0x1']));
 y0,y1,x0,x1=meta['box_y0y1x0x1'];z=np.load(O/'s4_baseline/cau/s4_recomposicio_box.npz');sy0,sy1,sx0,sx1=z['box'];sl=(slice(sy0-y0,sy1-y0),slice(sx0-x0,sx1-x0));oldref=z['totO'];newref=z['totN'];good=np.all(np.isfinite(oldref)&(oldref>0)&np.isfinite(arrays['old'][sl])&(arrays['old'][sl]>0),-1)
 checks={}
 for key,ref in [('old',oldref),('full',newref)]:
  v=arrays[key][sl];vr=np.all(np.isfinite(ref)&(ref>0),-1);vv=np.all(np.isfinite(v)&(v>0),-1);g=vr&vv;rel=np.abs(v[g]/ref[g]-1);refden=z['denO' if key=='old' else 'denN'];dmask=np.all(arrays['den_old' if key=='old' else 'den_full'][sl]>0,-1);rdmask=np.all(refden>0,-1);checks[key]={'n':int(g.sum()),'relative_max':float(np.max(rel)),'p999':float(np.percentile(rel,99.9)),'median':float(np.median(rel)),'positive_RGB_support_difference':int(np.count_nonzero(vr^vv)),'denominator_support_difference':int(np.count_nonzero(dmask^rdmask))};assert np.percentile(rel,99.9)<5e-4 and np.array_equal(dmask,rdmask),checks
 oldsupport=np.load(O/'b3_baseline/cau/support_v42.npy',mmap_mode='r')[sy0:sy1,sx0:sx1];supN=np.load(O/'s4_baseline/cau/s4_support_new_box.npy');use=supN&((~oldsupport)|(z['Dmin']<6));common=good&supN
 boundary=(binary_dilation(use)^binary_erosion(use))&common
 delta=np.log(np.maximum(newref[...,1],1e-30)/np.maximum(oldref[...,1],1e-30));q=delta[boundary];checks['S4_same_coordinate_substitution']={'boundary_pixels':int(boundary.sum()),'median_abs_log_difference':float(np.median(np.abs(q))),'p95_abs_log_difference':float(np.percentile(np.abs(q),95)),'max_abs_log_difference':float(np.max(np.abs(q))),'meaning':'substitution-value difference on old splice boundary; not a one-sided spatial gradient'}
 for tag,path in [('vixen',O/'b2_vixen/cau/vixen_total_v38.npy'),('fusion',O/'b3_baseline/cau/fusion_total_v42.npy')]:
  pre=np.load(path,mmap_mode='r')[sy0:sy1,sx0:sx1,1];valid=boundary&np.isfinite(pre)&(pre>0);v=np.log(np.maximum(newref[...,1],1e-30)/np.maximum(pre,1e-30))[valid];checks[tag+'_realized_substitution']={'n':int(valid.sum()),'median_abs_log_difference':float(np.median(np.abs(v))),'p95_abs_log_difference':float(np.percentile(np.abs(v),95)),'meaning':'photometric sources before stellar subtraction; no claim of spatial-edge energy'}
 np.savez(out/'SPLICE_DIAG.npz',delta=delta,use=use,boundary=boundary,box=z['box']);save(out/'RECOMPOSE.json',{'formula':'B2 numerator/denominator plus historical linear S4 tiers times a C1 per-frame D taper, no Dmin output switch','tapers':{'t8':[2,8],'t12':[2,12]},'TIERS':TIERS,'GT':GT,'checks':checks,'limitations':'Conditional on historical radiance calibration and lunar response. This ablates source-splice only; filter boundary condition is separate.'});save(out/'COMPLETE.json',{'PASS':True,'arrays':sha(out/'STACKS.npz'),'verified_against':'S4 V51 linear-sum core, not later V52 median variant'})

if __name__=='__main__':guard();main()
