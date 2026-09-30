from common58 import *
import sys,copy,gc,tifffile as tf
from psd_tools import PSDImage
from psd_tools.psd.layer_and_mask import ChannelData,ChannelInfo
from psd_tools.psd.image_data import ImageData
from psd_tools.constants import Compression,Tag
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
claim();s=PSDImage.open(O/'V58_overlap_work.psb');q=tf.imread(O/'V58O_solar_composite_native.tif');assert q.shape==(7506,10551,4) and q.dtype==np.uint16;l=s[10];assert len(l._record.channel_info)==4 and l._record.mask_data is None
l._record.left,l._record.top,l._record.right,l._record.bottom=0,0,10551,7506;l.name='09 Compost de perles i protuberàncies · alineat V58';expected=json.loads((O/'G4_overlap_correction.json').read_text())['edited_channel_raw_sha256']
for i,ci in enumerate(l._record.channel_info):
 c=int(ci.id);a=q[...,3 if c==-1 else c];cd=ChannelData(Compression.ZIP);cd.set_data(np.ascontiguousarray(a).astype('>u2').tobytes(),10551,7506,16,2);l._channels[i]=cd;ci.length=len(cd.data)+2;expected[f'10:{c}']=hashlib.sha256(a.astype('>u2').tobytes()).hexdigest()
del q;gc.collect();finalize_lr16(s);a=tf.imread(O/'V58O_default_native.tif');assert a.shape==(7506,10551,3) and a.dtype==np.uint16;im=ImageData(compression=Compression.RAW);im.set_data([np.ascontiguousarray(a[...,i]).astype('>u2').tobytes() for i in range(3)],s._record.header);s._record.image_data=im;s._updated=False;p=O/'V58.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
save('G6_package.json',dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,size=s.size,depth=s.depth,layers=len(s),edited_channel_raw_sha256=expected,composite10='Native Photoshop merge of aligned12,11,10,09 with corrected11mask; preserves separate source layers',source_sha256=json.loads((O/'A0_freeze.json').read_text())['sha256'],cached_merge='V58O_default_native.tif native Photoshop, composite10 hidden'))
print('PACKAGED',p,flush=True)
