from common58 import *
import sys,copy,gc
from psd_tools import PSDImage
from psd_tools.psd.layer_and_mask import ChannelInfo,ChannelData
from psd_tools.constants import Compression,Tag,Resource
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
claim();prep=json.loads((O/'G0_prepared_layers.json').read_text());assert (O/'E6_fixed_radius_filters.json').exists();s=PSDImage.open(O/'V57_Pere_input.psb');C=O/'prepared_layers';F=O/'filters';expected={};edits={}
def put(l,c,a):
 idx=next(i for i,x in enumerate(l._record.channel_info) if int(x.id)==c);cd=ChannelData(Compression.ZIP);h,w=a.shape;cd.set_data(np.ascontiguousarray(a).astype('>u2').tobytes(),w,h,16,2);l._channels[idx]=cd;l._record.channel_info[idx].length=len(cd.data)+2;return hashlib.sha256(a.astype('>u2').tobytes()).hexdigest()
for key,p in prep.items():
 if not key.isdigit():continue
 i=int(key);l=s[i];bb=p['bbox'];l._record.left,l._record.top,l._record.right,l._record.bottom=bb;md=l._record.mask_data
 if md:md.left,md.top,md.right,md.bottom=bb
 for row in p['channels']:
  c=row['channel'];a=np.load(C/f'L{i:02d}_C{c}.npy',mmap_mode='r');expected[f'{i}:{c}']=put(l,c,a)
 l.name=l.name+' · alineada V58';edits[str(i)]=p;print('replaced alignment',i,flush=True)
fm={11:'P01_NRGF',12:'P01_NRGF_extrap',13:'P02_RHEF',14:'P02b_RHEF_ups0.35',15:'P02c_RHEF_local60_native',16:'P02d_RHEF_local30_native',17:'03',18:'03v30',19:'07',20:'01',21:'04',22:'05',23:'06',24:'P03_MGN',25:'P04_WOW',26:'P05_WOW_bilateral'}
moon=roi(29,-2);physical=65535-moon;support=np.load(O/'sources/support.npy')
for i,tag in fm.items():
 l=s[i];a=np.load(F/f'{tag}_u16.npy',mmap_mode='r');expected[f'{i}:0']=put(l,0,a)
 # All filter channels are the same grayscale raster; share immutable compressed bytes.
 j=next(j for j,q in enumerate(l._record.channel_info) if int(q.id)==0)
 for c in [1,2]:
  k=next(k for k,q in enumerate(l._record.channel_info) if int(q.id)==c);l._channels[k]=copy.copy(l._channels[j]);l._record.channel_info[k].length=l._record.channel_info[j].length;expected[f'{i}:{c}']=expected[f'{i}:0']
 mask=chan(l,-2).copy();md=l._record.mask_data;assert (md.left,md.top,md.right,md.bottom)==(0,0,10551,7506);mask[2777:4777,4377:6377]=physical
 sup=np.load(F/f'{tag}_support.npy') if (F/f'{tag}_support.npy').exists() else np.load(F/'angular_support.npy') if i in [17,18,19] else support
 mask[~sup]=0;expected[f'{i}:-2']=put(l,-2,mask);l.name=l.name.replace('V42','V58')+' · sense estrelles';edits[str(i)]=dict(filter=tag,mask='native physical lunar occlusion plus real operator support',source='D4 sources; Vixen nondetections restored D4b');print('replaced filter',i,tag,flush=True);del mask,sup;gc.collect()
# Complete view; every alternative remains editable. Preserve Earthshine and source layers byte for byte.
s[9].visible=True;s[14].visible=True;s[14].opacity=89
for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
 if tag in s._record.layer_and_mask_information.tagged_blocks:s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
finalize_lr16(s);s._updated=False;p=O/'V58_work.psb';assert not p.exists()
with p.open('xb') as f:s.save(f)
save('G1_assembly.json',dict(path=str(p),layers=len(s),size=s.size,depth=s.depth,edited_channel_raw_sha256=expected,edits=edits,identity_channels_preserved=[0,7,8,9,29],presentation_changes={'9':{'visible':True},'14':{'visible':True,'opacity':89}},pending='Native rebuild of prominence composite10 from aligned12+11+10+09; native merged cache and final readback required'))
print('ASSEMBLED',p,p.stat().st_size,flush=True)
