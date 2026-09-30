"""V112 delivery evidence: exact source roster and manual operation, active causal rasters, native recomposition. Science is separate."""
from pathlib import Path
import sys,json,copy,ast,numpy as np,tifffile
R=Path(__file__).resolve().parents[3];O=R/'4-RESULTATS/v112_20260928'
sys.path.insert(0,str(R/'3-RECERCA/tools/guardrails_postprocessat'))
from porta_torre_pisa import PSB,llegeix_registres,rid,sha,record_bytes,same_array,colour,channel_digest,q_blocs
CONTRACT='607e0936fb1799899e3e90d6d8cebe6a198239e8ea7c5eb809c50ff8232aa4df'
APPROVED_NATIVE={'6ee50b7f5fa9619b1f84be4614882a3ae9b10d04610ef325156ff1e0e979c557'} # Observed native_save COMPLET 2026-09-28 02:15:49 UTC. Method only, quality FAIL.
def gate(file,targets=None,native=None):
 rep=dict(file=str(file),sha256=sha(file),contract_sha256=sha(O/'CONTRACTE_PREVI.json'),gate_sha256=sha(Path(__file__)),status='FAIL',scientific_status='NOT_ASSESSED',failures=[],layers=[])
 def ck(ok,name,**kw):
  if not ok:rep['failures'].append(dict(check=name,**kw))
  return ok
 ck(rep['contract_sha256']==CONTRACT,'frozen_requirements')
 c=json.loads((O/'CONTRACTE_PREVI.json').read_text());s=R/c['source']['source'];ck(sha(s)==c['source']['sha256'],'source_hash')
 b,p=PSB(str(s)),PSB(str(file))
 ck([l['id'] for l in p.layers]==[l['id'] for l in b.layers],'exact_roster_order_no_new_layers')
 ck(p.channels in (3,4),'merged_channel_count');ck((p.width,p.height,p.depth)==(b.width,b.height,b.depth),'canvas_depth');ck(colour(file)==colour(s),'ICC')
 if rep['failures']:return rep
 target=json.loads(Path(targets).read_text()) if targets else {'replacement':{}}
 ids=set(map(int,target['replacement']))
 ck(ids in ({41,42,45,46},{41,42,45,46,301}) if targets else not ids,'exact_causal_roster')
 rr={rid(r):r for r,_ in llegeix_registres(Path(file))['recs']}
 for rec,_ in llegeix_registres(s)['recs']:
  lid=rid(rec);expected=copy.deepcopy(rec)
  if lid==412:expected.flags.visible=False
  ck(record_bytes(rr[lid])==record_bytes(expected),'exact_operation_metadata',layer=lid)
  ck(set(p.layer(lid)['chans'])==set(b.layer(lid)['chans']),'channel_inventory',layer=lid)
  spec=target['replacement'].get(str(lid)); rasters={}
  if spec:
   mapping=spec['channels'] if lid==301 else {str(c):spec for c in (0,1,2)}
   ck(set(mapping)=={'0','1','2'},'exact_corrected_RGB',layer=lid)
   for cid,v in mapping.items():
    ck(sha(v['path'])==v['sha256'],'causal_output_hash',layer=lid,channel=cid);rasters[int(cid)]=q_blocs(np.load(v['path'],mmap_mode='r'))
  changed=0
  for cid in b.layer(lid)['chans']:
   if cid in rasters:
    got,org=p.channel(lid,cid);orig,baseorg=b.channel(lid,cid)
    ck(org==baseorg and same_array(got,rasters[cid]),'active_operator_output',layer=lid,channel=cid)
    changed=max(changed,int(np.count_nonzero(got!=orig)));del got,orig
   elif channel_digest(p,lid,cid)!=channel_digest(b,lid,cid):
    got,org=p.channel(lid,cid);orig,baseorg=b.channel(lid,cid)
    ck(org==baseorg and same_array(got,orig),'protected_channel',layer=lid,channel=cid);del got,orig
  if spec:ck(changed>0,'actual_causal_change',layer=lid)
  del rasters
  rep['layers'].append(dict(id=lid,changed_rgb_pixels=changed));print('checked',lid,flush=True)
 if not rep['failures']:rep['status']='STRUCTURE_PASS'
 if native and not rep['failures']:
  if not ck(sha(native) in APPROVED_NATIVE,'observed_native_envelope'):
   rep['status']='FAIL';return rep
  if not ck(ids=={41,42,45,46,301},'visible_corner_dependency_regenerated'):
   rep['status']='FAIL';return rep
  from llinatge_v112 import validate
  lineage=validate(target,b);rep['lineage']=lineage
  if not ck(lineage['status']=='LINEAGE_PASS','verified_operator_lineage'):
   rep['status']='FAIL';return rep
  from semantic_v112 import knee_stack_check
  semantic=knee_stack_check(target,p);rep['semantic_dependency']=semantic
  if not ck(semantic['status']=='NECESSARY_DEPENDENCIES_PASS','knee_valid_for_active_stack',details=semantic['failures']):
   rep['status']='FAIL';return rep
  ev=json.loads(Path(native).read_text());ck(ev['psb_sha256']==rep['sha256'],'native_bound_to_actual_file')
  required={'control','candidate','control_off','candidate_off','final','control_stage','candidate_stage','control_log','candidate_log','control_off_log','candidate_off_log','final_log','control_jsx','candidate_jsx','control_off_jsx','candidate_off_jsx','final_jsx'}
  if not ck(required.issubset(ev['files']),'native_evidence_complete',missing=sorted(required-set(ev['files']))):
   rep['status']='FAIL';return rep
  for k,v in ev['files'].items():ck(sha(v['path'])==v['sha256'],'native_evidence_hash',item=k)
  def template(name):
   tree=ast.parse((Path(__file__).parent/name).read_text())
   return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='template' for t in n.targets))
  for prefix,stage,hidden in [('control','control_stage',[]),('candidate','candidate_stage',[]),('control_off','control_stage',[239,241]),('candidate_off','candidate_stage',[239,241])]:
   jsx=Path(ev['files'][prefix+'_jsx']['path']).read_text();expected=template('native_render.py').replace('__SRC__',json.dumps(ev['files'][stage]['path'])).replace('__DIR__',json.dumps(str(Path(ev['files'][prefix]['path']).parent))).replace('__HIDE__',json.dumps(hidden))
   ck(jsx==expected,'complete_native_JSX_binding',item=prefix)
  for role,t in [('control_stage',None),('candidate_stage',targets)]:
   sub=gate(Path(ev['files'][role]['path']),t);ck(sub['status']=='STRUCTURE_PASS','native_stage_verified',role=role,failures=sub['failures'])
  jsx=Path(ev['files']['final_jsx']['path']).read_text();expected=template('native_save.py').replace('__STAGE__',json.dumps(ev['files']['candidate_stage']['path'])).replace('__DEST__',json.dumps(str(file.resolve()))).replace('__DIR__',json.dumps(str(Path(ev['files']['final']['path']).parent)))
  ck(jsx==expected,'complete_native_save_binding')
  imgs={k:tifffile.memmap(ev['files'][k]['path'],mode='r') for k in ('control','candidate','control_off','candidate_off','final')}
  for k in imgs:
   with tifffile.TiffFile(ev['files'][k]['path']) as tf:ck(tf.pages[0].tags[34675].value==colour(s)[1],'native_TIFF_ICC',item=k)
  for k,im in imgs.items():ck(im.shape==(p.height,p.width,3) and im.dtype.kind=='u' and im.dtype.itemsize==2,'full_native_shape',item=k)
  merged=p.composite();ck(same_array(merged[...,:3],imgs['final']),'full_ImageData_exact_native')
  ck(same_array(imgs['candidate'],imgs['final']),'candidate_equals_final_render')
  if p.channels==4:ck(merged[...,3].min()>60000 and merged[...,3].mean()>65000,'full_alpha_p6_policy')
  del merged
  mask=b.channel_box(234,-2,(0,0,b.width,b.height),fill=0)>0;ck(int(mask.sum())==2130,'manual_support_bound_to_source'); delta=imgs['candidate'][mask].astype(np.int32)-imgs['control'][mask].astype(np.int32)
  mx=int(np.abs(delta).max()); rms=float(np.sqrt(np.mean(delta.astype(float)**2)))
  rep['manual_visible']=dict(pixels=int(mask.sum()),max_abs_DN=mx,rms_DN=rms)
  ck(mx<=c['native_manual']['max_abs_DN'] and rms<=c['native_manual']['rms_DN'],'manual_native_appearance')
  changed=response=0
  for y in range(0,p.height,128):
   a,z,a0,z0=[imgs[k][y:y+128].astype(np.int32) for k in ('control','candidate','control_off','candidate_off')]
   d=z-a;changed+=int(np.any(d!=0,axis=-1).sum());response+=int(np.any(d-(z0-a0)!=0,axis=-1).sum())
  rep['native_response']=dict(changed_pixels=changed,dependent_adjustment_pixels=response)
  ck(changed>0,'correction_reaches_native');ck(response>0,'dependent_adjustments_recomposed')
  for k,v in ev['files'].items():
   if k.endswith('_log'):
    txt=Path(v['path']).read_text();ck('COMPLET' in txt and 'ERROR' not in txt,'native_completed',item=k)
  if not rep['failures']:rep['status']='METHOD_AND_NATIVE_PASS'
 if rep['failures']:rep['status']='FAIL'
 return rep
if __name__=='__main__':
 rep=gate(Path(sys.argv[1]),sys.argv[2] if len(sys.argv)>2 and sys.argv[2]!='-' else None,sys.argv[3] if len(sys.argv)>3 else None)
 out=Path(sys.argv[4]) if len(sys.argv)>4 else O/(Path(sys.argv[1]).stem+'_GUARD.json');out.write_text(json.dumps(rep,indent=2)+'\n');print(rep['status'],rep['failures']);sys.exit(bool(rep['failures']))
