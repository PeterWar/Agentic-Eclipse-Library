"""Isolate historical source producers; explicitly reuse frozen measured geometry.
Run stages in separate processes so F2 monkey patches cannot leak into V29 grid.
"""
from pathlib import Path
import sys,os,json,ast,copy,time,hashlib,datetime,traceback
import numpy as np,cv2,rawpy
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parents[4];O=R/'4-RESULTATS/v97_refundacio_20260924/cadena_raw';H=R/'2-ARXIU/reconstruccio_compactacio_20260915/raw_replay'
sys.path.insert(0,str(H/'frozen_code'));import comu,f0,f2
CID='CLAUDE_REFUNDACIO_V97_20260924';TRAIN={'vixen':'VIXEN','sony':'SONYTOT'}
f0dirs={t:O/('calibration_'+T) for t,T in TRAIN.items()};f12dirs={t:H/('f12_round1_'+T) for t,T in TRAIN.items()}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n')
def definition(path,name,ns):
 tree=ast.parse(Path(path).read_text());nodes=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name];assert len(nodes)==1,(path,name)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns);return ns[name]
def frozen_map(name):
 j=json.loads((H/name).read_text())
 for key,row in j.get('sources',{}).items():
  copyrow=row['copy'];old=copyrow['path'] if isinstance(copyrow,dict) else copyrow;wanted=copyrow['sha256'] if isinstance(copyrow,dict) else row['sha256']
  tail=old.split('/raw_replay/',1)[1];p=H/tail;assert p.exists() and sha(p)==wanted,(key,p);row['copy']=str(p)
 return j
def guard():
 pass  # 30-09-2026: regla de l'escriptor únic retirada per Pere
 for t,p in f0dirs.items():assert json.loads((p/'COMPLETE.json').read_text())['PASS'],t
 for t,T in TRAIN.items():comu.TRENS[T]=dict(comu.TRENS[T],dir=str(O/'raw_inputs'/T))
 comu.TRENS['SONY']['dir']=str(O/'raw_inputs/SONYTOT');cv2.setNumThreads(6)
def context():
 frozen=frozen_map('V36_RGB_FROZEN.json');out=O/'sources_v36';out.mkdir(exist_ok=True)
 for q in [out/'cau',out/'output/v36_20260908/4-rebuts']:q.mkdir(parents=True,exist_ok=True)
 c=dict(globals(),frozen=frozen,out=out,roundno=1,offset_row={'path':str(H/'offset_round1/offset_model.json')},r33_row={'path':str(H/'v32g_r33_round1/receipts/R33_linealitat_sensor.json')})
 tree=ast.parse((H/'v36_rgb_replay.py').read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');body=next(n.body for n in run.body if isinstance(n,ast.Try));start=next(i for i,n in enumerate(body) if isinstance(n,ast.ClassDef) and n.name=='ReadRun');end=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='f2.Ctx.plans')
 nodes=copy.deepcopy(body[start:end+1]);exec(compile(ast.Module(body=nodes,type_ignores=[]),'V36 literal namespace only','exec'),c);return c['ns'],frozen

def verify_arrays(folder,fr,basename=False):
 expected={Path(k).name:v for k,v in fr['references'].items() if k.endswith('.npy') and (basename or (k.startswith('cau_final/') and not k.endswith('_sky.npy') and not k.endswith('resolution_sigma.npy')))}
 actual={p.name:p for p in folder.glob('*.npy')}
 assert set(actual)==set(expected),{'missing':sorted(set(expected)-set(actual)),'extra':sorted(set(actual)-set(expected))}
 rows=[]
 for name,p in sorted(actual.items()):
  ref=expected[name];h=sha(p);want=ref.get('sha256',ref.get('file_sha256'));assert want,ref
  rows.append({'name':name,'sha256':h,'expected':want,'exact':h==want})
 assert rows,'No reference checks';return rows

def grid():
 origplans=f2.Ctx.plans;origwindow=f2.finestra;ns,fr=context();f2.Ctx.plans=origplans;f2.finestra=origwindow
 out=O/'sources_v29';out.mkdir(exist_ok=True);fr=frozen_map('V29_SOURCES_FROZEN.json')
 ns.update(CAU=out,HERE=out,M=np.eye(2,3),SUN_XY=(ns['CX'],ns['CY']),FINAL_GRID=True,savejson=save)
 definition(fr['sources']['common']['copy'],'coords',ns)
 tree=ast.parse(Path(fr['sources']['grid']['copy']).read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');removed=[]
 class DropSky(ast.NodeTransformer):
  def visit_Assign(self,n):
   if len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['oldsky','sky']:removed.append(ast.unparse(n));return None
   return self.generic_visit(n)
  def visit_Expr(self,n):
   if isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='np.save' and any(isinstance(x,ast.Constant) and x.value=='_sky.npy' for x in ast.walk(n)):
    removed.append(ast.unparse(n));return None
   return self.generic_visit(n)
  def visit_Delete(self,n):
   n.targets=[x for x in n.targets if not (isinstance(x,ast.Name) and x.id in ['sky','oldsky'])];return n if n.targets else None
 fn=DropSky().visit(copy.deepcopy(fn));assert len(removed)==3,removed;ast.fix_missing_locations(fn)
 save(out/'MANIFEST.json',{'stage':'V29 observed supports/weights on existing final canvas','calibrations':'new RAW reconstructed and hash-exact','frozen_measurements':['F1.3 registration','F2.2 coherence','V27 geometry'],'adaptations':removed,'scientific_operator':'unchanged except unused sky output omitted','canvas':[10551,7506]})
 exec(compile(ast.Module(body=[fn],type_ignores=[]),'isolated V29 direct grid','exec'),ns);ns['main']();rows=verify_arrays(out,fr);save(out/'VERIFY.json',rows);assert all(x['exact'] for x in rows),rows
 save(out/'COMPLETE.json',{'PASS':True,'verified_arrays':len(rows),'scope':'Historical RAW-to-source support/weight reproduction with frozen measured metadata'})

def v36():
 ns,fr=context();out=O/'sources_v36'
 save(out/'MANIFEST.json',{'stage':'V36 RGB samples and per-frame fields','calibrations':'new hash-exact from RAW','reuse_measurements':['F1.2','F1.3','F2.2','offset_model','R33_linealitat_sensor','V27 geometry'],'source_pins':fr['sources']})
 definition(fr['sources']['a1']['copy'],'main',ns)();definition(fr['sources']['b1']['copy'],'main',ns)();rows=verify_arrays(out/'cau',fr,True);save(out/'VERIFY.json',rows);assert all(x['exact'] for x in rows),[x for x in rows if not x['exact']]
 save(out/'COMPLETE.json',{'PASS':True,'verified_arrays':len(rows)})

if __name__=='__main__':
 guard();stage=sys.argv[1];t=time.monotonic()
 try:
  {'grid':grid,'v36':v36}[stage]();print('COMPLETE',stage,time.monotonic()-t,flush=True)
 except BaseException as e:
  save(O/(stage+'_FAILURE_'+str(time.time_ns())+'.json'),{'error':repr(e),'traceback':traceback.format_exc(),'seconds':time.monotonic()-t});raise
