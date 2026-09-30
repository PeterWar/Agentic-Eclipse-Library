"""A broad-scatter temporal witness, not a PSF inverse or photographic edit.
Native green data are aggregated into fixed5px cells. Wide predictors come
from valid observed per-frame radiance, without brightness weighting.
"""
from scatter_common import *
from scipy.ndimage import gaussian_filter,map_coordinates
import time
train=[f'572A{n}' for n in [2973,2974,2975,2976,2991,2992,2993,2994]]
reserved=[f'572A{n}' for n in [2968,2969,2970,2986,2987,2988,2998,2999,3000,3004,3005,3006]]
sigmas=[12.,24.];step=5;nc=N//step
epochs=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F2_temporal.json').read_text())['epochs'];metadata={s:dict(epoch=k,time_C2=t) for k,v in epochs.items() for s,t in zip(v['frames'],v['times'])}
plan=dict(method=__doc__,training_stems=train,reserved_stems=reserved,wide_sigmas=sigmas,cell_size_px=step,native_radius=[415,445],new_frame_nuisance_fit_radius=[415,423],validation_radius=[[426,435],[435,445]],max_missing_kernel_mass=.005,regression='Common lunar cell value, per-frame plane, and shared nonnegative coefficients for wide observed-field predictors; f12+f24<=0.10. Coefficients are temporal leakage witnesses, NOT physical PSF fractions.',controls='Refitted zero-scatter baseline and90degree rotated predictors; global coefficient fit checked on withheld epochs and angular sectors',limitations=['Observed broad predictors are only first-order scatter proxies; a physical correction requires joint or exact inverse qualification','Common calibration and sampled blur predictor are not independent of native data','Fixed5px aggregation is a diagnostic statistic, never source resampling or a new FOV','Pixel variances omit correlated calibration/FPN; spatial agreement required rather than naive formal confidence'])
save('PLAN.json',plan);rows=[]
for stem in train+reserved:
    start=time.time();z=np.load(SRC/f'A0_quincunx_{stem}.npz');native=np.load(SRC/f'A0_native_samples_{stem}.npz');good=np.isfinite(z['g'])&(z['q']>0);predictors=[];support=[]
    x=native['x'];y=native['y'];radius=np.hypot(x-CX,y-CY);selection=(radius>=415)&(radius<445)&native['valid']&(native['q']>0)&np.isfinite(native['g'])&np.isfinite(native['variance'])&(native['variance']>0)
    for sigma in sigmas:
        den=gaussian_filter(good.astype(float),sigma,truncate=5);num=gaussian_filter(np.where(good,z['g'],0).astype(float),sigma,truncate=5);field=num/np.maximum(den,1e-30);predictors.append(map_coordinates(field,[y,x],order=1,mode='nearest',prefilter=False));support.append(map_coordinates(den,[y,x],order=1,mode='nearest',prefilter=False))
        # Wrong-angle null retains actual time and spatial coverage; no pixels
        # from this transformed diagnostic predictor enter any image product.
        xr=CX-(y-CY);yr=CY+(x-CX);predictors.append(map_coordinates(field,[yr,xr],order=1,mode='nearest',prefilter=False));support.append(map_coordinates(den,[yr,xr],order=1,mode='nearest',prefilter=False))
    available=np.minimum.reduce(support);native_before=int(selection.sum());selection &= available>=.995
    ids=(np.floor(y/step).astype(int)*nc+np.floor(x/step).astype(int));use=selection;count=np.bincount(ids[use],minlength=nc*nc);cells=np.flatnonzero(count>=5);cnt=count[cells];values={}
    for key,array in [('g',native['g']),('x',x),('y',y)]+[(f't{i}',a) for i,a in enumerate(predictors)]:values[key]=np.bincount(ids[use],weights=array[use],minlength=nc*nc)[cells]/cnt
    # Constant per-frame precision avoids response-dependent weighting of an
    # individual faint downward noise fluctuation. Keep native variance sum.
    vmean=float(np.median(native['variance'][use]));values['variance_conditional']=np.bincount(ids[use],weights=native['variance'][use],minlength=nc*nc)[cells]/cnt**2;values['weight_variance']=vmean/cnt;values['count']=cnt;values['cell']=cells;values['cell_x']=(cells%nc+.5)*step;values['cell_y']=(cells//nc+.5)*step;values['radius']=np.hypot(values['cell_x']-CX,values['cell_y']-CY);values['angle']=np.arctan2(values['cell_y']-CY,values['cell_x']-CX)%(2*np.pi)
    np.savez_compressed(OUT/f'A0_cells_{stem}.npz',**values);row=dict(stem=stem,train=stem in train,**metadata[stem],native_before_support=native_before,native_after_support=int(use.sum()),cells=len(cells),median_native_variance=vmean,support_mass_quantiles=np.percentile(available[(radius>=415)&(radius<445)],[0,1,5,50,95,100]).tolist(),seconds=time.time()-start);rows.append(row);save('A0_witness_inputs.json',dict(method=__doc__,frames=rows));print(stem,'cells',len(cells),'retained',round(use.sum()/max(native_before,1),3),'seconds',round(time.time()-start,2),flush=True)
print('DONE',len(rows),flush=True)
