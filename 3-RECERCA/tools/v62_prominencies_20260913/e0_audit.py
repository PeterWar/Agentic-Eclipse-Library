from pathlib import Path
import sys,json,hashlib,gc,numpy as np,tifffile as tf
from psd_tools import PSDImage
from psd_tools.constants import Tag,Resource,BlendMode
R=Path.cwd();O=R/'output/v62_prominencies_20260913';A=O/'arrays'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan,sha
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V62_V61_PROMINENCES_20260913'
p=O/'V62_preserved_work.psb';s=PSDImage.open(p);src=PSDImage.open(O/'V61_Pere_input.psb');assert s.size==src.size==(10551,7506) and s.depth==src.depth==16 and len(s)==len(src)==24
ids=lambda doc:{int(l._record.tagged_blocks.get_data(Tag.LAYER_ID)):l for l in doc}
old=ids(src);now=ids(s);assert old.keys()==now.keys();checks=[];metadata=[]
def eq(a,b):return a.shape==b.shape and np.array_equal(a,b)
for lid,l in old.items():
 z=now[lid];assert z.bbox==l.bbox,(lid,z.bbox,l.bbox);assert z.opacity==l.opacity and z.blend_mode==l.blend_mode and z.clipping==l.clipping
 assert z.visible==(False if lid==78 else l.visible),(lid,z.visible,l.visible)
 for ci in l._record.channel_info:
  c=int(ci.id)
  if lid==76 and c!=-2:continue
  a=chan(z,c);b=chan(l,c)
  if lid==3 and c in [0,1,2]:
   b=b.copy();b[2777-l.top:4777-l.top,4377-l.left:6377-l.left]=np.load(A/'C1_base_RGB16.npy')[...,c];tol=2;role='new coronal colour'
  elif lid==76 and c==-2:b=np.load(A/'D0_user_mask_normalized.npy');tol=2;role='user mask pedestal normalized'
  else:tol=0;role='preserved'
  assert a.shape==b.shape;mx=int(abs(a.astype('int32')-b.astype('int32')).max());assert mx<=tol,(lid,c,mx,tol);checks.append(dict(id=lid,channel=c,max_DN16=mx,role=role));del a,b;gc.collect()
 metadata.append(dict(id=lid,name=z.name,bbox=z.bbox,visible=z.visible,opacity=z.opacity,blend=str(z.blend_mode),clipping=str(z.clipping)))
 print('LAYER VERIFIED',lid,z.name,flush=True)
so=now[76];assert so.smart_object.kind=='data';tr=list(so.smart_object.transform_box);assert tr==list(old[76].smart_object.transform_box)
with so.smart_object.open() as f:embedded=PSDImage.open(f)
orig_emb=PSDImage.open(O/'V61_Pere_SO_input.psb');g=embedded[0];og=orig_emb[0];assert embedded.size==orig_emb.size==(8512,6686) and len(g)==8 and len(og)==7
for i in range(7):
 a=g[i];b=og[i];assert a.name==b.name and a.bbox==b.bbox and a.visible==b.visible and a.opacity==b.opacity and a.blend_mode==b.blend_mode
 for ci in b._record.channel_info:
  c=int(ci.id);aa=chan(a,c);bb=chan(b,c);mx=int(abs(aa.astype('int32')-bb.astype('int32')).max());assert mx==0,(i,c,mx);checks.append(dict(embedded_index=i,channel=c,max_DN16=mx,role='original interior preserved'));del aa,bb
 print('EMBEDDED ORIGINAL VERIFIED',i,a.name,flush=True);gc.collect()
assert g[7].blend_mode==BlendMode.DIVIDE and g[7].visible
mask=chan(g,-2);expected=np.load(A/'C2_matte_alpha16_local.npy');md=g._record.mask_data
# Native Photoshop trims or expands stored mask rectangles. Compare coverage
# in object coordinates, including its required opaque surroundings.
mask_expected=np.full(mask.shape,65535,np.uint16)
roi_readback=np.full(expected.shape,65535,np.uint16)
x0,y0=max(3480,md.left),max(2365,md.top)
x1,y1=min(5480,md.right),min(4365,md.bottom)
assert x1>x0 and y1>y0
mask_expected[y0-md.top:y1-md.top,x0-md.left:x1-md.left]=expected[y0-2365:y1-2365,x0-3480:x1-3480]
roi_readback[y0-2365:y1-2365,x0-3480:x1-3480]=mask[y0-md.top:y1-md.top,x0-md.left:x1-md.left]
mx=max(int(abs(mask.astype('int32')-mask_expected.astype('int32')).max()),int(abs(roi_readback.astype('int32')-expected.astype('int32')).max()));assert mx<=2
assert md.background_color==255
mask_storage=dict(bbox=[md.left,md.top,md.right,md.bottom],expected_ROI=[3480,2365,5480,4365],outside_ROI_opaque=True)
del mask,mask_expected,roi_readback;gc.collect()
assert g[7].bbox==(3480,2365,5480,4365)
for c in [0,1,2]:
 a=chan(g[7],c);assert np.max(abs(a.astype('int32')-expected.astype('int32')))<=2
native=tf.imread(O/'V62_embedded_dematte.tif');ref=np.load(A/'C2_original_RGB16_local.npy');premul_error=int(abs(native[...,:3].astype('int32')-ref.astype('int32')).max());assert premul_error==0
v=tf.imread(O/'V62_candidate_ROI.tif');r=tf.imread(O/'V62_saved_readback.tif');readback=int(abs(v.astype('int32')-r.astype('int32')).max());assert readback==0
icc=s._record.image_resources[Resource.ICC_PROFILE].data;assert icc==src._record.image_resources[Resource.ICC_PROFILE].data
sources=json.loads((O/'A0_sources.json').read_text());h=sha(Path(sources['path']));assert h==sources['sha256']
report=dict(PASS=True,path=str(p),sha256=sha(p),bytes=p.stat().st_size,size=s.size,depth=s.depth,top_level=24,metadata=metadata,channel_checks=checks,embedded_originals=7,embedded_added_layers=1,embedded_kind=so.smart_object.kind,embedded_filename=so.smart_object.filename,transform=tr,transform_exact=True,matte_mask_max_DN16=mx,matte_mask_storage=mask_storage,photographic_premultiplied_reconstruction_max_DN16=premul_error,save_readback_max_DN16=readback,ICC_preserved=True,user_V61_unchanged_SHA=h,not_promoted=['simple black cutoff B2','global geometric shrink B0','pixel-area mask integration C3','clipping all filters D5/D7'])
(O/'E0_integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('AUDIT PASS',len(checks),'checks',report['sha256'],flush=True)
