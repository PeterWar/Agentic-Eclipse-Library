"""Pre-S4 WOW ablation, fixed R01 scalar continuation and display."""
from a13_filters import *
import a43_physical_boundary as boundary
from functools import partial

def main():
 src=O/'domain_pres4_R02/sources';assert json.loads((src.parent/'COMPLETE.json').read_text())['PASS']
 out=O/'filters_pres4_WOW_R02';out.mkdir();products=out/'products';(products/'filters').mkdir(parents=True)
 fr,deps,h,codes,ev=setup_programs();inp=dict(G_INPUT=src/'base_G.npy',SUP_INPUT=src/'support.npy',F_INPUT=src/'fusion_starless.npy',V_INPUT=src/'vixen_starless.npy',S_INPUT=src/'sony_starless.npy',REFINE_INPUT=H/'v29_profiles_round1/cau/refined_detail_receipt.json',GRAN_INPUT=H/'v29_profiles_round1/cau/gran_azimuthal_receipt.json',SIGMA_INPUT=sigma(),VIXEN_SUPPORT_INPUT=src.parent/'train_supports/vixen_support.npy',SONY_SUPPORT_INPUT=src.parent/'train_supports/sony_support.npy',WEIGHT_INPUT=O/'b3_baseline/cau/weight_vixen_v42.npy',S4_NPZ=src.parent/'s4/s4_recomposicio_box.npz',S4_SUP=src.parent/'s4/s4_support_new_box.npy')
 ns=dict(__name__='v85_pres4_WOW',np=np,cv2=cv2,ne=ne,Path=Path,json=json,hashlib=hashlib,ast=ast,time=time,gc=gc,ctypes=ctypes,sys=sys,gaussian_filter=gaussian_filter,map_coordinates=map_coordinates,gaussian_filter1d=gaussian_filter1d,R=R,O=products,T=deps,DEPS=deps,V42=out,claim=guard,CAU=inp['SIGMA_INPUT'].parent,SOURCES_DIR=src,S4_DIR=inp['S4_NPZ'].parent,DISPLAY_DIR=deps/'display',VARIANTS_INPUT=deps/'fine_variants_receipt.json',DYLIB_INPUT=deps/'sparse_conv.dylib',**inp)
 exec(codes['common'],ns);exec(codes['filters'],ns)
 # Preserve exactly the existing solver. Only remove the now-inapplicable
 # assertion that every unknown source pixel lies under the presentation Moon.
 tree=ast.parse(Path(boundary.__file__).read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PhysicalLunarBoundary');fn=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__'))
 dropped=[n for n in fn.body if isinstance(n,ast.Assert) and ast.unparse(n.test)=="not np.any(mask & ~z['support'])"]
 assert len(dropped)==1;fn.body=[n for n in fn.body if n not in dropped];scope=dict(vars(boundary));exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'preS4 unknown-domain constructor','exec'),scope);boundary.PhysicalLunarBoundary.__init__=scope['__init__']
 a=np.load(inp['G_INPUT']);m=np.load(inp['SUP_INPUT'])&np.isfinite(a)&(a>0);z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=map(int,z['box']);sl=(slice(y0,y1),slice(x0,x1));bc=out/'boundary';bc.mkdir()
 engine=boundary.install(ns,bc,engine_class=partial(boundary.PhysicalBiharmonic,validity=m[sl]))
 save(bc/'DOMAIN_OVERRIDE.json',{'authoritative_source':'domain_pres4_R02/FROZEN_ABLATION.json','unknown_mask':'not finite positive preS4 source in original support_v42 AND outside photoMoon','unknown_pixels':engine.n,'unknown_exterior_to_photo':int(np.sum(engine.mask&~z['support'])),'original_equation':'L^2 residual, same R01 scalar method','no_new_margin':True,'generic_adapter_labels_superseded':True})
 save(out/'MANIFEST.json',{'source_manifest':'domain_pres4_R02/MANIFEST.json','source_SHA':sha(inp['G_INPUT']),'support_SHA':sha(inp['SUP_INPUT']),'filter':'literal E2 WOW,11 scales; standard and bilateral; R01profileA/residualL2; frozen baseline LUT','no_MGN_yet':True,'scope':'source ablation; not a claim of recovered lost observations'})
 r,_=ns['coords']();full=np.ones_like(m);ent,frA=ns['farcit_perfil_A'](a,m,r);display=json.loads((O/'filters_baseline/products/E2_purs_filters.json').read_text());rep={}
 for tag,bilat in [('P04_WOW',False),('P05_WOW_bilateral',True)]:
  t=time.monotonic();q=ns['wow'](ent,full,11,bilat);assert np.isfinite(q[m]).all();lo,hi=display[tag]['display'];u=np.round(np.clip(np.where(m,(q-lo)/(hi-lo),0),0,1)*65535).astype('uint16');np.save(products/'filters'/(tag+'_u16.npy'),u);np.save(products/'filters'/(tag+'_float.npy'),np.where(m,q,np.nan).astype('float32'));rep[tag]={'display':[lo,hi],'sha256':sha(products/'filters'/(tag+'_u16.npy'))};del q,u;gc.collect();print('PRES4_WOW_DONE',tag,time.monotonic()-t,flush=True)
 rep['fill_A']=frA;save(products/'E2_purs_filters.json',rep);save(out/'COMPLETE.json',{'PASS':True,'meaning':'numerical integrity only','products':rep});print('PRES4_WOW_COMPLETE',flush=True)

if __name__=='__main__':guard();main()
