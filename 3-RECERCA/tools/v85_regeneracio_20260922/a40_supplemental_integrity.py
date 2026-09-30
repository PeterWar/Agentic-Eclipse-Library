from a34_native_integrity import *
from psb69 import _rf

def records(path):
 with Path(path).open('rb') as f:
  f.seek(26)
  for _ in range(2):n=_rf(f,'I')[0];f.seek(n,1)
  n=_rf(f,'Q')[0];end=f.tell()+n;n=_rf(f,'Q')[0];body=f.tell() if n else None;f.seek(n,1);n=_rf(f,'I')[0];f.seek(n,1)
  while f.tell()+12<=end:
   _,key=_rf(f,'4s4s');n=_rf(f,'Q' if key in BIG_KEYS else 'I')[0];start=f.tell()
   if key in (b'Lr16',b'Lr32'):body=start
   f.seek(start+(n+3)//4*4)
  assert body is not None;f.seek(body);count=abs(_rf(f,'h')[0]);rr=[LayerRecord.read(f,version=2) for _ in range(count)]
  return {int(r.tagged_blocks.get_data(Tag.LAYER_ID)):r for r in rr}

def main():
 old=PSB(str(O/'V84_Pere_input.psb'));stage=PSB(str(O/'V85_final_stage.psb'));final=PSB(str(R/'1-PHOTOSHOP/V85.psb'));ids=[l['id'] for l in old.layers];assert ids==[l['id'] for l in stage.layers];assert ids==[l['id'] for l in final.layers if l['id'] in set(ids)]
 a=records(old.path);b=records(final.path)
 for lid,rec in a.items():assert {k:v.tobytes(version=2) for k,v in rec.tagged_blocks.items()}=={k:v.tobytes(version=2) for k,v in b[lid].tagged_blocks.items()},lid
 added=set(b)-set(a);assert len(added)==1;lid=added.pop();plate=final.layer(lid);assert tuple(plate[k] for k in ['left','top','right','bottom'])==(4908,3493,5036,3867);source=tf.imread(O/'Moon_V84_preserved.tif');assert source.shape==(374,128,4) and source.dtype==np.uint16
 alpha,_=final.channel(lid,-1);np.testing.assert_array_equal(alpha,source[...,3]);active=alpha>0;assert set(np.unique(alpha))=={0,65535} and active.sum()==13903
 for cid in [0,1,2]:rgb,_=final.channel(lid,cid);np.testing.assert_array_equal(rgb[active],source[...,cid][active])
 z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=z['box'];m=z['support'][plate['top']-y0:plate['bottom']-y0,plate['left']-x0:plate['right']-x0];assert not np.any(active&~m)
 save(O/'SUPPLEMENTAL_INTEGRITY.json',{'PASS':True,'original_layer_order_preserved':True,'original_tagged_blocks_exact_layers':len(a),'plate_layer_id':lid,'plate_alpha_exact':True,'plate_active_RGB_max_DN16':0,'plate_active_pixels':int(active.sum()),'plate_active_pixels_outside_moon':0,'scope':'supplemental preservation integrity; independent peer method persisted and executed by root on delivered V85'})
 print('SUPPLEMENTAL_INTEGRITY_PASS')
if __name__=='__main__':guard();main()
