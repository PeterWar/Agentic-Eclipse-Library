"""Numerical pixel-area accuracy of the observed silhouette in the forward model.
This is not an estimate of the physical edge's accuracy or an edited PSB mask.
Only boundary pixels require subpixel quadrature; all other pixels are exact
zero/one for the supplied radial polygon. Test4 reproduces B0/B1 exactly.
"""
from forward_model import *
from scipy.fft import dctn,idctn
import time
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
y,x=np.mgrid[:N,:N];xx=x-CX;yy=y-CY
def radius(xx,yy):
    t=(np.arctan2(yy,xx)%(2*np.pi))*len(edge)/(2*np.pi);j=np.floor(t).astype(int);u=t-j
    return edge[j]*(1-u)+edge[(j+1)%len(edge)]*u
rr=radius(xx,yy);rad=np.hypot(xx,yy)
# The radial function's Lipschitz bound plus the pixel half diagonal is <1px.
# The generous3px strip is verified using the original whole-grid4x4 result.
band=abs(rr-rad)<3;bx=xx[band];by=yy[band]
def area(q):
    p=(rad<rr).astype(float);v=(np.arange(q)+.5)/q-.5;oy,ox=np.meshgrid(v,v,indexing='ij');ox=ox.ravel();oy=oy.ravel();values=np.empty(len(bx))
    for i in range(0,len(bx),64):
        u=bx[i:i+64,None]+ox;v=by[i:i+64,None]+oy
        values[i:i+64]=np.mean(np.hypot(u,v)<radius(u,v),axis=1)
    p[band]=values;return p
start=time.time();P4=area(4);assert np.array_equal(P4,silhouette())
P16=area(16);P64=area(64);P128=area(128)
sigma=np.sqrt(1.5140726846997261**2-1/12);f=np.arange(N)/(2*N);H=np.exp(-2*np.pi**2*sigma**2*(f[:,None]**2+f[None,:]**2))
conv=lambda a:idctn(dctn(a,type=2,norm='ortho')*H,type=2,norm='ortho')
checks=[]
for q,p in [(4,P4),(16,P16),(64,P64)]:
    d=p-P128;pred=conv(d)*(500-100000)
    checks.append(dict(samples_per_axis=q,pixel_area_abs_error_quantiles=np.percentile(abs(d[band]),[50,90,99,100]).tolist(),constant_step_prediction_error_G_quantiles=np.percentile(abs(pred[abs(rad-rr)<8]),[50,90,99,100]).tolist()))
np.savez_compressed(OUT/'A1_occlusion_area.npz',P4=P4,P16=P16,P64=P64,P128=P128)
save('A1_occlusion_area.json',dict(method=__doc__,boundary_pixels=int(band.sum()),seconds=time.time()-start,original_4x4_reproduced_exactly=True,synthetic_step=dict(lunar_G=500,solar_G=100000,core_sigma=sigma),checks=checks,limits=['Only quadrature convergence on the supplied observed edge, not physical geometric truth','The constant step is a numerical diagnostic, not recovered lunar data','No source pixel, PSB mask, FOV, or image sampling grid changed']))
print(json.dumps(checks,indent=2),flush=True)
