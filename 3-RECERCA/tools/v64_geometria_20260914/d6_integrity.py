from pathlib import Path
import sys,json,gc,hashlib,numpy as np,tifffile as tf
from psd_tools import PSDImage
from psd_tools.constants import Tag,Resource
R=Path.cwd();O=R/'output/v64_geometria_20260914';A=O/'arrays'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan,sha
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V64_V63_GREEN_GEOMETRY_20260914'
p=O/'V64_native.psb';s=PSDImage.open(p);src=PSDImage.open(O/'V63_Pere_input.psb');assert s.size==src.size==(10551,7506) and s.depth==src.depth==16 and len(s)==len(src)==25
ids=lambda d:{int(l._record.tagged_blocks.get_data(Tag.LAYER_ID)):l for l in d};old=ids(src);now=ids(s);assert list(old)==list(now);assert list(now).index(76)>list(now).index(30)
checks=[];metadata=[]
def exact(a,b,c):
 ia=next(i for i,q in enumerate(a._record.channel_info) if int(q.id)==c);ib=next(i for i,q in enumerate(b._record.channel_info) if int(q.id)==c)
 if a._channels[ia].compression==b._channels[ib].compression and a._channels[ia].data==b._channels[ib].data:return 'compressed bytes exact'
 aa=chan(a,c);bb=chan(b,c);assert aa.shape==bb.shape and np.array_equal(aa,bb),(a.name,c);return 'decoded pixels exact'
for lid,l in old.items():
 z=now[lid];assert z.bbox==l.bbox,(lid,z.bbox,l.bbox);assert (z.opacity,z.blend_mode,z.clipping)==(l.opacity,l.blend_mode,l.clipping);assert z.visible==(False if lid==87 else l.visible)
 if l.has_mask():assert z._record.mask_data==l._record.mask_data,(lid,'mask metadata')
 for ci in l._record.channel_info:
  c=int(ci.id)
  if lid==76 and c!=-2:continue
  proof=exact(z,l,c);checks.append(dict(id=lid,channel=c,max_DN16=0,proof=proof))
 metadata.append(dict(id=lid,name=z.name,bbox=z.bbox,opacity=z.opacity,visible=z.visible,blend=str(z.blend_mode)));print('ROOT VERIFIED',lid,flush=True);gc.collect()
assert list(now[76].smart_object.transform_box)==list(old[76].smart_object.transform_box)
with now[76].smart_object.open() as f:es=PSDImage.open(f)
with old[76].smart_object.open() as f:eo=PSDImage.open(f)
g=es[0];og=eo[0];assert es.size==eo.size==(8512,6686) and len(g)==len(og)==8
for i in range(8):
 l=og[i];z=g[i];assert l.bbox==z.bbox and l.name==z.name and (l.visible,l.opacity,l.blend_mode)==(z.visible,z.opacity,z.blend_mode)
 for ci in l._record.channel_info:
  c=int(ci.id);proof=exact(z,l,c);checks.append(dict(embedded_index=i,channel=c,max_DN16=0,proof=proof))
 print('EMBEDDED VERIFIED',i,flush=True);gc.collect()
md=g._record.mask_data;mask=chan(g,-2);expected=np.full(mask.shape,65535,np.uint16);roi=np.load(A/'D0_native_expected_mask.npy');read=np.full(roi.shape,65535,np.uint16)
x0,y0=max(3480,md.left),max(2365,md.top);x1,y1=min(5480,md.right),min(4365,md.bottom)
expected[y0-md.top:y1-md.top,x0-md.left:x1-md.left]=roi[y0-2365:y1-2365,x0-3480:x1-3480];read[y0-2365:y1-2365,x0-3480:x1-3480]=mask[y0-md.top:y1-md.top,x0-md.left:x1-md.left]
mx=max(int(abs(mask.astype('int32')-expected.astype('int32')).max()),int(abs(read.astype('int32')-roi.astype('int32')).max()));assert mx<=2 and md.background_color==255
assert s._record.image_resources[Resource.ICC_PROFILE].data==src._record.image_resources[Resource.ICC_PROFILE].data
a=tf.imread(O/'D1_candidate_with83.tif');b=tf.imread(O/'D5_final_ROI.tif');c=tf.imread(O/'V64_saved_ROI.tif');assert a.shape==b.shape==c.shape and np.array_equal(a,b) and np.array_equal(b,c)
source=json.loads((O/'A1_sources.json').read_text());h=sha(Path(source['path']));assert h==source['sha256']
copy=tf.imread(O/'A0_extra12_masked.tif');without=tf.imread(O/'A0_without_extra12.tif');clean=tf.imread(O/'A0_clean.tif');assert not copy.any() and np.array_equal(clean,without)
rep=dict(PASS=True,path=str(p),sha256=sha(p),bytes=p.stat().st_size,size=s.size,depth=s.depth,top_level=25,metadata=metadata,channel_checks=checks,all_original_RGB_exact=True,all_original_source_alpha_exact=True,all_Pere_root_masks_exact=True,accepted_V62_colour_exact=True,embedded_originals=7,embedded_divider_preserved=True,embedded_mask_max_DN16=mx,source_transform_exact=True,source_transform=list(now[76].smart_object.transform_box),source_above_Moon=True,saved_native_ROI_max_DN16=0,V63_frozen_disk_unchanged=h,ICC_exact=True,copy12_original_preserved_exact=True,copy12_native_effect_max_DN16=0,copy12_transform_promoted=False,nonopaque_ROI_before=int(np.count_nonzero(clean[...,3]<65535)),nonopaque_ROI_after=int(np.count_nonzero(c[...,3]<65535)),alpha_ROI_max_difference_DN16=int(abs(clean[...,3].astype('int32')-c[...,3].astype('int32')).max()))
(O/'D6_integrity.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print('AUDIT PASS',len(checks),rep['sha256'],flush=True)
