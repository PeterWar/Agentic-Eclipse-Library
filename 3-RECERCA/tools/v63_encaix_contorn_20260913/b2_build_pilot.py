from pathlib import Path
import sys,json,numpy as np,gc
from psd_tools import PSDImage
from psd_tools.constants import Compression,Tag,Resource
from psd_tools.psd.layer_and_mask import ChannelData
R=Path.cwd();O=R/'output/v63_encaix_contorn_20260913';P=R/'output/v62_prominencies_20260913';A=P/'arrays'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V63_INNER_ALIGNMENT_LUNAR_CONTOUR_20260913'
s=PSDImage.open(O/'V62_input.psb');assert len(s)==24;layers={int(l._record.tagged_blocks.get_data(Tag.LAYER_ID)):l for l in s}
def putmask(l,roi):
 a=chan(l,-2).copy();md=l._record.mask_data;bb=(4377,2777,6377,4777);x0,y0=max(bb[0],md.left),max(bb[1],md.top);x1,y1=min(bb[2],md.right),min(bb[3],md.bottom)
 a[y0-md.top:y1-md.top,x0-md.left:x1-md.left]=roi[y0-bb[1]:y1-bb[1],x0-bb[0]:x1-bb[0]]
 i=next(i for i,c in enumerate(l._record.channel_info) if int(c.id)==-2);cd=ChannelData(Compression.ZIP);cd.set_data(a.astype('>u2').tobytes(),a.shape[1],a.shape[0],16,2);l._channels[i]=cd;l._record.channel_info[i].length=len(cd.data)+2
for i in range(3,9):
 putmask(layers[38+i],np.load(O/'arrays'/f'B0_L{i:02d}_mask.npy'));print('MASK',38+i,flush=True);gc.collect()
putmask(layers[3],np.load(O/'arrays/B1_base_validity_mask.npy'))
mm=np.load(A/'V61_L22_C-2.npy');old=np.load(R/'output/v61_interiors_limbe_20260913/arrays/V60_L29_C-2.npy');base=np.load(A/'C1_base_RGB16.npy');bad=(mm>0)&(mm<65535)&(~base.any(-1));assert bad.sum()==347 and np.all(old[bad]==65535)
new=mm.copy();new[bad]=old[bad];np.save(O/'arrays/B2_Moon_mask.npy',new);putmask(layers[30],new)
(O/'B2_moon_repair.json').write_text(json.dumps(dict(changed=347,all_pre_Pere_mask_opaque=True,source_RGB_missing_in_base=True,rule='Restore lunar opacity only where user edit revealed a pixel with no coronal source. These pixels were all opaque in the already validated lunar mask. Other user mask edits retained.',remaining_Pere_edits=int(np.count_nonzero(new!=old))),indent=2)+'\n')
for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
 if tag in s._record.layer_and_mask_information.tagged_blocks:s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
finalize_lr16(s);s._updated=False;p=O/'V63_pilot_serialized.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
print('PILOT SERIALIZED',flush=True)
