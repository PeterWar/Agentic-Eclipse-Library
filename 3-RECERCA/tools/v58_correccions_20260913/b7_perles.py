from common58 import *
from scipy.optimize import minimize
import ast
claim();tree=ast.parse((T/'b2_geometry_local.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fit');y,x=np.mgrid[:2000,:2000];mc=(999.5681,999.6475);mr=np.hypot(x-mc[0],y-mc[1]);mt=np.mod(np.degrees(np.arctan2(y-mc[1],x-mc[0])),360);sr=np.hypot(x+ROI[0]-CX,y+ROI[1]-CY);th=np.mod(np.degrees(np.arctan2(y+ROI[1]-CY,x+ROI[0]-CX)),360);exec(compile(ast.Module(body=[fn],type_ignores=[]),'fit','exec'));rep={}
for ch in [0,1]:
 a=(np.load(O/'arrays/L00_C0_roi.npy') if ch==0 else roi(0)).astype('float32')/65535;b=(np.load(O/'arrays/L10_C0_roi.npy') if ch==0 else roi(10)).astype('float32')/65535;A=gaussian_filter(a,1)-gaussian_filter(a,4);B=gaussian_filter(b,1)-gaussian_filter(b,4);good=(mr>450)&(mr<550)&(a>.03)&(a<.97)&(b>.05)&(b<.97);rep[str(ch)]=fit(A,B,good);print(ch,rep[str(ch)],flush=True)
save('B7_perles_registration.json',rep)
