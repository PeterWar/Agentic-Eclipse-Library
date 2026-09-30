"""Native-green mixture inverse: numerical step and texture injection checks.
Synthetic scenes are validation phantoms only, never lunar source material.
Compare with the known narrow-core image, not the unblurred latent terrain.
"""
from scatter_common import *
import sys,time
sys.path.insert(0,str(ROOT/'research/tools/earthshine_native_psf_20260911'))
from quincunx import interpolate
from scipy.fft import rfftn,irfftn,fftfreq,rfftfreq
from scipy.ndimage import map_coordinates,gaussian_filter,spline_filter
from numpy.polynomial.legendre import leggauss
p=json.loads((OUT/'B1_physical_mixture.json').read_text())['p'];a=p/(1-p);coeff=np.array([a,-a*a,a**3,-a**4]);step=.25;x0,y0,x1,y1=960,520,1330,880;xx=np.arange(x0,x1,step);yy=np.arange(y0,y1,step);Y,X=np.meshgrid(yy,xx,indexing='ij');radius=np.hypot(X-CX,Y-CY);angle=np.arctan2(Y-CY,X-CX)%(2*np.pi);edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');limb=np.interp(angle,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);P=radius<limb
fx=rfftfreq(len(xx),d=step);fy=fftfreq(len(yy),d=step);f2=fy[:,None]**2+fx[None,:]**2;Hc=np.exp(-2*np.pi**2*.97**2*f2);Hb=np.exp(-2*np.pi**2*12**2*f2)
solar=100000*(1+.0006*(X-1153)+.0003*(Y-700))+70000*np.exp(-((X-1159)**2+(Y-686)**2)/(2*8**2));baseline=np.where(P,650.,solar)
save('C0_injection_plan.json',dict(method=__doc__,physical_wing_p=p,core_sigma=.97,incremental_wing_sigma=12,continuous_scene_grid_step=step,point_spread='Fourier Gaussian convolution, far padded local field',pixel_aperture='GL4x4 in native unit pixel; compare GL6 at a subset',sampling='Actual native green-lattice affine phase from2976 and2994; positive quincunx interpolation only for broad terms',signals='Baseline lunar650/solar100000+prominence; added lunar25G sinusoid at8,16,32px and oblique orientation',gates='Recovered narrow-core baseline RMS<2G at native r435-453; signal gain0.995..1.005 and relativeRMS<0.01 for all signals/phases; apertureGL4-vsGL6<0.10G. No physical-PSF identification claim.'))
node,weight=leggauss(4);ox,oy=np.meshgrid(node/2,node/2);weights=(weight[:,None]*weight[None,:]/4).ravel();offsets=np.stack([ox.ravel(),oy.ravel()],1)
def samples(field,points,J,order=4):
    nn,ww=leggauss(order);ox,oy=np.meshgrid(nn/2,nn/2);wt=(ww[:,None]*ww[None,:]/4).ravel();off=np.stack([ox.ravel(),oy.ravel()],1)@J.T;pref=spline_filter(field,order=3);result=np.zeros(len(points))
    for delta,w in zip(off,wt):result+=w*map_coordinates(pref,[(points[:,1]+delta[1]-y0)/step,(points[:,0]+delta[0]-x0)/step],order=3,mode='nearest',prefilter=False)
    return result
def render(F):
    z=rfftn(F);core=irfftn(z*Hc,s=F.shape);observed=irfftn(z*Hc*((1-p)+p*Hb),s=F.shape);return core,observed
basex,basey=render(baseline);worldy,worldx=np.mgrid[y0:y1,x0:x1];world=np.stack([worldx.ravel(),worldy.ravel()],1);results=[];scenes=[dict(name='baseline',lam=None,angle=0)]
scenes += [dict(name=f'texture{lam}',lam=lam,angle=.37) for lam in [8,16,32]]
for stem in ['572A2976','572A2994']:
    z=np.load(SRC/f'A0_native_samples_{stem}.npz');J=z['native_to_world'];origin=np.array([z['x'][0],z['y'][0]])-J@np.array([z['native_x'][0],z['native_y'][0]]);native=(world-origin)@np.linalg.inv(J).T;u=(native[:,0]+native[:,1]-1)/2;v=(native[:,0]-native[:,1]-1)/2;u0=int(np.floor(u.min()))-3;u1=int(np.ceil(u.max()))+3;v0=int(np.floor(v.min()))-3;v1=int(np.ceil(v.max()))+3;V,U=np.mgrid[v0:v1+1,u0:u1+1];nxy=np.stack([(1+U+V).ravel(),(U-V).ravel()],1);points=nxy@J.T+origin;rad=np.hypot(points[:,0]-CX,points[:,1]-CY);test=(rad>=435)&(rad<453)&(points[:,0]>=1117)&(points[:,0]<1187)&(points[:,1]>=630)&(points[:,1]<770);base_rec=None;base_truth=None
    for scene in scenes:
        start=time.time();F=baseline if scene['lam'] is None else baseline+np.where(P,25*np.sin(2*np.pi*((X-1100)*np.cos(scene['angle'])+(Y-700)*np.sin(scene['angle']))/scene['lam']),0)
        core,observed=(basex,basey) if scene['lam'] is None else render(F);g=samples(observed,points,J);truth=samples(core,points,J);matrix=g.reshape(U.shape);one=np.ones(U.shape);mapped,_=interpolate(matrix,one,one,np.zeros(U.shape,bool),u.reshape(worldx.shape),v.reshape(worldy.shape),u0,v0);assert np.isfinite(mapped['g']).all();correction=np.zeros(len(points))
        for k,c in enumerate(coeff,1):
            b=gaussian_filter(mapped['g'],12*np.sqrt(k),truncate=5,mode='nearest');correction+=c*map_coordinates(b,[points[:,1]-y0,points[:,0]-x0],order=1,mode='nearest',prefilter=False)
        recovered=(g-correction)/(1-p);error=recovered[test]-truth[test]
        if scene['lam'] is None:
            base_rec=recovered.copy();base_truth=truth.copy();subset=points[test][::30];aperture=float(np.max(abs(samples(core,subset,J,4)-samples(core,subset,J,6))));row=dict(stem=stem,scene=scene['name'],native_samples=int(test.sum()),rms_G=float(np.sqrt(np.mean(error**2))),max_abs_G=float(abs(error).max()),aperture_4_vs_6_max_G=aperture,PASS=bool(np.sqrt(np.mean(error**2))<2 and aperture<.1))
        else:
            expected=(truth-base_truth)[test];actual=(recovered-base_rec)[test];gain=float(expected@actual/(expected@expected));relative=float(np.linalg.norm(actual-expected)/np.linalg.norm(expected));row=dict(stem=stem,scene=scene['name'],native_samples=int(test.sum()),signal_gain=gain,relative_RMS_error=relative,PASS=bool(.995<=gain<=1.005 and relative<.01))
        row['seconds']=time.time()-start;results.append(row);save('C0_native_injection.json',dict(method=__doc__,tests=results,all_pass=all(r['PASS'] for r in results),scope='Numerical operator and known synthetic texture recovery only; no astronomical texture generated or introduced'));print(json.dumps(row),flush=True)
print('DONE',len(results),'PASS',all(r['PASS'] for r in results),flush=True)
