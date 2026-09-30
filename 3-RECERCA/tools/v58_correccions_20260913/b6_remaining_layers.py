from common58 import *
from scipy.optimize import minimize
import ast
claim();tree=ast.parse((T/'b2_geometry_local.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fit');y,x=np.mgrid[:2000,:2000];mc=(999.5681,999.6475);mr=np.hypot(x-mc[0],y-mc[1]);mt=np.mod(np.degrees(np.arctan2(y-mc[1],x-mc[0])),360);sr=np.hypot(x+ROI[0]-CX,y+ROI[1]-CY);th=np.mod(np.degrees(np.arctan2(y+ROI[1]-CY,x+ROI[0]-CX)),360);exec(compile(ast.Module(body=[fn],type_ignores=[]),'fit','exec'));rep={};b=roi(29).astype('float32')/65535;a=roi(27).astype('float32')/65535;good=(mr<.8*453.5)&(mr>60);A=gaussian_filter(a,3)-gaussian_filter(a,12);B=gaussian_filter(b,3)-gaussian_filter(b,12);rep['27']=fit(A,B,good,mc,True);print('27',rep['27'],flush=True)
base=roi(9).astype('float32')/65535;B=gaussian_filter(np.log(np.maximum(base,.001)),4)-gaussian_filter(np.log(np.maximum(base,.001)),16)
for i in [7,8,10]:
 a=roi(i).astype('float32')/65535;A=gaussian_filter(np.log(np.maximum(a,.001)),4)-gaussian_filter(np.log(np.maximum(a,.001)),16);good=(sr>1.25*RS)&(sr<1.85*RS)&(a>.025)&(a<.92)&(base>.025)&(base<.96);rep[str(i)]=fit(A,B,good);print(i,rep[str(i)],flush=True)
save('B6_remaining_layers.json',rep)
