"""Unclipped discrete biharmonic padding inside the exact lunar photo only.
Exterior radiance is immutable. This estimates an operator boundary, not data.
"""
from a18_boundary_extension import *
from scipy.sparse.linalg import LinearOperator
sys.path.insert(0,str(O/'runtime_deps'))
import pyamg

class BiharmonicBoundary(LunarBoundary):
 def __init__(self,out):
  super().__init__(out)
  self.laplace=self.A;mask=self.mask;idx=np.full(mask.shape,-1,np.int32);idx[mask]=np.arange(mask.sum());iy,ix=np.where(mask);rows=[];cols=[];values=[];self.outer2=[]
  stencil=[(0,0,20),(-1,0,-8),(1,0,-8),(0,-1,-8),(0,1,-8),(-2,0,1),(2,0,1),(0,-2,1),(0,2,1),(-1,-1,2),(-1,1,2),(1,-1,2),(1,1,2)]
  for dy,dx,c in stencil:
   yy,xx=iy+dy,ix+dx;nb=idx[yy,xx];inside=nb>=0;rows.append(np.flatnonzero(inside));cols.append(nb[inside]);values.append(np.full(inside.sum(),c,np.float64));self.outer2.append((np.flatnonzero(~inside),yy[~inside],xx[~inside],c))
  self.A=coo_matrix((np.concatenate(values),(np.concatenate(rows),np.concatenate(cols))),shape=(self.n,self.n)).tocsr()
  assert (self.A-self.A.T).nnz==0
  ml=pyamg.smoothed_aggregation_solver(self.laplace,symmetry='symmetric',presmoother=('gauss_seidel',{'sweep':'symmetric'}),postsmoother=('gauss_seidel',{'sweep':'symmetric'}));self.ml=ml;P=ml.aspreconditioner(cycle='V');self.M=LinearOperator(self.A.shape,matvec=lambda v:P@(P@v),dtype=np.float64)
  save(out/'BIHARMONIC_SOLVER.json',{'pyamg':pyamg.__version__,'stencil':stencil,'unknowns':self.n,'matrix_nnz':self.A.nnz,'boundary':'two observed exterior pixel rings fixed; no mask expansion','clip':False,'preconditioner':'squared symmetric AMG V-cycle for Dirichlet Laplace','interpretation':'discrete clamped extension, no claim of exact continuum C1 at pixelated edge'})

 def extend(self,result,source,m,r,nodes,profile,islog,method):
  ent,receipt=result;mask=self.mask;sl=self.sl;assert not m[sl][mask].any()
  radial=np.interp(r[sl],nodes,profile).astype(np.float64);raw=np.asarray(source[sl],np.float64);known=(raw if islog else np.log(np.maximum(raw,1e-30)))-radial
  b=np.zeros(self.n,np.float64)
  for ids,yy,xx,c in self.outer2:
   assert m[sl][yy,xx].all() and np.isfinite(known[yy,xx]).all()
   b[ids]-=c*known[yy,xx]
  key=hashlib.sha256(b.tobytes()+radial[mask].tobytes()).hexdigest();t=time.monotonic()
  if key in self.cache:u,metric=self.cache[key];cached=True
  else:
   iterations=[0]
   def callback(x):
    iterations[0]+=1
    if iterations[0]%100==0:print('BIHARMONIC_ITER',method,iterations[0],flush=True)
   u,info=cg(self.A,b,M=self.M,rtol=1e-9,atol=1e-10,maxiter=1500,callback=callback);res=self.A@u-b;assert info==0,(method,info)
   edge=np.concatenate([known[yy,xx] for ids,yy,xx,c in self.outer2 if len(ids)]);metric={'iterations':iterations[0],'residual_l2':float(np.linalg.norm(res)),'residual_max':float(np.max(np.abs(res))),'boundary_min_max':list(map(float,[edge.min(),edge.max()])),'extension_min_max':list(map(float,[u.min(),u.max()]))};self.cache[key]=(u,metric);cached=False
  values=radial[mask]+u;assert np.isfinite(values).all() and values.min()>-70 and values.max()<70,'unbounded operator padding';ent[sl][mask]=(values if islog else np.exp(values)).astype(np.float32)
  row={'method':method,'input_is_log':islog,'pixels':self.n,'cached':cached,'seconds':time.monotonic()-t,**metric};self.receipts.append(row);save(self.out/'BOUNDARY_SOLVES.json',self.receipts);print('BIHARMONIC_SOLVED',row,flush=True)
  return ent,{**receipt,'lunar_boundary':'original radial profile plus unclipped discrete biharmonic log residual; two exterior rings fixed','lunar_mask_pixels':self.n,'numerical_padding_only':True,'exterior_values_unchanged':True,'solver':row}

def install(ns,out,engine_class=BiharmonicBoundary):
 engine=engine_class(out);ns['_lunar_boundary_extend']=engine.extend;deps=H/'filters_v58_dependencies';evidence={}
 for name,filename,var,islog in [('farcit_perfil','b4c_purs_v42.py','a',False),('farcit_perfil_A','b4c_purs_v42.py','a',False),('farcit_perfil_ln_A','comu37.py','L',True)]:
  tree=ast.parse((deps/filename).read_text());fn=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name));before=ast.dump(fn,include_attributes=False);returns=[n for n in fn.body if isinstance(n,ast.Return)];assert len(returns)==1;n=returns[0];n.value=ast.Call(func=ast.Name(id='_lunar_boundary_extend',ctx=ast.Load()),args=[n.value,*[ast.Name(id=k,ctx=ast.Load()) for k in [var,'m','r','nodes','p']],ast.Constant(islog),ast.Constant(name)],keywords=[]);ast.fix_missing_locations(fn);exec(compile(ast.Module(body=[fn],type_ignores=[]),'V85 biharmonic padding only','exec'),ns);evidence[name]={'source_AST':hashlib.sha256(before.encode()).hexdigest(),'adapted_AST':hashlib.sha256(ast.dump(fn,include_attributes=False).encode()).hexdigest()}
 save(out/'BOUNDARY_METHOD.json',{'method':'unclipped discrete biharmonic log residual on exact existing lunar-photo mask','purpose':'numerical filter padding, not recovered corona','exterior_unchanged':True,'new_output_radius_or_mask_margin':False,'source_AST_and_delta':evidence});return engine
