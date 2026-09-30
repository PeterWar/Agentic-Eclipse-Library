from pathlib import Path
import numpy as np,cv2,json
from scipy.ndimage import map_coordinates,gaussian_filter
from scipy.optimize import least_squares
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';P=R/'output/v61_interiors_limbe_20260913/arrays'
a=np.stack([np.load(P/f'V57_L01_C{c}.npy') for c in range(3)],-1).astype('float32')/65535;b=np.stack([np.load(A/f'L76_C{c}.npy') for c in range(3)],-1).astype('float32')/65535
# Colour ratios cancel the common foreground divider. Fit only the upper stem; lower stem is reserved.
def feature(v):return gaussian_filter(np.log(np.maximum(v[...,0],.002)/np.maximum(v[...,1],.002)),.7)
f=feature(a);g=feature(b)
y,x=np.mgrid[3305:3317,5265:5290];xx=x-4377;yy=y-2777;target=g[yy,xx]
def pred(p,x,y):return p[2]*map_coordinates(f,[y-p[1],x-p[0]],order=3)+p[3]
sol=least_squares(lambda p:(pred(p,xx,yy)-target).ravel(),[2,-.5,.5,-.0],bounds=([-4,-4,.1,-1],[4,4,2,1]),max_nfev=150,diff_step=.003)
p=sol.x;y,x=np.mgrid[3317:3329,5265:5295];xx=x-4377;yy=y-2777;tar=g[yy,xx];est=pred(p,xx,yy);rep=dict(parameters=p.tolist(),train_RMS=float(np.sqrt(np.mean(sol.fun**2))),held_out_correlation=float(np.corrcoef(tar.ravel(),est.ravel())[0,1]),held_out_RMS=float(np.sqrt(np.mean((tar-est)**2))),purpose='Only locate short-exposure colour reference on existing upper prominence. No project-layer transformation.')
(O/'B9_top_colour_registration.json').write_text(json.dumps(rep,indent=2));print(rep)
