"""Lineage gate: candidate pixels must derive from frozen, independently replayed operators."""
from pathlib import Path
import json,numpy as np
from porta_torre_pisa import PSB,sha,q_blocs,same_array
# Filled only after a branch has a complete traced replay; not read from TARGETS.
APPROVED_MANIFESTS={'18defc700f7b7f827c1c111c580f0abd7aa12c9362042e834faefebf9b5884ba'}  # Method only; scientific quality remains separate.

def formula_counts(source,old,new,target):
 counts=dict(changed=0,control_mismatch_on_change=0,target_mismatch=0)
 if any(x.ndim!=2 or x.dtype.kind!='u' or x.dtype.itemsize!=2 for x in (source,old,new,target)):return dict(error='uint16_2D_required')
 if any(x.shape!=source.shape for x in (old,new,target)):return dict(error='shape')
 for y in range(0,source.shape[0],256):
  s=source[y:y+256];o=q_blocs(old[y:y+256]);n=q_blocs(new[y:y+256]);t=target[y:y+256];m=n!=o
  counts['changed']+=int(m.sum());counts['control_mismatch_on_change']+=int(np.count_nonzero(m&(s!=o)))
  counts['target_mismatch']+=int(np.count_nonzero(t!=np.where(m,n,s)))
 return counts

def validate(target,base):
 out=dict(status='FAIL',failures=[],layers={})
 def ck(ok,name,**kw):
  if not ok:out['failures'].append(dict(check=name,**kw))
  return bool(ok)
 spec=target.get('lineage')
 if not ck(isinstance(spec,dict),'lineage_present'):return out
 path=Path(spec['path']);digest=sha(path)
 if not ck(digest==spec.get('sha256') and digest in APPROVED_MANIFESTS,'frozen_branch_manifest'):return out
 m=json.loads(path.read_text());out['manifest_sha256']=digest
 ck(target.get('source_sha256')==m['source']['sha256']==sha(base.path),'lineage_source')
 ck(set(m['layers'])=={'41','42','45','46'} and set(target['replacement'])==set(m['layers'])|{'301'},'exact_causal_roster_with_visible_corner')
 ck(m.get('schema')=='V112-causal-replay-1','lineage_schema')
 ck(len(m.get('replays',[]))==4 and {str(r.get('layer')) for r in m.get('replays',[])}==set(m['layers']),'complete_replay_roster')
 ck(len(m.get('traces',[]))==3 and {r.get('role') for r in m.get('traces',[])}=={'e6_replay','g1_first','g1_replay'},'complete_trace_roster')
 required={m['source']['path'],m['parameter_source']}
 for v in m['layers'].values():required.update((v['old'],v['new']))
 for v in m.get('replays',[]):required.update((v['first'],v['replay']))
 for v in m.get('traces',[]):required.add(v['path'])
 corner=m.get('corner301',{})
 ck(set(corner)=={'lower_stage','lower_targets','native','jsx','log','receipt','renderer','producer'},'corner_proof_complete')
 required.update(corner.values())
 ck(required.issubset(m['files']),'all_graph_nodes_frozen',missing=sorted(required-set(m['files'])))
 if out['failures']:return out
 for p,h in m['files'].items():ck(Path(p).is_file() and sha(p)==h,'frozen_lineage_file',path=p)
 if out['failures']:return out
 history=PSB(m['parameter_source'])
 ck(history.layer(46)['opacity']==8 and base.layer(46)['opacity']==31,'producer8_manual31')
 for r in m['replays']:
  ck(r['first']==m['layers'][str(r['layer'])]['new'],'replay_bound_to_active_output',layer=r['layer'])
  ck(Path(r['first']).resolve()!=Path(r['replay']).resolve(),'separate_replay_file',layer=r['layer'])
  a=np.load(r['first'],mmap_mode='r');b=np.load(r['replay'],mmap_mode='r')
  ck(same_array(a,b),'clean_directory_replay',first=r['first'],replay=r['replay'])
 traces={}
 for receipt in m['traces']:
  tr=json.loads(Path(receipt['path']).read_text())
  traces[receipt['role']]=tr
  root=Path(__file__).resolve().parents[3];base_inputs=root/'4-RESULTATS/v108_20260926/cadena/v108'
  ck(tr['cwd']==str(root),'producer_canonical_cwd',role=receipt['role'])
  ck(tr['env'].get('V97_FONTS')==str(base_inputs/'lineal') and tr['env'].get('V98_FRANJA')==str(base_inputs/'franja/A3C_franja_silueta.npz'),'producer_scientific_inputs',role=receipt['role'])
  if receipt['role']=='e6_replay':
   ck(tr['argv']==[str(Path(__file__).parent/'run_rhef_mass.py'),'mass','E6','--rhef-detrend','no'],'exact_mass_operator_arguments')
  else:
   aliases=m.get('g1_inputs',{}).get(receipt['role'],{});folders={str(Path(p).parent) for p in aliases}
   ck(len(folders)==1,'single_generation_input_folder',role=receipt['role'])
   if len(folders)==1:
    expected=[str(root/'3-RECERCA/tools/v108_20260926/negres_v2/g1_nrgf_genoll.py'),'G_MAX_T_e30_W_H0','--psb',m['parameter_source'],'--filtres-std',next(iter(folders))]
    ck(tr['argv']==expected,'exact_g1_recipe_arguments',role=receipt['role'])
   ck(tr['env'].get('V108_BASE')==str(base_inputs/'base/base_v108_final_u16.npy') and tr['env'].get('V108_R')==str(base_inputs),'g1_base_input',role=receipt['role'])
  ck(tr['status']=='COMPLETED' and tr['argv']==receipt['argv'] and tr['env']==receipt['env'],'trace_execution_binding',path=receipt['path'])
  for p,h in tr['inputs'].items():
   if '/.coordination/' not in p:ck(m['files'].get(p)==h,'traced_input_closed',path=p)
  for p,h in tr['outputs'].items():ck(m['files'].get(p)==h,'traced_output_closed',path=p)
 replay_by_id={str(r['layer']):r for r in m['replays']}
 for lid,paths in m['layers'].items():
  role='e6_replay' if lid in ('45','46') else 'g1_replay'
  rp=replay_by_id[lid]['replay'];ck(traces[role]['outputs'].get(rp)==m['files'][rp],'replay_output_producer',layer=lid)
  ck(Path(rp).is_relative_to(Path(traces[role]['env']['V97_SORT'])),'replay_under_declared_output',layer=lid)
  if lid in ('41','42'):ck(traces['g1_first']['outputs'].get(paths['new'])==m['files'][paths['new']],'active_output_producer',layer=lid)
 for role in ('g1_first','g1_replay'):
  spec=m.get('g1_inputs',{}).get(role,{})
  ck(len(spec)==6,'six_filter_generation_inputs',role=role)
  for alias,resolved in spec.items():
   ck(str(Path(alias).resolve())==resolved and resolved in m['files'] and traces[role]['inputs'].get(resolved)==m['files'].get(resolved),'generation_input_binding',role=role,path=alias)
  for lid in ('45','46'):
   raw=m['layers'][lid]['new'] if role=='g1_first' else replay_by_id[lid]['replay']
   ck(raw in spec.values(),'g1_depends_on_corrected_RHEF',role=role,layer=lid)
   for suffix in ('_u16.npy','_alfa_u16.npy'):
    stem='P02c_RHEF_local60_native' if lid=='45' else 'P02d_RHEF_local30_native';name=stem+suffix
    match=[v for k,v in spec.items() if Path(k).name==name];expected=str(Path(raw).parent/name)
    ck(match==[expected],'exact_RGB_alpha_pairing',role=role,layer=lid,input_name=name)
  for suffix in ('_u16.npy','_alfa_u16.npy'):
   name='P03_MGN'+suffix;match=[v for k,v in spec.items() if Path(k).name==name];expected=str(base_inputs/'filtres_std/filtres'/name)
   ck(match==[expected],'unchanged_MGN_generation_input',role=role,input_name=name)
 for lid,paths in m['layers'].items():
  actual=base.channel(int(lid),1)[0];old=np.load(paths['old'],mmap_mode='r');new=np.load(paths['new'],mmap_mode='r');t=np.load(target['replacement'][lid]['path'],mmap_mode='r')
  for cid in (0,2):
   other=base.channel(int(lid),cid)[0];ck(same_array(other,actual),'source_operator_is_declared_gray',layer=lid,channel=cid);del other
  c=formula_counts(actual,old,new,t);out['layers'][lid]=c
  ck('error' not in c and c['changed']>0 and c['control_mismatch_on_change']==0 and c['target_mismatch']==0,'causal_target_formula',layer=lid,details=c)
  del actual
 if not out['failures']:
  from corner_guard_v112 import validate_corner
  proof=validate_corner(corner,target,base);out['corner301']=proof
  ck(proof['status']=='PASS','regenerated_corner_proof',details=proof)
 if not out['failures']:out['status']='LINEAGE_PASS'
 return out
