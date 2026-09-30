"""Bounded301 presentation branch. A PASS here never approves scientific filters."""
from pathlib import Path
import ast,copy,importlib.util,json,sys
import numpy as np,tifffile
from porta_v112 import R,O,PSB,sha,colour,llegeix_registres,rid,record_bytes,channel_digest,same_array,q_blocs
S=O/'corner_only'
SOURCE_SHA='8a607e75967b4ef0d8a52eedabbedd986742781ecf3622b12c6e2630faba0da3'
CONTRACT_SHA='9873112ffbec1fd06b2a013fe2b954891fee4d7b528361d4293318744ef5f158'
APPROVED_NATIVE=set() # Filled only after an observed native save; never supplied by TARGETS.

def jsx_template(name):
 tree=ast.parse((Path(__file__).parent/name).read_text())
 return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='template' for t in n.targets))

def gate(file,native=None):
 out=dict(status='FAIL',scope='Presentation maintenance301 only; other artifacts unresolved',failures=[],file=str(file),sha256=sha(file))
 def ck(ok,name,**kw):
  if not ok:out['failures'].append(dict(check=name,**kw))
  return bool(ok)
 source=O.parent/'v110_torre_20260928/V111.psb'
 ck(sha(S/'CONTRACT.json')==CONTRACT_SHA,'frozen_scope_and_thresholds')
 ck(sha(source)==SOURCE_SHA,'source_hash')
 target=json.loads((S/'TARGETS.json').read_text())
 ck(target['source_sha256']==SOURCE_SHA and set(target['replacement'])=={'301'},'only301RGB')
 b,p=PSB(str(source)),PSB(str(file))
 ck([x['id'] for x in p.layers]==[x['id'] for x in b.layers],'exact_roster_order')
 ck((p.width,p.height,p.depth)==(b.width,b.height,b.depth),'canvas')
 ck(colour(file)==colour(source),'ICC')
 if out['failures']:return out
 rr={rid(r):r for r,_ in llegeix_registres(file)['recs']}
 mapping=target['replacement']['301']['channels'];ck(set(mapping)=={'0','1','2'},'RGB_roster')
 for rec,_ in llegeix_registres(source)['recs']:
  lid=rid(rec);e=copy.deepcopy(rec)
  if lid==412:e.flags.visible=False
  ck(record_bytes(rr[lid])==record_bytes(e),'exact_operation_metadata',layer=lid)
  ck(set(p.layer(lid)['chans'])==set(b.layer(lid)['chans']),'channel_inventory',layer=lid)
  for cid in b.layer(lid)['chans']:
   if lid==301 and cid in (0,1,2):
    v=mapping[str(cid)];ck(sha(v['path'])==v['sha256'],'target_hash',channel=cid)
    a,org=p.channel(lid,cid);z,org0=b.channel(lid,cid)
    ck(org==org0 and same_array(a,np.load(v['path'],mmap_mode='r')),'active_RGB',channel=cid)
    ck(bool(np.any(a!=z)),'actual_change',channel=cid);del a,z
   elif channel_digest(p,lid,cid)!=channel_digest(b,lid,cid):
    a,org=p.channel(lid,cid);z,org0=b.channel(lid,cid)
    ck(org==org0 and same_array(a,z),'protected_channel',layer=lid,channel=cid);del a,z
  print('checked',lid,flush=True)
 # A second evaluation of the original corner recipe; the lower stack has no filter changes.
 from porta_v112 import gate as original_gate
 lower=O/'V111_control_stage.psb'
 g=original_gate(lower);ck(g['status']=='STRUCTURE_PASS','unchanged_lower_stack',details=g['failures'])
 folder=O/'control_below301';impath=folder/'visible_complet.tif'
 ids=[x['id'] for x in b.layers];hidden=ids[ids.index(301):]
 expected=jsx_template('native_render.py').replace('__SRC__',json.dumps(str(lower))).replace('__DIR__',json.dumps(str(folder))).replace('__HIDE__',json.dumps(hidden))
 ck((folder/'render.jsx').read_text()==expected,'exact_lower_render_binding')
 log=(folder/'RENDER.log').read_text();ck('COMPLET' in log and 'ERROR' not in log,'lower_completed')
 receipt=json.loads((O/'control_301/RECEIPT.json').read_text())
 ck(receipt['source_sha256']==SOURCE_SHA and receipt['input_native']==str(impath) and receipt['input_sha256']==sha(impath),'lower_input_hash')
 producer=R/'3-RECERCA/tools/v86_neta_20260923/a5_cantonada.py'
 ck(sha(producer)=='547b57ce273103464aeb5d994a2e9eea6ec3e3ce3f06990d5f08fb3f221bab9c','original_recipe')
 if out['failures']:return out
 sp=importlib.util.spec_from_file_location('corner_only_replay',producer);mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
 lowerim=tifffile.memmap(impath,mode='r')
 rgb,alpha,_=mod.calcula(lowerim[4320:6263,7356:9348].astype(np.float32)/65535.)
 a=np.round(alpha*65535).astype('uint16');a[0,0]=max(a[0,0],1);a[-1,-1]=max(a[-1,-1],1)
 sa,org=b.channel(301,-1);ck(org==(7356,4320) and same_array(q_blocs(a),sa),'alpha_exact_original')
 for cid,v in mapping.items():
  z=q_blocs(np.round(np.clip(rgb[...,int(cid)],0,1)*65535).astype('uint16'))
  ck(same_array(z,np.load(v['path'],mmap_mode='r')),'recipe_RGB_replay',channel=cid)
 if not out['failures']:out['status']='METHOD_PASS_PRESENTATION_ONLY'
 if not native or out['failures']:return out
 ck(sha(native) in APPROVED_NATIVE,'observed_native_envelope')
 ev=json.loads(Path(native).read_text());ck(ev['psb_sha256']==out['sha256'],'native_actual_PSB')
 required={'control','candidate','control_off','candidate_off','final','control_stage','candidate_stage','control_log','candidate_log','control_off_log','candidate_off_log','final_log','control_jsx','candidate_jsx','control_off_jsx','candidate_off_jsx','final_jsx'}
 ck(required.issubset(ev['files']),'native_evidence_complete')
 if out['failures']:out['status']='FAIL';return out
 for k,v in ev['files'].items():ck(sha(v['path'])==v['sha256'],'native_evidence_hash',item=k)
 for role,stage,h in [('control','control_stage',[]),('candidate','candidate_stage',[]),('control_off','control_stage',[239,241]),('candidate_off','candidate_stage',[239,241])]:
  v=ev['files'];expected=jsx_template('native_render.py').replace('__SRC__',json.dumps(v[stage]['path'])).replace('__DIR__',json.dumps(str(Path(v[role]['path']).parent))).replace('__HIDE__',json.dumps(h))
  ck(Path(v[role+'_jsx']['path']).read_text()==expected,'native_render_binding',item=role)
 v=ev['files'];expected=jsx_template('native_save.py').replace('__STAGE__',json.dumps(v['candidate_stage']['path'])).replace('__DEST__',json.dumps(str(file.resolve()))).replace('__DIR__',json.dumps(str(Path(v['final']['path']).parent)))
 ck(Path(v['final_jsx']['path']).read_text()==expected,'native_save_binding')
 for k,z in v.items():
  if k.endswith('_log'):
   text=Path(z['path']).read_text();ck('COMPLET' in text and 'ERROR' not in text,'native_completed',item=k)
 imgs={k:tifffile.memmap(v[k]['path'],mode='r') for k in ['control','candidate','control_off','candidate_off','final']}
 for k,im in imgs.items():
  ck(im.shape==(7506,10551,3) and im.dtype.kind=='u' and im.dtype.itemsize==2,'native_uint16_canvas',item=k)
  with tifffile.TiffFile(v[k]['path']) as tf:ck(tf.pages[0].tags[34675].value==colour(source)[1],'native_ICC',item=k)
 merged=p.composite();ck(same_array(merged[...,:3],imgs['final']),'full_ImageData_equals_native');del merged
 ck(same_array(imgs['candidate'],imgs['final']),'candidate_equals_saved')
 mask=b.channel_box(234,-2,(0,0,b.width,b.height),fill=0)>0
 ck(int(mask.sum())==2130 and same_array(imgs['candidate'][mask],imgs['control'][mask]),'manual234_native_exact')
 changed=outside=response=0
 for y in range(0,b.height,128):
  a,z,a0,z0=[imgs[k][y:y+128].astype(np.int32) for k in ['control','candidate','control_off','candidate_off']]
  d=z-a;ch=np.any(d!=0,axis=-1);changed+=int(ch.sum());response+=int(np.any(d-(z0-a0)!=0,axis=-1).sum())
  inside=np.zeros(ch.shape,bool);lo=max(y,4320);hi=min(y+len(ch),6263)
  if lo<hi:inside[lo-y:hi-y,7356:9348]=sa[lo-4320:hi-4320]>0
  outside+=int(np.count_nonzero(ch&~inside))
 out['native_response']=dict(changed=changed,outside301=outside,dependent_adjustment=response)
 ck(changed>0 and response>0,'native_dependent_recomposition');ck(outside==0,'native_unchanged_outside301')
 out['status']='METHOD_AND_NATIVE_PASS_PRESENTATION_ONLY' if not out['failures'] else 'FAIL'
 return out

if __name__=='__main__':
 r=gate(Path(sys.argv[1]),Path(sys.argv[2]) if len(sys.argv)>2 and sys.argv[2]!='-' else None)
 out=Path(sys.argv[3]) if len(sys.argv)>3 else S/'GUARD.json';out.write_text(json.dumps(r,indent=2)+'\n')
 print(r['status'],r['failures']);sys.exit(bool(r['failures']))
