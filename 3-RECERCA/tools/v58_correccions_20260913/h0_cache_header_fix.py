from common58 import *
from psd_tools import PSDImage
from psd_tools.psd.image_data import ImageData
from psd_tools.constants import Compression,Tag
import tifffile as tf
claim();s=PSDImage.open(O/'V58_protected_work.psb');a=tf.imread(O/'V58O_default_native.tif');assert s._record.header.channels==4 and a.shape==(7506,10551,3);im=ImageData(Compression.RAW);im.set_data([np.ascontiguousarray(a[...,i]).astype('>u2').tobytes() for i in range(3)]+[np.full((7506,10551),65535,dtype='>u2').tobytes()],s._record.header);s._record.image_data=im;s._updated=False;p=O/'V58_protected_fixed_work.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
save('H0_cache_header_fix.json',dict(path=str(p),source_merged_channels=4,native_default_tiff_channels=3,issue='User-savedV57 had merged transparency and4header channels. G6 temporary cached merge had only3planes. Photoshop rejected this mismatch; all layers had independently passed pixel decoding.',fix='Supply RGB plus opaque merged alpha, matching actual complete native view. Native recomposition still required.',layer_count=s._record.layer_and_mask_information.tagged_blocks.get_data(Tag.LAYER_16).layer_count))
print('FIXED',flush=True)
