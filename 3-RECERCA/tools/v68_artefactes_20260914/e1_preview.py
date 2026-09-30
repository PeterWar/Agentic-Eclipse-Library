from pathlib import Path
import numpy as np,tifffile as tf,json
from PIL import Image,ImageCms
R=Path.cwd();O=R/'output/v68_artefactes_20260914';V=O/'vistes'
assert (O/'V68_native.psb').exists(), 'native TIFF must be closed before reading'
q=tf.imread(O/'D5_full_native.tif');assert q.shape==(7506,10551,4)
with tf.TiffFile(O/'D5_full_native.tif') as t:assert int(t.pages[0].extrasamples[0])==1
def rgb(a):
 # Stored RGB has associated alpha; display over neutral dark grey without unpremultiplying.
 a=a.astype('float32')/65535;c=a[...,:3]+.1*(1-a[...,3:])
 return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(c,0,1)*255+.5)),ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc')),ImageCms.createProfile('sRGB'),outputMode='RGB')
rgb(q[::3,::3]).save(V/'V68_previsualitzacio.png')
rgb(q[2777:4777,4377:6377]).save(V/'V68_lluna_i_limbe.png')
print('PREVIEW COMPLETE',flush=True)
