from common58 import *
import ast
from scipy.optimize import nnls
claim();tree=ast.parse((T/'d3_empirical_stars.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='extract_empirical');rad=32;yy,xx=np.mgrid[-rad:rad+1,-rad:rad+1];rr=np.hypot(xx,yy);X=np.stack([np.ones_like(xx),xx/rad,yy/rad,(xx/rad)**2,xx*yy/rad**2,(yy/rad)**2],axis=-1);ann=(rr>=16)&(rr<30);valid=rr<22;nodes=np.arange(-6,7,3);G=np.stack([np.exp(-((xx-a)**2+(yy-b)**2)/8.) for a in nodes for b in nodes],axis=-1);D=G[valid];exec(compile(ast.Module(body=[fn],type_ignores=[]),'empirical','exec'));data=np.load(O/'arrays/D3_empirical_pilot.npz')['before'];rep=[]
for idx in [0,1,12,30,39]:
 q=data[idx];comp,_=extract_empirical(q);comp[rr>=22]=0;clean=q-comp;noise=1.4826*np.median(np.abs((q-gaussian_filter(q,1))[ann]))
 for lam in [24.,40.,64.,96.]:
  for deg in [0,45,90]:
   for phase in [0,np.pi/2]:
    sig=.2*noise*np.sin(2*np.pi*(xx*np.cos(np.deg2rad(deg))+yy*np.sin(np.deg2rad(deg)))/lam+phase);cc,_=extract_empirical(q+sig);cc[rr>=22]=0;diff=(q+sig-cc)-clean;gain=float(np.sum(diff*sig)/np.sum(sig*sig));outside=float(np.max(np.abs((diff-sig)[rr>=22])));rep.append(dict(star=idx,wavelength=lam,angle=deg,phase=phase,gain_whole_patch=gain,uncontaminated_max_error=outside,PASS=.9<=gain<=1.1))
save('D5_star_injections.json',dict(rows=rep,whole_patch_pass=sum(r['PASS'] for r in rep),n=len(rep),outside_exact_to_float=max(r['uncontaminated_max_error'] for r in rep),note='Weak injected corona over full 65x65 patch. The measured stellar footprint remains excluded from claims of recovered coronal detail.'));print('gain',min(r['gain_whole_patch'] for r in rep),max(r['gain_whole_patch'] for r in rep),'pass',sum(r['PASS'] for r in rep),'of',len(rep))
