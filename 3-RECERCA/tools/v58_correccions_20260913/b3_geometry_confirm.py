from common58 import *
import ast
from psd_tools import PSDImage
claim();tree=ast.parse((T/'b2_geometry_local.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fit');from scipy.optimize import minimize
y,x=np.mgrid[:2000,:2000];sr=np.hypot(x+ROI[0]-CX,y+ROI[1]-CY);th=np.mod(np.degrees(np.arctan2(y+ROI[1]-CY,x+ROI[0]-CX)),360);mc=(999.5681,999.6475);mr=np.hypot(x-mc[0],y-mc[1]);mt=np.mod(np.degrees(np.arctan2(y-mc[1],x-mc[0])),360);exec(compile(ast.Module(body=[fn],type_ignores=[]),'fit','exec'))
rep={};lunar=roi(29).astype('float32')/65535;lroc=roi(28).astype('float32')/65535;good=(mr<.85*453.5)&(mr>45)
for a,b in [(32,160),(40,200)]:
 rep[f'LROC_{a}_{b}']=fit(bp(lroc,a,b),bp(lunar,a,b),good,mc,True);print('LROC',a,rep[f'LROC_{a}_{b}'],flush=True)
s=PSDImage.open(O/'V57_Pere_input.psb')
for idx in [0,1,9,10]:
 l=s[idx]
 for c in [0,2]:
  a=chan(l,c);q=np.zeros((2000,2000),np.uint16);left,top,right,bottom=l.bbox;xa=max(left,ROI[0]);ya=max(top,ROI[1]);xb=min(right,ROI[2]);yb=min(bottom,ROI[3]);q[ya-ROI[1]:yb-ROI[1],xa-ROI[0]:xb-ROI[0]]=a[ya-top:yb-top,xa-left:xb-left];np.save(O/'arrays'/f'L{idx:02d}_C{c}_roi.npy',q)
del s
# Chromosphere/prominence features outside current lunar occultation; separate 12 from texture-star geometry.
for idx in [0,1]:
 a=np.load(O/'arrays'/f'L{idx:02d}_C0_roi.npy').astype('float32')/65535;b=np.load(O/'arrays/L09_C0_roi.npy').astype('float32')/65535
 A=gaussian_filter(a,1)-gaussian_filter(a,5);B=gaussian_filter(b,1)-gaussian_filter(b,5);good=(mr>457)&(mr<530)&(a>.01)&(a<.97)&(b>.05)&(b<.97)
 rep[f'{idx}_red']=fit(A,B,good);print('RED',idx,rep[f'{idx}_red'],flush=True)
save('B3_geometry_confirm.json',rep)
