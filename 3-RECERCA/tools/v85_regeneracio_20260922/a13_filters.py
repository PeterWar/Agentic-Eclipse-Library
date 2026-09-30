"""Full-canvas V58 filter operators on explicitly supplied regenerated sources."""
from a4_sources import *
import ctypes,gc,tempfile,shutil
import numexpr as ne
from scipy.ndimage import gaussian_filter,map_coordinates,gaussian_filter1d

def setup_programs():
 fr=frozen_map('FILTERS_V58_FROZEN.json');deps=H/'filters_v58_dependencies'
 for name,row in fr['fixed_inputs'].items():
  p=deps/name;assert sha(p)==row['copy']['sha256']==row['sha256'],name
 source=H/'filters_v58_replay.py';tree=ast.parse(source.read_text());wanted=['OPERATORS','GROUPS','ROUTES','HELPER_PATHS'];nodes=[]
 for n in tree.body:
  if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in wanted:nodes.append(n)
  if isinstance(n,ast.For) and ast.unparse(n.target)=='_p':nodes.append(n)
  if isinstance(n,ast.FunctionDef) and n.name in ['names','programs']:nodes.append(n)
 ns=dict(Path=Path,ast=ast,copy=copy,hashlib=hashlib);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
 codes,ev=ns['programs']({k:Path(v['copy']).read_text() for k,v in fr['sources'].items()});assert ev==fr['AST'];return fr,deps,ns,codes,ev

def sigma():
 target=O/'fixed_inputs';target.mkdir(exist_ok=True);p=target/'resolution_sigma.npy'
 fr=json.loads((H/'V29_SOURCES_FROZEN.json').read_text());row=fr['references']['cau_final/resolution_sigma.npy']
 if p.exists():
  assert sha(p)==row['sha256'];return p
 j=json.loads((R/'3-RECERCA/tools/v29/cau_final/coherent_resolution.json').read_text());grid=np.array(j['grid_sigma'],np.float32);a=cv2.resize(cv2.erode(grid,np.ones((3,3),np.uint8)),(10551,7506),interpolation=cv2.INTER_LINEAR)
 y,x=np.ogrid[:7506,:10551];r=np.hypot(y-3775.747534140857,x-5361.768111973117).astype(np.float32);q=np.clip((r/440.60304883027544-2)/(.65),0,1);w=q*q*(3-2*q);a=(1-w)*.7+w*a;np.save(p,a)
 assert sha(p)==row['sha256'];save(target/'resolution_receipt.json',{'sha256':sha(p),'exact':True,'from':'retained coherent_resolution grid_sigma, historical erode/resize/blend recipe'});return p

def run(label,sources,baseline=False,lunar_domain=False,only=None,harmonic=False,biharmonic=False,screened=False):
 assert sources.is_dir()
 if not lunar_domain:assert sha(sources/'support.npy')=='c03e9faf570deffcc9ab63dec23f06dac9e8f71de8d76c7b36270de46a27d695','This adapter requires unchanged physical support unless explicit lunar domain'
 else:
  domain=json.loads((sources.parent/'MANIFEST.json').read_text());assert sha(sources/'support.npy')==domain['sources']['physical']['operator_sha256'];assert (domain['physical_radiance_arrays_unchanged'] or domain.get('physical_support_unchanged')) and not domain['new_output_radius_or_margin']
 fr,deps,h,codes,ev=setup_programs();out=O/label;out.mkdir();products=out/'products';(products/'filters').mkdir(parents=True);(out/'scratch').mkdir();tempfile.tempdir=str(out/'scratch')
 inp=dict(G_INPUT=sources/'base_G.npy',SUP_INPUT=sources/'support.npy',F_INPUT=sources/'fusion_starless.npy',V_INPUT=sources/'vixen_starless.npy',S_INPUT=sources/'sony_starless.npy',REFINE_INPUT=H/'v29_profiles_round1/cau/refined_detail_receipt.json',GRAN_INPUT=H/'v29_profiles_round1/cau/gran_azimuthal_receipt.json',SIGMA_INPUT=sigma(),VIXEN_SUPPORT_INPUT=O/'sources_v29/vixen_support.npy',SONY_SUPPORT_INPUT=O/'sources_v29/sony_support.npy',WEIGHT_INPUT=O/'b3_baseline/cau/weight_vixen_v42.npy',S4_NPZ=O/'s4_baseline/cau/s4_recomposicio_box.npz',S4_SUP=O/'s4_baseline/cau/s4_support_new_box.npy')
 if lunar_domain:
  inp.update(VIXEN_SUPPORT_INPUT=sources.parent/'train_supports/vixen_support.npy',SONY_SUPPORT_INPUT=sources.parent/'train_supports/sony_support.npy',S4_NPZ=sources.parent/'s4/s4_recomposicio_box.npz',S4_SUP=sources.parent/'s4/s4_support_new_box.npy')
 def claim():assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CID
 ops=h['OPERATORS'] if only is None else only.split(',');assert all(op in h['OPERATORS'] for op in ops)
 rows={k:{'path':str(p.relative_to(R)),'sha256':sha(p)} for k,p in inp.items()};save(out/'MANIFEST.json',{'inputs':rows,'source_manifest':str(sources),'AST':ev,'operators':'literal V58 on full canvas','operator_list':ops,'canvas':[10551,7506],'baseline_exact_expected':baseline,'supported_mask':'explicit existing lunar-photo filter domain' if lunar_domain else 'unchanged baseline physical support','frozen_display':True});stages=[]
 for op in ops:
  claim();t=time.monotonic();print('FILTER_START',op,flush=True)
  ns=dict(__name__='v85_filter_literal',np=np,cv2=cv2,ne=ne,Path=Path,json=json,hashlib=hashlib,ast=ast,time=time,gc=gc,ctypes=ctypes,sys=sys,gaussian_filter=gaussian_filter,map_coordinates=map_coordinates,gaussian_filter1d=gaussian_filter1d,R=R,O=products,T=deps,DEPS=deps,V42=out,claim=claim,CAU=inp['SIGMA_INPUT'].parent,SOURCES_DIR=sources,S4_DIR=inp['S4_NPZ'].parent,DISPLAY_DIR=deps/'display',VARIANTS_INPUT=deps/'fine_variants_receipt.json',DYLIB_INPUT=deps/'sparse_conv.dylib',**inp)
  exec(codes['common'],ns);exec(codes['filters'],ns)
  if (harmonic or biharmonic or screened) and op in ['e2_purs.py','e3_isotropic.py']:
   assert lunar_domain and not baseline
   if screened:
    from a29_screened_boundary import install
   elif biharmonic:
    from a24_biharmonic_boundary import install
   else:
    from a18_boundary_extension import install
   bcdir=out/(op+'.boundary');bcdir.mkdir();extension=install(ns,bcdir)
  if op=='e6_native_cdf.py':exec(codes['native'],ns)
  exec(codes[op],ns);del ns;gc.collect();row={'operator':op,'seconds':time.monotonic()-t};stages.append(row);save(out/(op+'.COMPLETE.json'),row);print('FILTER_DONE',row,flush=True)
 actual={str(p.relative_to(products)):p for p in products.rglob('*') if p.is_file()};expected={n for op in ops for n in h['names'](op)};assert set(actual)==expected;rows=[]
 for name,p in sorted(actual.items()):
  got=sha(p);ref=fr['references'][name];row={'name':name,'sha256':got}
  if name.endswith('.npy'):
   a=np.load(p,mmap_mode='r');assert list(a.shape)==[7506,10551];dtype='bool' if name.endswith('_support.npy') else ('uint16' if name.endswith('_u16.npy') else 'float32');assert a.dtype==np.dtype(dtype);row.update(shape=list(a.shape),dtype=str(a.dtype))
  if baseline:row.update(expected=ref['sha256'],exact=got==ref['sha256'])
  rows.append(row)
 save(out/'PRODUCTS.json',rows)
 if baseline:assert all(r['exact'] for r in rows),[r for r in rows if not r['exact']]
 save(out/'COMPLETE.json',{'PASS':True,'stages':stages,'products':len(rows),'baseline_exact':baseline,'scientific_QA':'separate from numerical integrity'})

if __name__=='__main__':
 guard();only=next((a.split('=',1)[1] for a in sys.argv if a.startswith('--only=')),None);run(sys.argv[1],Path(sys.argv[2]),'--baseline' in sys.argv,'--lunar-domain' in sys.argv,only,'--harmonic' in sys.argv,'--biharmonic' in sys.argv,'--screened' in sys.argv)
