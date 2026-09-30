"""Read every final layer channel and verify original preservation / planned edits."""
from a16_build_psb import *
import tifffile as tf

def rawsha(p,lid,cid):
 pos,n=p.layer(lid)['chans'][cid];h=hashlib.sha256()
 with open(p.path,'rb') as f:
  f.seek(pos)
  while n:
   b=f.read(min(n,16<<20));assert b;n-=len(b);h.update(b)
 return h.hexdigest()

def main():
 original=PSB(str(O/'V84_Pere_input.psb'));stage=PSB(str(O/'V85_final_stage.psb'));final=PSB(str(O/'V85_candidate_native.psb'));assert (final.width,final.height,final.depth,final.mode)==(10551,7506,16,3);assert len(final.layers)==42
 oldids={l['id'] for l in original.layers};newids={l['id'] for l in final.layers};assert oldids<newids and len(newids-oldids)==1;plateid=(newids-oldids).pop();changed={(3,c) for c in [0,1,2,-2]}|{(i,c) for i in MAP for c in [0,1,2]}|{(225,-2),(234,-2),(45,-2),(46,-2)};rows=[];metadata=[]
 for layer in stage.layers:
  lid=layer['id'];q=final.layer(lid)
  for key in ['left','top','right','bottom','visible','opacity','blend','clipping','mask']:
   if lid==225 and key=='mask':
    assert layer[key]['background']==q[key]['background']==0 and not q[key]['disabled']
   else:assert layer[key]==q[key],(lid,key,layer[key],q[key])
  assert set(layer['chans'])==set(q['chans']);metadata.append(lid)
  for cid in layer['chans']:
   planned=(lid,cid) in changed
   if not planned:assert rawsha(stage,lid,cid)==rawsha(original,lid,cid),(lid,cid,'unplanned stage edit')
   a,org=stage.channel(lid,cid);b,orgb=final.channel(lid,cid)
   if lid==225 and cid==-2:
    # Native Photoshop expands a newly added mask to the whole canvas.
    # Compare its exact canvas meaning, including all newly stored zero pixels.
    expected=np.zeros_like(b);x,y=org;xb,yb=orgb;expected[y-yb:y-yb+a.shape[0],x-xb:x-xb+a.shape[1]]=a;a=expected;org=orgb
   assert org==orgb and a.shape==b.shape
   if a.size:
    delta=np.abs(a.astype(np.int32)-b.astype(np.int32));maximum=int(delta.max());count=int(np.count_nonzero(delta))
   else:maximum=count=0
   assert maximum<=(1 if planned and cid in [0,1,2] else 0),(lid,cid,maximum,count)
   rows.append({'id':lid,'channel':cid,'planned_change':planned,'native_roundtrip_max_DN16':maximum,'native_roundtrip_changed_pixels':count});del a,b
  print('NATIVE_LAYER_VERIFIED',lid,flush=True)
 z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=z['box'];moon=z['support']
 for lid in MAP:
  a=final.channel_box(lid,-2,(x0,y0,x1,y1));assert not a[moon].any()
 plate=final.layer(plateid);assert (plate['left'],plate['top'],plate['right'],plate['bottom'])==(4908,3493,5036,3867);a,_=final.channel(plateid,-1);assert set(np.unique(a))=={0,65535} and np.count_nonzero(a)==13903
 with open(final.path,'rb') as f:f.seek(final.image_data_offset);compression=struct.unpack('>H',f.read(2))[0]
 assert compression in [0,1],'Merged compatibility data must not be ZIP'
 composite=final.composite();native=tf.imread(O/'Q_final_preserved_roi.tif');region=composite[3000:4550,4600:6150,:3];assert np.array_equal(region,native);assert np.array_equal(region[y0-3000:y1-3000,x0-4600:x1-4600][moon],tf.imread(O/'A_current_roi.tif')[y0-3000:y1-3000,x0-4600:x1-4600][moon]);del composite
 record={'PASS':True,'scope':'pixel and metadata integrity, not universal scientific artifact acceptance','input_sha256':sha(O/'V84_Pere_input.psb'),'native_sha256':sha(O/'V85_candidate_native.psb'),'shape':[7506,10551],'depth':16,'layers':42,'metadata_verified_layers':metadata,'layer_channels':rows,'all17_filter_masks_zero_on_653168_lunar_pixels':True,'moon_composite_exact':True,'native_cache_matches_fresh_render':True,'plate_layer_id':plateid,'merged_compression':compression,'preserved_original_channels':sum(not r['planned_change'] for r in rows),'new_RGB_roundtrip_tolerance_DN16':1}
 save(O/'NATIVE_INTEGRITY.json',record);print('NATIVE_INTEGRITY_PASS',flush=True)

if __name__=='__main__':guard();main()
