from pathlib import Path
import numpy as np,pandas as pd,json
from scipy.optimize import least_squares
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';W=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17');S=W/'sony';X=W/'xmatch'
cat=pd.read_csv(X/'final_match_sony.csv');M=np.load(S/'warpM.npy');T=np.load(S/'warpT.npy');C=np.load(S/'warpC.npy');rows=[];imgs={g:np.load(S/f'IMG{g}.npy',mmap_mode='r') for g in ['A','C']}
def fit(im,x,y):
 H=12;xx=int(round(x));yy=int(round(y));z=np.array(im[yy-H:yy+H+1,xx-H:xx+H+1],float)
 if z.shape!=(25,25):return None
 Y,X=np.mgrid[-H:H+1,-H:H+1];bg=np.median(z[np.hypot(X,Y)>9]);sig=max(1.4826*np.median(abs(z[np.hypot(X,Y)>9]-bg)),.01);amp=max(z[10:15,10:15].max()-bg,.01)
 def model(p):
  a,b=(X-p[1])*np.cos(p[5])+(Y-p[2])*np.sin(p[5]),-(X-p[1])*np.sin(p[5])+(Y-p[2])*np.cos(p[5]);return p[0]*np.exp(-.5*((a/p[3])**2+(b/p[4])**2))+p[6]+p[7]*X+p[8]*Y
 init=[amp,x-xx,y-yy,2,1.5,0,bg,0,0];lo=[0,-4,-4,.6,.6,-np.pi,-np.inf,-np.inf,-np.inf];hi=[np.inf,4,4,6,6,np.pi,np.inf,np.inf,np.inf]
 sol=least_squares(lambda p:(model(p)-z).ravel()/sig,init,bounds=(lo,hi),loss='soft_l1',max_nfev=120)
 p=sol.x;return dict(x=float(xx+p[1]),y=float(yy+p[2]),sigma1=float(p[3]),sigma2=float(p[4]),theta=float(p[5]),flux=float(p[0]*2*np.pi*p[3]*p[4]),snr_peak=float(p[0]/sig),relative_residual=float(np.std((model(p)-z)[np.hypot(X,Y)<6])/p[0]),background_noise=sig)
for i,row in cat.iterrows():
 c=np.array([row.x,row.y]);a=(c-C-T)@np.linalg.inv(M).T+C
 for g,xy in [('A',a),('C',c)]:
  f=fit(imgs[g],*xy)
  if f:rows.append(dict(det=row.det,V=row.V,group=g,reserved=bool(i%3==0),**f))
pd.DataFrame(rows).to_csv(O/'S1_psf_stacks.csv',index=False)
for g in ['A','C']:
 sel=[v for v in rows if v['group']==g and not v['reserved'] and v['snr_peak']>10 and v['relative_residual']<.3];print(g,len(sel),np.median([[v['sigma1'],v['sigma2'],v['theta']] for v in sel],axis=0),flush=True)
(O/'S1_psf_stacks.json').write_text(json.dumps(rows,indent=2))
print('COMPLETE',flush=True)
