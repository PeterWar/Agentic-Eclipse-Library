from common58 import *
from scipy.optimize import minimize
import ast
claim();tree=ast.parse((T/'b2_geometry_local.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fit');y,x=np.mgrid[:2000,:2000];mc=(999.5681,999.6475);mr=np.hypot(x-mc[0],y-mc[1]);mt=np.mod(np.degrees(np.arctan2(y-mc[1],x-mc[0])),360);exec(compile(ast.Module(body=[fn],type_ignores=[]),'fit','exec'));rep={};a=roi(28).astype('float32')/65535;b=roi(29).astype('float32')/65535;good=(mr<.8*453.5)&(mr>60)
for ln in [False,True]:
 aa=np.log(np.maximum(a,.005)) if ln else a;bb=np.log(np.maximum(b,.005)) if ln else b
 for sig in [(3,12),(5,16)]:
  A=gaussian_filter(aa,sig[0])-gaussian_filter(aa,sig[1]);B=gaussian_filter(bb,sig[0])-gaussian_filter(bb,sig[1]);z=fit(A,B,good,mc,True);rep[f'log{ln}_{sig[0]}_{sig[1]}']=z;print(ln,sig,z,flush=True)
save('B5_lroc_local.json',rep)
