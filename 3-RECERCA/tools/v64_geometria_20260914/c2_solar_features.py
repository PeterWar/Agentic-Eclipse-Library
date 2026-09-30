from pathlib import Path
import numpy as np,json,cv2
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.optimize import minimize
R=Path.cwd();O=R/'output/v64_geometria_20260914';P=R/'output/v61_interiors_limbe_20260913';A=O/'arrays'
base=np.load(A/'L3_C1.npy').astype(float)/65535
def hp(a):return gaussian_filter(a,.8)-gaussian_filter(a,4)
B=hp(base);M=np.array(json.loads((P/'C3_rigid_controls.json').read_text())['matrix_global']);M[:,2]+=M[:,:2]@np.array([4377,2777])-np.array([4377,2777])
spec=[('top_reserved',5277,3318,22),('main_prominence',4890,3755,30),('upper_beads',4910,3690,20),('lower_west_reserved',4895,3820,30),('SE',5793,3956,25),('NW_unreliable_edge_only',5000,3520,24)]
rows=[]
for i in [1,2,3]:
    source=cv2.warpAffine(np.load(P/'arrays'/f'V57_L{i:02d}_C1.npy').astype(float)/65535,M,(2000,2000),flags=cv2.INTER_CUBIC);S=hp(source)
    for name,x,y,h in spec:
        yy,xx=np.mgrid[y-h:y+h,x-h:x+h];rad=np.hypot(xx-5376.568111973117,yy-3776.647534140857);sel=(rad>466)&(rad<510)&(source[yy-2777,xx-4377]>.008)&(source[yy-2777,xx-4377]<.97)&(base[yy-2777,xx-4377]>.01)&(base[yy-2777,xx-4377]<.97)
        x=xx[sel]-4377;y=yy[sel]-2777;v=S[y,x]
        if len(v)<80:rows.append(dict(layer=12-i,feature=name,points=len(v),measurable=False));continue
        def score(q,field=B):
            z=map_coordinates(field,[y+q[1],x+q[0]],order=1);return float(np.corrcoef(v,z)[0,1])
        starts=[(score([dx,dy]),[dx,dy]) for dx in range(-6,7,2) for dy in range(-6,7,2)];sol=[]
        for _,q in sorted(starts,reverse=True)[:3]:sol.append(minimize(lambda q:-score(q),q,method='Nelder-Mead',bounds=[(-8,8),(-8,8)],options={'xatol':1e-5,'maxiter':500}))
        best=min(sol,key=lambda z:z.fun);rows.append(dict(layer=12-i,feature=name,points=len(v),source_to_base_sampling_dxdy=best.x.tolist(),before=score([0,0]),after=-float(best.fun),residual_px=float(np.linalg.norm(best.x)),boundary=bool(np.any(abs(best.x)>7.9)),control_rotated180=score(best.x,B[::-1,::-1]),scope='External solar structure; lunar rim excluded. NW may have no unique coronal feature.'))
        print(rows[-1],flush=True)
(O/'C2_solar_features.json').write_text(json.dumps(dict(rows=rows,new_transform_applied=False),indent=2)+'\n')
