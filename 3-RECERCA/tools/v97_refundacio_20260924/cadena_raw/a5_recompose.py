"""Recreate V38/V42 coronal-source baseline from freshly calibrated RAW."""
from a4_sources import *
import types,math

def literal_helpers(path,names,constants=()):
 ns=dict(globals());tree=ast.parse(Path(path).read_text());nodes=[]
 for n in tree.body:
  if isinstance(n,ast.FunctionDef) and n.name in names:nodes.append(copy.deepcopy(n))
  elif isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in constants:nodes.append(copy.deepcopy(n))
 assert len(nodes)==len(names)+len(constants),(path,len(nodes));exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+' isolated helpers','exec'),ns);return ns

def b2(which):
 ns,fr=context();out=O/('b2_'+which);out.mkdir()
 for x in ['cau','receipts']:(out/x).mkdir()
 ns.update(CAU36=O/'sources_v36/cau',REB36=O/'sources_v36/output/v36_20260908/4-rebuts',CAUF=O/'sources_v29',sha=sha,FLAT_CENTRE_YX={'sony':(2660.,4000.)},FLAT_SIGMA_PX=32.)
 definition(fr['sources']['common32']['copy'],'flat_ripple_correction',ns);definition(fr['sources']['common']['copy'],'savejson',ns)
 expected={'sony_A':('sony_A_total_v36.npy','9972718acbf058d14eb715b4dfe3e5a6a815f9b7baba2535dc3d7e34a2037845'),'vixen':('vixen_total_v38.npy','de3515dca0bbb50ed0811554a80862ffe2e45bd499f8848a29d9026c491ffcc9'),'sony_B':('sony_B_total_v42.npy','900bae3bfea2e796df4a6d2d10eb258076ad0eae2275dc0d409931e643e898a8')}
 if which=='sony_A':
  h=literal_helpers(H/'b2_v36_replay.py',['install_b2','execute_one_group'],['B2_SHA'])
  ns.update(B2_OUT=out/'cau',B2_REB=out/'receipts',_new_total_ready=lambda *x:None)
  digest=h['install_b2'](H/'b2_v36_source.py',ns);h['execute_one_group'](ns,which)
 elif which=='vixen':
  h=literal_helpers(H/'b2_v38_replay.py',['program','require'],['SOURCE_SHA'])
  ns.update(CAU38=out/'cau',REB38=out/'receipts',A2_CAU=H/'v38_limb_round1/cau',_total_ready=lambda *x:None)
  code,digest=h['program'](H/'b2_v38_source.py');exec(code,ns);sys.argv=['b2_recomposicio.py','vixen'];ns['main']()
 elif which=='sony_B':
  h=literal_helpers(H/'b2_v42_replay.py',['programs','require'],['SOURCE_SHA','HELPERS_SHA'])
  ns.update(CAU42=out/'cau',REB42=out/'receipts',math=math)
  code,digest=h['programs'](H/'b2_v42_source.py',H/'b2_v42_v38_helpers.py');exec(code[1],ns);ns['B']=types.SimpleNamespace(flat_ripple_correction=ns['flat_ripple_correction'],upsample=ns['upsample'],CHN=ns['CHN']);exec(code[0],ns)
  sys.argv=['b2_recomposicio_v42.py','sony_B','delta_arcmin=8.10','corr='+str(H/'b2_v42_correccions_B.json')];ns['main']()
 name,want=expected[which];got=sha(out/'cau'/name);report={'group':which,'input':'new F0 and V36; frozen measured metadata and historical V38 edge-correction table','AST':digest,'output':name,'sha256':got,'expected':want,'PASS':got==want};save(out/'VERIFY.json',report);assert report['PASS'],report;save(out/'COMPLETE.json',report)

def b3():
 out=O/'b3_baseline';out.mkdir()
 for x in ['cau','receipts']:(out/x).mkdir()
 fr=frozen_map('B3_V42_FROZEN.json');texts={k:Path(row['copy']).read_text() for k,row in fr['sources'].items()};h=literal_helpers(H/'b3_v42_replay.py',['literal_programs']);programs,evidence=h['literal_programs'](texts)
 lookup={p.name:p for p in (O/'sources_v29').glob('*.npy')}
 for d in ['b2_sony_A','b2_vixen','b2_sony_B']:
  assert json.loads((O/d/'COMPLETE.json').read_text())['PASS'];lookup.update({p.name:p for p in (O/d/'cau').glob('*.npy')})
 class ArrayInputs:
  def __getattr__(self,name):return getattr(np,name)
  def load(self,path,*args,**kw):return np.load(lookup.get(Path(path).name,path),*args,**kw)
 geom=json.loads((H/'v36_rgb_dependencies/geometry.json').read_text());M=np.array(geom['M_llenc_a_v23']);CX,CY=5361.768111973117,3775.747534140857
 ns=dict(np=ArrayInputs(),cv2=cv2,Path=Path,json=json,types=types,distance_transform_edt=distance_transform_edt,savejson=save,sha=sha,log=lambda s:print(s,flush=True),H=7506,W=10551,CX=CX,CY=CY,RS=440.60304883027544,SUN_XY=(CX,CY),GHOST_XY=tuple(M@np.array([2825,3988,1])),CAUF=out/'cau',CAU36=out/'cau',CAU38=out/'cau',CAU42=out/'cau',REB42=out/'receipts')
 exec(programs['common'],ns);exec(programs['comu'],ns);ns['comu']=types.SimpleNamespace(mascara_dada=ns['mascara_dada']);ns['_LIN']=json.loads((H/'v32g_r33_round1/receipts/R33_linealitat_sensor.json').read_text());exec(programs['lut'],ns);ns['LIN_X'],ns['LIN_LN']=ns['_lut']('sony')
 for stage in ['34','35','36','37']:
  if stage!='34':ns['REP_CANVIS_V'+str(int(stage)-1)]=ns['REP_CANVIS']
  exec(programs[stage],ns)
 save(out/'MANIFEST.json',{'stage':'B3 baseline','AST':evidence,'inputs':{k:str(v.relative_to(R)) for k,v in lookup.items()},'scope':'Historical pre-correction source, not candidate V85'})
 exec(programs['b3'],ns);ns['main']();rows=verify_arrays(out/'cau',fr,True);save(out/'VERIFY.json',rows);assert all(x['exact'] for x in rows),[x for x in rows if not x['exact']];save(out/'COMPLETE.json',{'PASS':True,'verified_arrays':len(rows)})

if __name__=='__main__':
 guard();stage=sys.argv[1];t=time.monotonic()
 try:
  if stage=='b3':b3()
  else:b2(stage)
  print('COMPLETE',stage,time.monotonic()-t,flush=True)
 except BaseException as e:
  save(O/(stage+'_FAILURE_'+str(time.time_ns())+'.json'),{'error':repr(e),'traceback':traceback.format_exc(),'seconds':time.monotonic()-t});raise
