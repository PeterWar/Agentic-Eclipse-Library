from pathlib import Path
import sys,json,gc,shutil,hashlib,numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Compression,Tag,Resource
from psd_tools.psd.layer_and_mask import ChannelData
R=Path.cwd();O=R/'output/v62_prominencies_20260913';A=O/'arrays'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan,sha
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V62_V61_PROMINENCES_20260913'
s=PSDImage.open(O/'V61_Pere_input.psb');rows=list(s);so=rows[19];assert so.kind=='smartobject' and len(s)==24
dst=O/'V61_Pere_SO_input.psb';assert not dst.exists()
with so.smart_object.open() as f,dst.open('xb') as g:shutil.copyfileobj(f,g,8*1024*1024)
def put(l,c,a):
 i=next(i for i,q in enumerate(l._record.channel_info) if int(q.id)==c);h,w=a.shape;cd=ChannelData(Compression.ZIP);cd.set_data(a.astype('>u2').tobytes(),w,h,16,2);l._channels[i]=cd;l._record.channel_info[i].length=len(cd.data)+2
new=np.load(A/'C1_base_RGB16.npy');b=rows[2]
for c in range(3):
 a=chan(b,c).copy();a[2777-b.top:4777-b.top,4377-b.left:6377-b.left]=new[...,c];put(b,c,a);del a
b.name='00 Base corba · color coronal sense difusió vermella · V62'
a=chan(so,-2).copy();vals,cnt=np.unique(a,return_counts=True);floor=int(vals[np.argmax(cnt)]);assert floor==386,(floor,vals[:10]);an=np.rint(np.clip((a.astype('float32')-floor)/(65535-floor),0,1)*65535).astype('uint16');put(so,-2,an);np.save(A/'D0_user_mask_normalized.npy',an);del a,an
so.name='Interiors 06–12 · protuberàncies de Pere · V62';rows[23].name='Marques de Pere · V61';rows[23].visible=False
for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
 if tag in s._record.layer_and_mask_information.tagged_blocks:s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
finalize_lr16(s);s._updated=False;out=O/'V62_work.psb';assert not out.exists()
with out.open('xb') as f:s.save(f)
(O/'D0_stage.json').write_text(json.dumps(dict(root_layers=24,path=str(out),provisional_cache=True,source_embedded=str(dst),source_embedded_sha=sha(dst),source_transform=list(so.smart_object.transform_box),mask_pedestal_DN16=floor,unchanged_Moon_RGB_mask_geometry=True),indent=2));print('STAGED',flush=True)
