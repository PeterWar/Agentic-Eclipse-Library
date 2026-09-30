from common58 import *
from psd_tools import PSDImage
from psd_tools.psd.image_data import ImageData
from psd_tools.constants import Compression
import tifffile as tf
claim();s=PSDImage.open(O/'V58_protected_fixed_work.psb');a=tf.imread(O/'V58P_default_native.tif');assert a.shape==(7506,10551,3);assert s._record.header.channels==4;im=ImageData(Compression.RAW);im.set_data([np.ascontiguousarray(a[...,i]).astype('>u2').tobytes() for i in range(3)]+[np.full((7506,10551),65535,dtype='>u2').tobytes()],s._record.header);s._record.image_data=im;s._updated=False;p=O/'V58_final.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
save('H2_final_package.json',dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,layers=len(s),size=s.size,depth=s.depth,merged_channels=4,merged_alpha='opaque; complete displayed photograph',expected_channels=json.loads((O/'G9_RHEF_protection.json').read_text())['edited_channel_raw_sha256']));print('FINAL_CACHE_WRITTEN',flush=True)
