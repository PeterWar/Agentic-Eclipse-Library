"""Descriptive source profiles after the all88 ordinary-CFA correction.
Use the same complete tangent columns throughout each radial fitting window,
so a changing saturation footprint cannot become an apparent limb profile.
No source pixel, geometry, mask or PSB is modified.
"""
from optics_common import *
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares
from scipy.special import ndtr
import warnings

old=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames']
meta={(m['tren'],m['stem']):m for m in old}
frames=json.loads((SRC/'B0_all_native.json').read_text())['frames']
frames.sort(key=lambda m:(m['tren'],meta[m['tren'],m['stem']]['t_mid_C2']))
angles=np.arange(0.,360.,7.5);dist=np.arange(-70.,40.01,.5);tangent=np.arange(-20.,20.01,2.)
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
rad=np.interp(angles*4,np.arange(len(edge)),edge)
th=np.deg2rad(angles)[:,None,None];rr=rad[:,None,None]+dist[None,:,None]
xx=CX+rr*np.cos(th)-tangent*np.sin(th);yy=CY+rr*np.sin(th)+tangent*np.cos(th)
co=np.array([np.broadcast_to(yy,xx.shape),xx])
core=(dist>=-18)&(dist<=18);wing=(dist>=-60)&(dist<=30)
records=[];profiles=[];errors=[];counts=[];fits=[]

def fit_core(x,y,noise):
    b=float(np.median(y[x<-10]));amplitude=float(np.median(y[x>10])-b)
    if not np.isfinite(amplitude) or amplitude<=0:return None
    yn=(y-b)/amplitude;err=np.maximum(noise/amplitude,.005)
    # Convolution of a step plus different linear backgrounds with a Gaussian.
    # All brightness and slopes are nuisance parameters, not imposed darkness.
    def model(p):
        bg,mi,A,dm,c,s=p;t=x-c;F=ndtr(t/s);phi=np.exp(-.5*(t/s)**2)/np.sqrt(2*np.pi)
        return bg+mi*t+A*F+dm*(t*F+s*phi)
    fun=lambda p:(model(p)-yn)/err
    p0=[0,0,1,0,0,2]
    fit=least_squares(fun,p0,bounds=([-1,-.2,.1,-.3,-8,.35],[1,.2,5,.3,8,12]),loss='soft_l1',f_scale=2,max_nfev=180)
    p=fit.x;res=model(p)-yn
    return dict(center=float(p[4]),sigma=float(p[5]),fwhm=float(2.354820045*p[5]),relative_rms=float(np.sqrt(np.mean(res**2))),amplitude=amplitude,inside_level=b,inside_slope=float(p[1]*amplitude),outside_slope=float((p[1]+p[3])*amplitude),success=bool(fit.success),at_bound=bool(abs(p[4])>7.9 or p[5]>.99*12 or p[5]<.36),parameters=p.tolist())

for j,m in enumerate(frames):
    z=np.load(m['file']);g=z['g'];valid=np.isfinite(g)&(z['q']>0);var=z['variance']
    v=map_coordinates(valid.astype(float),co,order=1,mode='constant',cval=0)>.999
    p=map_coordinates(np.nan_to_num(g),co,order=1,mode='nearest')
    ev=map_coordinates(np.nan_to_num(var,nan=1e30),co,order=1,mode='nearest')
    allp=[];alle=[];alln=[];frame_fits=[]
    for k,angle in enumerate(angles):
        col=np.all(v[k,core],axis=0);n=int(col.sum());colw=np.all(v[k,wing],axis=0)
        prof=np.full(len(dist),np.nan);err=prof.copy()
        if n>=6:
            values=p[k][:,col];safe=np.all(v[k][:,col],axis=1)
            prof[safe]=np.median(values[safe],axis=1)
            # Tangent structure is real scene variation, retained as a nuisance
            # uncertainty; interpolation covariance forbids chi-square claims.
            scatter=1.4826*np.median(abs(values-prof[:,None]),axis=1)
            stat=np.sqrt(np.median(ev[k][:,col],axis=1)/n)
            err[safe]=np.maximum(scatter[safe]/np.sqrt(n),stat[safe])
            f=fit_core(dist[core],prof[core],err[core])
        else:f=None
        info=dict(angle=float(angle),complete_core_columns=n,complete_wing_columns=int(colw.sum()),fit=f)
        if f:
            # Descriptive normalized observed wing, not a PSF or subtraction.
            for lo,hi in [(-50,-40),(-30,-20),(-15,-10),(-8,-4)]:
                select=(dist>=lo)&(dist<=hi)&np.isfinite(prof)
                info[f'observed_{lo}_{hi}']=float(np.median(prof[select])) if select.sum()>=5 else None
        frame_fits.append(info);allp.append(prof);alle.append(err);alln.append(n)
    mm=meta[m['tren'],m['stem']];records.append(dict(stem=m['stem'],tren=m['tren'],exp=m['exp'],time_C2=mm['t_mid_C2'],group=m['group'],profile_index=j,raw_sha256=m['raw_sha256']))
    fits.append(dict(**records[-1],sectors=frame_fits));profiles.append(allp);errors.append(alle);counts.append(alln)
    if (j+1)%8==0 or j==len(frames)-1:print('PROFILES',j+1,len(frames),'fits',sum(x['fit'] is not None for x in frame_fits),flush=True)
np.savez_compressed(OUT/'A0_profiles.npz',angles=angles,distance=dist,tangent=tangent,g=np.array(profiles),error=np.array(errors),complete_columns=np.array(counts))
save('A0_profiles.json',dict(method=__doc__,frames=fits,core_window=[-18,18],wing_window=[-60,30],model='Gaussian convolved step and two independent linear backgrounds; descriptive only',limits=['Fits include seeing, illumination changes, CFA sampling and residual registration; no uniquely identified PSF','Fixed complete tangent columns, minimum6; partial saturated radial profiles never fitted','No source modification, deconvolution or halo subtraction','No formal chi-square confidence because interpolation and tangent samples correlate']))
print('DONE88',flush=True)
