"""Numerical native-operator qualification before fitting any real scene.
Known constants and affine fields, adjoint identities, quadrature refinement
and sharp synthetic lunar/solar scenes. Does not validate the physical PSF.
"""
from native_operator import *
from scipy.sparse import save_npz
import time
start=time.time();geo=Geometry(PLAN['limb_polygon_refinement']);rows,reference=source_rows();m=next(m for m in rows if m['stem']=='572A2976');data=observed(m);points=data['xy'];J=data['J'];sigma=PLAN['gaussian_optical_sigma_assumed']
qm=geo.quadrature(order=4);qc=geo.quadrature(m['solar_shift'],inside=False,order=4);print('QUADRATURE',len(qm[0]),len(qc[0]),'samples',len(points),'seconds',time.time()-start,flush=True)
A=response_matrix(points,J,qm,sigma);B=response_matrix(points,J,qc,sigma);print('MATRICES',A.shape,A.nnz,B.nnz,time.time()-start,flush=True)
one=np.ones(geo.size);sums=A@one+B@one;constant_error=float(np.max(abs(sums-1)))
ny,nx=geo.shape;y,x=np.mgrid[:ny,:nx];x=x.ravel()+geo.box[0];y=y.ravel()+geo.box[1];affineM=(x-1150)+.3*(y-700);affineC=affineM+m['solar_shift'][0]+.3*m['solar_shift'][1];prediction=A@affineM+B@affineC;affine_error=float(np.max(abs(prediction-((points[:,0]-1150)+.3*(points[:,1]-700)))))
assert constant_error<1e-6 and affine_error<1e-4,(constant_error,affine_error)
rng=np.random.default_rng(114999);v=rng.normal(size=2*geo.size);z=rng.normal(size=len(points));lhs=np.dot(A@v[:geo.size]+B@v[geo.size:],z);rhs=np.dot(v,np.r_[A.T@z,B.T@z]);adjoint_error=float(abs(lhs-rhs)/max(abs(lhs),abs(rhs),1));assert adjoint_error<1e-12
# Stratify by distance to the supplied limb, including the sharp transition.
distance=points[:,0]-geo.border(points[:,1]);chosen=[]
for lo,hi in [(-35,-8),(-8,-2),(-2,2),(2,8),(8,35)]:
    ids=np.flatnonzero((distance>=lo)&(distance<hi));chosen.extend(ids[np.linspace(0,len(ids)-1,min(30,len(ids)),dtype=int)].tolist())
chosen=np.unique(chosen);fine=Geometry(64);qmf=fine.quadrature(order=6);qcf=fine.quadrature(m['solar_shift'],inside=False,order=6);Af=response_matrix(points[chosen],J,qmf,sigma);Bf=response_matrix(points[chosen],J,qcf,sigma)
fixtures={'constant_step':(np.full(geo.size,500.),np.full(geo.size,100000.)),'affine_step':(500.+2*(x-1150)+.5*(y-700),100000.+100*(x-1150)+40*(y-700)),'fine_texture':(500.+25*np.sin((x+y)*2*np.pi/6),100000.+5000*np.sin(x*2*np.pi/8)*np.cos(y*2*np.pi/10))}
tests=[]
for name,(M,C) in fixtures.items():
    p=A[chosen]@M+B[chosen]@C;q=Af@M+Bf@C;d=p-q;tests.append(dict(fixture=name,max_error_G=float(abs(d).max()),rms_error_G=float(np.sqrt(np.mean(d*d))),median_error_G=float(np.median(d))))
assert max(t['max_error_G'] for t in tests)<1.,tests
save_npz(OUT/'A0_2976_lunar.npz',A);save_npz(OUT/'A0_2976_solar.npz',B);np.savez_compressed(OUT/'A0_2976_observations.npz',**data,solar_shift=m['solar_shift'],solar_reference=reference)
save('A0_operator_pilot.json',dict(method=__doc__,frame=m['stem'],shape=geo.shape,samples=len(points),nnz=[A.nnz,B.nnz],constant_max_error=constant_error,affine_max_error=affine_error,adjoint_relative_error=adjoint_error,refined_samples=len(chosen),refinement_tests=tests,positive_matrix_coefficients=True,seconds=time.time()-start,PASS=True,limits=['Numerical operator qualification only; sigma0.97 and observed opaque contour remain assumptions','Gaussian core does not include independently measured broad optical wings','No native source altered and no fitted lunar image or new PSB yet']))
print('PASS',json.dumps(tests),flush=True)
