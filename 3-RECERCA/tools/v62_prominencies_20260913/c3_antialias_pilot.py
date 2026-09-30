from pathlib import Path
import numpy as np,json
from scipy.ndimage import gaussian_filter1d
R=Path.cwd();O=R/'output/v62_prominencies_20260913';A=O/'arrays';old=np.load(R/'output/v61_interiors_limbe_20260913/arrays/V60_L29_C-2.npy').astype('float64')/65535;user=np.load(A/'V61_L22_C-2.npy').astype('float64')/65535
cx=5376.568111973117;cy=3776.647534140857;y,x=np.mgrid[2777:4777,4377:6377];f4=gaussian_filter1d(np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'),3,mode='wrap');th=np.linspace(0,2*np.pi,1441);fv=np.r_[f4,f4[0]]
def mask(x,y):
 phi=np.mod(np.arctan2(y-cy,x-cx),2*np.pi);dist=np.hypot(x-cx,y-cy)-np.interp(phi,th,fv);return np.clip((1-dist)/2,0,1)
mc=mask(x,y);sel=(abs(np.hypot(x-cx,y-cy)-452)<8)&(old==user);err=abs(mc[sel]-old[sel])*65535;assert err.max()<3,err.max()
xx=x[sel];yy=y[sel]
def integrate(n):
 v=np.zeros(xx.shape)
 for oy in (np.arange(n)+.5)/n-.5:
  for ox in (np.arange(n)+.5)/n-.5:v+=mask(xx+ox,yy+oy)/(n*n)
 return v
a8=integrate(8);a16=integrate(16);new=user.copy();new[sel]=a16;u=np.rint(new*65535).astype('uint16');np.save(A/'C3_moon_AA_pilot.npy',u)
changed=u!=np.rint(user*65535).astype('uint16');delta=new-user
rep=dict(claim='Pilot pixel-area integration of the unchanged physical contour; not a new lunar edge or an artifact-correction PASS',baseline_reproduction_max_DN16=float(err.max()),max_difference_8_vs_16_DN16=float(abs(a8-a16).max()*65535),changed_pixels=int(changed.sum()),lunar_area_change_pixels=float(delta.sum()),max_mask_delta=float(abs(delta).max()),user_edit_pixels_preserved=bool(np.array_equal(u[old!=user],np.rint(user[old!=user]*65535).astype('uint16'))))
(O/'C3_antialias_pilot.json').write_text(json.dumps(rep,indent=2));print(rep)
