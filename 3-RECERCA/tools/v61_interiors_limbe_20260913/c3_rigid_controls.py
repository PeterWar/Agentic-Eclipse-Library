from common61 import *
import ast,cv2
import tifffile as tf
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.optimize import minimize
claim();j=json.loads((O/'C2_common_rigid.json').read_text());p=np.array(j['transform_output_dx_dy_deg']);ref=tf.imread(O/'Vista_V57_reference.tif')[...,1]/65535
A=gaussian_filter(ref,1)-gaussian_filter(ref,5);pts=[(4890,3755,40),(5793,3956,30),(5277,3318,25),(4895,3820,40)];patch=[]
for x,y,h in pts:
 yy,xx=np.mgrid[y-h:y+h,x-h:x+h];r=np.hypot(xx-5376.5681,yy-3776.6475);ok=(r>466)&(r<510)&(ref[yy-2777,xx-4377]>.008);patch.append((xx[ok].astype(float),yy[ok].astype(float),A[yy[ok]-2777,xx[ok]-4377]))
def matrix(q):
 t=np.deg2rad(q[2]);rot=np.array([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]]);return np.c_[rot,np.array([CX,CY])+q[:2]-rot@np.array([CX,CY])]
def sample(B,q,patch):
 x,y,v=patch;M=matrix(np.asarray(q));xx=M[0,0]*x+M[0,1]*y+M[0,2];yy=M[1,0]*x+M[1,1]*y+M[1,2];return float(np.corrcoef(v,map_coordinates(B,[yy-2777,xx-4377],order=1))[0,1])
rep=[]
for q in [np.zeros(3),np.array([1.25,-.75,.17])]:
 M=matrix(q);M[:,2]+=M[:,:2]@np.array([4377,2777])-np.array([4377,2777]);B=cv2.warpAffine(A,M,(2000,2000),flags=cv2.INTER_CUBIC)
 loss=lambda z:-np.mean([sample(B,z,v) for v in patch[:2]]);opt=minimize(loss,q+[.2,-.2,.02],method='Nelder-Mead',options={'xatol':1e-5});err=opt.x-q;rep.append({'injected':q.tolist(),'recovered':opt.x.tolist(),'error':err.tolist(),'reserved_scores':[sample(B,opt.x,v) for v in patch[2:]],'PASS':bool(np.max(abs(err[:2]))<.15 and abs(err[2])<.02)})
save('C3_rigid_controls.json',{'controls':rep,'matrix_global':matrix(p).tolist(),'reserved_real_features_nonregression':all(r['after']>=r['before'] for r in j['fits'] if r['reserved']),'PASS':all(r['PASS'] for r in rep)});print(rep)
