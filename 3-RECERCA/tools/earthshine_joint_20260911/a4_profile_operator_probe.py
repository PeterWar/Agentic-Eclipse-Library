"""Known-blur injection through the actual A0 profile-measurement operator.
The synthetic two-level scene calibrates diagnostic bias only. It supplies no
pixels to a reconstruction and cannot identify the real optical PSF uniquely.
"""
from joint_common import *
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares
from scipy.special import ndtr
from scipy.fft import dctn,idctn
import ast

source=ROOT/'research/tools/earthshine_optics_20260911/a0_profiles.py';tree=ast.parse(source.read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fit_core')
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'))
old=json.loads((OPT/'A0_profiles.json').read_text())['frames'];counts=np.zeros(48,dtype=int)
for row in old:
    if row['tren']!='vixen' or not any(np.isclose(row['exp'],e) for e in [.0005,.001,.002]):continue
    for k,s in enumerate(row['sectors']):
        f=s['fit']
        if f and f['success'] and not f['at_bound'] and f['relative_rms']<.03:counts[k]+=1
target=json.loads((OPT/'A1_core_prediction.json').read_text())['models']['vixen']['constant_sigma']
with np.load(OUT/'A2_occlusion_polygon.npz') as z:P=z['P64']
scene=P*500+(1-P)*100000
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
angles=np.arange(0.,360.,7.5);dist=np.arange(-18.,18.01,.5);tangent=np.arange(-20.,20.01,2.)
rad=np.interp(angles*4,np.arange(len(edge)),edge);th=np.deg2rad(angles)[:,None,None];rr=rad[:,None,None]+dist[None,:,None]
xx=CX+rr*np.cos(th)-tangent*np.sin(th);yy=CY+rr*np.sin(th)+tangent*np.cos(th);co=np.array([np.broadcast_to(yy,xx.shape),xx])
freq=np.arange(N)/(2*N);f2=freq[:,None]**2+freq[None,:]**2;F=dctn(scene,type=2,norm='ortho');results=[]
for sigma in [1.,1.2,1.4,float(np.sqrt(target**2-1/12)),1.6]:
    g=idctn(F*np.exp(-2*np.pi**2*sigma*sigma*f2),type=2,norm='ortho')
    samples=map_coordinates(g,co,order=1,mode='nearest');fits=[]
    for k,values in enumerate(samples):
        prof=np.median(values,axis=1);scatter=1.4826*np.median(abs(values-prof[:,None]),axis=1)
        error=scatter/np.sqrt(len(tangent));fit=fit_core(dist,prof,error);fits.append(fit)
    # Match the angular multiplicities used by the actual short-frame estimate.
    sigmas=np.repeat([f['sigma'] for f in fits],counts)
    results.append(dict(injected_source_grid_sigma=sigma,measured_sigma_matching_training_angles=float(np.median(sigmas)),measured_sigma_quantiles=np.percentile(sigmas,[10,50,90]).tolist(),fits=fits))
    print('PROFILE OPERATOR',sigma,results[-1]['measured_sigma_matching_training_angles'],flush=True)
measured=np.array([a['measured_sigma_matching_training_angles'] for a in results]);physical=np.array([a['injected_source_grid_sigma'] for a in results]);assert np.all(np.diff(measured)>0)
bracket=measured.min()<=target<=measured.max();estimate=float(np.interp(target,measured,physical)) if bracket else None
assert bracket
g=idctn(F*np.exp(-2*np.pi**2*estimate*estimate*f2),type=2,norm='ortho');samples=map_coordinates(g,co,order=1,mode='nearest');validation=[]
for values in samples:
    prof=np.median(values,axis=1);scatter=1.4826*np.median(abs(values-prof[:,None]),axis=1);validation.append(fit_core(dist,prof,scatter/np.sqrt(len(tangent)))['sigma'])
validated=float(np.median(np.repeat(validation,counts)));assert abs(validated-target)<.001
save('A4_profile_operator_probe.json',dict(method=__doc__,profile_function_sha256=hashlib.sha256(ast.get_source_segment(source.read_text(),fn).encode()).hexdigest(),source_profile_function=str(source),target_observed_sigma=target,angular_training_profile_count=int(counts.sum()),angular_counts=counts.tolist(),probes=results,bracketed=bool(bracket),inverse_mapping_estimate=estimate,inverse_validation=dict(measured_sigma=validated,error=validated-target,PASS=True),limits=['Synthetic uniform interior/exterior on the supplied optical silhouette, without real illumination gradients or noise','Calibrates the diagnostic sampling operator and curvature mixture; not a native-CFA or end-to-end PSF determination','No real lunar texture injection, no new image, no basis to declare recovery or overwrite V48']))
print('INVERSE MAPPING',estimate,'target',target,flush=True)
