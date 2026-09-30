"""Independent decoded-pixel and source-preservation verification of V109."""
from pathlib import Path
import sys,json,hashlib,copy,io
import numpy as np,tifffile
from psd_tools.constants import Tag
ROOT=Path(__file__).resolve().parents[3];O=ROOT/'4-RESULTATS/v109_pixi_20260928'
sys.path.insert(0,str(ROOT/'3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB,llegeix_registres,rid,sha
dst,targetpath,view=map(lambda x:Path(x).resolve(),sys.argv[1:4])
P=PSB(str(dst));B=PSB(str(ROOT/'1-PHOTOSHOP/V108.psb'))
target=np.load(targetpath,mmap_mode='r');pixi=np.load(O/'entrades/PIXI_net.npy',mmap_mode='r')
report={'file':str(dst.relative_to(ROOT)),'sha256':sha(dst),'layers':len(P.layers),'dimensions':[P.width,P.height],
        'depth':P.depth,'original_layers':[],'new_layers':[],'sources':{},'native_layerTime_changes':[]}
assert [x['id'] for x in P.layers[:len(B.layers)]]==[x['id'] for x in B.layers]
rb={rid(r):r for r,_ in llegeix_registres(Path(B.path))['recs']}
rp={rid(r):r for r,_ in llegeix_registres(dst)['recs']}
for l in B.layers:
 lid=l['id'];nr=0;npix=0
 for cid in l['chans']:
  a,_=B.channel(lid,cid);b,_=P.channel(lid,cid)
  assert np.array_equal(a,b),(lid,cid);nr+=1;npix+=a.size
 for table in (rb,rp):
  for c in table[lid].channel_info:c.length=0
 # Photoshop refreshes each layer's modification timestamp when duplicating.
 # Compare every other byte of the record, including adjustment payloads.
 times=[]
 for table in (rb,rp):
  tt=[]
  if Tag.METADATA_SETTING in table[lid].tagged_blocks:
   for item in table[lid].tagged_blocks[Tag.METADATA_SETTING].data:
    if item.key==b'cust' and b'layerTime' in item.data:
     tt.append(item.data[b'layerTime'].value);item.data[b'layerTime'].value=0
  times.append(tt)
 if times[0]!=times[1]:report['native_layerTime_changes'].append({'id':lid,'before':times[0],'after':times[1]})
 def record(r):
  out=io.BytesIO();r.write(out,version=2);return out.getvalue()
 assert record(rb[lid])==record(rp[lid]),('metadata',lid)
 report['original_layers'].append({'id':lid,'exact_channels':nr,'samples':npix,'metadata_exact_except_native_layerTime':True})
 print('exact original layer',lid,flush=True)
box=(0,0,P.width,P.height)
for lid,wanted,under in [(400,pixi,np.load(O/'entrades/V108_compost.npy',mmap_mode='r')),(401,target,pixi)]:
 l=P.layer(lid);assert l['blend']=='NORMAL' and l['opacity']==255 and l['visible']
 alpha=P.channel_box(lid,-1,box);expected=np.any(wanted!=under,axis=2)
 assert np.array_equal(alpha,np.uint16(expected)*65535)
 for c in range(3):assert np.array_equal(P.channel_box(lid,c,box),np.where(expected,wanted[...,c],0))
 report['new_layers'].append({'id':lid,'changed_pixels':int(expected.sum()),'binary_alpha_exact':True,'RGB_inside_exact_outside_zero':True})
visible=tifffile.memmap(view);comp=P.composite()[...,:3]
assert np.array_equal(visible,target) and np.array_equal(comp,target)
report['native_render_equals_target']=True;report['ImageData_equals_native_render']=True
H=np.load(O/'entrades/retoc_local_mask.npy',mmap_mode='r')
assert np.array_equal(target[H],pixi[H]);report['local_retouched_pixels_exact']=int(H.sum())
for k,v in json.loads((O/'FONTS.json').read_text())['sources'].items():
 actual=sha(Path(v['path']));assert actual==v['sha256'],('original changed',k)
 report['sources'][k]={'sha256':actual,'unchanged':True}
actual=sha(ROOT/'1-PHOTOSHOP/V108_Artefactes.psb')
assert actual=='e2156820a32d15e7e6816fdaf7111ef8f6e4cc6518491cf9add0041d69d2cc91'
report['sources']['artefactes']={'sha256':actual,'unchanged':True}
report['status']='PASS'
(O/'VERIFICACIO_FINAL.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('PASS FINAL',report['sha256'],flush=True)
