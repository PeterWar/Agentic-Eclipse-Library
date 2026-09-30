from common58 import *
from scipy.ndimage import label,binary_dilation
from scipy.optimize import minimize
claim();a=np.load(O/'arrays/L00_C0_roi.npy').astype('float32')/65535;b=np.load(O/'arrays/L10_C0_roi.npy').astype('float32')/65535;y,x=np.mgrid[:2000,:2000];r=np.hypot(x-999.5681,y-999.6475);lab,n=label(binary_dilation((a>.25)&(r>452)&(r<520),iterations=4));A=gaussian_filter(a,1)-gaussian_filter(a,4);B=gaussian_filter(b,1)-gaussian_filter(b,4);rows=[]
for i in range(1,n+1):
 yy,xx=np.where(lab==i)
 if len(yy)<30:continue
 xc,yc=int(xx.mean()),int(yy.mean());v=A[yc-22:yc+23,xc-22:xc+23];gy,gx=np.mgrid[yc-22:yc+23,xc-22:xc+23]
 def score(p):return ncc(v.ravel(),map_coordinates(B,[gy+p[1],gx+p[0]],order=1).ravel())
 grid=[(score((dx,dy)),dx,dy) for dx in range(-6,7) for dy in range(-6,7)];best=max(grid);p=minimize(lambda p:-score(p),best[1:],method='Nelder-Mead',bounds=[(-6,6),(-6,6)],options={'xatol':.002}).x;row=dict(center=[xc+ROI[0],yc+ROI[1]],pixels=len(xx),shift_applied_to12=p,score_before=score([0,0]),score_after=score(p));rows.append(row);print(row,flush=True)
save('B8_perles_components.json',rows)
