from a5_recompose import *
from scipy.ndimage import gaussian_filter
from scipy.optimize import nnls

def s4():
 ns,v36=context();fr=frozen_map('S4_V51_FROZEN.json');out=O/'s4_baseline';out.mkdir();(out/'cau').mkdir()
 h=literal_helpers(H/'s4_v51_replay.py',['core_program','require'],['SOURCE_SHA'])
 # Adapt only the missing NPZ box input to its preserved exact metadata.
 source=H/'s4_v51_replay.py';tree=ast.parse(source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='core_program');fn=copy.deepcopy(fn)
 at=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='nodes')
 fn.body.insert(at+1,ast.parse("nodes[0].value=ast.Name(id='FROZEN_BOX',ctx=ast.Load())").body[0]);ast.fix_missing_locations(fn);exec(compile(ast.Module(body=[fn],type_ignores=[]),'S4 exact box metadata adaptation','exec'),h)
 code,digest=h['core_program'](fr['sources']['s4']['copy']);old=json.loads((H/'s4_v51_round1/cau/S4_CORE.json').read_text());box=old['box'];assert box==[3277,4273,4863,5859]
 ns.update(CAU=out/'cau',CAU38=H/'v38_limb_round1/cau',CAU36=O/'sources_v36/cau',A1_RECEIPT=H/'v38_limb_round1/receipts/A1_franja_font.json',B2_CAU=O/'b2_vixen/cau',FROZEN_BOX=box,FLAT_CENTRE_YX={'sony':(2660.,4000.)},FLAT_SIGMA_PX=32.)
 definition(v36['sources']['common32']['copy'],'flat_ripple_correction',ns);definition(fr['sources']['comu38']['copy'],'upsample',ns)
 save(out/'MANIFEST.json',{'stage':'S4 historical baseline','AST':digest,'adaptation':'NPZ box-only lookup replaced with preserved S4_CORE exact box','box':box})
 exec(code,ns);core={'guardarail_1_vixen_total_v38':ns['g1'],'box':box,'fotogrames':ns['info'],'TIERS':ns['TIERS'],'GT':ns['GT'],'scope':'S4 numerical core and first guard only'};save(out/'cau/S4_CORE.json',core)
 assert core==old,(core['guardarail_1_vixen_total_v38'],old['guardarail_1_vixen_total_v38'])
 rows=[]
 for name in ['s4_recomposicio_box.npz','s4_support_new_box.npy']:
  got=sha(out/'cau'/name);want=fr['references'][name]['sha256'];rows.append({'name':name,'sha256':got,'expected':want,'exact':got==want})
 save(out/'VERIFY.json',rows);assert all(x['exact'] for x in rows),rows;save(out/'COMPLETE.json',{'PASS':True,'files':rows,'core_exact':True})

def d4():
 fr=frozen_map('D4_D4B_FROZEN.json');out=O/'d4_baseline';out.mkdir();(out/'products').mkdir();h=literal_helpers(H/'d4_d4b_replay.py',['programs']);texts={k:Path(v['copy']).read_text() for k,v in fr['sources'].items()};code,evidence=h['programs'](texts)
 def current_claim():assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CID
 ns=dict(__name__='v85_d4_baseline',np=np,Path=Path,json=json,hashlib=hashlib,ast=ast,time=time,gaussian_filter=gaussian_filter,nnls=nnls,R=R,O=out/'products',T=H/'d4_d4b_dependencies',V42=O/'b3_baseline',S4_DIR=O/'s4_baseline/cau',claim=current_claim,
 D3_INPUT=H/'star_models_round1/products/D3_empirical_pilot.json',STARS_INPUT=H/'star_catalog_round1/products/estrelles_v42.json',F_INPUT=O/'b3_baseline/cau/fusion_total_v42.npy',V_INPUT=O/'b2_vixen/cau/vixen_total_v38.npy',S_INPUT=O/'b3_baseline/cau/sony_corrected_total_v42.npy',SUP_INPUT=O/'b3_baseline/cau/support_v42.npy')
 save(out/'MANIFEST.json',{'stage':'D4/D4b baseline','AST':evidence,'static_models':'preserved empirical star models/catalog, new source pixels from RAW'})
 exec(code[0],ns);exec(code[1],ns);stage=sha(out/'products/sources/vixen_starless.npy');save(out/'D4_STAGE.json',{'sha256':stage,'expected':fr['D4_vixen_original_sha'],'exact':stage==fr['D4_vixen_original_sha']});assert stage==fr['D4_vixen_original_sha'];exec(code[2],ns)
 actual={str(p.relative_to(out/'products')):p for p in (out/'products').rglob('*') if p.is_file()};assert set(actual)==set(fr['references']),{'missing':list(set(fr['references'])-set(actual)),'extra':list(set(actual)-set(fr['references']))}
 rows=[]
 for name,p in actual.items():
  if name=='D4_sources.json':continue
  got=sha(p);want=fr['references'][name]['sha256'];rows.append({'name':name,'sha256':got,'expected':want,'exact':got==want})
 a=json.loads((out/'products/D4_sources.json').read_text());b=json.loads((H/'d4_d4b_round1/products/D4_sources.json').read_text())
 for tag in ['fusion','vixen','sony']:
  for field in ['source','output']:a['outputs'][tag][field]=b['outputs'][tag][field]
 a['limb_source']['file']=b['limb_source']['file'];jexact=a==b
 save(out/'VERIFY.json',{'files':rows,'D4_JSON_normalized_exact':jexact});assert jexact and all(x['exact'] for x in rows),[x for x in rows if not x['exact']];save(out/'COMPLETE.json',{'PASS':True,'verified_files':len(actual),'scope':'Historical source replay conditioned on preserved measured metadata'})

if __name__=='__main__':
 guard();stage=sys.argv[1];t=time.monotonic()
 try:
  {'s4':s4,'d4':d4}[stage]();print('COMPLETE',stage,time.monotonic()-t,flush=True)
 except BaseException as e:
  save(O/(stage+'_FAILURE_'+str(time.time_ns())+'.json'),{'error':repr(e),'traceback':traceback.format_exc(),'seconds':time.monotonic()-t});raise
