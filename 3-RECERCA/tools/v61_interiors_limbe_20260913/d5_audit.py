from common61 import *
import gc
from psd_tools import PSDImage
from psd_tools.constants import Tag,Resource
claim();p=O/'V61_native.psb';s=PSDImage.open(p);src=PSDImage.open(O/'V60_Pere_input.psb');v57=PSDImage.open(V57);build=json.loads((O/'D0_build.json').read_text());report={'size':s.size,'depth':s.depth,'top_level':len(s),'layers':[],'channel_checks':[]};assert s.size==(10551,7506) and s.depth==16
alllayers=list(s.descendants());pixels=[l for l in alllayers if not l.is_group()];so=next(l for l in pixels if l.kind=='smartobject');g=next(l for l in alllayers if l.is_group());assert len(g)==7 and not g.visible and not so.visible
def compare(a,b,c,limit=0):
 aa=chan(a,c);bb=chan(b,c);assert aa.shape==bb.shape,(a.name,c,aa.shape,bb.shape)
 eq=np.array_equal(aa,bb);mx=0 if eq else int(np.max(abs(aa.astype('int32')-bb.astype('int32'))));assert mx<=limit,(a.name,c,mx,limit);return mx
byid={int(l._record.tagged_blocks.get_data(Tag.LAYER_ID)):l for l in pixels if Tag.LAYER_ID in l._record.tagged_blocks}
srcids={int(l._record.tagged_blocks.get_data(Tag.LAYER_ID)):i for i,l in enumerate(src) if Tag.LAYER_ID in l._record.tagged_blocks}
for i,l in enumerate(src):
 if i<7:continue
 lid=int(l._record.tagged_blocks.get_data(Tag.LAYER_ID));a=byid[lid];report['layers'].append({'source_index':i,'name':a.name,'id':lid,'visible':a.visible,'bbox':a.bbox});assert a.bbox==l.bbox
 for ci in l._record.channel_info:
  c=int(ci.id)
  if 11<=i<=16 and c==-2:
   aa=chan(a,c);expected=chan(l,c).copy();m=l._record.mask_data;expected[2777-m.top:4777-m.top,4377-m.left:6377-m.left]=np.load(O/'arrays'/f'B1_L{i:02d}_mask.npy');mx=int(np.max(abs(aa.astype('int32')-expected.astype('int32'))));assert mx<=2,(i,c,mx);tag='corrected mask'
  else:mx=compare(a,l,c);tag='unchanged'
  report['channel_checks'].append({'source_index':i,'channel':c,'max_DN16':mx,'kind':tag})
 print('CHECKED',i,a.name,flush=True);gc.collect()
for i,l in enumerate(g):
 ref=v57[i];assert l.bbox==ref.bbox,(i,l.bbox,ref.bbox)
 for ci in ref._record.channel_info:
  c=int(ci.id)
  if i==1 and c==-2:
   a=chan(l,c);expected=chan(ref,c).copy();md=ref._record.mask_data;q=expected[2777-md.top:4777-md.top,4377-md.left:6377-md.left];q[np.load(O/'arrays/V60_L29_C-2.npy')==65535]=0;mx=int(abs(a.astype('int32')-expected.astype('int32')).max());assert mx<=2
  else:mx=compare(l,ref,c)
  report['channel_checks'].append({'restored_index':i,'channel':c,'max_DN16':mx})
 print('RESTORED EXACT',i,flush=True)
assert so.smart_object.kind=='data';report['smartobject']={'kind':so.smart_object.kind,'filename':so.smart_object.filename,'transform':list(so.smart_object.transform_box)}
with so.smart_object.open() as f:e=PSDImage.open(f)
eg=next(l for l in e.descendants() if l.is_group());assert len(eg)==7 and e.depth==16
for i,l in enumerate(eg):
 for ci in l._record.channel_info:
  c=int(ci.id);mx=compare(l,g[i],c,2);report['channel_checks'].append({'embedded_index':i,'channel':c,'max_DN16':mx})
print('EMBEDDED 7 VERIFIED',flush=True);report['smartobject']['embedded_layers']=7;report['ICC_exact_to_source']=s._record.image_resources[Resource.ICC_PROFILE].data==src._record.image_resources[Resource.ICC_PROFILE].data;assert report['ICC_exact_to_source'];report['sha256']=sha(p);report['bytes']=p.stat().st_size;report['PASS']=True;save('D5_final_integrity.json',report)
