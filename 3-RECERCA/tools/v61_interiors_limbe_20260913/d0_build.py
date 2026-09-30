from common61 import *
import copy,gc
from psd_tools import PSDImage
from psd_tools.api.layers import Group
from psd_tools.constants import Compression,Tag,Resource,BlendMode
from psd_tools.psd.layer_and_mask import ChannelData
from psd_tools.psd.image_data import ImageData
import tifffile as tf
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
claim();p=O/'V61_work.psb';assert not p.exists();s=PSDImage.open(O/'V60_Pere_input.psb');v=PSDImage.open(V57);orig=list(s);expected={}
def put(l,c,a):
 i=next(i for i,q in enumerate(l._record.channel_info) if int(q.id)==c);cd=ChannelData(Compression.ZIP);h,w=a.shape;raw=a.astype('>u2').tobytes();cd.set_data(raw,w,h,16,2);l._channels[i]=cd;l._record.channel_info[i].length=len(cd.data)+2;return hashlib.sha256(raw).hexdigest()
for i in range(7):
 l=orig[i];l._record=copy.deepcopy(v[i]._record);l._channels=copy.deepcopy(v[i]._channels);l.name=v[i].name+' · encaix V57';l.visible=i<6
 expected[str(i)]={'source':'V57','all_channels_original':True,'bbox':v[i].bbox};print('RESTORED',i,flush=True)
# Remove only the old accidental mask islands inside the already fully occulted Moon.
l=orig[1];a=chan(l,-2).copy();md=l._record.mask_data;view=a[2777-md.top:4777-md.top,4377-md.left:6377-md.left];moon=np.load(O/'arrays/V60_L29_C-2.npy');hit=(moon==65535)&(view>0);view[hit]=0;expected['1']['mask_changed_inside_opaque_moon']=int(hit.sum());expected['1']['mask_sha256']=put(l,-2,a);del a
for i in range(11,17):
 l=orig[i];a=chan(l,-2).copy();md=l._record.mask_data;a[2777-md.top:4777-md.top,4377-md.left:6377-md.left]=np.load(O/'arrays'/f'B1_L{i:02d}_mask.npy');expected[str(i)]={'mask_sha256':put(l,-2,a)};l.name=l.name.replace('V60','V61');del a;print('SINGLE COVERAGE',i,flush=True)
del v;gc.collect()
orig[10].visible=False;orig[10].name='09 Compost anterior V58 · comparació (ocult)'
orig[29].visible=True
orig[30].visible=False;orig[30].name='Marques blaves de Pere · V60'
orig[31].visible=False;orig[31].name='Marques de Pere · V59'
group=Group.new(s,'Interiors 06–12 · encaix original V57',open_folder=True);group.blend_mode=BlendMode.NORMAL
for l in orig[:7]:group.append(l)
# Place above the corona filters and below references / Earthshine. Editable and hidden by default.
s.remove(group);s.insert(list(s).index(orig[27]),group);group.visible=False
for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
 if tag in s._record.layer_and_mask_information.tagged_blocks:s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
finalize_lr16(s);s._updated=False
# Provisional native cache: refreshed from Photoshop before publication.
a=tf.imread(O/'V60_clean.tif');assert s._record.header.channels in [3,4]
if a.shape[2]==3 and s._record.header.channels==4:a=np.dstack([a,np.full(a.shape[:2],65535,np.uint16)])
data=[np.ascontiguousarray(a[...,c].astype('>u2')).tobytes() for c in range(s._record.header.channels)];merged=ImageData(compression=Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;del a,data;gc.collect()
with p.open('xb') as f:s.save(f)
save('D0_build.json',{'path':str(p),'pixel_layers':32,'top_level_layers':len(s),'restored':expected,'group':'Interiors 06–12 · encaix original V57','group_visible':False,'default_interiors':[12,11,10,9,8,7],'source_compound10_hidden_due_to_superseded_interiors':True,'earthshine_visible':True,'all_original_annotations_preserved':True,'provisional_cache':True});print('BUILT',p.stat().st_size,flush=True)
