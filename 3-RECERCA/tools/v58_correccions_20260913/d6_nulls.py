from common58 import *
import ast,pandas as pd
claim();tree=ast.parse((T/'d1_detect_stars.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='detect');exec(compile(ast.Module(body=[fn],type_ignores=[]),'detect','exec'));F=np.load(V42/'cau/fusion_total_v42.npy',mmap_mode='r');m=np.load(V42/'cau/support_v42.npy');cat=pd.read_csv(O/'catalog_projected.csv');rep={}
for deg in range(30,331,30):
 n=0;hits=[];t=np.deg2rad(deg)
 for _,c in cat.iterrows():
  ux,uy=c.x_pred-CX,c.y_pred-CY;x=CX+np.cos(t)*ux-np.sin(t)*uy;y=CY+np.sin(t)*ux+np.cos(t)*uy
  if not(35<x<10516 and 35<y<7471) or not m[int(y),int(x)] or np.hypot(x-CX,y-CY)<1.15*RS:continue
  d=detect(F,x,y)
  if d is None:continue
  n+=1
  if d['snr']>=7 and d['contrast']>=4:hits.append(d)
 rep[str(deg)]=dict(tested=n,passes=len(hits),hits=hits);print(deg,n,len(hits),flush=True)
save('D6_rotated_catalog_nulls.json',rep)
