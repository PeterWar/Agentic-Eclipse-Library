"""Declare a separate filter-computation domain using the existing lunar photo mask.
Photometric source arrays and physical support remain intact and available.
"""
from a4_sources import *
import subprocess

def clone(src,dst):
 subprocess.run(['/bin/cp','-c',str(src),str(dst)],check=True)

def main():
 base=O/'d4_baseline/products/sources';out=O/'domain_v1';out.mkdir();(out/'sources').mkdir();(out/'s4').mkdir();(out/'train_supports').mkdir();lunar=np.load(O/'current_lunar_support.npz');m=lunar['support'];x0,y0,x1,y1=lunar['box'];sl=(slice(y0,y1),slice(x0,x1));rows={}
 for name in ['base_G.npy','fusion_starless.npy','vixen_starless.npy','sony_starless.npy']:
  clone(base/name,out/'sources'/name);rows[name]={'sha256':sha(out/'sources'/name),'unchanged_photometric_source':True};assert rows[name]['sha256']==sha(base/name)
 for name,src,dst in [('physical',base/'support.npy',out/'sources/support.npy'),('vixen',O/'sources_v29/vixen_support.npy',out/'train_supports/vixen_support.npy'),('sony',O/'sources_v29/sony_support.npy',out/'train_supports/sony_support.npy')]:
  old=np.load(src);new=old.copy();new[sl]&=~m;assert np.array_equal(new[sl][~m],old[sl][~m]);np.save(dst,new);rows[name]={'physical_source':str(src.relative_to(R)),'physical_sha256':sha(src),'operator_sha256':sha(dst),'excluded_under_existing_lunar_photo':int(np.count_nonzero(old^new))};del old,new
 npz=O/'s4_baseline/cau/s4_recomposicio_box.npz';clone(npz,out/'s4'/npz.name);z=np.load(npz);sy0,sy1,sx0,sx1=z['box'];sm=np.load(O/'s4_baseline/cau/s4_support_new_box.npy');sm&=~m[sy0-y0:sy1-y0,sx0-x0:sx1-x0];np.save(out/'s4/s4_support_new_box.npy',sm)
 save(out/'MANIFEST.json',{'purpose':'Filter-computation domain excludes the same full lunar photo already excluded by all V84 output masks','physical_support':str((base/'support.npy').relative_to(R)),'physical_radiance_arrays_unchanged':True,'new_output_radius_or_margin':False,'lunar_mask_source':'all positive existing layer30 mask pixels, interior holes filled; exact V84 exclusion','lunar_mask_pixels':int(m.sum()),'sources':rows,'status':'candidate boundary ablation; not promoted','scientific_limit':'Pixels under the final lunar photo can be physically observed corona at other times; they are retained in sources but excluded from this presentation-filter domain.'})
 print('DOMAIN_READY',flush=True)

if __name__=='__main__':guard();main()
