"""Continue the existing static control to its unchanged KKT threshold."""
from fit_system import *
from scipy.optimize import minimize
import time
s=build('static');z=np.load(OUT/'B1_static_scene.npz');assert np.array_equal(z['scale'],s.scale) and np.array_equal(z['lunar_indices'],s.mi) and np.array_equal(z['solar_indices'],s.ci)
start=time.time();opt=minimize(s.objective,z['u'],method='L-BFGS-B',jac=True,bounds=[(0,None)]*len(s.rhs),options={'maxiter':1000,'maxcor':30,'ftol':0,'gtol':1e-7,'maxls':50});f,g=s.objective(opt.x);pg=np.where((opt.x<=1e-10)&(g>0),0,g);kkt={k:float(np.max(abs(pg[a]))/max(np.max(abs(s.rhs[a])),1)) for k,a in [('lunar',slice(None,len(s.mi))),('solar',slice(len(s.mi),None))]}
v=opt.x*s.scale;lunar=np.zeros(s.geo.size);solar=lunar.copy();lunar[s.mi]=v[:len(s.mi)]*s.ms;solar[s.ci]=v[len(s.mi):]*s.cs;pred={};changes={}
for r in s.rows:
    stem=r['stem'];p=load_npz(s.folder/f'{stem}_lunar.npz')@lunar+load_npz(s.folder/f'{stem}_solar_static.npz')@solar;pred[stem]=p;changes[stem]=float(np.max(abs(p-z[stem])))
receipt=dict(method=__doc__,success=bool(opt.success),message=str(opt.message),iterations=int(opt.nit),objective=float(opt.fun),max_projected_gradient=float(abs(pg).max()),kkt_by_block=kkt,numerical_PASS=max(kkt.values())<1e-6,prediction_change_max_G=changes,seconds=time.time()-start,scope='Numerical refinement of static control only, no physical validation')
np.savez_compressed(OUT/'B2_static_refined.npz',lunar=lunar.reshape(s.geo.shape),solar=solar.reshape(s.geo.shape),u=opt.x,**pred);save('B2_static_refined.json',receipt);print(receipt,flush=True);assert receipt['numerical_PASS']
