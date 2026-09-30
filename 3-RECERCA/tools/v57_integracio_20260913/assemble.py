from pathlib import Path
import json, hashlib, copy, gc, sys
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Tag, Resource
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026')
OUT=ROOT/'output/v57_integracio_20260913'
CLAIM='CODEX_CAPES_TOTALS_V57_20260913'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
sys.path.insert(0,str(ROOT/'research/tools/encaix_sony'))
from psb_utils import finalize_lr16

def fp(l):
 return dict(name=l.name,bbox=list(l.bbox),opacity=l.opacity,blend=str(l.blend_mode),visible=l.visible,
  channels=[dict(id=int(ci.id),compression=int(cd.compression),sha256=hashlib.sha256(cd.data).hexdigest()) for ci,cd in zip(l._record.channel_info,l._channels)],
  mask=None if l._record.mask_data is None else l._record.mask_data.tobytes().hex())

sources=json.loads((OUT/'A0_sources.json').read_text())
s=PSDImage.open(sources['V42']['path']); e=PSDImage.open(sources['V56']['path'])
assert s.size==e.size==(10551,7506) and s.depth==e.depth==16 and len(s)==32 and len(e)==26
for label,doc in [('V42',s),('V56',e)]:
 for l,r in zip(doc,sources[label]['layers']):
  assert fp(l)=={k:v for k,v in r.items() if k!='index'}
originals=list(s)
base=PixelLayer(s,copy.deepcopy(e[1]._record),copy.deepcopy(e[1]._channels))
solar=PixelLayer(s,copy.deepcopy(e[7]._record),copy.deepcopy(e[7]._channels))
moon=PixelLayer(s,copy.deepcopy(e[25]._record),copy.deepcopy(e[25]._channels))
base.name='00 Base corba · limbe corregit V56'
solar.name='09 Compost de perles i protuberàncies · V56'
moon.name='Earthshine V56 · detall i revelat de Pere'
s[8].visible=False; s[26].visible=False
s._layers=originals[:9]+[base,solar]+originals[9:]+[moon]
for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
 if tag in s._record.layer_and_mask_information.tagged_blocks:s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
finalize_lr16(s)
# Temporary cached merge is the V42 baseline. Photoshop must recompose before publication.
s._updated=False
p=OUT/'V57_work.psb'; assert not p.exists()
with p.open('xb') as f:s.save(f)
expected=[fp(l) for l in s]
(OUT/'B0_assembly.json').write_text(json.dumps(dict(path=str(p),layers=35,expected=expected,
 original_order_preserved=True,original_visibility_changes={8:False,26:False},
 imported={'9':['V56',1],'10':['V56',7],'34':['V56',25]},
 source_channels_preserved=True,geometry='identity; no resampling',cached_merge='V42 temporary; native recomposition required'),ensure_ascii=False,indent=2))
print('ASSEMBLED',p,p.stat().st_size,flush=True)
