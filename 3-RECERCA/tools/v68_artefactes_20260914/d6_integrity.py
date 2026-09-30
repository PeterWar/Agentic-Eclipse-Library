from pathlib import Path
import sys,json,gc,hashlib,numpy as np,tifffile as tf
from psd_tools import PSDImage
from psd_tools.constants import Tag,Resource,BlendMode
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan,sha
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V68_V67_ARTIFACTS_20260914'
s=PSDImage.open(O/'V68_native.psb');src=PSDImage.open(O/'V67_Pere_input.psb')
assert s.size==src.size==(10551,7506) and s.depth==src.depth==16 and len(s)==len(src)==31
ids=lambda d:{int(l._record.tagged_blocks.get_data(Tag.LAYER_ID)):l for l in d}
old=ids(src);now=ids(s);assert list(old)==list(now);checks=[];metadata=[]
for lid,l in old.items():
 z=now[lid];assert z.bbox==l.bbox,(lid,'geometry');assert (z.opacity,z.clipping)==(l.opacity,l.clipping)
 assert z.blend_mode==(BlendMode.NORMAL if lid==30 else l.blend_mode)
 assert z.visible==(False if lid==205 else l.visible)
 if lid not in [3,30,205]:assert z.name==l.name
 if l.has_mask():assert z._record.mask_data==l._record.mask_data,(lid,'mask metadata')
 for ci in l._record.channel_info:
  c=int(ci.id);io=next(i for i,q in enumerate(l._record.channel_info) if int(q.id)==c);iz=next(i for i,q in enumerate(z._record.channel_info) if int(q.id)==c)
  edited=lid in [3,30] and c in [0,1,2]
  if not edited and l._channels[io].compression==z._channels[iz].compression and l._channels[io].data==z._channels[iz].data:mx=0;proof='compressed bytes exact';changed=0
  else:
   aa=chan(l,c).copy();bb=chan(z,c);assert aa.shape==bb.shape
   if edited:
    if lid==3:aa[2777:4777,4377:6377]=np.load(A/'B4_L3_colour.npy')[...,c]
    else:aa[:]=np.load(A/'B10_photo_pilot.npz')['candidate'][...,c]
   delta=np.abs(aa.astype('int32')-bb);mx=int(delta.max());changed=int(np.count_nonzero(delta));proof='decoded expected pixels';del aa,bb,delta;gc.collect()
  assert mx<=(1 if edited else 0),(lid,c,mx)
  checks.append(dict(id=lid,channel=c,edited=edited,max_DN16=mx,quantization_pixels=changed,proof=proof))
 metadata.append(dict(id=lid,name=z.name,bbox=z.bbox,opacity=z.opacity,visible=z.visible,blend=str(z.blend_mode),geometry_exact=True));print('VERIFIED',lid,flush=True)
assert s._record.image_resources[Resource.ICC_PROFILE].data==src._record.image_resources[Resource.ICC_PROFILE].data
del s,src,old,now;gc.collect()
full=tf.imread(O/'D5_full_native.tif');small=tf.imread(O/'D2_pilot_native.tif');assert full.shape==(7506,10551,4)
roi=full[2777:4777,4377:6377];diff=abs(roi.astype('int32')-small);pilotmax=int(diff.max());assert pilotmax<=4,pilotmax
# Outside the diagnosed ROI every visible input is unchanged. Check the native full-frame composition too.
before=tf.imread(O/'A2_clean_full.tif');assert before.shape==full.shape
mask=np.zeros(full.shape[:2],bool);mask[2777:4777,4377:6377]=True
outside_max=0;alpha_max=0
for y in range(0,7506,256):
 d=abs(full[y:y+256].astype('int32')-before[y:y+256]);outside_max=max(outside_max,int(d[~mask[y:y+256]].max(initial=0)));alpha_max=max(alpha_max,int(d[...,3].max()))
assert outside_max==0 and alpha_max==0,(outside_max,alpha_max)
sourcehash=json.loads((O/'A1_layers.json').read_text())['sha256'];assert sha('/Users/USUARI/Downloads/V67.psb')==sourcehash==sha(O/'V67_Pere_input.psb')
rep=dict(PASS=True,path=str(O/'V68_native.psb'),sha256=sha(O/'V68_native.psb'),bytes=(O/'V68_native.psb').stat().st_size,size=[10551,7506],depth=16,top_level=31,metadata=metadata,channel_checks=checks,source_sha256=sourcehash,all_original_geometry_exact=True,all_original_masks_exact=True,all_original_alpha_exact=True,perles96_all_channels_exact=True,stars_all_channels_exact=True,RGB_edits_only_layers=[3,30],blend_change_only_layer30='HARD_LIGHT to NORMAL',ICC_exact=True,pilot_to_full_max_DN16=pilotmax,full_canvas_alpha_max_change=alpha_max,outside_ROI_max_change_DN16=outside_max)
(O/'D6_integrity.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print('INTEGRITY PASS',len(checks),rep['sha256'],flush=True)
