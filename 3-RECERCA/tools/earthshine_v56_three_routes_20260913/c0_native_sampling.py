"""Native CFA sampling identifiability, without an optical-resolution claim."""
from common import *
claim();fs=[m for m in frames() if m['tren']=='vixen'];rows=[];ph=[];long=[]
for i,m in enumerate(fs):
 A=np.array(m['roi_to_native']);centre=A@np.array([CX,CY,1]);z=np.load(m['detector_file']);phases=[]
 for c in ['G1','G2']:
  p=((z[c+'_origin']-centre)/2)%1;ph.append(p);long.append(m['exp']>=.5);phases.append(p)
 rows.append(dict(stem=m['stem'],exposure=m['exp'],phases=phases,native_to_world=np.linalg.inv(A[:,:2])))
ph=np.array(ph);freq=np.array([[0,0],[1,0],[0,1],[1,1]]);M=np.exp(2j*np.pi*(ph@freq.T));res=[]
for name,sel in [('all',np.ones(len(M),bool)),('long',np.array(long))]:
 s=np.linalg.svd(M[sel],compute_uv=False);res.append(dict(subset=name,observations=int(sel.sum()),singular_values=s,condition=float(s[0]/s[-1]),rank=int(np.sum(s>s[0]*1e-8))))
save('C0_native_sampling.json',dict(frames=rows,modes=freq,results=res,limits=['Sampling phase rank only, not a reconstructed image or resolution gain','Native pixel integration/geometry/calibration and independent source gates remain necessary','Two CFA greens and epochs share detector/calibration; not independent sensors'],next='Positive integration of pixel footprint onto same native-scale scene grid; no optical deconvolution or product resampling.'))
print('NATIVE SAMPLING',res,flush=True)
