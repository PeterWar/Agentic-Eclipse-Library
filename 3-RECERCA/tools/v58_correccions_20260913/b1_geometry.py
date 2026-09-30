from common58 import *
from scipy.optimize import minimize
from scipy.ndimage import label
claim();freeze=json.loads((O/'A0_freeze.json').read_text());names={r['name']:r['index'] for r in freeze['layers']};y,x=np.mgrid[:2000,:2000];sr=np.hypot(x+ROI[0]-CX,y+ROI[1]-CY);th=np.mod(np.degrees(np.arctan2(y+ROI[1]-CY,x+ROI[0]-CX)),360);mc=(999.57,999.65);mr=np.hypot(x-mc[0],y-mc[1]);mt=np.mod(np.degrees(np.arctan2(y-mc[1],x-mc[0])),360)
base=roi(9).astype('float32')/65535;B=bp(np.log(np.maximum(base,1e-3)),8,64)

def fit(mov,ref,good,center=(CX-ROI[0],CY-ROI[1]),lunar=False):
 sec=np.floor((mt if lunar else th)/45).astype('int8');points=[]
 for k in range(8):
  yy,xx=np.where(good&(sec==k)&((x%3)==0)&((y%3)==0));points.append((yy.astype(float),xx.astype(float),ref[yy,xx]))
 def values(p,k,arr=mov):
  yy,xx,target=points[k];u=xx-center[0]-p[0];v=yy-center[1]-p[1];an=np.deg2rad(p[2]);s=(1+p[3]) if lunar else 1.;sx=center[0]+(np.cos(an)*u+np.sin(an)*v)/s;sy=center[1]+(-np.sin(an)*u+np.cos(an)*v)/s
  val=map_coordinates(arr,[sy,sx],order=1,mode='nearest',prefilter=False);return ncc(val,target) if len(target)>80 else np.nan
 def score(p,sectors):
  v=[values(p,k) for k in sectors];return float(np.nanmean(v))
 bounds=[(-8,8),(-8,8),(-1,1),(-.025,.025)] if lunar else [(-8,8),(-8,8),(-.4,.4)]
 z=np.zeros(len(bounds));fit=minimize(lambda p:-score(p,[0,2,4,6]),z,method='Powell',bounds=bounds,options={'xtol':1e-3,'ftol':1e-7,'maxiter':45})
 p=fit.x;res=dict(transform_output_dx_dy_deg_scale_delta=p.tolist(),fit_ncc_before=score(z,[0,2,4,6]),fit_ncc_after=score(p,[0,2,4,6]),heldout_ncc_before=score(z,[1,3,5,7]),heldout_ncc_after=score(p,[1,3,5,7]),sectors_before=[values(z,k) for k in range(8)],sectors_after=[values(p,k) for k in range(8)],points=[len(q[0]) for q in points],success=bool(fit.success))
 return res
rep={}
for i in range(7):
 a=roi(i).astype('float32')/65535;A=bp(np.log(np.maximum(a,1e-3)),8,64);good=(sr>1.25*RS)&(sr<1.85*RS)&(a>.025)&(a<.92)&(base>.025)&(base<.96)&(roi(i,-1)>65000)
 if good.sum()<2000:rep[str(i)]=dict(name=freeze['layers'][i]['name'],status='insufficient unsaturated coronal support');continue
 r=fit(A,B,good);r['name']=freeze['layers'][i]['name'];rep[str(i)]=r;print(i,r,flush=True)
# Frozen control validates displacement/rotation of the magnitude already suspected.
from scipy.ndimage import affine_transform
an=np.deg2rad(.15);center=np.array([CY-ROI[1],CX-ROI[0]]);M=np.array([[np.cos(an),-np.sin(an)],[np.sin(an),np.cos(an)]]);offset=center-M@(center+np.array([0.,-12.]));control=affine_transform(B,M,offset=offset,order=1,mode='nearest')
rep['control']=fit(control,B,(sr>1.25*RS)&(sr<1.85*RS)&(base>.025)&(base<.96)) # bound +/-8 intentionally not enough for12; recorded diagnostic only
# LROC against lunar texture. Use native albedo, edge excluded; transforms apply only to reference LROC.
lunar=roi(29).astype('float32')/65535;lroc=roi(28).astype('float32')/65535;L=bp(lunar,24,96);C=bp(lroc,24,96);good=(mr<.85*453.5)&(mr>45)&(roi(29,-1)>65000)&(roi(28,-1)>65000)
rep['LROC']=fit(C,L,good,mc,True);rep['LROC']['reflected_null']=fit(np.flip(C,axis=1).copy(),L,good,mc,True);print('LROC',rep['LROC'],flush=True)
# Same half-height edge detector for masks/alpha, radial threshold only for geometry diagnostic.
ang=np.linspace(0,2*np.pi,1440,endpoint=False);rr=np.arange(410,490,.1);sx=mc[0]+rr[:,None]*np.cos(ang);sy=mc[1]+rr[:,None]*np.sin(ang)
def edge(a,ascending=True):
 v=map_coordinates(a.astype('float32')/65535,[sy,sx],order=1,prefilter=False);v=v if ascending else 1-v;k=np.argmax(v>=.5,axis=0);ok=(k>0)&(k<len(rr)-1);r50=rr[k[ok]];ta=ang[ok];D=np.c_[np.ones(len(ta)),np.cos(ta),np.sin(ta)];beta=np.linalg.lstsq(D,r50,rcond=None)[0];res=r50-D@beta;keep=np.abs(res-np.median(res))<max(1,4*1.4826*np.median(np.abs(res-np.median(res))));beta=np.linalg.lstsq(D[keep],r50[keep],rcond=None)[0]
 return dict(radius=float(beta[0]),cx=float(mc[0]+ROI[0]+beta[1]),cy=float(mc[1]+ROI[1]+beta[2]),rms=float(np.std(r50[keep]-D[keep]@beta)),n=int(keep.sum()),r50_by_theta=r50.tolist())
rep['edges']={}
for i in [0,1,2,7,8,9,13,14,15,16,28,29]:
 for c in [-1,-2]:
  if not (O/'arrays'/f'L{i:02d}_C{c}_roi.npy').exists():continue
  a=roi(i,c);v=a[mr<400];direction=np.median(v)<32768
  try:rep['edges'][f'{i}_{c}']=edge(a,direction)
  except Exception as e:rep['edges'][f'{i}_{c}']={'error':str(e)}
# Mask 11 islands strictly inside occulted disc.
a=roi(1,-2);bad=(a>100)&(mr<445);labels,n=label(bad);components=[]
for k in range(1,n+1):
 ys,xs=np.where(labels==k)
 if len(xs)>2:components.append(dict(pixels=len(xs),bbox=[int(xs.min()+ROI[0]),int(ys.min()+ROI[1]),int(xs.max()+ROI[0]+1),int(ys.max()+ROI[1]+1)],max=int(a[labels==k].max())))
rep['mask11_internal_islands']=components;print('MASK11',components,flush=True);save('B1_geometry_initial.json',rep)
