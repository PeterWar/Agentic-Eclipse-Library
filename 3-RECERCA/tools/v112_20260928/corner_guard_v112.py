"""Verify the existing presentation dependency, including its exact native lower-stack input."""
from pathlib import Path
import json,ast,importlib.util,numpy as np,tifffile
from porta_torre_pisa import sha,colour,q_blocs,same_array

def validate_corner(c,target,source):
 out=dict(status='FAIL',failures=[])
 def ck(ok,name,**kw):
  if not ok:out['failures'].append(dict(check=name,**kw))
  return bool(ok)
 from porta_v112 import gate
 root=Path(__file__).resolve().parents[3];tool=Path(__file__).parent
 ck(Path(c['renderer'])==tool/'native_render.py','renderer_identity')
 ck(Path(c['producer'])==root/'3-RECERCA/tools/v86_neta_20260923/a5_cantonada.py','corner_producer_identity')
 ck(sha(c['producer'])=='547b57ce273103464aeb5d994a2e9eea6ec3e3ce3f06990d5f08fb3f221bab9c','original_corner_recipe')
 lower=json.loads(Path(c['lower_targets']).read_text())
 ck(set(lower['replacement'])=={'41','42','45','46'},'lower_stack_causal_roster')
 for lid,spec in lower['replacement'].items():ck(spec==target['replacement'].get(lid),'same_underlying_operators',layer=lid)
 g=gate(Path(c['lower_stage']),c['lower_targets']);ck(g['status']=='STRUCTURE_PASS','lower_stage_structure',details=g['failures'])
 ids=[l['id'] for l in source.layers];hidden=ids[ids.index(301):]
 tree=ast.parse(Path(c['renderer']).read_text());template=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='template' for t in n.targets))
 expected=template.replace('__SRC__',json.dumps(c['lower_stage'])).replace('__DIR__',json.dumps(str(Path(c['native']).parent))).replace('__HIDE__',json.dumps(hidden))
 ck(Path(c['jsx']).read_text()==expected,'full_native_lower_stack_binding')
 log=Path(c['log']).read_text();ck('COMPLET' in log and 'ERROR' not in log,'native_lower_completed')
 with tifffile.TiffFile(c['native']) as tf:ck(tf.pages[0].tags[34675].value==colour(source.path)[1],'lower_native_ICC')
 im=tifffile.memmap(c['native'],mode='r');ck(im.shape==(7506,10551,3) and im.dtype.kind=='u' and im.dtype.itemsize==2,'lower_native_uint16_full_canvas')
 receipt=json.loads(Path(c['receipt']).read_text());ck(receipt['input_native']==c['native'] and receipt['input_sha256']==sha(c['native']) and receipt['source_sha256']==sha(source.path),'corner_receipt_inputs')
 if out['failures']:return out
 sp=importlib.util.spec_from_file_location('v112_verified_corner',c['producer']);module=importlib.util.module_from_spec(sp);sp.loader.exec_module(module)
 rgb,alpha,calc=module.calcula(im[4320:6263,7356:9348].astype(np.float32)/65535.)
 a=np.round(alpha*65535).astype('uint16');a[0,0]=max(a[0,0],1);a[-1,-1]=max(a[-1,-1],1);actual,origin=source.channel(301,-1)
 ck(origin==(7356,4320) and same_array(q_blocs(a),actual),'generated_alpha_equals_protected_source')
 mapping=target['replacement']['301']['channels'];ck(set(mapping)=={'0','1','2'},'corner_RGB_roster')
 for cid,v in mapping.items():
  expected=q_blocs(np.round(np.clip(rgb[...,int(cid)],0,1)*65535).astype('uint16'));got=np.load(v['path'],mmap_mode='r')
  ck(got.ndim==2 and got.dtype.kind=='u' and got.dtype.itemsize==2 and same_array(expected,got),'corner_active_RGB_replayed',channel=cid)
 out['meaning']='Original presentation-only sky continuation, not recovered coronal radiance.'
 if not out['failures']:out['status']='PASS'
 return out
