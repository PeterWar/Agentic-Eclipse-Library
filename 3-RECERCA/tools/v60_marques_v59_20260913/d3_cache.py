from common60 import *
from psd_tools import PSDImage
from psd_tools.psd.image_data import ImageData
from psd_tools.constants import Compression
import tifffile as tf
claim();s=PSDImage.open(O/'V60_work.psb');a=tf.imread(O/'V60_native.tif');assert a.shape==(7506,10551,4) and a.dtype==np.uint16
proof=json.loads((O/'D3a_alpha_semantics.json').read_text());assert all(v['white_matte'][-1]<3 for v in proof['comparisons'].values())
# Native Photoshop PSB stores its merged RGB against a white matte; TIFF exports associated alpha.
# D3a established this from the user's saved V59 away from the painted marks.
im=ImageData(Compression.RAW);im.set_data([np.clip(a[...,i].astype('int32')+65535-a[...,3],0,65535).astype('>u2').tobytes() for i in range(3)]+[a[...,3].astype('>u2').tobytes()],s._record.header);s._record.image_data=im;s._updated=False;p=O/'V60_ready.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
save('D3_cache.json',{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'native_RGB16':True,'merged_channels':4,'layers':len(s),'alpha':'Exact native alpha; white-matte merged RGB, proven against native V59 cache'});print('FINAL CACHE WRITTEN',flush=True)
