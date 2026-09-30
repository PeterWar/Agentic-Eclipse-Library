from pathlib import Path
import sys,json,numpy as np,hashlib,gc
from psd_tools import PSDImage
from psd_tools.constants import BlendMode,Tag,Compression
R=Path.cwd();O=R/'output/v62_prominencies_20260913';A=O/'arrays'
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import add_pixel_layer,add_mask16,finalize_lr16
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan,box,sha
p=O/'V61_Pere_SO_input.psb';s=PSDImage.open(p);assert s.size==(8512,6686) and s.depth==16 and len(s)==1;g=s[0];assert g.is_group() and len(g)==7 and not g.has_mask()
rows=[];comp=np.zeros((2000,2000,3),np.float32);alpha=np.zeros((2000,2000),np.float32);roi=(3480,2365,5480,4365)
for i,l in enumerate(g):
 rows.append(dict(index=i,name=l.name,bbox=l.bbox,visible=l.visible,blend=str(l.blend_mode),opacity=l.opacity,channels=[dict(id=int(ci.id),sha=hashlib.sha256(cd.data).hexdigest()) for ci,cd in zip(l._record.channel_info,l._channels)]))
 if not l.visible:continue
 assert l.blend_mode==BlendMode.NORMAL and l.opacity==255
 rgb=np.stack([box(l,c,roi) for c in range(3)],-1).astype('float32')/65535;a=box(l,-1,roi).astype('float32')/65535
 if l.has_mask():a*=box(l,-2,roi).astype('float32')/65535
 comp=rgb*a[...,None]+comp*(1-a[...,None]);alpha=a+alpha*(1-a)
ref=np.load(A/'C2_original_RGB16_local.npy').astype('float32')/65535;diff=abs(comp-ref);err=float(diff.max()*65535);assert err<5,(err,np.unravel_index(np.argmax(diff),diff.shape));print('Source reproduction maxDN',err,flush=True)
matte=np.load(A/'C2_matte_alpha16_local.npy');div=add_pixel_layer(s,np.repeat(matte[...,None],3,axis=2),'Despremultiplicació del fons negre · V62',top=2365,left=3480,parent=g,blend=BlendMode.DIVIDE,compression=Compression.ZIP)
add_mask16(g,matte,top=2365,left=3480,compression=Compression.ZIP);g._record.mask_data.background_color=255;g.blend_mode=BlendMode.NORMAL
g.name='Interiors originals V57 + composició del fons negre V62'
for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
 if tag in s._record.layer_and_mask_information.tagged_blocks:s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
finalize_lr16(s);s._updated=False;out=O/'Interiors_V62_editables.psb';assert not out.exists()
with out.open('xb') as f:s.save(f)
(O/'D1_embedded.json').write_text(json.dumps(dict(input=str(p),output=str(out),original_layers=rows,native_source_reproduction_max_DN16=err,source_RGB_preserved=True,source_masks_preserved=True,source_geometry_preserved=True,added_layers=1,added_group_mask=True,provisional_cache=True),indent=2,ensure_ascii=False));print('EMBEDDED BUILT',out.stat().st_size,flush=True)
