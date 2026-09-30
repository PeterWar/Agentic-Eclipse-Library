"""Native terms for the cascade of frozen12px and candidate4px mixtures.
H12 and H4 act on the unknown narrow-core image. All inverse terms are formed
from observed radiance; a common support selection includes every kernel.
"""
from intermediate_common import *
from scipy.ndimage import gaussian_filter,map_coordinates
import time
aa=P12/(1-P12);cw=np.array([aa,-aa**2,aa**3,-aa**4]);step=5;nc=N//step;edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');old=json.loads((OUT/'A0_inputs.json').read_text())['frames'];rows=[]
save('A1_physical_plan.json',dict(method=__doc__,reason='The first-order witness improves all6epochs and is consistent between angular halves, but misses the5percent gate in2epochs. Evaluate the declared physical cascade without claiming first-order qualification.',model='Y=H12(H4(X)); H12=(1-p12)I+p12G12 frozen; H4=(1-p4)I+p4G4; X retains unknown narrow core.',p4_bounds=[0,.1],inverse_terms=dict(H12=4,H4=5),selection='Recompute a single common native support for all powers, normal and rotated; require mass>=.995. Same6px guard and415-449radius. Paired zero/candidate comparisons on this exact support.',gates='Unchanged:>=5percent improvement in EACH of6epochs;>=75percent sectors no worse than2percent; actual-angle preferred in>=5epochs; coefficient not bound; numeric remainder<=0.1G.',promotion='No image promotion if gates fail. Physical-model evidence may remain useful for a later separately validated forward model.'))
for r in old:
    start=time.time();stem=r['stem'];z=np.load(SRC/f'A0_quincunx_{stem}.npz');n=np.load(SRC/f'A0_native_samples_{stem}.npz');good=np.isfinite(z['g'])&(z['q']>0);raw=np.where(good,z['g'],0).astype(float);x=n['x'];y=n['y'];xr=CX-(y-CY);yr=CY+(x-CX);radius=np.hypot(x-CX,y-CY);angle=np.arctan2(y-CY,x-CX)%(2*np.pi);distance=radius-np.interp(angle,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);selection=(radius>=415)&(radius<449)&(distance<=-6)&n['valid']&(n['q']>0)&np.isfinite(n['g'])&np.isfinite(n['variance'])&(n['variance']>0);available=np.ones(len(x));Z=n['g'].copy();T=np.zeros((5,len(x)));Q=T.copy()
    specs=[(0,j,144*j,-cw[j-1]) for j in range(1,5)]+[(k,j,16*k+144*j,1 if j==0 else -cw[j-1]) for k in range(1,6) for j in range(5)]
    for k,j,sigma2,coef in specs:
        sigma=np.sqrt(sigma2);den=gaussian_filter(good.astype(float),sigma,truncate=5);field=gaussian_filter(raw,sigma,truncate=5)/np.maximum(den,1e-30);v=map_coordinates(field,[y,x],order=1,mode='nearest',prefilter=False);available=np.minimum(available,map_coordinates(den,[y,x],order=1,mode='nearest',prefilter=False))
        if k==0:Z+=coef*v
        else:
            T[k-1]+=coef*v;Q[k-1]+=coef*map_coordinates(field,[yr,xr],order=1,mode='nearest',prefilter=False);available=np.minimum(available,map_coordinates(den,[yr,xr],order=1,mode='nearest',prefilter=False))
    Z/=1-P12;T/=1-P12;Q/=1-P12;selection &= available>=.995;ids=np.floor(y/step).astype(int)*nc+np.floor(x/step).astype(int);cnt=np.bincount(ids[selection],minlength=nc*nc);cells=np.flatnonzero(cnt>=5);count=cnt[cells];v={}
    arrays=[('g',Z),('raw_g',n['g']),('distance',distance)]+[(f't{k+1}',T[k]) for k in range(5)]+[(f'q{k+1}',Q[k]) for k in range(5)]
    for key,array in arrays:v[key]=np.bincount(ids[selection],weights=array[selection],minlength=nc*nc)[cells]/count
    vm=float(np.median(n['variance'][selection]))/(1-P12)**2;v['weight_variance']=vm/count;v['cell']=cells;v['count']=count;v['cell_x']=(cells%nc+.5)*step;v['cell_y']=(cells//nc+.5)*step;v['radius']=np.hypot(v['cell_x']-CX,v['cell_y']-CY);v['angle']=np.arctan2(v['cell_y']-CY,v['cell_x']-CX)%(2*np.pi);v['t']=v['t1'];v['q']=v['q1'];np.savez_compressed(OUT/f'A1_cells_{stem}.npz',**v);rows.append(dict(**{k:r[k] for k in ['stem','role','epoch','time_C2']},native_samples=int(selection.sum()),cells=len(cells),maximum_abs_observed_G=float(np.max(abs(z['g'][good]))),seconds=time.time()-start));save('A1_inputs.json',dict(method=__doc__,frames=rows));print(stem,len(cells),'cells',round(time.time()-start,2),'seconds',flush=True)
print('DONE',len(rows),flush=True)
