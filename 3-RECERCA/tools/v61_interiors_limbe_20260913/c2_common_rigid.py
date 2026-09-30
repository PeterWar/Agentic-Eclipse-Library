from common61 import *
import tifffile as tf
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.optimize import minimize
claim();ref=tf.imread(O/'Vista_V57_reference.tif')[...,:3]/65535;base=np.stack([np.load(O/'arrays'/f'V60_L09_C{c}.npy') for c in range(3)],-1)/65535
A=gaussian_filter(ref[...,1],1)-gaussian_filter(ref[...,1],5);B=gaussian_filter(base[...,1],1)-gaussian_filter(base[...,1],5)
# Fixed external features, disk / lunar edge excluded. Even 45-degree sectors fit; odd top sector reserved.
spec=[('west_fit',4890,3755,40,False),('SE_fit',5793,3956,30,False),('top_reserved',5277,3318,25,True),('west_lower_check',4895,3820,40,True)]
patches=[]
for name,x,y,h,reserved in spec:
 gy,gx=np.mgrid[y-h:y+h,x-h:x+h];lr=np.hypot(gx-5376.5681,gy-3776.6475);v=A[gy-2777,gx-4377];ok=(lr>466)&(lr<510)&(ref[gy-2777,gx-4377,1]>.008)&(base[gy-2777,gx-4377,1]>.01)
 patches.append((name,gx[ok].astype(float),gy[ok].astype(float),v[ok],reserved))
def ncc(a,b):return float(np.corrcoef(a,b)[0,1])
def score(p,item,field=B):
 _,x,y,v,_=item;th=np.deg2rad(p[2]);xx=CX+np.cos(th)*(x-CX)-np.sin(th)*(y-CY)+p[0];yy=CY+np.sin(th)*(x-CX)+np.cos(th)*(y-CY)+p[1]
 return ncc(v,map_coordinates(field,[yy-2777,xx-4377],order=1))
fit=[q for q in patches if not q[-1]]
def loss(p):return -np.mean([score(p,q) for q in fit])
starts=[(loss([dx,dy,th]),[dx,dy,th]) for dx in [-.5,0,.5] for dy in [-.5,0,.5] for th in [-.2,-.1,0,.1,.2]];p0=min(starts,key=lambda q:q[0])[1];opt=minimize(loss,p0,method='Nelder-Mead',bounds=[(-2,2),(-2,2),(-.3,.3)],options={'xatol':1e-4});p=opt.x
report={'transform_output_dx_dy_deg':p.tolist(),'scale':1,'centre':[CX,CY],'fits':[],'status':'candidate not applied; external astronomical features tested, disk edge excluded'}
for item in patches:report['fits'].append({'name':item[0],'points':len(item[1]),'reserved':item[-1],'before':score([0,0,0],item),'after':score(p,item)})
print(report);save('C2_common_rigid.json',report)
