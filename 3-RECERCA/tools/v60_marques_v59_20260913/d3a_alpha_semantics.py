from common60 import *
from psd_tools import PSDImage
import tifffile as tf
claim();native=tf.imread(O/'V59_clean_native.tif');s=PSDImage.open(O/'V59_Pere_input.psb');data=s._record.image_data.get_data(s._record.header);a=native[...,3].astype(float)/65535
m=(a>.94)&(a<.999);m[2777:4777,4377:6377]&=np.load(O/'arrays/L30_C-1_roi.npy')==0;report={'partial_pixels':int(m.sum()),'comparisons':{}}
for c in range(3):
 v=np.frombuffer(data[c],dtype='>u2').reshape(a.shape)[m].astype(float)/65535;ref=native[...,c][m].astype(float)/65535;al=a[m]
 report['comparisons'][str(c)]={n:np.quantile(abs(v-q)*65535,[.5,.99,1]).tolist() for n,q in [('associated',ref),('unassociated',ref/al),('white_matte',ref+1-al)]}
report['alpha_cache_vs_native_max']=int(abs(np.frombuffer(data[3],dtype='>u2').reshape(a.shape).astype('int32')-native[...,3].astype('int32')).max());save('D3a_alpha_semantics.json',report);print(report)
