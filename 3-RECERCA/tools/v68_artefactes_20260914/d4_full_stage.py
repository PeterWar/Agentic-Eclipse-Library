from pathlib import Path
import sys,json,numpy as np,gc
from psd_tools import PSDImage
from psd_tools.constants import Tag,Compression,BlendMode
from psd_tools.psd.layer_and_mask import ChannelData
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan
sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import finalize_lr16
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V68_V67_ARTIFACTS_20260914'
assert json.loads((O/'D3_pilot_qa.json').read_text())['PASS']
p=PSDImage.open(O/'V67_Pere_input.psb');assert p.size==(10551,7506) and len(p)==31
for l in p:
 lid=int(l._record.tagged_blocks.get_data(Tag.LAYER_ID))
 if lid==205:l.visible=False;l.name='Marques de Pere · V67 · referència'
 if lid not in [3,30]:continue
 if lid==30:
  assert l.bbox==(4678,3077,6078,4477)
  l.blend_mode=BlendMode.NORMAL;new=np.load(A/'B10_photo_pilot.npz')['candidate'].astype('uint16')
  l.name='Earthshine · revelat de Pere · patró fi corregit V68'
 else:
  new=np.load(A/'B4_L3_colour.npy');l.name='00 Base corba · color del limbe V68'
 for c in range(3):
  a=chan(l,c).copy()
  if lid==30:a[:]=new[...,c]
  else:a[2777:4777,4377:6377]=new[...,c]
  i=next(i for i,v in enumerate(l._record.channel_info) if int(v.id)==c)
  cd=ChannelData(Compression.ZIP);cd.set_data(a.astype('>u2').tobytes(),l.width,l.height,16,2)
  l._channels[i]=cd;l._record.channel_info[i].length=len(cd.data)+2
  del a,cd;gc.collect();print('PATCHED',lid,c,flush=True)
finalize_lr16(p);p._updated=False;dst=O/'D4_V68_stage.psb';assert not dst.exists()
with dst.open('xb') as f:p.save(f)
print('FULL STAGE BUILT',dst.stat().st_size,flush=True)
