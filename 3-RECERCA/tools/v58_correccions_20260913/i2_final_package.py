from common58 import *
from psd_tools import PSDImage
from psd_tools.psd.image_data import ImageData
from psd_tools.constants import Compression
import tifffile as tf
claim();assert (O/'I1_NRGF_native_QA.json').exists();s=PSDImage.open(O/'V58_reviewed_work.psb');a=tf.imread(O/'V58E_default_native.tif');assert a.shape==(7506,10551,3)
for i in range(11,27):assert not s[i]._record.mask_data.flags.mask_disabled
assert not s[11].visible and not s[12].visible
im=ImageData(Compression.RAW);im.set_data([np.ascontiguousarray(a[...,i]).astype('>u2').tobytes() for i in range(3)]+[np.full((7506,10551),65535,dtype='>u2').tobytes()],s._record.header);s._record.image_data=im;s._updated=False;p=O/'V58_ready.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
save('I2_package.json',dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,layers=len(s),size=s.size,depth=s.depth,merged_channels=4,profile='Adobe RGB (1998)',all_filter_masks_enabled=True,expected_channels=json.loads((O/'I0_NRGF_protection.json').read_text())['expected_channels']));print('FINAL_READY',flush=True)
