from common58 import *
from scipy.optimize import minimize
claim();a=np.load(O/'arrays/L00_C0_roi.npy').astype('float32')/65535;b=np.load(O/'arrays/L10_C0_roi.npy').astype('float32')/65535;A=gaussian_filter(a,1)-gaussian_filter(a,4);B=gaussian_filter(b,1)-gaussian_filter(b,4);rows=[]
for yc in range(820,1181,30):
 for xc in range(490,651,30):
  q=a[yc-15:yc+16,xc-15:xc+16]
  if (q>.25).sum()<25:continue
  v=A[yc-15:yc+16,xc-15:xc+16];gy,gx=np.mgrid[yc-15:yc+16,xc-15:xc+16]
  def score(p):return ncc(v.ravel(),map_coordinates(B,[gy+p[1],gx+p[0]],order=1).ravel())
  before=score([0,0])
  if before<.45:continue
  grid=[(score((dx,dy)),dx,dy) for dx in range(-4,5) for dy in range(-4,5)];best=max(grid);p=minimize(lambda p:-score(p),best[1:],method='Nelder-Mead',bounds=[(-4,4),(-4,4)],options={'xatol':.003}).x;row=dict(center=[xc+ROI[0],yc+ROI[1]],shift=p,score_before=before,score_after=score(p));rows.append(row)
print(rows);save('B9_perles_tiles.json',dict(rows=rows,median_dxdy=np.median([r['shift'] for r in rows],axis=0),note='Perles12 shares observed bright structures with native accepted composite. Preserve its registration; coronal transform of11..06 cannot be inferred from12 dark corona.'))
