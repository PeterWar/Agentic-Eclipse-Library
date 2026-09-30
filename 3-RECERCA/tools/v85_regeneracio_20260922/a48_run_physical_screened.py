"""Physical-support scalar test with fixed unit tension, same as selected RGB E3."""
from a13_filters import *
from a43_physical_boundary import install_physical

def main(family):
 assert family=='E2';out=O/'filters_physical_T_E2';out.mkdir();products=out/'products';(products/'filters').mkdir(parents=True);fr,deps,h,codes,ev=setup_programs();src=O/'d4_baseline/products/sources';inp=dict(G_INPUT=src/'base_G.npy',SUP_INPUT=src/'support.npy',F_INPUT=src/'fusion_starless.npy',V_INPUT=src/'vixen_starless.npy',S_INPUT=src/'sony_starless.npy',REFINE_INPUT=H/'v29_profiles_round1/cau/refined_detail_receipt.json',GRAN_INPUT=H/'v29_profiles_round1/cau/gran_azimuthal_receipt.json',SIGMA_INPUT=sigma(),VIXEN_SUPPORT_INPUT=O/'sources_v29/vixen_support.npy',SONY_SUPPORT_INPUT=O/'sources_v29/sony_support.npy',WEIGHT_INPUT=O/'b3_baseline/cau/weight_vixen_v42.npy',S4_NPZ=O/'s4_baseline/cau/s4_recomposicio_box.npz',S4_SUP=O/'s4_baseline/cau/s4_support_new_box.npy')
 def claim():guard()
 ns=dict(__name__='v85_R02_physical',np=np,cv2=cv2,ne=ne,Path=Path,json=json,hashlib=hashlib,ast=ast,time=time,gc=gc,ctypes=ctypes,sys=sys,gaussian_filter=gaussian_filter,map_coordinates=map_coordinates,gaussian_filter1d=gaussian_filter1d,R=R,O=products,T=deps,DEPS=deps,V42=out,claim=claim,CAU=inp['SIGMA_INPUT'].parent,SOURCES_DIR=src,S4_DIR=inp['S4_NPZ'].parent,DISPLAY_DIR=deps/'display',VARIANTS_INPUT=deps/'fine_variants_receipt.json',DYLIB_INPUT=deps/'sparse_conv.dylib',**inp)
 exec(codes['common'],ns);exec(codes['filters'],ns);bcdir=out/'boundary';bcdir.mkdir();engine=install_physical(ns,bcdir,screened=True);save(out/'MANIFEST.json',{'family':family,'sources':{k:{'path':str(v.relative_to(R)),'sha256':sha(v)} for k,v in inp.items()},'frozen_ABLATION':'physical_boundary_R02/SCREENED_E2_FROZEN.json','AST':ev,'same_final_canvas':True,'existing_output_moon_masks':'unchanged, applied only in PSB assembly; these operator outputs retain physical support'})
 if family=='E3':exec(codes['e3_isotropic.py'],ns)
 else:
  a=np.load(inp['G_INPUT']);m=np.load(inp['SUP_INPUT'])&np.isfinite(a)&(a>0);r,_=ns['coords']();full=np.ones_like(m);ent,frB=ns['farcit_perfil'](a,m,r);rep={}
  displays=json.loads((O/'filters_baseline/products/E2_purs_filters.json').read_text())
  for tag in ['P03_MGN','P04_WOW','P05_WOW_bilateral']:
   start=time.monotonic()
   if tag=='P03_MGN':q=ns['mgn'](np.maximum(ent,0),full,limits=[float(a[m].min()),float(a[m].max())])
   elif tag=='P04_WOW':
    entA,frA=ns['farcit_perfil_A'](a,m,r);q=ns['wow'](entA,full,11,False)
   else:q=ns['wow'](entA,full,11,True)
   lo,hi=displays[tag]['display'];assert np.isfinite(q[m]).all();u=np.round(np.clip(np.where(m,(q-lo)/(hi-lo),0),0,1)*65535).astype('uint16');np.save(products/'filters'/(tag+'_u16.npy'),u);np.save(products/'filters'/(tag+'_float.npy'),np.where(m,q,np.nan).astype('float32'));rep[tag]={'display':[lo,hi],'sha256':sha(products/'filters'/(tag+'_u16.npy'))};del q,u;gc.collect();print('PHYSICAL_FILTER_DONE',tag,time.monotonic()-start,flush=True)
  rep['fill_B']=frB;rep['fill_A']=frA;save(products/'E2_purs_filters.json',rep)
 products_rows=[]
 for p in products.rglob('*'):
  if p.is_file():products_rows.append({'path':str(p.relative_to(products)),'sha256':sha(p)})
 save(out/'COMPLETE.json',{'PASS':True,'meaning':'numerical integrity; scientific acceptance separate','products':products_rows});print('PHYSICAL_COMPLETE',family,flush=True)
if __name__=='__main__':guard();main(sys.argv[1])
