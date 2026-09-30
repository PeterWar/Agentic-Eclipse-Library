from pathlib import Path
import sys,json,numpy as np,hashlib,gc,tifffile as tf
from psd_tools import PSDImage
from psd_tools.constants import Tag,Compression
from psd_tools.psd.layer_and_mask import ChannelData
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16,add_pixel_layer
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V65_PERE_GEOMETRY_STARS_20260914';p=PSDImage.open(O/'V64_Pere_input.psb');before=[]
def fingerprint(l):return dict(id=int(l._record.tagged_blocks.get_data(Tag.LAYER_ID)),name=l.name,bbox=list(l.bbox),visible=l.visible,opacity=l.opacity,blend=str(l.blend_mode),channels=[dict(id=int(q.id),compression=int(c.compression),sha=hashlib.sha256(c.data).hexdigest()) for q,c in zip(l._record.channel_info,l._channels)])
for l in p:
 before.append(fingerprint(l));lid=before[-1]['id']
 if lid in [87,97]:l.visible=False
 if lid not in [3,76]:continue
 new=np.load(A/('B11_base_k0.9.npy' if lid==3 else 'B10_L76_colour.npy'));x0,y0,x1,y1=max(l.left,4377),max(l.top,2777),min(l.right,6377),min(l.bottom,4777)
 for c in range(3):
  a=chan(l,c).copy();a[y0-l.top:y1-l.top,x0-l.left:x1-l.left]=new[y0-2777:y1-2777,x0-4377:x1-4377,c];i=next(i for i,v in enumerate(l._record.channel_info) if int(v.id)==c);cd=ChannelData(Compression.ZIP);cd.set_data(a.astype('>u2').tobytes(),l.width,l.height,16,2);l._channels[i]=cd;l._record.channel_info[i].length=len(cd.data)+2;del a,cd;gc.collect();print('patched',lid,c,flush=True)
 l.name=('00 Base corba · color i llums alts V65' if lid==3 else 'Interiors 06–12 · encaix de Pere · color superior V65')
# Complement only lost transparency in the existing overlap. Exact original RGB/masks preserved above this new backing.
support=np.load(A/'D6_opacity_support.npy');norm=np.load(A/'D6_normalized_RGBA16.npy');ys,xs=np.nonzero(support);x0,x1=xs.min(),xs.max()+1;y0,y1=ys.min(),ys.max()+1;rgb=norm[y0:y1,x0:x1,:3].copy();mask=support[y0:y1,x0:x1];rgb[~mask]=0
layer=add_pixel_layer(p,rgb,'Contorn · normalització de cobertura V65',top=2777+int(y0),left=4377+int(x0),mask8=mask.astype('uint8')*255);layer._record.tagged_blocks.set_data(Tag.LAYER_ID,200);p.remove(layer);idx=next(i for i,l in enumerate(p) if int(l._record.tagged_blocks.get_data(Tag.LAYER_ID))==3);p.insert(idx,layer)
finalize_lr16(p);p._updated=False;dst=O/'D7_V65_artifacts_stage.psb';assert not dst.exists()
with dst.open('xb') as f:p.save(f)
(O/'D7_artifact_stage.json').write_text(json.dumps(dict(source_frozen=str(O/'V64_Pere_input.psb'),before=before,after=[fingerprint(l) for l in p],support_layer_bbox=layer.bbox,stage=str(dst),note='Staging cached composite is still source preview; force Photoshop recomposition before any inspection/delivery.'),ensure_ascii=False,indent=2));print('BUILT',dst,dst.stat().st_size,flush=True)
