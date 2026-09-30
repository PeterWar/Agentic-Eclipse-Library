"""Terms for a core-preserving mixture-PSF inverse on native observed samples.
Model Y=((1-p)I+pG12)X, where X retains the unknown narrow optical core.
No PSF core sharpening. Store B^2Y,B^3Y; B^1/B^4 are A0 sigma12/24.
"""
from scatter_common import *
from scipy.ndimage import gaussian_filter,map_coordinates
import time
rows=json.loads((OUT/'A0_witness_inputs.json').read_text())['frames'];receipts=[];step=5;nc=N//step
save('A1_inverse_plan.json',dict(method=__doc__,model='ObservedY=(1-p)X+pG12X; optical narrow core retained inX',inverse='X=(Y-aBY+a^2B^2Y-a^3B^3Y+a^4B^4Y)/(1-p),a=p/(1-p)',optimization='Only original training epochs, positivep<=0.1; determine final truncation error before accepting',support='Exactly A0 normal+rotated mass>=0.995 for sigma12 and24; no new selection by residual',limits=['Missing sample normalization is not an optical operator and requires a separate numerical/native check','p is conditional on isotropic broad mixture and inherited radiometric calibration','Finite-series remainder bounded at finalp; no unqualified inverse image promotion']))
for r in rows:
    start=time.time();stem=r['stem'];z=np.load(SRC/f'A0_quincunx_{stem}.npz');n=np.load(SRC/f'A0_native_samples_{stem}.npz');cells=np.load(OUT/f'A0_cells_{stem}.npz');good=np.isfinite(z['g'])&(z['q']>0);x=n['x'];y=n['y'];rad=np.hypot(x-CX,y-CY);selection=(rad>=415)&(rad<445)&n['valid']&(n['q']>0)&np.isfinite(n['g'])&np.isfinite(n['variance'])&(n['variance']>0)
    masks=[];fields={}
    for power in [1,2,3,4]:
        sigma=12*np.sqrt(power);den=gaussian_filter(good.astype(float),sigma,truncate=5);num=gaussian_filter(np.where(good,z['g'],0).astype(float),sigma,truncate=5);field=num/np.maximum(den,1e-30);fields[power]=map_coordinates(field,[y,x],order=1,mode='nearest',prefilter=False)
        if power in [1,4]:
            xr=CX-(y-CY);yr=CY+(x-CX);masks.extend([map_coordinates(den,[y,x],order=1,mode='nearest',prefilter=False),map_coordinates(den,[yr,xr],order=1,mode='nearest',prefilter=False)])
    selection &= np.minimum.reduce(masks)>=.995;ids=(np.floor(y/step).astype(int)*nc+np.floor(x/step).astype(int));count=np.bincount(ids[selection],minlength=nc*nc);c=cells['cell'];assert np.array_equal(count[c],cells['count'])
    terms={f'b{k}':np.bincount(ids[selection],weights=v[selection],minlength=nc*nc)[c]/count[c] for k,v in fields.items()};assert np.array_equal(terms['b1'],cells['t0']) and np.array_equal(terms['b4'],cells['t2'])
    np.savez_compressed(OUT/f'A1_terms_{stem}.npz',**terms);row=dict(stem=stem,maximum_abs_observed_valid_G=float(np.max(abs(z['g'][good]))),cells=len(c),seconds=time.time()-start);receipts.append(row);save('A1_neumann_terms.json',dict(method=__doc__,frames=receipts));print(stem,'DONE',round(time.time()-start,2),flush=True)
