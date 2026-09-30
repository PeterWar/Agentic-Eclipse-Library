"""Compare cascade inversion on the native green lattice and resampled predictors.
Synthetic validation phantoms only; no generated astronomical source material.
The measured green quincunx is a square lattice with sqrt(2) native-pixel pitch.
"""
from intermediate_common import *
import sys,time,ast
sys.path.insert(0,str(ROOT/'research/tools/earthshine_native_psf_20260911'))
from quincunx import interpolate
from scipy.fft import rfftn,irfftn,fftfreq,rfftfreq
from scipy.ndimage import map_coordinates,gaussian_filter,spline_filter
from numpy.polynomial.legendre import leggauss
p4=json.loads((OUT/'B1_physical_cascade.json').read_text())['p4'];a12=P12/(1-P12);a4=p4/(1-p4);terms=[(np.sqrt(144*j+16*k),(-a12)**j*(-a4)**k) for j in range(5) for k in range(6) if j+k>0];norm=(1-P12)*(1-p4);step=.25;x0,y0,x1,y1=960,520,1330,880;xx=np.arange(x0,x1,step);yy=np.arange(y0,y1,step);Y,X=np.meshgrid(yy,xx,indexing='ij');radius=np.hypot(X-CX,Y-CY);angle=np.arctan2(Y-CY,X-CX)%(2*np.pi);edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');limb=np.interp(angle,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);P=radius<limb;fx=rfftfreq(len(xx),d=step);fy=fftfreq(len(yy),d=step);f2=fy[:,None]**2+fx[None,:]**2;Hc=np.exp(-2*np.pi**2*.97**2*f2);H12=np.exp(-2*np.pi**2*144*f2);H4=np.exp(-2*np.pi**2*16*f2);solar=100000*(1+.0006*(X-1153)+.0003*(Y-700))+70000*np.exp(-((X-1159)**2+(Y-686)**2)/(2*8**2));baseline=np.where(P,650.,solar)
save('C0_native_plan.json',dict(method=__doc__,p12=P12,p4=p4,core_sigma=.97,continuous_grid_step=.25,native_phases=['572A2976','572A2994'],pixel_aperture='GL4x4 with GL6 subset comparison',operators=['Resampled observed predictor Gaussian on world grid','Direct Gaussian on native green lattice with sigma divided bysqrt2; final values stay native'],gates='Same native validation limits as prior broad candidate: baseline RMS<2G at435-453px; GL4-vsGL6<0.1G; texture gain0.995..1.005 and relativeRMS<0.01.',scope='Operator arithmetic only. No measured astronomical texture is replaced. The temporal cascade gate remains separate and may fail.'))
tree=ast.parse((ROOT/'research/tools/earthshine_scatter_witness_20260911/c0_native_injection.py').read_text());fn=next(r for r in tree.body if isinstance(r,ast.FunctionDef) and r.name=='samples');exec(compile(ast.Module(body=[fn],type_ignores=[]),'frozen_GL_native_aperture','exec'))
def render(F):
    z=rfftn(F);return irfftn(z*Hc,s=F.shape),irfftn(z*Hc*((1-P12)+P12*H12)*((1-p4)+p4*H4),s=F.shape)
basex,basey=render(baseline);wy,wx=np.mgrid[y0:y1,x0:x1];world=np.stack([wx.ravel(),wy.ravel()],1);results=[];scenes=[dict(name='baseline',lam=None)]+[dict(name=f'texture{lam}',lam=lam) for lam in [8,16,32]]
for stem in ['572A2976','572A2994']:
    z=np.load(SRC/f'A0_native_samples_{stem}.npz');J=z['native_to_world'];assert np.max(abs(J.T@J-np.eye(2)))<1e-8;origin=np.array([z['x'][0],z['y'][0]])-J@np.array([z['native_x'][0],z['native_y'][0]]);native=(world-origin)@np.linalg.inv(J).T;u=(native[:,0]+native[:,1]-1)/2;v=(native[:,0]-native[:,1]-1)/2;u0=int(np.floor(u.min()))-3;u1=int(np.ceil(u.max()))+3;v0=int(np.floor(v.min()))-3;v1=int(np.ceil(v.max()))+3;V,U=np.mgrid[v0:v1+1,u0:u1+1];nxy=np.stack([(1+U+V).ravel(),(U-V).ravel()],1);points=nxy@J.T+origin;rad=np.hypot(points[:,0]-CX,points[:,1]-CY);test=(rad>=435)&(rad<453)&(points[:,0]>=1117)&(points[:,0]<1187)&(points[:,1]>=630)&(points[:,1]<770);base_rec={};base_truth=None
    for scene in scenes:
        start=time.time();F=baseline if scene['lam'] is None else baseline+np.where(P,25*np.sin(2*np.pi*((X-1100)*np.cos(.37)+(Y-700)*np.sin(.37))/scene['lam']),0);core,observed=(basex,basey) if scene['lam'] is None else render(F);g=samples(observed,points,J);truth=samples(core,points,J);matrix=g.reshape(U.shape);one=np.ones(U.shape);mapped,_=interpolate(matrix,one,one,np.zeros(U.shape,bool),u.reshape(wx.shape),v.reshape(wy.shape),u0,v0);assert np.isfinite(mapped['g']).all();rec_world=g.copy();rec_native=g.copy()
        for sigma,coef in terms:
            b=gaussian_filter(mapped['g'],sigma,truncate=5,mode='nearest');rec_world+=coef*map_coordinates(b,[points[:,1]-y0,points[:,0]-x0],order=1,mode='nearest',prefilter=False);rec_native+=coef*gaussian_filter(matrix,sigma/np.sqrt(2),truncate=5,mode='nearest').ravel()
        for name,recovered in [('world_predictors',rec_world/norm),('native_lattice',rec_native/norm)]:
            error=recovered[test]-truth[test]
            if scene['lam'] is None:
                base_rec[name]=recovered.copy();base_truth=truth.copy();subset=points[test][::30];aperture=float(np.max(abs(samples(core,subset,J,4)-samples(core,subset,J,6))));rms=float(np.sqrt(np.mean(error**2)));row=dict(stem=stem,operator=name,scene=scene['name'],native_samples=int(test.sum()),rms_G=rms,max_abs_G=float(abs(error).max()),aperture_4_vs_6_max_G=aperture,PASS=bool(rms<2 and aperture<.1))
            else:
                expected=(truth-base_truth)[test];actual=(recovered-base_rec[name])[test];gain=float(expected@actual/(expected@expected));rel=float(np.linalg.norm(actual-expected)/np.linalg.norm(expected));row=dict(stem=stem,operator=name,scene=scene['name'],native_samples=int(test.sum()),signal_gain=gain,relative_RMS_error=rel,PASS=bool(.995<=gain<=1.005 and rel<.01))
            row['seconds']=time.time()-start;results.append(row);save('C0_native_lattice_check.json',dict(method=__doc__,tests=results,operators=[dict(name=n,all_PASS=all(r['PASS'] for r in results if r['operator']==n)) for n in ['world_predictors','native_lattice']],scope='Numerical known-scene validation only; no eclipse source generated or altered'));print(json.dumps(row),flush=True)
print('DONE',len(results),flush=True)
