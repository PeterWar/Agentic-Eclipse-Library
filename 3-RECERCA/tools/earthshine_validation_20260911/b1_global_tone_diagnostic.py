"""Can a spatially uniform tone response explain the CameraRaw replay mismatch?
Diagnostic only: fit on alternating angular sectors, judge on disjoint sectors.
No edited raster is saved. This cannot recover unknown historical sliders.
"""
from validation_common import *
from scipy.interpolate import PchipInterpolator
from scipy.optimize import isotonic_regression
a=np.load(OUT/'B0_replay_rgb.npy').astype(float);target=np.load(PREV/'A0_live_layer21_rgb.npy').astype(float)
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);th=np.arctan2(y-CY,x-CX)%(2*np.pi);training=((th//(np.pi/8)).astype(int)%2)==0
knots=[];rows=[];curves=[]
for c in range(3):
    xx=a[...,c];yy=target[...,c];bins=(xx/64).astype(int);bx=[];by=[];wt=[]
    for k in np.unique(bins[training]):
        m=training&(bins==k)
        if m.sum()<20:continue
        bx.append(float(xx[m].mean()));by.append(float(yy[m].mean()));wt.append(int(m.sum()))
    by=isotonic_regression(np.array(by),weights=np.array(wt)).x
    f=PchipInterpolator(bx,by,extrapolate=False);pred=f(np.clip(xx,min(bx),max(bx)));error=pred-yy
    curve=dict(input_DN16=bx,output_DN16=by.tolist(),training_counts=wt);curves.append(curve)
    rr=[]
    for lo,hi in [(0,350),(350,420),(420,440),(440,455),(455,500),(500,990)]:
        m=(~training)&(r>=lo)&(r<hi)&(xx>=min(bx))&(xx<=max(bx));rr.append(dict(radius=[lo,hi],n=int(m.sum()),abs_error_q=np.percentile(abs(error[m]),[50,95,99,100]).tolist(),rms=float(np.sqrt(np.mean(error[m]**2)))))
    rows.append(dict(channel=c,knots=len(bx),radial_holdout=rr))
save('B1_global_tone_diagnostic.json',dict(method=__doc__,bin_width_DN16=64,curves=curves,results=rows,scope='Empirical uniform tone-response diagnostic. Not an exact CameraRaw setting recovery or authorization to substitute a different aesthetic. No spatial masks or retouch applied.'))
print(json.dumps(rows),flush=True)
