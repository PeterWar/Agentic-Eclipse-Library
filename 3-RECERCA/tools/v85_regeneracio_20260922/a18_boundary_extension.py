"""Declared numerical padding: harmonic log-residual inside the existing Moon only.
This is not recovered radiance. All observed exterior samples stay exact.
"""
from a4_sources import *
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import cg

class LunarBoundary:
 def __init__(self,out):
  z=np.load(O/'current_lunar_support.npz');self.mask=z['support'];x0,y0,x1,y1=z['box'];self.sl=(slice(y0,y1),slice(x0,x1));self.out=out;self.cache={};self.receipts=[]
  mask=self.mask;h,w=mask.shape;idx=np.full(mask.shape,-1,np.int32);idx[mask]=np.arange(mask.sum());iy,ix=np.where(mask);n=len(iy);rows=[np.arange(n)];cols=[np.arange(n)];values=[np.full(n,4.,np.float64)];self.outer=[]
  assert not(mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any())
  for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
   ny,nx=iy+dy,ix+dx;nb=idx[ny,nx];inside=nb>=0;rows.append(np.flatnonzero(inside));cols.append(nb[inside]);values.append(np.full(inside.sum(),-1.));self.outer.append((np.flatnonzero(~inside),ny[~inside],nx[~inside]))
  self.A=coo_matrix((np.concatenate(values),(np.concatenate(rows),np.concatenate(cols))),shape=(n,n)).tocsr();self.n=n

 def extend(self,result,source,m,r,nodes,profile,islog,method):
  ent,receipt=result;mask=self.mask;sl=self.sl;assert not m[sl][mask].any(),'Moon must already be excluded from operator domain'
  radial=np.interp(r[sl],nodes,profile).astype(np.float64);raw=np.asarray(source[sl],np.float64);known=(raw if islog else np.log(np.maximum(raw,1e-30)))-radial;known=np.where(m[sl],known,0);assert np.isfinite(known).all()
  b=np.zeros(self.n,np.float64)
  for ids,yy,xx in self.outer:b[ids]+=known[yy,xx]
  key=hashlib.sha256(b.tobytes()+radial[mask].tobytes()).hexdigest();t=time.monotonic()
  if key in self.cache:u,metric=self.cache[key];cached=True
  else:
   iterations=[0]
   def callback(x):iterations[0]+=1
   u,info=cg(self.A,b,rtol=1e-8,atol=1e-10,maxiter=4000,callback=callback);res=self.A@u-b;assert info==0,(method,info)
   edge=np.concatenate([known[yy,xx] for ids,yy,xx in self.outer]);assert u.min()>=edge.min()-1e-5 and u.max()<=edge.max()+1e-5
   metric={'iterations':iterations[0],'residual_l2':float(np.linalg.norm(res)),'residual_max':float(np.max(np.abs(res))),'boundary_min_max':list(map(float,[edge.min(),edge.max()])),'extension_min_max':list(map(float,[u.min(),u.max()]))};self.cache[key]=(u,metric);cached=False
  block=ent[sl];values=radial[mask]+u;block[mask]=(values if islog else np.exp(values)).astype(np.float32);assert np.isfinite(block[mask]).all()
  row={'method':method,'input_is_log':islog,'pixels':self.n,'cached':cached,'seconds':time.monotonic()-t,**metric};self.receipts.append(row);save(self.out/'BOUNDARY_SOLVES.json',self.receipts)
  return ent,{**receipt,'lunar_boundary':'original radial profile plus discrete harmonic log-residual; Dirichlet values from observed exterior; C0 only','lunar_mask_pixels':self.n,'numerical_padding_only':True,'exterior_values_unchanged':True,'solver':row}

def install(ns,out):
 engine=LunarBoundary(out);ns['_lunar_boundary_extend']=engine.extend;deps=H/'filters_v58_dependencies';evidence={}
 for name,filename,var,islog in [('farcit_perfil','b4c_purs_v42.py','a',False),('farcit_perfil_A','b4c_purs_v42.py','a',False),('farcit_perfil_ln_A','comu37.py','L',True)]:
  tree=ast.parse((deps/filename).read_text());fn=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name));before=ast.dump(fn,include_attributes=False)
  returns=[n for n in fn.body if isinstance(n,ast.Return)];assert len(returns)==1;n=returns[0];n.value=ast.Call(func=ast.Name(id='_lunar_boundary_extend',ctx=ast.Load()),args=[n.value,*[ast.Name(id=k,ctx=ast.Load()) for k in [var,'m','r','nodes','p']],ast.Constant(islog),ast.Constant(name)],keywords=[]);ast.fix_missing_locations(fn)
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'V85 lunar harmonic boundary only','exec'),ns);evidence[name]={'source_AST':hashlib.sha256(before.encode()).hexdigest(),'adapted_AST':hashlib.sha256(ast.dump(fn,include_attributes=False).encode()).hexdigest()}
 save(out/'BOUNDARY_METHOD.json',{'method':'discrete harmonic log-residual on exact existing lunar-photo mask','purpose':'numerical filter padding, not photographed/recovered corona','no_observed_exterior_change':True,'no_new_radius_or_mask_margin':True,'C1_claim':False,'source_AST_and_delta':evidence});return engine
