from common60 import *
import sys,gc,copy
from psd_tools import PSDImage
from psd_tools.constants import Compression,Tag,Resource
from psd_tools.psd.layer_and_mask import ChannelData
from psd_tools.psd.image_data import ImageData
import tifffile as tf
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
claim();p=O/'V60_work.psb';assert not p.exists();assert json.loads((O/'C3_frozen_controls.json').read_text())['PASS'];assert sha(SRC)==json.loads((O/'A0_freeze.json').read_text())['sha256']
s=PSDImage.open(O/'V59_Pere_input.psb');assert len(s)==31 and s.size==(10551,7506) and s.depth==16;exp={};edits={}
def put(l,c,a):
 i=next(i for i,q in enumerate(l._record.channel_info) if int(q.id)==c);cd=ChannelData(Compression.ZIP);h,w=a.shape;raw=a.astype('>u2').tobytes();cd.set_data(raw,w,h,16,2);l._channels[i]=cd;l._record.channel_info[i].length=len(cd.data)+2;return hashlib.sha256(raw).hexdigest()
for i in range(11,17):
 l=s[i];assert tuple(l.bbox)==(0,0,10551,7506)
 for c in [0,-2]:
  a=chan(l,c).copy();a[2777:4777,4377:6377]=np.load(O/'arrays'/f'C2_L{i:02d}_{"gray" if c==0 else "mask"}.npy');exp[f'{i}:{c}']=put(l,c,a);del a
  if c==0:
   j=next(j for j,q in enumerate(l._record.channel_info) if int(q.id)==0)
   for cc in [1,2]:
    k=next(k for k,q in enumerate(l._record.channel_info) if int(q.id)==cc);l._channels[k]=copy.copy(l._channels[j]);l._record.channel_info[k].length=l._record.channel_info[j].length;exp[f'{i}:{cc}']=exp[f'{i}:0']
 l.name=l.name.replace('V58','V60')+' · nivell continu al limbe';print('FILTER',i,flush=True)
l=s[29];md=l._record.mask_data;a=chan(l,-2).copy();a[2777-md.top:4777-md.top,4377-md.left:6377-md.left]=np.load(O/'arrays/B4_L29_mask.npy');exp['29:-2']=put(l,-2,a);del a;l.name=l.name+' · interior opac V60';s[30].visible=False
for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
 if tag in s._record.layer_and_mask_information.tagged_blocks:s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
finalize_lr16(s);a=tf.imread(O/'V59_clean_native.tif');a[2777:4777,4377:6377,:3]=np.rint(np.load(O/'arrays/C2_combined_candidate_model.npy')*65535).astype('uint16');assert s._record.header.channels==4
data=[np.ascontiguousarray(a[...,c].astype('>u2')).tobytes() for c in range(3)]+[np.full((7506,10551),65535,dtype='>u2').tobytes()];merged=ImageData(compression=Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;s._updated=False;del a,data;gc.collect()
with p.open('xb') as f:s.save(f)
save('D0_build.json',{'path':str(p),'source_sha256':sha(SRC),'expected_channels':exp,'layers':31,'changed_layers':[11,12,13,14,15,16,29],'marks_hidden':True,'profile':'Adobe RGB (1998)','provisional_cache':'Must replace with actual native Photoshop rendering before delivery','blue':'not modified; no easy validated source correction identified'});print('BUILT',p,p.stat().st_size,flush=True)
