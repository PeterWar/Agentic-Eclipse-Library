from pathlib import Path
import numpy as np,json,tifffile as tf
R=Path.cwd();O=R/'output/v68_artefactes_20260914'
a=tf.imread(O/'D5_full_native.tif');b=tf.imread(O/'E3_final_readback.tif');assert a.shape==b.shape==(7506,10551,4)
mx=0;different=0
for y in range(0,7506,256):
 d=abs(a[y:y+256].astype('int32')-b[y:y+256]);mx=max(mx,int(d.max()));different+=int(np.any(d,-1).sum())
r=dict(PASS=mx<=4,max_DN16=mx,pixels_different=different,full_canvas=True,forced_recomposition=True,source=str(O/'D5_full_native.tif'),readback=str(O/'E3_final_readback.tif'))
(O/'E4_readback.json').write_text(json.dumps(r,indent=2)+'\n');assert r['PASS'];print(r,flush=True)
