from common61 import *
import tifffile as tf
claim();a=tf.imread(O/'V61_saved_readback.tif');b=tf.imread(O/'V61_final_readback.tif');assert a.shape==b.shape;diff=abs(a.astype('int32')-b.astype('int32'));mx=int(diff.max());assert mx<=3,mx
save('E2_final_readback.json',{'shape':a.shape,'max_DN16':mx,'p99_DN16':float(np.quantile(diff,.99)),'PASS':True,'scope':'saved native file compared with independently reopened published file, forced recomposition on an owned duplicate'});print('READBACK',mx)
