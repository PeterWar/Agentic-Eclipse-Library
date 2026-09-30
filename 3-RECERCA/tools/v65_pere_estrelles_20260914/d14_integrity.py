from pathlib import Path
import sys,json,gc,hashlib,numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Tag,Resource
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan,sha
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V65_PERE_GEOMETRY_STARS_20260914';p=O/'V65_native.psb';s=PSDImage.open(p);src=PSDImage.open(O/'V64_Pere_input.psb');assert s.size==src.size==(10551,7506) and s.depth==src.depth==16 and len(s)==31 and len(src)==27
ids=lambda d:{int(l._record.tagged_blocks.get_data(Tag.LAYER_ID)):l for l in d};old=ids(src);now=ids(s);assert [i for i in now if i in old]==list(old);checks=[];metadata=[]
for lid,l in old.items():
 z=now[lid];assert z.bbox==l.bbox,(lid,z.bbox,l.bbox);assert (z.opacity,z.blend_mode,z.clipping)==(l.opacity,l.blend_mode,l.clipping);assert z.visible==(False if lid in [87,97] else l.visible)
 if l.has_mask():assert z._record.mask_data==l._record.mask_data,(lid,'mask metadata')
 for ci in l._record.channel_info:
  c=int(ci.id);io=next(i for i,q in enumerate(l._record.channel_info) if int(q.id)==c);iz=next(i for i,q in enumerate(z._record.channel_info) if int(q.id)==c);edited=lid in [3,76] and c in [0,1,2]
  if not edited and l._channels[io].compression==z._channels[iz].compression and l._channels[io].data==z._channels[iz].data:mx=0;proof='compressed bytes exact';changed=0
  else:
   aa=chan(l,c).copy();bb=chan(z,c);assert aa.shape==bb.shape
   if edited:
    new=np.load(A/('B11_base_k0.9.npy' if lid==3 else 'B10_L76_colour.npy'));x0,y0,x1,y1=max(l.left,4377),max(l.top,2777),min(l.right,6377),min(l.bottom,4777);aa[y0-l.top:y1-l.top,x0-l.left:x1-l.left]=new[y0-2777:y1-2777,x0-4377:x1-4377,c]
   delta=np.abs(aa.astype('int32')-bb);mx=int(delta.max());changed=int(np.count_nonzero(delta));proof='decoded expected pixels';del aa,bb,delta;gc.collect()
  assert mx<=(1 if edited else 0),(lid,c,mx);checks.append(dict(id=lid,channel=c,edited=edited,max_DN16=mx,quantization_pixels=changed,proof=proof))
 metadata.append(dict(id=lid,name=z.name,bbox=z.bbox,opacity=z.opacity,visible=z.visible,blend=str(z.blend_mode),geometry_exact=True));print('ROOT VERIFIED',lid,flush=True)
assert now[76].kind==old[76].kind=='pixel';assert s._record.image_resources[Resource.ICC_PROFILE].data==src._record.image_resources[Resource.ICC_PROFILE].data
# New photographic star layers: masks and values must survive native import unchanged to within one 16-bit quantization unit.
pack=PSDImage.open(O/'S24b_estrelles_capes.psb')
for l in pack:
 lid=int(l._record.tagged_blocks.get_data(Tag.LAYER_ID));z=now[lid];assert z.bbox==l.bbox,(lid,z.bbox,l.bbox);assert (z.opacity,z.visible,z.blend_mode)==(l.opacity,l.visible,l.blend_mode)
 for ci in l._record.channel_info:
  c=int(ci.id);aa=chan(l,c);bb=chan(z,c);mx=int(np.max(np.abs(aa.astype('int32')-bb)));assert mx<=1,(lid,c,mx);checks.append(dict(id=lid,channel=c,edited=True,max_DN16=mx,proof='new layer expected'));del aa,bb;gc.collect()
 print('NEW STAR VERIFIED',lid,flush=True)
source=json.loads((O/'A0_source_freeze.json').read_text());h=sha(source['source_path']);assert h==source['sha256']==sha(source['frozen_path']);rep=dict(PASS=True,path=str(p),sha256=sha(p),bytes=p.stat().st_size,size=s.size,depth=s.depth,top_level=31,metadata=metadata,channel_checks=checks,source_sha256=h,all_original_geometry_exact=True,all_original_masks_exact=True,all_original_alpha_exact=True,Pere_added_beads96_all_channels_exact=True,Earthshine30_all_channels_exact=True,RGB_edits_only_layers=[3,76],ICC_exact=True,source_visible_order_exact=True,source76_is_Pere_rasterized_pixel_layer=True,new_layers=[200,201,202,203]);(O/'D14_integrity.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2));print('AUDIT PASS',len(checks),rep['sha256'],flush=True)
