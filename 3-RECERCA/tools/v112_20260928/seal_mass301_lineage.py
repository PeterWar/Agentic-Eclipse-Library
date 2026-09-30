"""Seal method provenance only. This does not approve the candidate's scientific quality."""
from pathlib import Path
import json,numpy as np
from psb_munta import ROOT,sha
O=ROOT/'4-RESULTATS/v112_20260928';T=Path(__file__).parent;S=O/'sensor_mass301';destination=S/'LINEAGE.json';assert not destination.exists()
source=ROOT/'4-RESULTATS/v110_torre_20260928/V111.psb';history=ROOT/'1-PHOTOSHOP/V108_Artefactes.psb'
m=dict(schema='V112-causal-replay-1',source=dict(path=str(source),sha256=sha(source)),parameter_source=str(history),layers={},replays=[],traces=[],g1_inputs={},corner301={},files={},scope='Method provenance only; WEDGE1/2 still FAIL; no promotion or complete artifact-resolution claim.')
def add(p):p=Path(p).resolve();m['files'][str(p)]=sha(p)
for role,p in [('e6_replay',O/'TRACE_MASS_E6.json'),('g1_first',O/'sensor_mass_raw/TRACE_G1.json'),('g1_replay',O/'replay_mass_g1/TRACE_G1.json')]:
 tr=json.loads(p.read_text());add(p);m['traces'].append(dict(role=role,path=str(p),argv=tr['argv'],env=tr['env']))
 for group in ('inputs','outputs'):
  for file,h in tr[group].items():
   if '/.coordination/' in file:continue
   assert sha(file)==h,('changed_since_execution',file);m['files'][file]=h
 if role.startswith('g1_'):
  fstd=Path(tr['argv'][-1]);m['g1_inputs'][role]={str(p):str(p.resolve()) for p in sorted(fstd.glob('*.npy'))}
for lid,tag in [(45,'P02c_RHEF_local60_native'),(46,'P02d_RHEF_local30_native'),(41,'P01_NRGF'),(42,'P01_NRGF_extrap')]:
 if lid in (45,46):old=O/'rhef_control/filtres';new=O/'rhef_mass/filtres';replay=O/'replay_mass_rhef/filtres'
 else:old=O/'nrgf_recipe8_control_raw/G_MAX_T_e30_W_H0';new=O/'sensor_mass_raw/nrgf/G_MAX_T_e30_W_H0';replay=O/'replay_mass_g1/nrgf/G_MAX_T_e30_W_H0'
 name=tag+'_u16.npy';m['layers'][str(lid)]=dict(old=str(old/name),new=str(new/name));m['replays'].append(dict(layer=lid,first=str(new/name),replay=str(replay/name)))
 for p in (old/name,new/name,replay/name):add(p)
 assert sha(new/name)==sha(replay/name),(lid,'replay not byteexact')
base=O/'sensor_mass_raw';corner=dict(lower_stage=base/'V112_sensor_mass_stage.psb',lower_targets=base/'TARGETS.json',native=base/'below301/visible_complet.tif',jsx=base/'below301/render.jsx',log=base/'below301/RENDER.log',receipt=base/'corner301/RECEIPT.json',renderer=T/'native_render.py',producer=ROOT/'3-RECERCA/tools/v86_neta_20260923/a5_cantonada.py')
m['corner301']={k:str(v.resolve()) for k,v in corner.items()}
for p in corner.values():add(p)
for p in [source,history,T/'regenera_301.py',T/'native_save.py',T/'psb_munta.py',T/'munta_mass301.py',T/'qa_mass_synthetic.py',O/'CONTRACTE_PREVI.json',O/'ADDENDUM_SENSOR_PREVI.json',O/'ADDENDUM_RECEPTA_PREVI.json',O/'ADDENDUM_RECEPTA_INPUTS.json',O/'ADDENDUM_MASS_PREVI.json',O/'ADDENDUM_301_PREVI.json',O/'MASS_SYNTHETIC.json']:add(p)
destination.write_text(json.dumps(m,indent=2)+'\n');h=sha(destination)
p=S/'TARGETS.json';targets=json.loads(p.read_text());targets['lineage']=dict(path=str(destination),sha256=h);p.write_text(json.dumps(targets,indent=2)+'\n')
# Approval here names a fully traced computational graph, never scientific delivery.
p=T/'llinatge_v112.py';code=p.read_text();assert 'APPROVED_MANIFESTS=set()' in code;code=code.replace('APPROVED_MANIFESTS=set()',"APPROVED_MANIFESTS={"+repr(h)+"}  # Method only; scientific quality remains separate.");p.write_text(code)
print('METHOD_LINEAGE_SEALED',h)
